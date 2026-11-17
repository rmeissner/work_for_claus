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
KEYRING_HOLE_DIAMETER = 5.0  # upper-left brick only, viewed from the lettered front
# slug, lettering, stud counts per course, max text width/height, include key-ring option
VARIANTS = (
    ("meissner", "Meissner", ((4, 4, 4), (2, 4, 4, 2), (4, 4, 4)), 84.0, 20.0, False),
    ("kate", "Käte", ((4, 2), (2, 4)), 40.0, 14.0, False),
    ("carlo", "Carlo", ((4, 4), (2, 4, 2)), 54.0, 14.0, True),
)
ROW_COLORS = ((214, 172, 112), (192, 145, 89), (214, 172, 112))


def parts(variant, *, keyring=False):
    _, text, courses, width, height, _ = variant
    rows = ("bottom", "middle", "top") if len(courses) == 3 else ("bottom", "top")
    return wall_parts(
        text,
        courses,
        rows,
        text_width=width,
        text_height=height,
        imprint_depth=IMPRINT_DEPTH,
        fit_adjustment=FIT_ADJUSTMENT,
        keyring_diameter=KEYRING_HOLE_DIAMETER if keyring else None,
    )


def main() -> None:
    for variant in VARIANTS:
        slug, _, courses, _, _, include_keyring = variant
        bricks = parts(variant)
        print_bricks = list(bricks)
        preview_parts = [
            (part.translate(position), ROW_COLORS[row])
            for _, part, position, row in bricks
        ]
        if include_keyring:
            ring_bricks = parts(variant, keyring=True)
            ring_corner = next(item for item in ring_bricks if item[0] == "top-1")
            print_bricks.append(ring_corner)
            # Show the two complete configurations; shared bricks print only once.
            wall_width = sum(courses[0]) * 8 - 0.2
            offset = (wall_width + 10) / 2
            preview_parts = [
                (part.translate(position).translate((shift, 0, 0)), ROW_COLORS[row])
                for configuration, shift in ((bricks, -offset), (ring_bricks, offset))
                for _, part, position, row in configuration
            ]
        plate = Path(__file__).with_name(f"{slug}-wall.stl")
        preview_name = "combined.stl" if slug == "meissner" else f"{slug}-combined.stl"
        preview = Path(__file__).with_name(preview_name)
        write_stl(
            wall_print_plate(print_bricks, gap=PRINT_GAP),
            plate,
            f"{slug}-wall-print-plate",
        )
        write_colored_stl(
            preview_parts,
            preview,
            f"{slug}-wall-assembled-preview",
        )
        print(f"wrote {plate} ({len(print_bricks)} separate pieces) and {preview}")


if __name__ == "__main__":
    main()
