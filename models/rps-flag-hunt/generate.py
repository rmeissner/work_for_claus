"""Board and chibi ninja teams for RPS Flag Hunt, in millimeters.

Print and play with the circular base at Z = 0. The engraved side faces -Y.
"""

import math
import sys
from itertools import pairwise
from pathlib import Path
from typing import NamedTuple

import numpy as np
from manifold3d import CrossSection, Manifold, OpType

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import (
    assert_printable,
    assert_supported,
    bar,
    extrude,
    layout_on_plate,
    write_colored_stl,
    write_stl,
)
from stlkit.rps import FOOT_DIAMETER, TEAM_COUNTS, role_marks

BOARD_COLUMNS = 7
BOARD_ROWS = 6
DEPLOYMENT_ROWS = 2
CELL_PITCH = 23.0
BOARD_BORDER = 4.0
BOARD_HEIGHT = 3.2
BOARD_WALL_FRACTION = 0.30
SEAT_DEPTH = 0.8
SEAT_CLEARANCE = 0.2  # Radial clearance around the 20 mm foot.
SEAT_BEVEL = 0.4
MARKER_WIDTH = 1.4
SKIN_THICKNESS = 1.2  # Solid layer below the seat floors.
RIB_WIDTH = 1.2  # Underside ribs, centred on the cell boundaries.
FOOT_HEIGHT = 2.4
FOOT_TOP_RADIUS = 9.5

# The game box: the figures lie in two bars, and the box board is its lid.
BOX_FLOOR = 1.2
BOX_WALL = 2.0
LID_FIT = 0.35  # Clearance between the sliding lid and the rails and the stop.
RAIL_WALL = 1.0  # The box is 2 * (0.35 + 1.0) mm wider than its board.
RAIL_LIP = 1.2  # Thickness of the lip tips.
RAIL_OVERLAP = BOARD_HEIGHT * (1 - BOARD_WALL_FRACTION)  # The lips cover the bevel.
RAIL_END_RADIUS = 3.5  # Plan-view nose of the rails at the open end.
BOX_CORNER = 8.0  # Radius of the box's outer vertical corners.
LID_CORNER = BOX_CORNER - LID_FIT - RAIL_WALL  # The lid's, so the gap stays even.
TOP_CHAMFER = 1.2  # On the outer top edge of the walls and the rails.
BASE_CHAMFER = 1.0  # On the outer bottom edge: 45°, so it prints without supports.
GRIP_RADIUS = 5.0  # Finger scoops in both short borders of the lid.
GRIP_DEPTH = 1.2
# The lip underside rises at 45° from the rail wall, 0.35 mm off the lid's bevel.
RAIL_ROOT = BOARD_HEIGHT * BOARD_WALL_FRACTION + LID_FIT * (2**0.5 - 1)
RAIL_TOP = RAIL_ROOT + LID_FIT + RAIL_OVERLAP + RAIL_LIP  # Above the wall tops.
LID_DETENT = 0.65  # A ridge the lid rides over; the lips allow only 0.5 mm of lift.
RIDGE_LENGTH = 60.0
RIDGE_INNER_ANGLE = 60.0  # Degrees from horizontal; the outer ramp is shallower.
RIDGE_TOP = 0.1
RIDGE_MAX_SLOPE = 65.0  # No face of the ridge may be steeper than this.
SHELF_INSET = 3.8  # The wall top reaches this far under the lid's solid border.
BAR_PITCH = 22.0
SLOT_CLEARANCE = 0.3
SLOT_RADIUS = FOOT_DIAMETER / 2 + SLOT_CLEARANCE
BAR_BACK = 1.6  # The wall between the slots on the two faces.
POCKET_DEPTH = FOOT_HEIGHT + SLOT_CLEARANCE
LIP = 1.2  # In front of the foot, either side of the opening.
BAR_HALF = BAR_BACK / 2 + POCKET_DEPTH + LIP
FOOT_OFFSET = BAR_BACK / 2 + SLOT_CLEARANCE / 2  # From the bar's center to the foot.
SLIT_HALF = 7.5  # Half the opening, wider than the legs, narrower than the foot.
SLIT_FLOOR = 8.0  # The opening ends this far below the foot's center.
POCKET_FLOOR = 1.2  # Solid below the grooves.
DETENT_DEPTH = 0.5
DISC_Z = BOX_FLOOR + POCKET_FLOOR + FOOT_DIAMETER / 2  # Foot center when seated.
BAR_TOP = DISC_Z + FOOT_DIAMETER / 2 + 1.5
LID_Z = BAR_TOP + 0.4  # The lid board's underside.
FIGURE_ROLL = 270  # Degrees about the figure's axis: the rear role symbol faces up.
BAR_MIDDLE_GAP = 4.0  # Between the heads of figures that face each other.
BAR_END_GAP = 1.0  # Between the heads and the wall-top shelf, so figures drop past it.
BAR_SIDE_GAP = 1.8  # The same for the figures at the ends of each bar.
TOUCH_VOLUME = 0.01  # mm³ of overlap that still counts as touching.

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


def along_x(shape: CrossSection, start: float, end: float) -> Manifold:
    """Extrude a section given as (y, z) along X from ``start`` to ``end``."""
    return extrude(shape, end - start).rotate((90, 0, 90)).translate((start, 0, 0))


def rounded_block(
    corner_x: float,
    corner_y: float,
    height: float,
    bottom_radius: float,
    top_radius: float | None = None,
) -> Manifold:
    """A prism or frustum with rounded corners around centers at (±corner_x, ±corner_y)."""
    corner = Manifold.cylinder(
        height, bottom_radius, bottom_radius if top_radius is None else top_radius, 64
    )
    return Manifold.batch_hull(
        [
            corner.translate((sx * corner_x, sy * corner_y, 0))
            for sx in (-1, 1)
            for sy in (-1, 1)
        ]
    )


