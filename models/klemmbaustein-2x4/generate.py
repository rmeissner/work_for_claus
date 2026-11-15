"""Simple LEGO-compatible 2 x 4 brick; all dimensions are in millimeters.

Run from the repository root: ``python models/klemmbaustein-2x4/generate.py``.
Print at 100% scale, open underside on the bed and studs facing up, without
supports. Start with 0.12-0.16 mm layers and elephant-foot compensation.
Nominal geometry is not a guarantee of clutch fit: test one brick on Claus.
Increase FIT_ADJUSTMENT in 0.025 mm steps for a looser fit, decrease for tighter.
It changes radial mating surfaces, preserving the grid and outside dimensions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from manifold3d import Manifold
from stlkit import assert_printable, write_stl

STUDS_X = 4
STUDS_Y = 2
PITCH = 8.0
BODY_GAP = 0.2  # clearance between neighboring bricks on the 8 mm grid
BODY_HEIGHT = 9.6
WALL_THICKNESS = 1.5
ROOF_THICKNESS = 1.2
STUD_DIAMETER = 4.8
STUD_HEIGHT = 1.8
STUD_TOP_CHAMFER = 0.15
TUBE_OUTER_DIAMETER = 6.51
TUBE_INNER_DIAMETER = 4.8
FIT_ADJUSTMENT = 0.0  # radial mm: positive loosens, negative tightens
SEGMENTS = 96
OUTPUT = Path(__file__).with_name("klemmbaustein-2x4.stl")


def build_brick() -> Manifold:
    """Open-bottom shell, eight solid studs, and three roof-connected tubes."""
    length = STUDS_X * PITCH - BODY_GAP
    width = STUDS_Y * PITCH - BODY_GAP
    wall = WALL_THICKNESS - FIT_ADJUSTMENT
    stud_radius = STUD_DIAMETER / 2 - FIT_ADJUSTMENT
    tube_outer = TUBE_OUTER_DIAMETER / 2 - FIT_ADJUSTMENT
    tube_inner = TUBE_INNER_DIAMETER / 2 + FIT_ADJUSTMENT
    cavity_height = BODY_HEIGHT - ROOF_THICKNESS
    if not (
        0 < wall < width / 2
        and STUD_TOP_CHAMFER < stud_radius < PITCH / 2
        and 0 < tube_inner < tube_outer < PITCH / 2
    ):
        raise ValueError("FIT_ADJUSTMENT leaves invalid walls, studs, or tubes")

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
    for column in range(STUDS_X):
        for row in range(STUDS_Y):
            brick += stud.translate(
                (
                    (column - (STUDS_X - 1) / 2) * PITCH,
                    (row - (STUDS_Y - 1) / 2) * PITCH,
                    BODY_HEIGHT,
                )
            )

    # Tube OD is tangent to the four surrounding studs of a mating brick;
    # the bore also accepts a single stud when the brick is offset half a pitch.
    tube = Manifold.cylinder(cavity_height, tube_outer, circular_segments=SEGMENTS)
    tube -= Manifold.cylinder(cavity_height, tube_inner, circular_segments=SEGMENTS)
    for column in range(STUDS_X - 1):
        brick += tube.translate(((column - (STUDS_X - 2) / 2) * PITCH, 0, 0))
    return brick


def main() -> None:
    brick = build_brick()
    assert_printable(brick)
    if len(brick.decompose()) != 1:
        raise ValueError("brick must be one connected solid")
    write_stl(brick, OUTPUT, "klemmbaustein-2x4")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
