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
RIVAL_ROLE_FACE_Y = -7.2
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


def eyes_and_nose() -> CrossSection:
    eye = CrossSection.circle(1.1, 40).translate((3.12, 7.75))
    nose = CrossSection(
        [[(0, 0.57), (-0.43, -0.08), (0, -0.36), (0.43, -0.08)]]
    ).translate((0, 6.35))
    return eye + eye.mirror((1, 0)) + nose


def neck_peg() -> tuple[Manifold, Manifold]:
    peg = extrude(NECK_KEY, PEG_HEIGHT - 0.6).translate((0, 0, HEAD_SEAT_Z))
    lead = Manifold.extrude(NECK_KEY, 0.6, scale_top=(0.78, 0.78)).translate(
        (0, 0, HEAD_SEAT_Z + PEG_HEIGHT - 0.6)
    )
    return peg, lead


def with_head_socket(head: Manifold) -> Manifold:
    bore = extrude(NECK_KEY, PEG_HEIGHT + 0.4).translate((0, 0, CHIN_LIFT - 0.1))
    roof = Manifold.extrude(NECK_KEY, 2.2, scale_top=(0.05, 0.05)).translate(
        (0, 0, CHIN_LIFT + PEG_HEIGHT + 0.3)
    )
    return head - bore - roof


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
    peg, lead = neck_peg()
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
    head = trim_ninja_back(head)

    whiskers = (
        bar((4.01, 6.22), (6.15, 6.43), 0.42)
        + bar((4.04, 5.64), (6.05, 5.43), 0.42)
        + bar((4.07, 5.06), (5.94, 4.49), 0.42)
    )
    face = eyes_and_nose() + whiskers + whiskers.mirror((1, 0))
    head = engrave_front(head, face, depth=0.5)
    head += forehead_plate()

    return with_head_socket(head)


def trim_ninja_back(head: Manifold) -> Manifold:
    # Keep the rear face flat at eye level and taper into the higher hair cut.
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
    return head - rear_trim


def rising_front_detail(
    shape: CrossSection, bottom: float, base_y: float, front_y: float
) -> Manifold:
    """Form a raised front detail with a 45-degree printable lead-in."""
    top = shape.bounds()[3] + 0.1
    ramp = CrossSection(
        [
            [
                (0, bottom),
                (base_y, bottom),
                (front_y, bottom + front_y - base_y),
                (front_y, top),
                (0, top),
            ]
        ]
    )
    limit = extrude(ramp, 22).transform(((0, 0, 1, -11), (1, 0, 0, 0), (0, 1, 0, 0)))
    return face_cut(shape, front_y, 0, depth=3.5) ^ limit


def raised_seam(solid: Manifold, outline: CrossSection) -> Manifold:
    region = face_cut(outline, 8.5, 0, depth=8.5)
    return solid + (region ^ solid.translate((0, 0.36, 0)))


def rival_belt() -> Manifold:
    wrap = loft(
        ROUNDED_PROFILE,
        [
            (10.9, 5.0, 3.36),
            (11.8, 5.85, 4.18),
            (13.15, 5.8, 4.15),
            (13.65, 5.3, 3.65),
        ],
    )
    twists = CrossSection()
    for x in (-3.1, -1.55, 0, 1.55, 3.1):
        twists += bar((x - 0.34, 11.95), (x + 0.32, 12.95), 0.35)
    wrap = engrave_front(wrap, twists, depth=0.34)

    # The ends descend over the thighs, with the knot and loops against the belt.
    left_tail = bar((-1.02, 8.05), (-2.42, 11.25), 1.07)
    right_tail = bar((1.65, 8.65), (1.15, 11.45), 1.07)
    loops = (
        CrossSection.circle(1, 24)
        .scale((1.65, 0.69))
        .rotate(28)
        .translate((-1.42, 11.9))
    )
    loops += (
        CrossSection.circle(1, 24)
        .scale((1.55, 0.67))
        .rotate(-27)
        .translate((1.4, 12.02))
    )
    loops += CrossSection.circle(0.9, 24).translate((0, 11.88))
    belt = (
        wrap
        + rising_front_detail(left_tail, 7.75, 2.62, 4.65)
        + rising_front_detail(right_tail, 8.43, 2.62, 4.65)
        + rising_front_detail(loops, 10.83, 3.32, 4.95)
    )
    return belt.translate((0, 0, 2.85))


