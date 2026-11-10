"""Star with 24 points: two slotted cross parts and two folded parts.

Four six-pointed stars of two shapes, two of each:

- A and B (cross parts): a slit from one notch to the center. They slot together into a cross.
  A has a hanging hook on the point at right angles to its slit.
- C and D (fold parts, identical): one closed slit through the center, as wide as the slits
  of A and B and twice as long plus SLIT_EXTRA at each end, and a thinner fold line across
  it. They are folded in half along that line, slipped onto the cross and stay folded.

``combined.stl`` shows the assembly for viewing, each part in its own color: A and B form the
cross (A in the XZ plane, B in the YZ plane); C and D are folded to FOLD_ANGLE about a hinge
parallel to X, their slits lie in B's plane, and their halves make three equal angles with A,
C on one side of A and D on the other.

Run from the repository root: ``python models/star-24/generate.py``.
All dimensions are in millimeters.
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from manifold3d import CrossSection, Manifold, OpType
from stlkit import (
    assert_printable,
    bar,
    extrude,
    layout_on_plate,
    ring,
    round_corners,
    star,
    write_colored_stl,
    write_stl,
)

POINTS = 6
PARTS = 4
OUTER_RADIUS = 45.0
INNER_RADIUS = 18.0
THICKNESS = 1.0  # five 0.2 mm layers
TIP_ROUNDING = 1.0
SLOT_CLEARANCE = 0.0  # nominal snug fit: slit width matches the part thickness
FOLD_WIDTH = 1.0
FOLD_THICKNESS = 0.6  # material left under the fold groove; thinner risks breaking
HOOK_OUTER = 4.0  # radius of the hook's rounded top
HOOK_HOLE = 2.0  # radius of the hole for the thread
HOOK_OVERLAP = 1.5  # how far the hook's ring reaches into the tip
CIRCLE_SEGMENTS = 64
PLATE_GAP = 5.0
PLATE_COLUMNS = 2

SLIT_WIDTH = THICKNESS + SLOT_CLEARANCE
SLIT_LENGTH = INNER_RADIUS  # cross parts: from a notch to the center
# Fold parts: extra slit length at each end, so they slide onto the cross more easily.
SLIT_EXTRA = 0.5
CENTER_SLIT_LENGTH = 2 * SLIT_LENGTH + 2 * SLIT_EXTRA  # fold parts: centered, closed
FOLD_DEPTH = THICKNESS - FOLD_THICKNESS
PART_NAMES = "abcd"
OUTPUT = Path(__file__).with_name("star-24.stl")
COMBINED_OUTPUT = Path(__file__).with_name("combined.stl")

# Assembled view only (the flat parts don't depend on these).
FOLD_ANGLE = 60.0  # angle between the two halves of a folded part
# Distance of C's and D's hinge from A's middle plane: the hinge rests beside A, and the
# offset keeps the slit ends clear of B's notches.
HINGE_OFFSET = 1.5
COLORS = [(229, 57, 53), (30, 136, 229), (67, 160, 71), (253, 216, 53)]  # A, B, C, D


def _slit(y_from: float, y_to: float) -> CrossSection:
    """Slit along local Y, centered on it."""
    return CrossSection.square((SLIT_WIDTH, y_to - y_from)).translate(
        (-SLIT_WIDTH / 2, y_from)
    )


def tip_x() -> float:
    """X of A's rounded tip on the +X axis, at right angles to the slit."""
    return cross_part_outline().bounds()[2]


def hook_center() -> tuple[float, float]:
    """Center of A's hook: beyond the tip on the +X axis, at right angles to the slit."""
    return (tip_x() + HOOK_OUTER - HOOK_OVERLAP, 0.0)


def hook() -> CrossSection:
    """Ring on A's tip at right angles to the slit, for the thread."""
    return ring(HOOK_OUTER, HOOK_HOLE).translate(hook_center())


def hook_hole() -> CrossSection:
    return CrossSection.circle(HOOK_HOLE, CIRCLE_SEGMENTS).translate(hook_center())


def cross_part_outline() -> CrossSection:
    """A's and B's star outline (no slit, no hook), notches on the Y axis."""
    return round_corners(
        star(POINTS, OUTER_RADIUS, INNER_RADIUS).rotate(180 / POINTS), TIP_ROUNDING
    )


def part_2d(k: int) -> CrossSection:
    """Part ``k`` flat; local Y is the slit direction."""
    if k < 2:
        # Notches on the Y axis; A is slit from the bottom notch, B from the top one.
        shape = cross_part_outline()
        reach = OUTER_RADIUS + 1
        if k == 1:
            return shape - _slit(0, reach)
        return (shape + hook()) - hook_hole() - _slit(-reach, 0)
    # Points on the Y axis; the slit stays well inside them.
    shape = round_corners(star(POINTS, OUTER_RADIUS, INNER_RADIUS), TIP_ROUNDING)
    half = CENTER_SLIT_LENGTH / 2
    return shape - _slit(-half, half)


