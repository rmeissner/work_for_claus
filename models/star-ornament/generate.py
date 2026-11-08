"""Slot-together faceted star ornament: two flat parts that slide into a 3D star.

Run from the repository root: ``python models/star-ornament/generate.py``.
All dimensions are in millimeters.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from manifold3d import CrossSection, JoinType  # noqa: E402
from stlkit import (  # noqa: E402
    assert_printable,
    bar,
    extrude,
    layout_on_plate,
    ring,
    round_corners,
    star,
    write_stl,
)

POINTS = 5
OUTER_RADIUS = 45.0
INNER_RADIUS = 22.0
THICKNESS = 3.0
FRAME_WIDTH = 2.6
RIB_WIDTH = 2.2
TIP_ROUNDING = 1.0
HUB_RADIUS = 5.5
SLOT_CLEARANCE = 0.2
SPINE_WALL = 2.4
LOOP_OUTER = 4.0
LOOP_INNER = 2.0
LOOP_OVERLAP = 1.5  # how far the loop's ring reaches down into the tip
PRONG_ROUNDING = 0.8  # blunts the two prongs of part B's split tip
PLATE_GAP = 5.0

SLOT_WIDTH = THICKNESS + SLOT_CLEARANCE
SPINE_WIDTH = SLOT_WIDTH + 2 * SPINE_WALL
SLOT_MEETING = (OUTER_RADIUS - INNER_RADIUS) / 2  # y where the two slots meet
OUTPUT = Path(__file__).with_name("star-ornament.stl")


def outline() -> CrossSection:
    return round_corners(star(POINTS, OUTER_RADIUS, INNER_RADIUS), TIP_ROUNDING)


def tip_y() -> float:
    """Highest point of the rounded outline (the top tip)."""
    return outline().bounds()[3]


def faceted_star() -> CrossSection:
    """Outline, frame, ribs to every tip and notch, hub and spine; windows are cut out."""
    shape = outline()
    frame_inside = shape.offset(-FRAME_WIDTH, JoinType.Miter)
    supports = CrossSection.circle(HUB_RADIUS, 64)
    supports += CrossSection.square((SPINE_WIDTH, 2 * OUTER_RADIUS), center=True)
    for i in range(2 * POINTS):
        radius = OUTER_RADIUS if i % 2 == 0 else INNER_RADIUS
        angle = math.pi * i / POINTS
        supports += bar((0, 0), (-radius * math.sin(angle), radius * math.cos(angle)), RIB_WIDTH)
    return shape - (frame_inside - supports)


def _slot(y_from: float, y_to: float) -> CrossSection:
    return CrossSection.square((SLOT_WIDTH, y_to - y_from)).translate((-SLOT_WIDTH / 2, y_from))


def part_a_2d() -> CrossSection:
    """Slot opens downward (bottom notch up to the meeting point); hanging loop on the top tip."""
    loop = ring(LOOP_OUTER, LOOP_INNER).translate((0, tip_y() + LOOP_OUTER - LOOP_OVERLAP))
    return (faceted_star() + loop) - _slot(-INNER_RADIUS - 1, SLOT_MEETING)


def part_b_2d() -> CrossSection:
    """Slot opens upward (meeting point up through the top tip).

    The slot splits the top tip into two prongs; rounding afterwards blunts their
    needle-thin ends (a rounding opening drops anything narrower than twice PRONG_ROUNDING).
    """
    return round_corners(faceted_star() - _slot(SLOT_MEETING, OUTER_RADIUS + 1), PRONG_ROUNDING)


def parts():
    """Both parts as flat solids (lying on Z = 0), part A first."""
    return extrude(part_a_2d(), THICKNESS), extrude(part_b_2d(), THICKNESS)


def assembled():
    """Both parts standing up and slotted together: A in the XZ plane, B in the YZ plane."""
    a, b = (p.translate((0, 0, -THICKNESS / 2)).rotate((90, 0, 0)) for p in parts())
    return a, b.rotate((0, 0, 90))


def build_plate():
    plate = layout_on_plate(list(parts()), PLATE_GAP)
    assert_printable(plate)
    return plate


def main() -> None:
    write_stl(build_plate(), OUTPUT, "star-ornament")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