def build_board(
    columns: int = BOARD_COLUMNS,
    rows: int = BOARD_ROWS,
    *,
    deployment_rows: int = DEPLOYMENT_ROWS,
    pitch: float = CELL_PITCH,
    size: tuple[float, float] | None = None,
    corner_radius: float | None = None,
) -> Manifold:
    """The board; ``size`` widens its border, ``corner_radius`` rounds it and adds grips."""
    field_width = columns * pitch
    field_depth = rows * pitch
    width, depth = size or (
        field_width + 2 * BOARD_BORDER,
        field_depth + 2 * BOARD_BORDER,
    )
    wall_height = BOARD_HEIGHT * BOARD_WALL_FRACTION
    bevel_height = BOARD_HEIGHT - wall_height
    if corner_radius is None:
        outline = CrossSection.square((width, depth), center=True)
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
    else:
        # The same bevel, carried around the corners by cones.
        corner_x, corner_y = width / 2 - corner_radius, depth / 2 - corner_radius
        rim = rounded_block(
            corner_x,
            corner_y,
            bevel_height,
            corner_radius,
            corner_radius - bevel_height,
        ).translate((0, 0, wall_height))
        base = rounded_block(corner_x, corner_y, wall_height, corner_radius) + rim

    radius = FOOT_DIAMETER / 2 + SEAT_CLEARANCE
    overcut = 0.1  # Extend the cutters past the top face.
    bevel = Manifold.cylinder(
        SEAT_BEVEL + overcut, radius, radius + SEAT_BEVEL + overcut, 96
    ).translate((0, 0, BOARD_HEIGHT - SEAT_BEVEL))
    seat_floor = BOARD_HEIGHT - SEAT_DEPTH
    seat = bevel + Manifold.cylinder(
        SEAT_DEPTH - SEAT_BEVEL, radius, circular_segments=96
    ).translate((0, 0, seat_floor))
    # The 23 mm pitch leaves a 3 mm gap between the 20 mm feet, and the seats
    # stay separate with material between them.
    cutters = [
        seat.translate(
            (
                (column + 0.5) * pitch - field_width / 2,
                (row + 0.5) * pitch - field_depth / 2,
                0,
            )
        )
        for row in range(rows)
        for column in range(columns)
    ]
    # Open one rectangular pocket per cell into the underside, up to the skin.
    # The ribs between them follow the cell boundaries, and the border stays solid.
    pocket_height = seat_floor - SKIN_THICKNESS
    pocket = Manifold.cube(
        (pitch - RIB_WIDTH, pitch - RIB_WIDTH, pocket_height + overcut),
        center=True,
    ).translate((0, 0, pocket_height / 2 - overcut / 2))
    cutters.extend(
        pocket.translate(
            (
                (column + 0.5) * pitch - field_width / 2,
                (row + 0.5) * pitch - field_depth / 2,
                0,
            )
        )
        for row in range(rows)
        for column in range(columns)
    )
    # Rim notches mark the two row boundaries without cutting into the seats.
    if deployment_rows:
        boundary = field_depth / 2 - deployment_rows * pitch
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
    if corner_radius is not None:
        # A shallow scoop at each short edge lets a finger start the lid sliding.
        scoop = Manifold.cylinder(
            GRIP_DEPTH + overcut, GRIP_RADIUS, circular_segments=48
        )
        for sign in (-1, 1):
            cutters.append(
                scoop.translate(
                    (sign * (width / 2 - 1.5), 0, BOARD_HEIGHT - GRIP_DEPTH)
                )
            )
    return Manifold.batch_boolean([base, *cutters], OpType.Subtract)


def write_board() -> Manifold:
    board = build_board()
    assert_printable(board)
    if len(board.decompose()) != 1:
        raise ValueError("board must be one connected solid")
    write_stl(board, Path(__file__).with_name("board.stl"), "rps-flag-hunt-board")
    return board


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
    pedestal = Manifold.cylinder(FOOT_HEIGHT, FOOT_DIAMETER / 2, FOOT_TOP_RADIUS, 96)
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
    shape: CrossSection,
    bottom: float,
    base_y: float,
    front_y: float,
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


def rival_belt_wrap() -> Manifold:
    """The rope band around the waist, symmetric about its centre at z 14."""
    # A 45-degree slope out of the skirt, a short vertical front face and the
    # same slope back in to the sash, which mirrors the skirt above the belt.
    return loft(
        ROUNDED_PROFILE,
        [
            (12.7, 4.54, 3.24),
            (13.5, 5.34, 4.04),
            (14.5, 5.34, 4.04),
            (15.3, 4.54, 3.24),
        ],
    )


def rival_belt() -> Manifold:
    """The rope: a wrap with one knot, one loop and one string hanging down."""
    knot = CrossSection.circle(1.1, 24).scale((1.2, 1)).translate((0, 14.0))
    # The loop hangs diagonally to one side, the string to the other.
    loop = CrossSection.circle(1, 24).scale((1.25, 2.2))
    loop -= CrossSection.circle(1, 24).scale((0.65, 1.1)).translate((0, -0.1))
    loop = loop.rotate(25).translate((2.0, 11.9))
    string = CrossSection([[(0.1, 13.8), (-1.2, 13.8), (-2.6, 10.4)]])
    return (
        rival_belt_wrap()
        + rising_front_detail(knot, 12.9, 3.4, 4.6)
        + rising_front_detail(loop, 9.3, 2.7, 3.9)
        + rising_front_detail(string, 10.3, 2.7, 3.9)
    )


BELT_CENTER_Z = 14.0
SKIRT_STATIONS = [(8.8, 4.3, 2.4), (10.2, 5.2, 3.7), (14.0, 4.2, 3.0), (15.0, 4.2, 3.0)]


def rival_skirt() -> Manifold:
    """An A-line skirt; its hem is a 45-degree chamfer."""
    return loft(ROUNDED_PROFILE, SKIRT_STATIONS)


def rival_sash() -> Manifold:
    """A wide, flat cloth band around the waist.

    Directly above the belt it angles in exactly like the skirt below it, so
    the silhouette is a mirror image about the belt's centre at z 14.
    """
    heights, x_radii, y_radii = zip(*SKIRT_STATIONS, strict=True)
    flare = []
    for rise in (0.0, 2.5):
        z = BELT_CENTER_Z - rise
        flare.append(
            (
                BELT_CENTER_Z + rise,
                float(np.interp(z, heights, x_radii)),
                float(np.interp(z, heights, y_radii)),
            )
        )
    return loft(ROUNDED_PROFILE, [*flare, (17.0, 4.85, 3.6), (17.4, 4.3, 3.2)])


