"""Bundled sans-serif outline text without a system-font dependency."""

import json
from functools import cache
from pathlib import Path

from manifold3d import CrossSection, FillRule


@cache
def _glyphs() -> dict:
    return json.loads(
        Path(__file__).with_name("fonts").joinpath("outline-sans-bold.json").read_text()
    )


def text_shape(text: str, *, width: float, height: float) -> CrossSection:
    """Fit printable ASCII into a centered box, preserving its aspect ratio.

    Width and height are maximum ink bounds in mm. Spaces advance the pen;
    counters (holes inside letters) remain empty. See fonts/ for provenance.
    """
    if not text.strip() or width <= 0 or height <= 0:
        raise ValueError("text needs visible characters and positive bounds")
    contours = []
    cursor = 0
    for character in text:
        if character not in _glyphs():
            raise ValueError(f"unsupported character: {character!r}")
        glyph = _glyphs()[character]
        contours.extend(
            [[x + cursor, y] for x, y in contour] for contour in glyph["contours"]
        )
        cursor += glyph["advance"]
    outline = CrossSection(contours, FillRule.EvenOdd)
    x0, y0, x1, y1 = outline.bounds()
    scale = min(width / (x1 - x0), height / (y1 - y0))
    return outline.translate((-(x0 + x1) / 2, -(y0 + y1) / 2)).scale((scale, scale))
