"""Board and chibi ninja teams for RPS Flag Hunt, in millimeters.

Print and play with the circular base at Z = 0. The engraved side faces -Y.
"""

import sys
from itertools import pairwise
from pathlib import Path

import numpy as np
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
    pedestal = Manifold.cylinder(2.4, FOOT_DIAMETER / 2, 9.5, 96)
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


if __name__ == "__main__":
    main()