def rival_arms() -> Manifold:
    # Like the first team, the sleeves hang from the shoulders against the torso
    # and skirt, ending in a point below the belt.
    sleeve = loft(
        ROUNDED_PROFILE,
        [
            (10.0, 0.15, 0.3),
            (11.2, 0.85, 1.45),
            (12.4, 1.2, 1.9),
            (13.4, 1.3, 2.05),
            (15.8, 1.35, 2.1),
            (19.2, 1.35, 2.1),
        ],
    )
    # The shoulder cap leans inwards and sinks into the torso, without a flat top.
    shoulder = loft(
        ROUNDED_PROFILE, [(19.2, 1.35, 2.1), (20.4, 1.1, 1.8), (21.2, 0.7, 1.4)]
    ).transform(((1, 0, -0.875, 0.875 * 19.2), (0, 1, 0, 0), (0, 0, 1, 0)))
    sleeve = (sleeve + shoulder).translate((4.75, 0, 0))
    return sleeve + sleeve.mirror((1, 0, 0))


def rival_neck() -> Manifold:
    return loft(
        ROUNDED_PROFILE,
        [
            (18.6, 0.75, 2.16),
            (20.5, 1.95, 2.32),
            (22.0, 2.2, 2.3),
            (HEAD_SEAT_Z, 2.75, 2.27),
        ],
    )


def rival_legs() -> Manifold:
    """A boot, a slim bare leg and the shorts' hem, as one leg to mirror."""
    # Like the first team's boots, the feet stick out forward a little.
    boot = loft(
        ROUNDED_PROFILE,
        [(2.3, 2.45, 3.65), (3.4, 2.45, 3.65), (4.6, 2.2, 2.8)],
    ).translate((0, 0.65, 0))
    # The shorts end in a small hem that widens at no more than 45 degrees.
    leg = loft(
        ROUNDED_PROFILE,
        [
            (4.4, 1.7, 2.1),
            (7.0, 1.6, 2.0),
            (7.8, 2.05, 2.45),
            (9.5, 2.05, 2.45),
        ],
    )
    return (boot + leg).translate((2.6, 0, 0))


def rival_body() -> Manifold:
    pedestal = Manifold.cylinder(FOOT_HEIGHT, FOOT_DIAMETER / 2, FOOT_TOP_RADIUS, 96)
    leg = rival_legs()
    skirt = rival_skirt()
    # An egg-shaped torso with narrow, sloping shoulders.
    shirt = loft(
        ROUNDED_PROFILE,
        [
            (16.8, 4.4, 3.2),
            (18.4, 4.7, 3.5),
            (19.6, 4.6, 3.45),
            (21.0, 3.9, 3.1),
            (22.1, 3.0, 2.7),
            (HEAD_SEAT_Z, 2.5, 2.3),
        ],
    )
    v_neck = CrossSection.hull_points(
        [
            (-2.3, 22.2),
            (-1.75, HEAD_SEAT_Z + 0.2),
            (1.73, HEAD_SEAT_Z + 0.2),
            (2.3, 22.2),
            (0, 19.0),
        ]
    )
    shirt -= face_cut(v_neck, 6, 0, depth=4.1)
    peg, lead = neck_peg()
    return (
        pedestal
        + leg
        + leg.mirror((1, 0, 0))
        + skirt
        + shirt
        + rival_sash()
        + rival_neck()
        + rival_belt()
        + rival_arms()
        + peg
        + lead
    )


def hair_shell() -> Manifold:
    """A thin shell, 0.5 mm off the head surface, that the flat locks are cut from."""
    return loft(
        ROUNDED_PROFILE,
        [
            (CHIN_LIFT, 6.9, 6.3),
            (2.8, 7.55, 6.85),
            (3.8, 8.2, 7.3),
            (12.3, 8.2, 7.3),
            (14.0, 8.1, 7.3),
        ],
    )


def wedge(left: float, right: float, tip: float, bottom: float) -> CrossSection:
    """A triangle from a top edge at the cap, height 13, to a sharp tip at ``bottom``."""
    return CrossSection([[(left, 13.0), (tip, bottom), (right, 13.0)]])


def front_lock(shell: Manifold, bottom: float, left: float, tip: float) -> Manifold:
    """A narrow flat lock on the cheek side of the face, cut from the shell."""
    return shell ^ face_cut(wedge(left, left + 2.4, tip, bottom), 12, 0, depth=10)


def side_locks(shell: Manifold, bottom: float) -> Manifold:
    """Two flat strands down the side of the head, the rear one a bit shorter."""
    outline = wedge(-0.2, 2.8, 1.1, bottom) + wedge(-3.2, -0.4, -1.9, bottom + 1.4)
    prism = extrude(outline, 8).transform(((0, 0, 1, 3), (1, 0, 0, 0), (0, 1, 0, 0)))
    return shell ^ prism


# A superellipse that rounds the cap without sharp corners.
CAP_EXPONENT = 3.5
CAP_PROFILE = CrossSection(
    [
        [
            (
                np.sign(np.cos(angle)) * abs(np.cos(angle)) ** (2 / CAP_EXPONENT),
                np.sign(np.sin(angle)) * abs(np.sin(angle)) ** (2 / CAP_EXPONENT),
            )
            for angle in np.linspace(0, 2 * np.pi, 56, endpoint=False)
        ]
    ]
)