def rival_arms() -> Manifold:
    # Sections are given as height, radii, and center. Move the lower
    # sections in front of the belt while keeping the sleeves at the shoulders.
    stations = [
        (11.65, 0.76, 0.68, 4.18, 2.34),
        (12.55, 1.02, 0.92, 4.4, 2.72),
        (13.85, 1.16, 1.01, 4.94, 3.28),
        (15.38, 1.17, 1.21, 5.65, 3.45),
        (16.5, 1.65, 1.47, 5.85, 2.68),
        (17.72, 1.83, 1.69, 5.77, 1.81),
        (19.85, 1.18, 1.38, 5.24, 0.85),
        (20.38, 0.73, 0.99, 4.94, 0.5),
    ]
    arm = Manifold()
    for (z, rx, ry, x, y), (top, tx, ty, end_x, end_y) in pairwise(stations):
        height = top - z
        arm += Manifold.extrude(
            ROUNDED_PROFILE.scale((rx, ry)), height, scale_top=(tx / rx, ty / ry)
        ).transform(
            (
                (1, 0, (end_x - x) / height, x),
                (0, 1, (end_y - y) / height, y),
                (0, 0, 1, z),
            )
        )
    return arm + arm.mirror((1, 0, 0))


def rival_neck() -> Manifold:
    return loft(
        ROUNDED_PROFILE,
        [
            (17.3, 0.75, 2.16),
            (19.5, 1.95, 2.32),
            (21.65, 2.35, 2.31),
            (HEAD_SEAT_Z, 2.75, 2.27),
        ],
    )


def rival_body() -> Manifold:
    pedestal = Manifold.cylinder(2.4, FOOT_DIAMETER / 2, 9.5, 96)
    leg = loft(
        ROUNDED_PROFILE,
        [
            (2.3, 2.4, 3.15),
            (3.7, 2.45, 3.45),
            (5.35, 2.05, 2.5),
            (6.15, 2.65, 2.98),
            (7.3, 2.65, 2.98),
            (8.1, 2.26, 2.63),
            (10.85, 3.12, 3.35),
            (12.35, 2.92, 3.2),
        ],
    ).translate((2.72, 0, 0))
    pants = loft(
        ROUNDED_PROFILE,
        [
            (10.3, 4.8, 3.05),
            (12.15, 5.08, 3.52),
            (16, 5.47, 3.73),
            (16.92, 5.34, 3.7),
        ],
    )
    waist = bar((-3.95, 16.78), (0.4, 16.41), 0.48)
    waist += bar((0.4, 16.41), (3.95, 16.76), 0.48)
    pants = raised_seam(pants, waist)
    shirt = loft(
        ROUNDED_PROFILE,
        [
            (15.85, 5.37, 3.58),
            (17.6, 6.6, 4.1),
            (19.4, 6.1, 3.75),
            (21.8, 3.7, 3.1),
            (HEAD_SEAT_Z, 2.9, 2.35),
        ],
    )
    lapel = bar((-3.0, 21.15), (0.43, 17.47), 0.59)
    lapel += bar((2.69, 21.34), (0.43, 17.47), 0.59)
    lapel += bar((0.43, 17.47), (0.43, 16.4), 0.52)
    v_opening = CrossSection.hull_points(
        [
            (-2.61, 21.13),
            (-1.75, HEAD_SEAT_Z + 0.2),
            (1.73, HEAD_SEAT_Z + 0.2),
            (2.25, 21.36),
            (0.43, 17.81),
        ],
    )
    shirt = raised_seam(shirt, lapel) - face_cut(v_opening, 6, 0, depth=4.1)
    peg, lead = neck_peg()
    return (
        pedestal
        + leg
        + leg.mirror((1, 0, 0))
        + pants
        + shirt
        + rival_neck()
        + rival_belt()
        + rival_arms()
        + peg
        + lead
    )


