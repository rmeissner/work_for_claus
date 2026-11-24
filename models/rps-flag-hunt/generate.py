"""Board, cylinders, and chibi ninjas for RPS Flag Hunt, in millimeters.

Print and play with the circular base at Z = 0. The engraved side faces -Y.
"""

import sys
from itertools import pairwise
from pathlib import Path

from manifold3d import CrossSection, Manifold, OpType

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import (
    assert_printable,
    bar,
    extrude,
    layout_on_plate,
    write_colored_stl,
    write_stl,
)
from stlkit.rps import FOOT_DIAMETER, TEAM_COUNTS, role_marks
from stlkit.text import text_shape

BODY_HEIGHT = 50.0
FOOT_HEIGHT = 10.0
FLAT_Y = -4.0
MARK_Z = 30.0
MARK_SCALE = 1.5
ENGRAVING_DEPTH = 0.8

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


CHIN_LIFT = 2.0
HEAD_SEAT_Z = 23.2
PEG_HEIGHT = 4.3
ROLE_FACE_Y = -6.35
ROLE_MARK_Z = 6.65
BAND_CENTER_Z = 11.75
BAND_HEIGHT = 3.5
BAND_BEVEL = 0.28
# A faceted outline with short flat faces for reliable detail at this scale.
ROUNDED_PROFILE = CrossSection(
    [
        [
            (-0.69, -1),
            (0.69, -1),
            (0.92, -0.73),
            (1, -0.25),
            (1, 0.40),
            (0.82, 0.79),
            (0.62, 1),
            (-0.62, 1),
            (-0.82, 0.79),
            (-1, 0.40),
            (-1, -0.25),
            (-0.92, -0.73),
        ]
    ]
)
NECK_KEY = CrossSection([[(-2.2, -1.8), (2.2, -1.8), (1.5, 1.8), (-1.5, 1.8)]])


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

    radius = FOOT_DIAMETER / 2 + SEAT_CLEARANCE
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


def blank_piece() -> Manifold:
    radius = FOOT_DIAMETER / 2
    cylinder = Manifold.cylinder(BODY_HEIGHT, radius, circular_segments=96)
    # Remove a circular segment above the foot to expose a vertical face.
    cut = Manifold.cube(
        (FOOT_DIAMETER + 2, radius + FLAT_Y + 1, BODY_HEIGHT - FOOT_HEIGHT + 1)
    ).translate((-radius - 1, -radius - 1, FOOT_HEIGHT))
    return cylinder - cut


def write_board_and_cylinders() -> None:
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


def loft(profile: CrossSection, stations: list[tuple[float, float, float]]) -> Manifold:
    """Join successive horizontal sections given as (z, x radius, y radius)."""
    result = Manifold()
    for (z, x, y), (upper_z, upper_x, upper_y) in pairwise(stations):
        result += Manifold.extrude(
            profile.scale((x, y)),
            upper_z - z,
            scale_top=(upper_x / x, upper_y / y),
        ).translate((0, 0, z))
    return result


def face_cut(shape: CrossSection, y: float, z: float, depth: float = 0.6) -> Manifold:
    """Extrude a front-facing detail through a vertical face at +Y."""
    return extrude(shape, depth + 0.2).rotate((90, 0, 0)).translate((0, y + 0.2, z))


def engrave_front(solid: Manifold, shape: CrossSection, depth: float) -> Manifold:
    """Project an XZ outline onto the front, following the surface along Y."""
    cutter = face_cut(shape, 8.5, 0, depth=8.5)
    return solid - (cutter - solid.translate((0, -depth, 0)))


def forehead_plate() -> Manifold:
    half_height = 1.45
    bevel_height = 0.39
    plate = loft(
        CrossSection.square((2, 2), center=True),
        [
            (BAND_CENTER_Z - half_height, 4.3, 0.29),
            (BAND_CENTER_Z - half_height + bevel_height, 4.7, 0.9),
            (BAND_CENTER_Z + half_height - bevel_height, 4.7, 0.9),
            (BAND_CENTER_Z + half_height, 4.3, 0.29),
        ],
    ).translate((0, 7.1, 0))
    # Trace the leaf spiral from its lower point, using single-nozzle-width strokes.
    spiral = [
        (-2.0, -0.87),
        (-1.04, -0.28),
        (-1.0, 0.35),
        (-0.53, 0.82),
        (0.18, 0.88),
        (0.85, 0.57),
        (1.15, 0.0),
        (0.89, -0.62),
        (0.29, -0.83),
        (-0.29, -0.60),
        (-0.53, -0.15),
        (-0.36, 0.26),
        (0.04, 0.39),
        (0.42, 0.20),
        (0.51, -0.11),
        (0.27, -0.32),
    ]
    stroke = 0.44
    mark = CrossSection()
    for start, end in pairwise(spiral):
        mark += bar(start, end, stroke)
    for point in spiral:
        mark += CrossSection.circle(stroke / 2, 12).translate(point)
    mark += bar((-2.0, -0.87), (0.29, -0.83), stroke)
    mark += bar((0.85, 0.57), (1.83, 0.98), stroke)
    for x in (-3.75, 3.75):
        for z in (-0.63, 0.63):
            mark += CrossSection.circle(0.31, 16).translate((x, z))
    mark = mark.scale((1, 0.9)).mirror((1, 0))
    return plate - face_cut(mark, 8.0, BAND_CENTER_Z, depth=0.5)


