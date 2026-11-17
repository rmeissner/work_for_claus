"""Rebuild the numerical portrait asset from the grayscale cutout.

Optional preprocessing dependency: Pillow 13.0.0, in addition to NumPy.
Normal model generation reads the committed NPZ and needs no Pillow install.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

root = Path(__file__).resolve().parent
im = Image.open(root / "baby-cutout-grayscale.png").convert("RGBA")
alpha = im.getchannel("A")
box = alpha.point(lambda x: 255 if x > 8 else 0).getbbox()
im = im.crop(box)
# Only the numerical asset is sampled/smoothed; the retained source stays intact.
width, height = 90.0, 70.0
scale = min(width / im.width, height / im.height)
physical = (im.width * scale, im.height * scale)
nx, ny = 321, 251
sample = im.resize((nx, ny), Image.Resampling.LANCZOS)
luma = (
    np.array(sample.convert("L").filter(ImageFilter.GaussianBlur(0.65)), dtype=float)
    / 255
)
mask = (
    np.array(sample.getchannel("A").filter(ImageFilter.GaussianBlur(0.5)), dtype=float)
    / 255
)
lo, hi = np.percentile(luma[mask > 0.95], [3, 97])
values = np.clip((luma - lo) / (hi - lo), 0, 1)
# Darker tones recess; highlights rise. Transparent background stays at zero.
heights = mask * (-0.45 + 1.35 * values)
# Source image row 0 is at the top; grid rows increase upwards in the model.
np.savez_compressed(
    root / "baby-heightmap.npz",
    heights=np.flipud(heights).astype(np.float32),
    width=np.float64(physical[0]),
    height=np.float64(physical[1]),
)
print(
    "source dimensions",
    im.size,
    "mapped size mm",
    physical,
    "range",
    heights.min(),
    heights.max(),
)