def fold_groove() -> CrossSection:
    """Strip along the X axis, across the slit (through the notches at +-X)."""
    reach = OUTER_RADIUS + 5
    return bar((-reach, 0), (reach, 0), FOLD_WIDTH)


def part(k: int) -> Manifold:
    """Part ``k`` as a flat solid on Z = 0; fold parts have the groove cut from the top."""
    solid = extrude(part_2d(k), THICKNESS)
    if k >= 2:
        groove = extrude(fold_groove(), FOLD_DEPTH + 1).translate(
            (0, 0, THICKNESS - FOLD_DEPTH)
        )
        solid -= groove
    return solid


def parts() -> list[Manifold]:
    """All four parts as flat solids (lying on Z = 0): A, B, C, D."""
    return [part(k) for k in range(PARTS)]


def build_plate() -> Manifold:
    plate = layout_on_plate(parts(), PLATE_GAP, columns=PLATE_COLUMNS)
    assert_printable(plate)
    return plate


def build_part(k: int) -> Manifold:
    """Part ``k`` alone, flat and centered on the XY origin."""
    solid = parts()[k]
    x0, y0, _, x1, y1, _ = solid.bounding_box()
    return solid.translate((-(x0 + x1) / 2, -(y0 + y1) / 2, 0))


def _rotation_x(degrees: float) -> np.ndarray:
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return np.array([[1.0, 0, 0], [0, c, -s], [0, s, c]])


def _place(solid: Manifold, rotation: np.ndarray, offset=(0.0, 0.0, 0.0)) -> Manifold:
    return solid.transform(np.hstack([rotation, np.reshape(offset, (3, 1))]))


def _centered(k: int) -> Manifold:
    """Part ``k`` flat, centered on its thickness (Z = 0 is its middle plane)."""
    return part(k).translate((0, 0, -THICKNESS / 2))


def folded_halves(k: int, side: int) -> list[Manifold]:
    """Both halves of fold part ``k`` in place: hinge parallel to X at Y = side * offset.

    The slit (local Y) ends up in the YZ plane, so B passes through it. Seen along X, the
    halves point FOLD_ANGLE / 2 above and below the Y direction, so together with A's two
    halves (along +-Z) they split the side ``side`` of A into three equal angles.
    """
    flat = _centered(k)
    upper = flat ^ Manifold.cube((200, 100, 10)).translate((-100, 0, -5))
    lower = flat ^ Manifold.cube((200, 100, 10)).translate((-100, -100, -5))
    half_angle = FOLD_ANGLE / 2
    hinge = (0.0, HINGE_OFFSET, 0.0)
    halves = [
        _place(upper, _rotation_x(half_angle), hinge),
        _place(lower, _rotation_x(180 - half_angle), hinge),
    ]
    return halves if side > 0 else [h.mirror((0, 1, 0)) for h in halves]


def assembled() -> list[Manifold]:
    """A, B (the cross) and the folded C, D in place, centered on the origin."""
    a = _place(_centered(0), _rotation_x(90))  # local Y -> Z, A in the XZ plane
    b = _place(_centered(1), _rotation_x(90)).rotate((0, 0, 90))  # B in the YZ plane
    c = Manifold.batch_boolean(folded_halves(2, 1), OpType.Add)
    d = Manifold.batch_boolean(folded_halves(3, -1), OpType.Add)
    return [a, b, c, d]


def build_combined() -> list[tuple[Manifold, tuple[int, int, int]]]:
    """The assembled star with one color per part, lowest point on Z = 0. Viewing only."""
    placed = assembled()
    lowest = min(p.bounding_box()[2] for p in placed)
    return [
        (p.translate((0, 0, -lowest)), color)
        for p, color in zip(placed, COLORS, strict=True)
    ]


def outputs() -> list[tuple[Manifold, Path, str]]:
    """Every generated file: ``(solid, path, name)``."""
    files = [(build_plate(), OUTPUT, "star-24")]
    for k, letter in enumerate(PART_NAMES):
        name = f"part-{letter}"
        files.append((build_part(k), OUTPUT.with_name(f"{name}.stl"), name))
    return files


def main() -> None:
    write_colored_stl(build_combined(), COMBINED_OUTPUT, "star-24 assembled")
    print(f"wrote {COMBINED_OUTPUT}")
    for solid, path, name in outputs():
        write_stl(solid, path, name)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
