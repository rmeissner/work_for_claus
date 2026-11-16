"""Interlocking 3-course, 12-stud wall with recessed 'Meissner' lettering.

Run from the repo root: ``python models/meissner-wall/generate.py``.
Print meissner-wall.stl (ten separate bricks), not combined.stl (assembly preview).
All dimensions are mm. Bricks have plain backs with no placement labels.
The print plate has bottom parts at the back,
middle parts in the center, and top parts at the front, all left to right.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import write_colored_stl, write_stl
from stlkit.walls import wall_parts, wall_print_plate

TEXT = "Meissner"
COURSES = ((4, 4, 4), (2, 4, 4, 2), (4, 4, 4))
TEXT_WIDTH = 84.0
TEXT_HEIGHT = 20.0
IMPRINT_DEPTH = 0.6  # leaves 0.9 mm of the tested 1.5 mm front wall
FIT_ADJUSTMENT = 0.0
PRINT_GAP = 5.0
OUTPUT = Path(__file__).with_name("meissner-wall.stl")
COMBINED_OUTPUT = Path(__file__).with_name("combined.stl")
ROW_NAMES = ("bottom", "middle", "top")
ROW_COLORS = ((214, 172, 112), (192, 145, 89), (214, 172, 112))


def parts():
    return wall_parts(
        TEXT,
        COURSES,
        ROW_NAMES,
        text_width=TEXT_WIDTH,
        text_height=TEXT_HEIGHT,
        imprint_depth=IMPRINT_DEPTH,
        fit_adjustment=FIT_ADJUSTMENT,
    )


def print_plate(bricks):
    return wall_print_plate(bricks, gap=PRINT_GAP)


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