def rival_hair() -> Manifold:
    # A thin cap hugs the head. Its lower edge is one straight line just above
    # the role mark and leaves the head on a 45-degree chamfer.
    cap = loft(
        CAP_PROFILE,
        [
            (10.8, 7.7, 6.8),
            (11.3, 8.2, 7.3),
            (12.3, 8.2, 7.3),
            (14.0, 8.1, 7.3),
            # The top rounds over like a dome.
            *[
                (14.4 + 2.6 * np.sin(angle), 8.2 * np.cos(angle), 7.4 * np.cos(angle))
                for angle in np.radians((15, 30, 45, 60, 75, 85))
            ],
        ],
    )
    # Three short bangs hang from the front of the cap, cut from the shell
    # like the locks; every edge of the gaps stays within 45 degrees of vertical.
    hairline = [
        (-5.6, 11.4),
        (-4.2, 12.9),
        (-2.9, 10.0),
        (-1.2, 13.0),
        (0.4, 10.8),
        (2.0, 13.0),
        (3.5, 10.2),
        (4.6, 12.9),
        (5.6, 11.4),
    ]
    forehead = CrossSection([[(-5.6, 5), (5.6, 5), *reversed(hairline)]])
    bangs = CrossSection([[(-5.6, 14), *hairline, (5.6, 14)]])
    shell = hair_shell()
    hair = cap - face_cut(forehead, 12, 0, depth=9.5)
    hair += shell ^ face_cut(bangs, 12, 0, depth=9.5)
    # Thick blades frame the back like an upside-down U: a row across the
    # top-back edge, then a column down each back corner that gets shorter
    # towards the bottom. They point back and outwards, and each underside is a
    # 45-degree plane, so they print without support. The corner columns stand
    # on flat shell strips and leave the middle of the back clear for the role mark.
    blades = [
        (0, -5.4, 13.0, 0, 5.0, 2.8, 5.0),
        (-3.9, -5.2, 12.9, -8, 4.6, 2.6, 4.5),
        (3.9, -5.2, 12.9, 8, 4.6, 2.6, 4.5),
    ]
    for side in (-1, 1):
        for z, width, thickness, length in (
            (12.7, 4.6, 2.6, 4.0),
            (10.9, 4.4, 2.5, 3.6),
            (9.1, 4.2, 2.3, 3.2),
            (7.3, 4.0, 2.2, 2.8),
            (5.5, 3.8, 2.0, 2.4),
        ):
            blades.append((side * 6.2, -5.4, z, side * 35, width, thickness, length))
    for x, y, z, yaw, width, thickness, length in blades:
        # The tip sits a little steeper than 45 degrees above the lower root edge.
        blade = Manifold.hull_points(
            [(sx * width / 2, 0, sz * thickness) for sx in (-1, 1) for sz in (0, 1)]
            + [(0, -length, 1.05 * length)]
        )
        hair += blade.rotate((0, 0, yaw)).translate((x, y, z))
    strip = hair_shell() ^ face_cut(wedge(5.9, 9.0, 7.4, 4.2), -2.6, 0, depth=5.4)
    hair += strip + strip.mirror((1, 0, 0))
    # The locks frame the face unevenly: the long front lock on one side
    # reaches the jaw next to the eye, the other side ends higher.
    long_side = front_lock(shell, 3.2, 4.9, 6.3) + side_locks(shell, 3.4)
    short_side = front_lock(shell, 4.0, 5.0, 6.4) + side_locks(shell, 4.2)
    return hair + long_side + short_side.mirror((1, 0, 0))


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
    # Flatten the plain back of the head for the role mark.
    head = trim_ninja_back(face) + hair
    return with_head_socket(engrave_front(head, features, depth=0.5))


def write_ninja_team(
    prefix: str, figure_body: Manifold, head: Manifold
) -> dict[str, Manifold]:
    """Write the team plate and return each role's head, chin on the print bed."""
    parts = {f"{prefix}-body": figure_body}
    team = [figure_body] * sum(TEAM_COUNTS.values())
    role_heads = {}
    for role, mark in role_marks().items():
        role_cut = (
            extrude(mark, 0.85)
            .rotate((90, 0, 0))
            .translate((0, ROLE_FACE_Y + 0.65, ROLE_MARK_Z))
        )
        # Lower the raised chin to the print bed for the standalone head.
        role_heads[role] = (head - role_cut).translate((0, 0, -CHIN_LIFT))
        parts[f"{prefix}-head-{role}"] = role_heads[role]
        team.extend([role_heads[role]] * TEAM_COUNTS[role])

    for name, solid in parts.items():
        assert_printable(solid, max_size=(20, 20, 31))
        if len(solid.decompose()) != 1:
            raise ValueError(f"{name} must be a single solid")

    plate = layout_on_plate(team, 4, columns=7)
    assert_printable(plate)
    if len(plate.decompose()) != len(team):
        raise ValueError("every team component must be separate on the print plate")
    write_stl(
        plate,
        Path(__file__).with_name(f"{prefix}-team-plate.stl"),
        f"{prefix}-team-plate",
    )
    return role_heads


Part = tuple[Manifold, tuple[int, int, int]]


def ninja_parts(
    figure_body: Manifold, role_heads: dict[str, Manifold]
) -> tuple[list[Part], dict[str, list[Part]]]:
    """Colored parts of the first team's body and of each role's head."""
    plate = forehead_plate().translate((0, 0, -CHIN_LIFT))
    heads = {
        role: [
            ((head - plate).translate((0, 0, HEAD_SEAT_Z)), (225, 183, 117)),
            (plate.translate((0, 0, HEAD_SEAT_Z)), (183, 191, 203)),
        ]
        for role, head in role_heads.items()
    }
    return [(figure_body, (221, 142, 54))], heads


def rival_parts(
    figure_body: Manifold, hair: Manifold, role_heads: dict[str, Manifold]
) -> tuple[list[Part], dict[str, list[Part]]]:
    """Colored parts of the rival team's body and of each role's head."""

    # Each color is a slightly grown region cut out of the figure, so that no
    # region boundary lies on the figure's own surface. The regions do not
    # overlap, and the body keeps everything outside them.
    def grown(solid: Manifold) -> Manifold:
        return solid.scale((1.01, 1.01, 1))

    arms = rival_arms().scale((1.03, 1.03, 1))
    belt_region = grown(rival_belt()) - arms
    sash_region = grown(rival_sash()) - arms - belt_region
    neck_region = grown(rival_neck()) ^ Manifold.cube((12, 7, 7)).translate(
        (-6, 1.9, 17)
    )
    body_parts = [
        (figure_body - belt_region - sash_region - neck_region, (120, 126, 169)),
        (figure_body ^ sash_region, (86, 92, 138)),
        (figure_body ^ belt_region, (131, 82, 169)),
        (figure_body ^ neck_region, (221, 182, 142)),
    ]
    heads = {}
    for role, head in role_heads.items():
        role_hair = head ^ hair.translate((0, 0, -CHIN_LIFT))
        heads[role] = [
            ((head - role_hair).translate((0, 0, HEAD_SEAT_Z)), (221, 182, 142)),
            (role_hair.translate((0, 0, HEAD_SEAT_Z)), (48, 43, 66)),
        ]
    return body_parts, heads


def write_assembled(name: str, parts: list[Part]) -> None:
    # Turn the figure around so its face looks at the viewer.
    write_colored_stl(
        [(solid.rotate((0, 0, 180)), color) for solid, color in parts],
        Path(__file__).with_name(f"{name}.stl"),
        name,
    )


