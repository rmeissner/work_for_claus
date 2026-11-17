"""Two-stud-deep interlocking bricks with adjustable stud diameter."""

from manifold3d import Manifold

STUDS_Y = 2
PITCH = 8.0
BODY_GAP = 0.2  # clearance between neighboring bricks on the 8 mm grid
BODY_HEIGHT = 9.6
WALL_THICKNESS = 1.5
ROOF_THICKNESS = 1.2
STUD_DIAMETER = 5.0  # 4.8 and 4.9 mm studs were loose in physical fit tests
STUD_HEIGHT = 1.8
STUD_TOP_CHAMFER = 0.15
TUBE_OUTER_DIAMETER = 6.51
TUBE_INNER_DIAMETER = 4.8
SEGMENTS = 96


def build_brick(
    studs_x: int = 4,
    *,
    fit_adjustment: float = 0.0,
    stud_diameter: float = STUD_DIAMETER,
) -> Manifold:
    """Build a 2 x N open-bottom brick with solid studs and clutch tubes.

    Positive fit_adjustment loosens mating surfaces by that radial distance
    in mm; negative values tighten them. stud_diameter changes only the top
    studs, preserving the underside clutch geometry. The 5.0 mm default adds
    0.1 mm radius to the initial 4.8 mm studs to compensate for a loose print.
    """
    if not isinstance(studs_x, int) or studs_x < 2:
        raise ValueError("a two-stud-deep brick needs at least two columns")
    length = studs_x * PITCH - BODY_GAP
    width = STUDS_Y * PITCH - BODY_GAP
    wall = WALL_THICKNESS - fit_adjustment
    stud_radius = stud_diameter / 2 - fit_adjustment
    tube_outer = TUBE_OUTER_DIAMETER / 2 - fit_adjustment
    tube_inner = TUBE_INNER_DIAMETER / 2 + fit_adjustment
    cavity_height = BODY_HEIGHT - ROOF_THICKNESS
    if not (
        0 < wall < width / 2
        and STUD_TOP_CHAMFER < stud_radius < PITCH / 2
        and 0 < tube_inner < tube_outer < PITCH / 2
    ):
        raise ValueError("fit_adjustment leaves invalid walls, studs, or tubes")

    # Extend the cavity below the bed to keep the underside fully open.
    body = Manifold.cube((length, width, BODY_HEIGHT)).translate(
        (-length / 2, -width / 2, 0)
    )
    cavity = Manifold.cube(
        (length - 2 * wall, width - 2 * wall, cavity_height + 1)
    ).translate((-length / 2 + wall, -width / 2 + wall, -1))
    brick = body - cavity

    stud = Manifold.cylinder(
        STUD_HEIGHT - STUD_TOP_CHAMFER, stud_radius, circular_segments=SEGMENTS
    )
    stud += Manifold.cylinder(
        STUD_TOP_CHAMFER,
        stud_radius,
        stud_radius - STUD_TOP_CHAMFER,
        circular_segments=SEGMENTS,
    ).translate((0, 0, STUD_HEIGHT - STUD_TOP_CHAMFER))
    for column in range(studs_x):
        for row in range(STUDS_Y):
            brick += stud.translate(
                (
                    (column - (studs_x - 1) / 2) * PITCH,
                    (row - (STUDS_Y - 1) / 2) * PITCH,
                    BODY_HEIGHT,
                )
            )

    # Preserve the underside sized for nominal 4.8 mm LEGO studs. The enlarged
    # printed studs intentionally have a small interference fit with this.
    tube = Manifold.cylinder(cavity_height, tube_outer, circular_segments=SEGMENTS)
    tube -= Manifold.cylinder(cavity_height, tube_inner, circular_segments=SEGMENTS)
    for column in range(studs_x - 1):
        brick += tube.translate(((column - (studs_x - 2) / 2) * PITCH, 0, 0))
    return brick
