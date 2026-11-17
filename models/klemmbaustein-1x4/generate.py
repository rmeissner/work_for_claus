"""Thin LEGO-compatible 1 x 4 and 1 x 2 bricks, with one row of studs.

Run: python models/klemmbaustein-1x4/generate.py
Print at 100% scale, open side down, studs up, without supports/internal brims.
All dimensions are millimeters. Test the single-row underside clutch fit.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import assert_printable, write_stl
from stlkit.bricks import build_brick


def main() -> None:
    for columns in (4, 2):
        brick = build_brick(columns, studs_y=1)
        assert_printable(brick)
        if len(brick.decompose()) != 1:
            raise ValueError("brick must be one connected solid")
        name = f"klemmbaustein-1x{columns}"
        path = Path(__file__).with_name(f"{name}.stl")
        write_stl(brick, path, name)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