def rival_hair() -> Manifold:
    crown = loft(
        ROUNDED_PROFILE,
        [
            (10.65, 7.45, 6.58),
            (12.55, 8.22, 7.44),
            (15.05, 8.2, 7.27),
            (17.9, 6.85, 6.05),
        ],
    )
    for x, y, start, tip, radius, lean in (
        (-4.85, -0.2, 13.55, 17.47, 2.68, -2.2),
        (-3.65, -0.72, 15, 19.73, 2.85, -2.65),
        (-1.34, -1.1, 15.9, 21.5, 2.98, -2.45),
        (1.55, -1.28, 15.7, 20.52, 2.84, -1.5),
        (3.99, -2.1, 14.9, 18.82, 2.65, -0.53),
        (4.55, 1.4, 14.6, 18.52, 2.5, 0.2),
        (2.75, 2.7, 15.2, 19.98, 2.8, -0.55),
        (0.1, -4.28, 13.9, 18.43, 2.7, -1.1),
    ):
        height = tip - start
        spike = Manifold.cylinder(height, radius, 0.25, 9).scale((1, 0.84, 1))
        crown += spike.transform(
            ((1, 0, lean / height, x), (0, 1, 0, y), (0, 0, 1, start))
        )
    side_lock = loft(
        ROUNDED_PROFILE,
        [
            (2.28, 0.51, 0.63),
            (3.45, 1.02, 1.07),
            (6.1, 1.55, 1.69),
            (10.7, 1.84, 2.03),
            (13.3, 1.92, 1.72),
            (14.8, 1.25, 1.23),
        ],
    ).transform(((1, 0, 0.085, 5.38), (0, 1, 0.018, 4.32), (0, 0, 1, 0)))
    mid_lock = loft(
        ROUNDED_PROFILE,
        [
            (2.24, 0.51, 0.78),
            (3.6, 0.99, 1.46),
            (5.82, 1.5, 2.02),
            (9.2, 1.82, 2.14),
            (13.85, 1.86, 2.08),
        ],
    ).transform(((1, 0, 0.068, 5.73), (0, 1, -0.038, 1.17), (0, 0, 1, 0)))
    side_lock += mid_lock + mid_lock.translate((-0.04, -2.86, 0.08))
    rear_locks = Manifold()
    for x in (-5.02, -2.51, 0, 2.51, 5.02):
        lower_radius = 0.75 if abs(x) > 4 else 1.12
        lock = loft(
            ROUNDED_PROFILE,
            [
                (CHIN_LIFT, lower_radius, 0.7),
                (3.35, 1.85, 1.99),
                (6.4, 2.15, 2.38),
                (10.5, 2.21, 2.47),
                (14.2, 1.82, 2.41),
            ],
        ).translate((x, -5.49, 0))
        rear_locks += lock
    fringe = CrossSection.hull_points([(-4.98, 13.1), (-2.08, 9.8), (0.27, 14.8)])
    fringe += CrossSection.hull_points([(-2.5, 13.5), (0.6, 9.72), (3.3, 14.8)])
    fringe += CrossSection.hull_points([(0.27, 13.75), (3.91, 10.3), (5.9, 13.78)])
    bangs = rising_front_detail(fringe, 9.68, 6.66, 8.05)
    hair = crown + side_lock + side_lock.mirror((1, 0, 0)) + bangs + rear_locks
    rear_trim = Manifold.cube((22, 12, 26)).translate((-11, RIVAL_ROLE_FACE_Y - 12, -1))
    return hair - rear_trim


def rival_head(hair: Manifold) -> Manifold:
    face = loft(
        ROUNDED_PROFILE,
        [
            (CHIN_LIFT, 6.4, 5.8),
            (2.8, 7.05, 6.35),
            (3.8, 7.7, 6.8),
            (12.3, 7.7, 6.8),
            (15.1, 7.2, 6.5),
        ],
    )
    brow = bar((1.88, 9.04), (4.25, 9.6), 0.47)
    features = eyes_and_nose() + brow + brow.mirror((1, 0))
    head = face + hair
    return with_head_socket(engrave_front(head, features, depth=0.5))


def write_ninja_team(
    prefix: str, figure_body: Manifold, head: Manifold, *, symbol_y: float = ROLE_FACE_Y
) -> Manifold:
    parts = {f"{prefix}-body": figure_body}
    team = [figure_body] * sum(TEAM_COUNTS.values())
    for role, mark in role_marks().items():
        role_cut = (
            extrude(mark, 0.85)
            .rotate((90, 0, 0))
            .translate((0, symbol_y + 0.65, ROLE_MARK_Z))
        )
        # Lower the raised chin to the print bed for the standalone head.
        role_head = (head - role_cut).translate((0, 0, -CHIN_LIFT))
        parts[f"{prefix}-head-{role}"] = role_head
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
        plate,
        Path(__file__).with_name(f"{prefix}-team-plate.stl"),
        f"{prefix}-team-plate",
    )
    return parts[f"{prefix}-head-flag"]


def write_ninjas() -> None:
    figure_body = body()
    preview_head = write_ninja_team("ninja", figure_body, blank_head())
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


def write_rival_ninjas() -> None:
    figure_body, hair = rival_body(), rival_hair()
    head = write_ninja_team(
        "rival-ninja", figure_body, rival_head(hair), symbol_y=RIVAL_ROLE_FACE_Y
    )
    hair = head ^ hair.translate((0, 0, -CHIN_LIFT))
    belt = figure_body ^ (rival_belt() - rival_arms())
    neck = figure_body ^ (
        rival_neck() ^ Manifold.cube((12, 7, 7)).translate((-6, 1.9, 17))
    )
    write_colored_stl(
        [
            ((figure_body - belt - neck).rotate((0, 0, 180)), (120, 126, 169)),
            (belt.rotate((0, 0, 180)), (131, 82, 169)),
            (neck.rotate((0, 0, 180)), (221, 182, 142)),
            (
                (head - hair).translate((0, 0, HEAD_SEAT_Z)).rotate((0, 0, 180)),
                (221, 182, 142),
            ),
            (hair.translate((0, 0, HEAD_SEAT_Z)).rotate((0, 0, 180)), (48, 43, 66)),
        ],
        Path(__file__).with_name("rival-ninja-assembled.stl"),
        "rival-ninja-assembled",
    )


def main() -> None:
    write_board_and_cylinders()
    write_ninjas()
    write_rival_ninjas()


if __name__ == "__main__":
    main()