def body() -> Manifold:
    pedestal = Manifold.cylinder(2.4, FOOT_DIAMETER / 2, 9.5, 96)
    boot = loft(
        ROUNDED_PROFILE,
        [(2.3, 2.6, 3.65), (3.4, 2.6, 3.65), (5.4, 2.25, 2.7)],
    ).translate((0, 0.65, 0))
    pants_leg = loft(
        ROUNDED_PROFILE,
        [(4.9, 2.25, 2.65), (8.6, 2.45, 3.1), (10.1, 3.15, 3.3), (11.5, 3.1, 3.4)],
    )
    legs = (boot + pants_leg).translate((2.8, 0, 0)) + (boot + pants_leg).translate(
        (-2.8, 0, 0)
    )
    strap = loft(
        ROUNDED_PROFILE,
        [(7.0, 2.32, 2.9), (7.6, 2.72, 3.37), (8.2, 2.76, 3.42), (8.8, 2.48, 3.12)],
    ).translate((2.8, 0, 0))
    pouch = loft(
        ROUNDED_PROFILE,
        [(6.6, 0.78, 0.18), (7.8, 1.27, 1.15), (9.1, 1.27, 1.15), (9.55, 1.05, 0.78)],
    ).translate((3.45, 2.85, 0))
    flap = bar((2.79, 8.68), (4.11, 8.68), 0.42)
    legs += strap + (pouch - face_cut(flap, 4, 0, depth=0.38))
    jacket = loft(
        ROUNDED_PROFILE,
        [
            (10.6, 5.05, 3.2),
            (12.3, 5.7, 3.9),
            (15.5, 6.5, 4.25),
            (17.8, 6.7, 4.25),
            (19.8, 5.7, 3.9),
            (22.25, 3.65, 2.95),
            (HEAD_SEAT_Z, 2.9, 2.35),
        ],
    )
    # Sleeves remain against the jacket, growing outward from its lower edge.
    sleeve = loft(
        ROUNDED_PROFILE,
        [(11.3, 1.1, 2.0), (13.9, 2.5, 2.8), (17.2, 2.3, 2.8), (19.2, 1.0, 1.75)],
    ).translate((4.65, 0, 0))
    jacket += sleeve + sleeve.mirror((1, 0, 0))
    zipper = bar((0, 10.5), (0, HEAD_SEAT_Z + 0.15), 1.36)
    tooth = CrossSection.square((0.72, 0.38), center=True)
    for index in range(14):
        zipper -= tooth.translate((0, 11.2 + index * 0.8))
    zipper -= CrossSection.square((0.68, 1.0), center=True).translate((0, 22.35))
    jacket = engrave_front(jacket, zipper, depth=0.5)
    peg = extrude(NECK_KEY, PEG_HEIGHT - 0.6).translate((0, 0, HEAD_SEAT_Z))
    lead = Manifold.extrude(NECK_KEY, 0.6, scale_top=(0.78, 0.78)).translate(
        (0, 0, HEAD_SEAT_Z + PEG_HEIGHT - 0.6)
    )
    return pedestal + legs + jacket + peg + lead