def team_roles() -> list[str]:
    """The roles of one team in seat order, with the flag behind the others."""
    roles = [role for role, count in TEAM_COUNTS.items() for _ in range(count)]
    roles.remove("flag")
    roles.insert(BOARD_COLUMNS // 2, "flag")
    return roles


def write_board_preview(
    board: Manifold,
    teams: list[tuple[list[Part], dict[str, list[Part]]]],
) -> None:
    """Stand both teams in their deployment rows, each facing the other.

    Each team is a single color in this preview: gold and dark blue.
    """
    field_width = BOARD_COLUMNS * CELL_PITCH
    field_depth = BOARD_ROWS * CELL_PITCH
    seat_floor = BOARD_HEIGHT - SEAT_DEPTH
    parts: list[Part] = [(board, (140, 140, 140))]
    # The first team stands at -Y facing +Y; the rival stands at +Y facing -Y.
    team_colors = ((212, 170, 60), (28, 32, 58))
    for (body_parts, heads), side, team_color in zip(
        teams, (-1, 1), team_colors, strict=True
    ):
        for seat, role in enumerate(team_roles()):
            row, column = divmod(seat, BOARD_COLUMNS)
            # Row 0 is the back row, farthest from the opponent.
            row = row if side < 0 else BOARD_ROWS - 1 - row
            x = (column + 0.5) * CELL_PITCH - field_width / 2
            y = (row + 0.5) * CELL_PITCH - field_depth / 2
            for solid, _ in body_parts + heads[role]:
                figure = solid if side < 0 else solid.rotate((0, 0, 180))
                parts.append((figure.translate((x, y, seat_floor)), team_color))
    write_colored_stl(
        parts,
        Path(__file__).with_name("board-assembled.stl"),
        "board-assembled",
    )


class Slot(NamedTuple):
    team: int  # 0 for the ninja team, 1 for the rival team.
    seat: int  # Index into ``team_roles()``.
    bar: float  # X of the bar's center line.
    along: float  # Y of the foot's center.
    facing: int  # +1 or -1: the direction the head points along X.


class BoxLayout(NamedTuple):
    # X, slotted faces and Y shift of the slots of each bar.
    bars: tuple[tuple[float, tuple[int, ...], float], ...]
    columns: int  # Slots along each bar face.
    half_y: float  # Half the inner length of the bars.
    board_size: tuple[float, float]  # The box board, which is the sliding lid.
    pitch: float  # Seat pitch of the box board.
    grid: tuple[int, int]  # Columns and rows of the box board.
    deployment_rows: int
    slots: tuple[Slot, ...]


def box_layout(figure_length: float) -> BoxLayout:
    """Size the box around two bars of lying figures, and the board around the box.

    The two bars stand in X, each with figures heading away on both faces. The
    figures on the inner faces nearly meet in the middle.
    """
    bar_x = FOOT_OFFSET + figure_length + BAR_MIDDLE_GAP / 2
    inset = (
        BOX_WALL - LID_FIT - RAIL_WALL
    )  # The inner wall is inside the board outline.
    shelf = SHELF_INSET - inset  # How far the wall-top shelf reaches in.
    half_x = bar_x + FOOT_OFFSET + figure_length + shelf + BAR_END_GAP
    half_y = BOARD_COLUMNS * BAR_PITCH / 2 + BAR_SIDE_GAP
    size = (2 * (half_x + inset), 2 * (half_y + inset))
    pitch = min(
        (size[0] - 2 * BOARD_BORDER) / BOARD_COLUMNS,
        (size[1] - 2 * BOARD_BORDER) / BOARD_ROWS,
    )
    slots = []
    for team, side in enumerate((-1, 1)):
        for seat in range(2 * BOARD_COLUMNS):
            row, column = divmod(seat, BOARD_COLUMNS)
            # Row 0 heads away from the box's middle, row 1 toward it.
            facing = side if row == 0 else -side
            along = (column - BOARD_COLUMNS // 2) * BAR_PITCH
            slots.append(Slot(team, seat, side * bar_x, along, facing))
    return BoxLayout(
        ((-bar_x, (1, -1), 0.0), (bar_x, (1, -1), 0.0)),
        BOARD_COLUMNS,
        half_y,
        size,
        math.floor(pitch * 2) / 2,
        (BOARD_COLUMNS, BOARD_ROWS),
        DEPLOYMENT_ROWS,
        tuple(slots),
    )


def small_layout(full: BoxLayout, figure_length: float) -> BoxLayout:
    """A small 3-by-3 box with the full box's borders, pitch, walls and fit.

    Two bars near the ends hold three figures each, one face slotted, heads
    pointing at each other. The slots are half a pitch apart, so the heads
    pass between each other's.
    """
    columns = 3
    pitch = full.pitch
    size = (
        full.board_size[0] - (full.grid[0] - columns) * pitch,
        full.board_size[1] - (full.grid[1] - columns) * pitch,
    )
    inset = BOX_WALL - LID_FIT - RAIL_WALL
    # Each bar's grooves start just inside the wall-top shelf, so figures drop in.
    bar = size[0] / 2 - SHELF_INSET - 0.2 + BAR_BACK / 2
    shift = BAR_PITCH / 4
    slots = []
    for side, mix in ((-1, ((0, 0), (1, 3), (0, 8))), (1, ((1, 0), (0, 3), (1, 8)))):
        for column, (team, seat) in enumerate(mix):
            along = (column - columns // 2) * BAR_PITCH + side * shift
            slots.append(Slot(team, seat, side * bar, along, -side))
    return BoxLayout(
        ((-bar, (1,), -shift), (bar, (-1,), shift)),
        columns,
        size[1] / 2 - inset,
        size,
        pitch,
        (columns, columns),
        1,
        tuple(slots),
    )


def small_variants(layout: BoxLayout) -> list[BoxLayout]:
    """The same slots with only ninja figures and with only rival figures."""
    return [
        layout._replace(slots=tuple(slot._replace(team=team) for slot in layout.slots))
        for team in (0, 1)
    ]


def bar_slots() -> Manifold:
    """The slots of one bar face, cut from its center line toward +X.

    Each is a groove open at the top, wide enough for a foot standing on its
    edge, behind a narrower opening that the figure's legs pass through.
    """
    top = BAR_TOP + 1.0
    arc = DISC_Z - FOOT_DIAMETER / 2 + SLOT_RADIUS  # Center of the rounded bottom.
    radius = SLOT_RADIUS
    wedge = CrossSection(
        [
            [
                (radius + 0.1, arc + 4.5),
                (radius - DETENT_DEPTH, arc + 3.0),
                (radius + 0.1, arc + 1.5),
            ]
        ]
    )
    groove = CrossSection.circle(radius, 96).translate((0, arc))
    groove += CrossSection.square((2 * radius, top - arc)).translate((-radius, arc))
    # A narrowing the foot squeezes past while it drops into the groove.
    groove -= wedge + wedge.mirror((1, 0))
    pocket_end = BAR_BACK / 2 + POCKET_DEPTH
    opening = CrossSection.square(
        (2 * SLIT_HALF, top - (DISC_Z - SLIT_FLOOR))
    ).translate((-SLIT_HALF, DISC_Z - SLIT_FLOOR))
    slots = [
        along_x(groove, BAR_BACK / 2, pocket_end),
        along_x(opening, pocket_end - 0.1, BAR_HALF + 0.1),
    ]
    return Manifold.batch_boolean(slots, OpType.Add)


def chamfered_block(
    corner_x: float,
    corner_y: float,
    radius: float,
    z0: float,
    z1: float,
    *,
    bottom: float = 0.0,
    top: float = 0.0,
) -> Manifold:
    """A rounded-corner block from ``z0`` to ``z1`` with 45° chamfers on its ends."""
    pieces = []
    if bottom:
        pieces.append(
            Manifold.cylinder(bottom, radius - bottom, radius, 64).translate((0, 0, z0))
        )
    pieces.append(
        Manifold.cylinder(
            z1 - top - z0 - bottom, radius, circular_segments=64
        ).translate((0, 0, z0 + bottom))
    )
    if top:
        pieces.append(
            Manifold.cylinder(top, radius, radius - top, 64).translate((0, 0, z1 - top))
        )
    return Manifold.batch_hull(
        [
            piece.translate((sx * corner_x, sy * corner_y, 0))
            for sx in (-1, 1)
            for sy in (-1, 1)
            for piece in pieces
        ]
    )


def rim_envelope(half_width: float, half_depth: float) -> Manifold:
    """The rounded, top-chamfered outline that the rails and the stop are cut to."""
    return chamfered_block(
        half_width - LID_CORNER,
        half_depth - LID_CORNER,
        BOX_CORNER,
        LID_Z - TOP_CHAMFER,
        LID_Z + RAIL_TOP,
        top=TOP_CHAMFER,
    )


def box_shell(half_width: float, half_depth: float) -> Manifold:
    """The solid outer shell: rounded corners, chamfered at the bottom and the top."""
    return chamfered_block(
        half_width - LID_CORNER,
        half_depth - LID_CORNER,
        BOX_CORNER,
        0.0,
        LID_Z,
        bottom=BASE_CHAMFER,
        top=TOP_CHAMFER,
    )


def lid_rails(half_width: float, half_depth: float) -> Manifold:
    """Dovetail rails along the long walls, closed around the stop end.

    Each lip grows out of its rail wall at 45° and runs parallel to the lid's
    bevel, ``LID_FIT`` away from it, then carries on at 45° over the border.
    At the closed +X end the rail follows the rounded corners and runs across
    the end, so the grooves end inside a solid corner. At the open end the
    rails end in rounded noses that also lead the lid in.
    """
    top = RAIL_TOP
    outer = LID_FIT + RAIL_WALL
    # The rim reaches down into the box's chamfered top edge to join it.
    low = -TOP_CHAMFER
    tip = RAIL_ROOT + LID_FIT + RAIL_OVERLAP
    profile = [
        (LID_FIT, low),
        (outer, low),
        (outer, top),
        (-RAIL_OVERLAP, top),
        (-RAIL_OVERLAP, tip),
        (LID_FIT, RAIL_ROOT),
    ]

    def section(offset: float) -> CrossSection:
        return CrossSection([[(offset + y, LID_Z + z) for y, z in profile]])

    corner_x, corner_y = half_width - LID_CORNER, half_depth - LID_CORNER
    reach = half_width + outer
    near, far = half_depth - RAIL_OVERLAP, half_depth + outer + 1.0
    nose = Manifold.batch_hull(
        [
            Manifold.cylinder(
                top - low + 1.0, RAIL_END_RADIUS, circular_segments=48
            ).translate((-reach + RAIL_END_RADIUS, y, LID_Z + low))
            for y in (near + RAIL_END_RADIUS, far - RAIL_END_RADIUS)
        ]
        + [
            Manifold.cube((1.0, far - near, top - low + 1.0)).translate(
                (corner_x, near, LID_Z + low)
            )
        ]
    )
    side = along_x(section(half_depth), -reach, corner_x) ^ nose
    # The profile turns the corner about the lid's corner center.
    corner = Manifold.revolve(section(LID_CORNER), 64, 90).translate(
        (corner_x, corner_y, 0)
    )
    end = (
        extrude(section(half_width), 2 * corner_y)
        .rotate((90, 0, 0))
        .translate((0, corner_y, 0))
    )
    rim = side + corner + end
    rim += rim.mirror((0, 1, 0))
    return rim ^ rim_envelope(half_width, half_depth)


def lid_detent(half_width: float, half_depth: float) -> Manifold:
    """A ridge across the open end wall that holds the closed lid.

    It rises from the wall top, and its outer face is a ramp from the wall's
    outer edge, at about 37°, so the lid's trailing edge rides up onto it as
    the lid closes. Its inner face is steeper, ``RIDGE_INNER_ANGLE``, and starts
    at the lid's end face, so the closed lid is held firmer than it closed. The
    outer wall face stays vertical under it, and the ridge's ends taper at 45°
    into the wall's chamfered top edge.
    """
    outer = LID_FIT + RAIL_WALL
    low = -TOP_CHAMFER  # Down into the chamfered top edge, which it replaces.
    far, foot = -(half_width + outer), -half_width
    inner_top = foot - LID_DETENT / math.tan(math.radians(RIDGE_INNER_ANGLE))
    profile = CrossSection(
        [
            [
                (far, low),
                (foot, low),
                (foot, 0.0),
                (inner_top, LID_DETENT),
                (inner_top - RIDGE_TOP, LID_DETENT),
                (far, 0.0),
            ]
        ]
    )

    def prism(length: float) -> Manifold:
        solid = extrude(profile, length).rotate((90, 0, 0))
        return solid.translate((0, length / 2, LID_Z))

    # The ridge's ends are the hull with a flat base that reaches LID_DETENT farther.
    length = RIDGE_LENGTH
    base = Manifold.cube((foot - far, length + 2 * LID_DETENT, -low)).translate(
        (far, -length / 2 - LID_DETENT, LID_Z + low)
    )
    return Manifold.batch_hull([prism(length), base])


def build_box(layout: BoxLayout) -> tuple[Manifold, Manifold]:
    """The box with its wall tops at ``LID_Z``, and the ridge that holds the lid."""
    outset = LID_FIT + RAIL_WALL
    half_width, half_depth = (side / 2 for side in layout.board_size)
    # All the rounded outlines share the lid's corner centers.
    corner_x, corner_y = half_width - LID_CORNER, half_depth - LID_CORNER
    overcut = 0.1
    inset = BOX_WALL - outset  # The inner wall face lies inside the board outline.
    inner = LID_CORNER - inset  # Radius of the inner corners.
    corbel = SHELF_INSET - inset
    flat = 0.8
    corbel_z = LID_Z - flat - corbel
    # The wall top widens inward at 45° under the lid's solid border.
    cavity = [
        rounded_block(corner_x, corner_y, corbel_z - BOX_FLOOR, inner).translate(
            (0, 0, BOX_FLOOR)
        ),
        rounded_block(corner_x, corner_y, corbel, inner, inner - corbel).translate(
            (0, 0, corbel_z)
        ),
        rounded_block(corner_x, corner_y, flat + overcut, inner - corbel).translate(
            (0, 0, corbel_z + corbel)
        ),
    ]
    shell = box_shell(half_width, half_depth)
    box = Manifold.batch_boolean([shell, *cavity], OpType.Subtract)
    # The bars stop at the inner wall, curved corners included, and reach 0.1 mm
    # into it to fuse with it.
    clip = (
        rounded_block(
            corner_x, corner_y, corbel_z - BOX_FLOOR + 0.2, inner + overcut
        ).translate((0, 0, BOX_FLOOR - 0.2))
        + rounded_block(
            corner_x, corner_y, corbel, inner + overcut, inner - corbel + overcut
        ).translate((0, 0, corbel_z))
        + rounded_block(
            corner_x, corner_y, flat + overcut, inner - corbel + overcut
        ).translate((0, 0, corbel_z + corbel))
    )

    slots = bar_slots()
    for bar_center, faces, shift in layout.bars:
        # The bar spans the box and carries a row of slots on each face.
        # A bar with one slotted face is solid back to the end wall behind it.
        wall = half_width - inset
        back = BAR_HALF if -1 in faces else bar_center + wall + overcut
        front = BAR_HALF if 1 in faces else wall - bar_center + overcut
        body = Manifold.cube(
            (back + front, 2 * layout.half_y + 1.0, BAR_TOP - BOX_FLOOR + overcut),
            center=False,
        ).translate((bar_center - back, -layout.half_y - 0.5, BOX_FLOOR - overcut))
        cuts = [
            face.translate(
                (bar_center, (column - layout.columns // 2) * BAR_PITCH + shift, 0)
            )
            for column in range(layout.columns)
            for facing, face in ((1, slots), (-1, slots.mirror((1, 0, 0))))
            if facing in faces
        ]
        box += Manifold.batch_boolean([body ^ clip, *cuts], OpType.Subtract)

    return box + lid_rails(half_width, half_depth), lid_detent(half_width, half_depth)


def place_figure(solid: Manifold, slot: Slot) -> Manifold:
    """Lay ``solid`` on its side with its foot in the slot and its head outward."""
    lying = solid.rotate((0, 90, 0)).rotate((FIGURE_ROLL, 0, 0))
    if slot.facing < 0:
        lying = lying.rotate((0, 0, 180))
    return lying.translate((slot.bar + slot.facing * FOOT_OFFSET, slot.along, DISC_Z))


def check_box_fit(
    core: Manifold,
    bump: Manifold,
    lid: Manifold,
    layout: BoxLayout,
    teams: list[tuple[list[Part], dict[str, list[Part]]]],
) -> None:
    """Raise ``ValueError`` unless feet, figures and the sliding lid all fit."""

    def touches(a: Manifold, b: Manifold) -> bool:
        return (a ^ b).volume() > TOUCH_VOLUME

    box = core + bump
    half_width, half_depth = (side / 2 for side in layout.board_size)
    corner_x, corner_y = half_width - LID_CORNER, half_depth - LID_CORNER
    outside = core - (
        box_shell(half_width, half_depth) + rim_envelope(half_width, half_depth)
    )
    # The ridge replaces the chamfer under it, so it may reach the unchamfered outline.
    outside += bump - rounded_block(corner_x, corner_y, LID_Z + 2.0, BOX_CORNER)
    if outside.volume() > TOUCH_VOLUME:
        raise ValueError("nothing of the box may stick out of its rounded outer shell")
    if len(box.decompose()) != 1 or len(lid.decompose()) != 1:
        raise ValueError("the box and the box board must be single solids")
    # Every layer must be held by the one below it. The lid's rib pockets are
    # bridges up to a pitch wide, which the grid has always printed.
    assert_supported(box)
    assert_supported(lid.translate((0, 0, -LID_Z)), bridge=layout.pitch)
    # Closed, the lid rests on the box and the rails hold it with under 0.5 mm of play.
    if touches(core, lid) or touches(bump, lid):
        raise ValueError("the closed lid must only rest on the box")
    if touches(core, lid.translate((0, 0, 0.45))) or not touches(
        core, lid.translate((0, 0, 0.6))
    ):
        raise ValueError("the rails must hold the lid with 0.5 mm of vertical play")
    for dy in (0.3, -0.3):
        if touches(core, lid.translate((0, dy, 0))) or not touches(
            core, lid.translate((0, 2 * dy, 0))
        ):
            raise ValueError("the rails must hold the lid sideways within 0.6 mm")
    # The lid slides out along X without touching the box; only the ridge is in its way.
    width = layout.board_size[0]
    for slide in np.arange(0.0, width + 10, 5.0):
        if touches(core, lid.translate((-slide, 0, 0))):
            raise ValueError("the lid must slide through its whole travel")
    if not any(
        touches(bump, lid.translate((-slide, 0, 0))) for slide in (0.5, 1.0, 1.5)
    ):
        raise ValueError("the lid must ride over the ridge that holds it")
    # The rails leave the lid 0.5 mm of lift, so the trailing edge must ride up
    # a slope in either direction, never meet a taller vertical face.
    section = bump.rotate((90, 0, 0)).slice(0.0)
    step = 0.05
    heights = []
    for x in np.arange(-half_width - 2.0, -half_width + 1.0, step):
        cut = section ^ CrossSection.square((0.01, 10)).translate(
            (x - 0.005, -LID_Z - 5)
        )
        heights.append(0.0 if cut.is_empty() else max(0.0, -cut.bounds()[1] - LID_Z))
    steepest = max(abs(b - a) for a, b in pairwise(heights)) / step
    if steepest > math.tan(math.radians(RIDGE_MAX_SLOPE)) + 1e-6:
        raise ValueError("the lid must be able to ride up both faces of the ridge")
    # Closed, the lid's end butts against the ridge's ramp and cannot slide out.
    if not touches(bump, lid.translate((-0.3, 0, 0))):
        raise ValueError("the closed lid must be held behind the ridge")

    # The foot is a disc standing in its groove; a foot grown by 0.29 mm still fits.
    foot = Manifold.cylinder(
        FOOT_HEIGHT,
        FOOT_DIAMETER / 2 + SLOT_CLEARANCE - 0.01,
        FOOT_TOP_RADIUS + SLOT_CLEARANCE - 0.01,
        96,
    )
    figures = []
    for slot in layout.slots:
        team, seat, facing = slot.team, slot.seat, slot.facing
        figure = Manifold.compose(figure_solids(teams[team], team_roles()[seat]))
        placed = place_figure(figure, slot)
        figures.append(placed)
        if touches(box, placed) or touches(lid, placed):
            raise ValueError(
                "a figure must lie clear of the box, the walls and the lid"
            )
        centered = place_figure(foot, slot).translate((0, 0, SLOT_CLEARANCE))
        if touches(box, centered):
            raise ValueError("a foot must fit its groove with the planned clearance")
        # The lips hold the foot against pulling out, and the narrowing against lifting.
        pulled = place_figure(foot, slot).translate((facing * 0.4, 0, 0))
        lifted = place_figure(foot, slot).translate((0, 0, SLOT_CLEARANCE + 3.0))
        if not touches(box, pulled) or not touches(box, lifted):
            raise ValueError("a foot must be held in its groove")
        # Lower the figure from above: only its foot meets the narrowing.
        edge = slot.bar + facing * (FOOT_OFFSET + FOOT_HEIGHT)
        legs = placed.trim_by_plane((facing, 0, 0), facing * edge)
        for drop in np.arange(0, 12.1, 1.5):
            if touches(box, legs.translate((0, 0, drop))):
                raise ValueError("a figure must drop into its groove")
    for index, first in enumerate(figures):
        for second in figures[index + 1 :]:
            if touches(first, second):
                raise ValueError("figures must not touch each other")


def write_box(
    layout: BoxLayout,
    teams: list[tuple[list[Part], dict[str, list[Part]]]],
    prefix: str = "",
    variants: list[BoxLayout] = (),
    plate: bool = False,
) -> None:
    """Write the box and its preview, with the figures lying in it and the lid closed.

    With ``plate`` it writes the box and its lid board side by side on one print plate
    instead of as separate files.
    """
    board = build_board(
        *layout.grid,
        deployment_rows=layout.deployment_rows,
        size=layout.board_size,
        pitch=layout.pitch,
        corner_radius=LID_CORNER,
    )
    assert_printable(board)
    core, bump = build_box(layout)
    box = core + bump
    assert_printable(box)
    lid = board.translate((0, 0, LID_Z))
    for fitted in (layout, *variants):
        check_box_fit(core, bump, lid, fitted, teams)
    root = Path(__file__)
    if plate:
        both = layout_on_plate([box, board], 5.0)
        assert_printable(both)
        assert_supported(both, bridge=layout.pitch)
        if len(both.decompose()) != 2:
            raise ValueError("the box and the board must be separate on the plate")
        write_stl(
            both,
            root.with_name(f"{prefix}box-plate.stl"),
            f"rps-flag-hunt-{prefix}box-plate",
        )
    else:
        write_stl(
            board,
            root.with_name(f"{prefix}box-board.stl"),
            f"rps-flag-hunt-{prefix}box-board",
        )
        write_stl(box, root.with_name(f"{prefix}box.stl"), f"rps-flag-hunt-{prefix}box")

    parts: list[Part] = [(box, (205, 200, 190)), (lid, (140, 140, 140))]
    colors = ((212, 170, 60), (28, 32, 58))
    for slot in layout.slots:
        team, seat = slot.team, slot.seat
        for solid in figure_solids(teams[team], team_roles()[seat]):
            parts.append((place_figure(solid, slot), colors[team]))
    write_colored_stl(
        parts, root.with_name(f"{prefix}box-assembled.stl"), f"{prefix}box-assembled"
    )


def figure_solids(team: tuple[list[Part], dict[str, list[Part]]], role: str):
    body_parts, heads = team
    return [solid for solid, _ in body_parts + heads[role]]


def main() -> None:
    board = write_board()
    figure_body = body()
    heads = write_ninja_team("ninja", figure_body, blank_head())
    ninja = ninja_parts(figure_body, heads)
    write_assembled("ninja-assembled", ninja[0] + ninja[1]["flag"])

    figure_body, hair = rival_body(), rival_hair()
    heads = write_ninja_team("rival-ninja", figure_body, rival_head(hair))
    rival = rival_parts(figure_body, hair, heads)
    write_assembled("rival-ninja-assembled", rival[0] + rival[1]["flag"])
    write_board_preview(board, [ninja, rival])
    tops = [
        solid.bounding_box()[5]
        for team in (ninja, rival)
        for role in TEAM_COUNTS
        for solid in figure_solids(team, role)
    ]
    full = box_layout(max(tops))
    write_box(full, [ninja, rival])
    small = small_layout(full, max(tops))
    write_box(
        small,
        [ninja, rival],
        prefix="test-",
        variants=small_variants(small),
        plate=True,
    )


if __name__ == "__main__":
    main()
