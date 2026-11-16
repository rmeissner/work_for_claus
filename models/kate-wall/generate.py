"""Four-brick test wall with recessed 'Käte'; plain backs, no placement labels.

Print kate-wall.stl at 100% scale, studs up, supports and internal brims off.
combined.stl is an assembled preview only. All dimensions are millimeters.
Run from the repo root: python models/kate-wall/generate.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import write_colored_stl, write_stl
from stlkit.walls import wall_parts, wall_print_plate

TEXT = "Käte"
COURSES = ((4, 4), (4, 4))
TEXT_WIDTH = 54.0
TEXT_HEIGHT = 14.0
IMPRINT_DEPTH = 0.6
FIT_ADJUSTMENT = 0.0
OUTPUT = Path(__file__).with_name("kate-wall.stl")
COMBINED_OUTPUT = Path(__file__).with_name("combined.stl")


def parts():
    return wall_parts(
        TEXT,
        COURSES,
        ("bottom", "top"),
        text_width=TEXT_WIDTH,
        text_height=TEXT_HEIGHT,
        imprint_depth=IMPRINT_DEPTH,
        fit_adjustment=FIT_ADJUSTMENT,
    )


def main() -> None:
    bricks = parts()
    write_stl(wall_print_plate(bricks), OUTPUT, "kate-wall-print-plate")
    write_colored_stl(
        [
            (part.translate(position), (214, 172, 112))
            for _, part, position, _ in bricks
        ],
        COMBINED_OUTPUT,
        "kate-wall-assembled-preview",
    )
    for name, part, _, _ in bricks:
        write_stl(part, Path(__file__).with_name(f"{name}.stl"), name)
    print(f"wrote {OUTPUT}, {COMBINED_OUTPUT}, and {len(bricks)} individual parts")


if __name__ == "__main__":
    main()
