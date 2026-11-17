"""Meissner, Käte and Carlo interlocking name walls; plain unnumbered backs.

Run from the repo root: python models/meissner-wall/generate.py
Print the named *-wall.stl plate once for that name. *combined.stl files are
assembly previews only. All dimensions are millimeters.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import write_colored_stl, write_stl
from stlkit.walls import wall_parts, wall_print_plate

IMPRINT_DEPTH = 0.6
FIT_ADJUSTMENT = 0.0
PRINT_GAP = 5.0
# slug, lettering, stud counts per course, maximum text width and height
VARIANTS = (
    ("meissner", "Meissner", ((4, 4, 4), (2, 4, 4, 2), (4, 4, 4)), 84.0, 20.0),
    ("kate", "Käte", ((4, 2), (2, 4)), 40.0, 14.0),
    ("carlo", "Carlo", ((4, 4), (2, 4, 2)), 54.0, 14.0),
)
ROW_COLORS = ((214, 172, 112), (192, 145, 89), (214, 172, 112))


def parts(variant):
    _, text, courses, width, height = variant
    rows = ("bottom", "middle", "top") if len(courses) == 3 else ("bottom", "top")
    return wall_parts(
        text,
        courses,
        rows,
        text_width=width,
        text_height=height,
        imprint_depth=IMPRINT_DEPTH,
        fit_adjustment=FIT_ADJUSTMENT,
    )


def main() -> None:
    for variant in VARIANTS:
        slug = variant[0]
        bricks = parts(variant)
        plate = Path(__file__).with_name(f"{slug}-wall.stl")
        preview_name = "combined.stl" if slug == "meissner" else f"{slug}-combined.stl"
        preview = Path(__file__).with_name(preview_name)
        write_stl(
            wall_print_plate(bricks, gap=PRINT_GAP), plate, f"{slug}-wall-print-plate"
        )
        write_colored_stl(
            [
                (part.translate(position), ROW_COLORS[row])
                for _, part, position, row in bricks
            ],
            preview,
            f"{slug}-wall-assembled-preview",
        )
        for name, part, _, _ in bricks:
            filename = f"{slug}-{name}.stl"
            write_stl(part, Path(__file__).with_name(filename), f"{slug}-{name}")
        print(f"wrote {plate}, {preview}, and {len(bricks)} individual parts")


if __name__ == "__main__":
    main()