def blank_head() -> Manifold:
    band_bottom = BAND_CENTER_Z - BAND_HEIGHT / 2
    band_top = BAND_CENTER_Z + BAND_HEIGHT / 2
    head = loft(
        ROUNDED_PROFILE,
        [
            (CHIN_LIFT, 6.4, 5.8),
            (2.8, 7.05, 6.35),
            (3.8, 7.7, 6.8),
            (9.05, 7.7, 6.8),
            (band_bottom, 8.13, 6.97),
            (band_bottom + BAND_BEVEL, 8.41, 7.25),
            (band_top - BAND_BEVEL, 8.41, 7.25),
            (band_top, 8.13, 6.97),
        ],
    )
    # Overlapping roots sit inside the band and cover the crown.
    for x, y, start, tip, radius, lean_x, lean_y in [
        (-6.0, 0.0, 12.9, 17.54, 2.2, -2.0, 0.24),
        (-4.9, 2.8, 12.9, 18.58, 2.6, -1.6, 0.64),
        (-2.5, 4.1, 12.9, 19.94, 2.7, -1.04, 0.64),
        (0.05, 4.2, 12.9, 20.34, 2.7, -0.4, 0.8),
        (2.65, 3.9, 12.9, 19.22, 2.7, 0.64, 0.88),
        (5.05, 2.5, 12.9, 18.02, 2.5, 1.52, 0.56),
        (6.0, -0.2, 12.9, 17.34, 2.2, 2.0, 0.12),
        (-4.55, -4.6, 12.9, 17.94, 2.65, -1.44, -0.96),
        (-1.4, -5.45, 12.9, 19.54, 3.2, -0.4, -0.84),
        (1.1, -5.46, 12.9, 18.82, 3.2, 0.36, -0.84),
        (4.4, -4.6, 12.9, 17.82, 2.7, 1.32, -0.96),
        (-2.65, -0.9, 12.9, 20.9, 3.05, -1.24, -0.8),
        (0.3, -0.8, 12.9, 21.46, 3.15, 0.04, -1.08),
        (3.1, -0.9, 12.9, 20.26, 2.9, 1.08, -0.96),
    ]:
        height = tip - start
        lock = Manifold.cylinder(height, radius, 0.26, 9).scale((1, 0.88, 1))
        head += lock.transform(
            ((1, 0, lean_x / height, x), (0, 1, lean_y / height, y), (0, 0, 1, start))
        )
    # Keep the rear face flat at eye level, then taper into the existing hair cut.
    rear_profile = CrossSection(
        [
            [
                (-19, -1),
                (ROLE_FACE_Y, -1),
                (ROLE_FACE_Y, 10.2),
                (-6.9, 11),
                (-6.9, 25),
                (-19, 25),
            ]
        ]
    )
    rear_trim = extrude(rear_profile, 22).transform(
        ((0, 0, 1, -11), (1, 0, 0, 0), (0, 1, 0, 0))
    )
    head -= rear_trim

    eye = CrossSection.circle(1.1, 40).translate((3.12, 7.75))
    nose = CrossSection(
        [[(0, 0.57), (-0.43, -0.08), (0, -0.36), (0.43, -0.08)]]
    ).translate((0, 6.35))
    whiskers = (
        bar((4.01, 6.22), (6.15, 6.43), 0.42)
        + bar((4.04, 5.64), (6.05, 5.43), 0.42)
        + bar((4.07, 5.06), (5.94, 4.49), 0.42)
    )
    face = eye + eye.mirror((1, 0)) + nose + whiskers + whiskers.mirror((1, 0))
    head = engrave_front(head, face, depth=0.5)
    head += forehead_plate()

    bore = extrude(NECK_KEY, PEG_HEIGHT + 0.4).translate((0, 0, CHIN_LIFT - 0.1))
    roof = Manifold.extrude(NECK_KEY, 2.2, scale_top=(0.05, 0.05)).translate(
        (0, 0, CHIN_LIFT + PEG_HEIGHT + 0.3)
    )
    return head - bore - roof


def write_ninjas() -> None:
    figure_body = body()
    head = blank_head()
    parts = {"ninja-body": figure_body}
    team = [figure_body] * sum(TEAM_COUNTS.values())
    for role, mark in role_marks().items():
        role_cut = (
            extrude(mark, 0.85)
            .rotate((90, 0, 0))
            .translate((0, ROLE_FACE_Y + 0.65, ROLE_MARK_Z))
        )
        # Lower the raised chin to the print bed for the standalone head.
        role_head = (head - role_cut).translate((0, 0, -CHIN_LIFT))
        parts[f"ninja-head-{role}"] = role_head
        team.extend([role_head] * TEAM_COUNTS[role])

    for name, solid in parts.items():
        assert_printable(solid, max_size=(20, 20, 31))
        if len(solid.decompose()) != 1:
            raise ValueError(f"{name} must be a single solid")
        write_stl(solid, Path(__file__).with_name(f"{name}.stl"), name)

    plate = layout_on_plate(team, 4, columns=7)
    assert_printable(plate)
    if len(plate.decompose()) != len(team):
        raise ValueError("every team component must be separate on the print plate")
    write_stl(
        plate, Path(__file__).with_name("ninja-team-plate.stl"), "ninja-team-plate"
    )

    preview_head = parts["ninja-head-flag"]
    preview_plate = forehead_plate().translate((0, 0, -CHIN_LIFT))
    write_colored_stl(
        [
            (figure_body.rotate((0, 0, 180)), (221, 142, 54)),
            (
                (preview_head - preview_plate)
                .translate((0, 0, HEAD_SEAT_Z))
                .rotate((0, 0, 180)),
                (225, 183, 117),
            ),
            (
                preview_plate.translate((0, 0, HEAD_SEAT_Z)).rotate((0, 0, 180)),
                (183, 191, 203),
            ),
        ],
        Path(__file__).with_name("ninja-assembled.stl"),
        "ninja-assembled",
    )


def main() -> None:
    write_board_and_cylinders()
    write_ninjas()


if __name__ == "__main__":
    main()
