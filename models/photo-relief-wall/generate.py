"""Background-free portrait relief across a 12-stud by 8-course thin brick wall.

Run from the repository root: python models/photo-relief-wall/generate.py
Print photo-relief-wall.stl; combined.stl is an assembled preview only.
All dimensions are millimeters. Keep 100% scale to preserve interlocking fit.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import assert_printable, write_colored_stl, write_stl
from stlkit import relief as relief_tools
from stlkit.bricks import BODY_HEIGHT, PITCH, build_brick
from stlkit.relief import photo_front
from stlkit.walls import wall_print_plate

COURSES = ((4, 4, 4), (2, 4, 4, 2)) * 4
STUDS_DEEP = 1
GRID_SPACING = 0.35
ASSET = (
    Path(relief_tools.__file__).resolve().parents[1]
    / "relief-assets"
    / "baby-heightmap.npz"
)
OUTPUT = Path(__file__).with_name("photo-relief-wall.stl")
COMBINED_OUTPUT = Path(__file__).with_name("combined.stl")


def parts():
    with np.load(ASSET, allow_pickle=False) as data:
        image = data["heights"]
        image_width, image_height = float(data["width"]), float(data["height"])
    result = []
    for row, columns in enumerate(COURSES):
        cursor = -sum(columns) * PITCH / 2
        for index, width in enumerate(columns, start=1):
            position = (cursor + width * PITCH / 2, 0, row * BODY_HEIGHT)
            brick = photo_front(
                build_brick(width, studs_y=STUDS_DEEP),
                position,
                image,
                image_width,
                image_height,
                len(COURSES) * BODY_HEIGHT,
                spacing=GRID_SPACING,
            )
            assert_printable(brick)
            if len(brick.decompose()) != 1:
                raise ValueError("portrait relief disconnected a brick")
            result.append((f"row-{row + 1}-brick-{index}", brick, position, row))
            cursor += width * PITCH
    return result


def main() -> None:
    bricks = parts()
    write_stl(wall_print_plate(bricks), OUTPUT, "photo-relief-wall-print-plate")
    write_colored_stl(
        [
            (part.translate(position), (218, 211, 194))
            for _, part, position, _ in bricks
        ],
        COMBINED_OUTPUT,
        "photo-relief-wall-assembled-preview",
    )
    print(f"wrote {OUTPUT} ({len(bricks)} separate bricks) and {COMBINED_OUTPUT}")


if __name__ == "__main__":
    main()
