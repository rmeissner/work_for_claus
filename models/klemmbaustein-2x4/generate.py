"""Simple LEGO-compatible 2 x 4 brick; all dimensions are in millimeters.

Run from the repository root: ``python models/klemmbaustein-2x4/generate.py``.
Print at 100% scale, open underside on the bed and studs facing up, without
supports. Start with 0.12-0.16 mm layers and elephant-foot compensation.
Nominal geometry is not a guarantee of clutch fit: test one brick on Claus.
Increase FIT_ADJUSTMENT in 0.025 mm steps for a looser fit, decrease for tighter.
It changes radial mating surfaces, preserving the grid and outside dimensions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import assert_printable, write_stl
from stlkit.bricks import build_brick as _build_brick

FIT_ADJUSTMENT = 0.0
OUTPUT = Path(__file__).with_name("klemmbaustein-2x4.stl")


def build_brick():
    return _build_brick(fit_adjustment=FIT_ADJUSTMENT)


def main() -> None:
    brick = build_brick()
    assert_printable(brick)
    if len(brick.decompose()) != 1:
        raise ValueError("brick must be one connected solid")
    write_stl(brick, OUTPUT, "klemmbaustein-2x4")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
