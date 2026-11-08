"""Slot-together star with 24 points: four flat six-pointed stars that slide onto each other.

Run from the repository root: ``python models/star-24/generate.py``.
All dimensions are in millimeters.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from manifold3d import CrossSection  # noqa: E402
from stlkit import (  # noqa: E402
    assert_printable,
    extrude,
    layout_on_plate,
    ring,
    round_corners,
    star,
    write_stl,
)

POINTS = 6
PARTS = 4
OUTER_RADIUS = 45.0
INNER_RADIUS = 18.0
THICKNESS = 3.0
TIP_ROUNDING = 1.0
SLOT_CLEARANCE = 0.3
LOOP_OUTER = 4.0
LOOP_INNER = 2.0
LOOP_OVERLAP = 1.0  # how far the loop's ring reaches down into the top notch
PLATE_GAP = 5.0
PLATE_COLUMNS = 2

PLANE_ANGLE = 180.0 / PARTS  # angle between neighbouring parts' planes
# Another part's slab crosses this part at PLANE_ANGLE, so it covers a wider strip than its thickness.
SLOT_WIDTH = THICKNESS / math.tan(math.radians(PLANE_ANGLE / 2)) + SLOT_CLEARANCE
SEGMENT = 2 * INNER_RADIUS / PARTS  # length of the axis owned by one part
OUTPUT = Path(__file__).with_name("star-24.stl")


def outline() -> CrossSection:
    """Star with a notch (not a point) at +Y and at -Y."""
    return round_corners(star(POINTS, OUTER_RADIUS, INNER_RADIUS).rotate(180.0 / POINTS), TIP_ROUNDING)


def tip_y() -> float:
    """Highest point of the rounded outline."""
    return outline().bounds()[3]


def segment_edges(k: int) -> tuple[float, float]:
    """Top and bottom y of the axis segment owned by part ``k`` (part 0 owns the top one)."""
    return INNER_RADIUS - SEGMENT * k, INNER_RADIUS - SEGMENT * (k + 1)


def _slot(y_from: float, y_to: float) -> CrossSection:
    return CrossSection.square((SLOT_WIDTH, y_to - y_from)).translate((-SLOT_WIDTH / 2, y_from))


def part_2d(k: int) -> CrossSection:
    """Part ``k`` flat: material on the axis only in its own segment, slots everywhere else."""
    shape = outline()
    margin = tip_y() + 1
    top, bottom = segment_edges(k)
    if k > 0:
        shape -= _slot(top, margin)
    if k < PARTS - 1:
        shape -= _slot(-margin, bottom)
    if k == 0:
        shape += ring(LOOP_OUTER, LOOP_INNER).translate((0, INNER_RADIUS + LOOP_OUTER - LOOP_OVERLAP))
    return shape


def parts():
    """All parts as flat solids (lying on Z = 0), part A (with the loop) first."""
    return [extrude(part_2d(k), THICKNESS) for k in range(PARTS)]


def assembled():
    """All parts standing up, slotted together: part k in a vertical plane turned by k * 45 degrees."""
    return [
        p.translate((0, 0, -THICKNESS / 2)).rotate((90, 0, 0)).rotate((0, 0, PLANE_ANGLE * k))
        for k, p in enumerate(parts())
    ]


def build_plate():
    plate = layout_on_plate(parts(), PLATE_GAP, columns=PLATE_COLUMNS)
    assert_printable(plate)
    return plate


def main() -> None:
    write_stl(build_plate(), OUTPUT, "star-24")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
