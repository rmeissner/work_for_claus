"""Board and recessed-role cylinders for RPS Flag Hunt, in millimeters.

Print and play with the circular base at Z = 0. The engraved side faces -Y.
"""

import sys
from pathlib import Path

from manifold3d import CrossSection, Manifold, OpType

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import assert_printable, bar, extrude, layout_on_plate, ring, write_stl
from stlkit.text import text_shape

BODY_DIAMETER = 20.0
BODY_HEIGHT = 50.0
FOOT_HEIGHT = 10.0
FLAT_Y = -4.0
MARK_Z = 30.0
MARK_SCALE = 1.5
ENGRAVING_DEPTH = 0.8

TEAM_COUNTS = {"rock": 4, "paper": 4, "scissors": 4, "bomb": 1, "flag": 1}

BOARD_COLUMNS = 7
BOARD_ROWS = 6
DEPLOYMENT_ROWS = 2
CELL_PITCH = 20.0
BOARD_BORDER = 4.0
BOARD_HEIGHT = 3.2
BOARD_WALL_FRACTION = 0.30
SEAT_DEPTH = 0.8
SEAT_CLEARANCE = 0.2  # Radial clearance around the 20 mm foot.
SEAT_BEVEL = 0.4
MARKER_WIDTH = 1.4
TEST_IMPRINT_DEPTH = 0.6


def build_board(
    columns: int = BOARD_COLUMNS,
    rows: int = BOARD_ROWS,
    *,
    deployment_rows: int = DEPLOYMENT_ROWS,
) -> Manifold:
    field_width = columns * CELL_PITCH
    field_depth = rows * CELL_PITCH
    width = field_width + 2 * BOARD_BORDER
    depth = field_depth + 2 * BOARD_BORDER
    outline = CrossSection.square((width, depth), center=True)
    wall_height = BOARD_HEIGHT * BOARD_WALL_FRACTION
    bevel_height = BOARD_HEIGHT - wall_height
    # A 45° bevel steps in horizontally by its height on each side.
    rim = Manifold.extrude(
        outline,
        bevel_height,
        scale_top=(
            (width - 2 * bevel_height) / width,
            (depth - 2 * bevel_height) / depth,
        ),
    ).translate((0, 0, wall_height))
    base = extrude(outline, wall_height) + rim

    radius = BODY_DIAMETER / 2 + SEAT_CLEARANCE
    overcut = 0.1  # Extend the cutters past the top face.
    bevel = Manifold.cylinder(
        SEAT_BEVEL + overcut, radius, radius + SEAT_BEVEL + overcut, 96
    ).translate((0, 0, BOARD_HEIGHT - SEAT_BEVEL))
    seat_floor = BOARD_HEIGHT - SEAT_DEPTH
    seat = bevel + Manifold.cylinder(
        SEAT_DEPTH - SEAT_BEVEL, radius, circular_segments=96
    ).translate((0, 0, seat_floor))
    # Adjacent seats meet along short arcs. The material at the cell corners
    # locates the feet while leaving clearance at the 20 mm pitch.
    cutters = [
        seat.translate(
            (
                (column + 0.5) * CELL_PITCH - field_width / 2,
                (row + 0.5) * CELL_PITCH - field_depth / 2,
                0,
            )
        )
        for row in range(rows)
        for column in range(columns)
    ]
    # Rim notches mark the two row boundaries without cutting into the seats.
    if deployment_rows:
        boundary = field_depth / 2 - deployment_rows * CELL_PITCH
        left_edge = -width / 2 - overcut
        right_edge = field_width / 2 + SEAT_CLEARANCE + SEAT_BEVEL + 0.4
        notch = Manifold.cube(
            (width / 2 - right_edge + overcut, MARKER_WIDTH, SEAT_DEPTH + overcut)
        )
        cutters.extend(
            notch.translate((x, y - MARKER_WIDTH / 2, seat_floor))
            for x in (left_edge, right_edge)
            for y in (-boundary, boundary)
        )
    return Manifold.batch_boolean([base, *cutters], OpType.Subtract)


