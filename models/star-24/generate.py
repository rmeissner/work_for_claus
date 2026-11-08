"""Slot-together star with 24 points: four identical six-pointed stars in tilted planes.

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
    round_corners,
    star,
    write_colored_stl,
    write_stl,
)

POINTS = 6
PARTS = 4
OUTER_RADIUS = 45.0
INNER_RADIUS = 18.0
THICKNESS = 1.2
TIP_ROUNDING = 1.0
SLOT_CLEARANCE = 0.3
PLATE_GAP = 5.0
PLATE_COLUMNS = 2

HUB_RADIUS = 3.0  # central hole
SLOT_DEPTH = 7.0  # the hole's arms and the edge slits meet here (center distance)

DIHEDRAL_COS = 1 / 3  # planes of the four parts cross at this angle
# Another part's slab crosses this part at the dihedral angle,
# so it covers a wider strip than its thickness.
SLOT_WIDTH = (
    THICKNESS * (1 + DIHEDRAL_COS) / math.sqrt(1 - DIHEDRAL_COS**2) + SLOT_CLEARANCE
)
# Notches with the edge slits: the lines shared with the other parts.
INNER_DIRECTIONS = (90.0, 210.0, 330.0)
# The other three notches: arms of the closed center hole.
OUTER_DIRECTIONS = (30.0, 150.0, 270.0)
# Parts 2-4 are part 1 turned by 180 degrees about the x, y and z axes.
ROTATIONS = [np.diag(d) for d in ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))]
OUTPUT = Path(__file__).with_name("star-24.stl")
COMBINED_OUTPUT = Path(__file__).with_name("combined.stl")
PART_NAMES = "abcd"[:PARTS]
# One color per part in the assembled view (red, blue, green, yellow).
PART_COLORS = [(229, 57, 53), (30, 136, 229), (67, 160, 71), (253, 216, 53)]
PART_OUTPUTS = [Path(__file__).with_name(f"part-{name}.stl") for name in PART_NAMES]


def _direction(angle: float) -> tuple[float, float]:
    return math.cos(math.radians(angle)), math.sin(math.radians(angle))


def _arm(angle: float, start: float, end: float) -> CrossSection:
    x, y = _direction(angle)
    return bar((start * x, start * y), (end * x, end * y), SLOT_WIDTH)


def part_2d() -> CrossSection:
    """One part flat: a six-pointed star with a closed Y-shaped hole and three edge slits."""
    shape = round_corners(
        star(POINTS, OUTER_RADIUS, INNER_RADIUS).rotate(30), TIP_ROUNDING
    )
    hole = CrossSection.circle(HUB_RADIUS, 48)
    for angle in OUTER_DIRECTIONS:
        hole += _arm(angle, 0, SLOT_DEPTH)
    for angle in INNER_DIRECTIONS:
        hole += _arm(angle, SLOT_DEPTH, OUTER_RADIUS + 5)
    return shape - hole


def frame() -> np.ndarray:
    """Local-to-world rotation of part 1: its plane has normal (1,1,1), local +Y is the line (1,-1,0)."""
    normal = np.array([1.0, 1.0, 1.0]) / math.sqrt(3)
    ey = np.array([1.0, -1.0, 0.0]) / math.sqrt(2)
    return np.column_stack([np.cross(ey, normal), ey, normal])


def parts():
    """All parts as flat solids (lying on Z = 0); they are identical."""
    return [extrude(part_2d(), THICKNESS) for _ in range(PARTS)]


def assembled():
    """All parts in their tilted planes: part 1 turned into its plane, the others turned by ROTATIONS."""
    return [
        p.translate((0, 0, -THICKNESS / 2)).transform(
            np.hstack([rotation @ frame(), np.zeros((3, 1))])
        )
        for p, rotation in zip(parts(), ROTATIONS, strict=False)
    ]


def build_plate():
    plate = layout_on_plate(parts(), PLATE_GAP, columns=PLATE_COLUMNS)
    assert_printable(plate)
    return plate


def build_combined():
    """The assembled parts, lowest point on Z = 0. For viewing only, not for printing."""
    placed = assembled()
    lowest = Manifold.batch_boolean(placed, OpType.Add).bounding_box()[2]
    return [part.translate((0, 0, -lowest)) for part in placed]


def write_combined(path: Path, name: str) -> None:
    """Write the assembled star with each part in its own color."""
    write_colored_stl(list(zip(build_combined(), PART_COLORS, strict=True)), path, name)


def build_part(k: int):
    """Part ``k`` flat on Z = 0, centered on the origin."""
    solid = parts()[k]
    x0, y0, _, x1, y1, _ = solid.bounding_box()
    return solid.translate((-(x0 + x1) / 2, -(y0 + y1) / 2, 0))


def outputs():
    """Every generated file with a function that writes it to a given path."""
    return [
        (COMBINED_OUTPUT, lambda path: write_combined(path, "star-24 assembled")),
        (OUTPUT, lambda path: write_stl(build_plate(), path, "star-24")),
        *(
            (
                path,
                lambda out, k=k, name=name: write_stl(
                    build_part(k), out, f"star-24 part {name}"
                ),
            )
            for k, (path, name) in enumerate(zip(PART_OUTPUTS, PART_NAMES, strict=True))
        ),
    ]


def main() -> None:
    for path, write in outputs():
        write(path)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
