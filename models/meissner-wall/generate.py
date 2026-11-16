"""Interlocking 3-course, 12-stud wall with recessed 'Meissner' lettering.

Run from the repo root: ``python models/meissner-wall/generate.py``.
Print meissner-wall.stl (ten separate bricks), not combined.stl (assembly preview).
All dimensions are mm. Viewed from the lettered front, assemble left to right:
bottom B1 B2 B3; middle M1 M2 M3 M4; top T1 T2 T3. Small recessed labels
on the backs identify parts. The print plate has bottom parts at the back,
middle parts in the center, and top parts at the front, all left to right.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import (
    assert_printable,
    extrude,
    layout_on_plate,
    write_colored_stl,
    write_stl,
)
from stlkit.bricks import BODY_HEIGHT, PITCH, WALL_THICKNESS, build_brick
from stlkit.text import text_shape

TEXT = "Meissner"
WALL_STUDS = 12
COURSES = ((4, 4, 4), (2, 4, 4, 2), (4, 4, 4))
TEXT_WIDTH = 84.0
TEXT_HEIGHT = 20.0
IMPRINT_DEPTH = 0.6  # leaves 0.9 mm of the tested 1.5 mm front wall
LABEL_DEPTH = 0.3
FIT_ADJUSTMENT = 0.0
PRINT_GAP = 5.0
OUTPUT = Path(__file__).with_name("meissner-wall.stl")
COMBINED_OUTPUT = Path(__file__).with_name("combined.stl")
ROW_NAMES = ("bottom", "middle", "top")
ROW_CODES = ("B", "M", "T")
ROW_COLORS = ((214, 172, 112), (192, 145, 89), (214, 172, 112))


def parts():
    """Return (filename stem, printable part, assembled position, row) tuples."""
    if not 0 < IMPRINT_DEPTH < WALL_THICKNESS - FIT_ADJUSTMENT:
        raise ValueError("imprint must leave material behind the front face")
    front_y = -(2 * PITCH - 0.2) / 2
    imprint = (
        extrude(
            text_shape(TEXT, width=TEXT_WIDTH, height=TEXT_HEIGHT), IMPRINT_DEPTH + 0.1
        )
        .rotate((90, 0, 0))
        .translate((0, front_y + IMPRINT_DEPTH, len(COURSES) * BODY_HEIGHT / 2))
    )
    result = []
    for row, columns in enumerate(COURSES):
        if sum(columns) != WALL_STUDS:
            raise ValueError("each course must be exactly 12 studs wide")
        cursor = -WALL_STUDS * PITCH / 2
        for index, width in enumerate(columns, start=1):
            position = (cursor + width * PITCH / 2, 0, row * BODY_HEIGHT)
            brick = build_brick(width, fit_adjustment=FIT_ADJUSTMENT)
            placed = brick.translate(position) - imprint
            local = placed.translate(tuple(-p for p in position))
            label = text_shape(f"{ROW_CODES[row]}{index}", width=4, height=2.5)
            # Readable from the back; label does not reach the cavity or front.
            label_cut = extrude(label, LABEL_DEPTH + 0.1).rotate((90, 0, 180))
            local -= label_cut.translate((0, -front_y - LABEL_DEPTH, 2.5))
            assert_printable(local)
            if len(local.decompose()) != 1:
                raise ValueError("engraving disconnected a brick")
            name = f"{ROW_NAMES[row]}-{index}"
            result.append((name, local, position, row))
            cursor += width * PITCH
    return result


def print_plate(bricks):
    """Keep each assembled course in its own row, each row centered on the bed."""
    rows = []
    for row in range(len(COURSES)):
        course = [part for _, part, _, r in bricks if r == row]
        line = layout_on_plate(course, PRINT_GAP)
        rows.append(line.translate((0, (1 - row) * (15.8 + PRINT_GAP), 0)))
    plate = rows[0]
    for row in rows[1:]:
        plate += row
    assert_printable(plate)
    return plate


def main() -> None:
    bricks = parts()
    write_stl(print_plate(bricks), OUTPUT, "meissner-wall-print-plate")
    write_colored_stl(
        [
            (part.translate(position), ROW_COLORS[row])
            for _, part, position, row in bricks
        ],
        COMBINED_OUTPUT,
        "meissner-wall-assembled-preview",
    )
    for name, part, _, _ in bricks:
        write_stl(part, Path(__file__).with_name(f"{name}.stl"), name)
    print(f"wrote {OUTPUT}, {COMBINED_OUTPUT}, and {len(bricks)} individual parts")


if __name__ == "__main__":
    main()