def role_marks() -> dict[str, CrossSection]:
    rock = CrossSection(
        [
            [
                (-3.6, -1.1),
                (-1.8, -2.7),
                (1.8, -2.6),
                (3.4, -0.9),
                (2.2, 2.0),
                (-0.1, 3.1),
                (-2.6, 1.3),
            ]
        ]
    )
    paper = (
        CrossSection([[(-2.5, -3.3), (2.5, -3.3), (2.5, 1.5), (0.9, 3.3), (-2.5, 3.3)]])
        - bar((-1.4, -1.4), (1.4, -1.4), 0.8)
        - bar((-1.4, 0.2), (1.4, 0.2), 0.8)
    )

    scissors = (
        ring(1.5, 0.6).translate((-1.55, -2.0))
        + ring(1.5, 0.6).translate((1.55, -2.0))
        + bar((-1.25, -0.9), (2.0, 3.2), 1.0)
        + bar((1.25, -0.9), (-2.0, 3.2), 1.0)
    )
    bomb = (
        CrossSection.circle(2.45, 48).translate((-0.5, -0.9))
        + bar((-0.3, 1.2), (0.2, 2.5), 1.0)
        + bar((-0.05, 2.3), (1.65, 3.1), 1.0)
    )
    flag = bar((-2.1, -3.3), (-2.1, 3.0), 1.0) + CrossSection(
        [[(-2.1, -0.4), (2.9, 1.5), (-2.1, 3.4)]]
    )
    return {
        "rock": rock,
        "paper": paper,
        "scissors": scissors,
        "bomb": bomb,
        "flag": flag,
    }


def blank_piece() -> Manifold:
    radius = BODY_DIAMETER / 2
    cylinder = Manifold.cylinder(BODY_HEIGHT, radius, circular_segments=96)
    # Remove a circular segment above the foot to expose a vertical face.
    cut = Manifold.cube(
        (BODY_DIAMETER + 2, radius + FLAT_Y + 1, BODY_HEIGHT - FOOT_HEIGHT + 1)
    ).translate((-radius - 1, -radius - 1, FOOT_HEIGHT))
    return cylinder - cut


def main() -> None:
    # Mirror in the print plane so the text reads correctly from underneath.
    imprint = text_shape("Claus RPS", width=34, height=6).mirror((0, 1))
    underside_cut = extrude(imprint, TEST_IMPRINT_DEPTH + 0.1).translate((0, 0, -0.1))
    boards = {
        "board": build_board(),
        "test-board-2x2": build_board(2, 2, deployment_rows=0) - underside_cut,
    }
    for name, board in boards.items():
        assert_printable(board)
        if len(board.decompose()) != 1:
            raise ValueError(f"{name} must be one connected solid")
        write_stl(
            board, Path(__file__).with_name(f"{name}.stl"), f"rps-flag-hunt-{name}"
        )

    blank = blank_piece()

    team = []
    for role, mark in role_marks().items():
        engraving = (
            extrude(mark.scale((MARK_SCALE, MARK_SCALE)), ENGRAVING_DEPTH + 1)
            .rotate((90, 0, 0))
            .translate((0, FLAT_Y + ENGRAVING_DEPTH, MARK_Z))
        )
        piece = blank - engraving
        assert_printable(piece)
        if len(piece.decompose()) != 1:
            raise ValueError(f"{role} must be one connected solid")
        write_stl(piece, Path(__file__).with_name(f"{role}.stl"), role)
        team.extend([piece] * TEAM_COUNTS[role])

    plate = layout_on_plate(team, gap=4, columns=4)
    assert_printable(plate)
    if len(plate.decompose()) != sum(TEAM_COUNTS.values()):
        raise ValueError("each team piece must be separate on the print plate")
    write_stl(plate, Path(__file__).with_name("team-plate.stl"), "rps-flag-hunt-team")


if __name__ == "__main__":
    main()
