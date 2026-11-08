"""3D helpers: extrusion and plate layout."""

from collections.abc import Sequence

from manifold3d import CrossSection, Manifold


def extrude(shape: CrossSection, height: float) -> Manifold:
    """Extrude a 2D shape from Z = 0 up to ``height``."""
    return Manifold.extrude(shape, height)


def layout_on_plate(parts: Sequence[Manifold], gap: float) -> Manifold:
    """Place parts side by side along X, ``gap`` apart, on Z = 0, centered on the XY origin."""
    placed = []
    cursor = 0.0
    for part in parts:
        x0, y0, z0, x1, y1, _ = part.bounding_box()
        placed.append(part.translate((cursor - x0, -(y0 + y1) / 2, -z0)))
        cursor += (x1 - x0) + gap
    shift = (cursor - gap) / 2
    return Manifold.compose([p.translate((-shift, 0, 0)) for p in placed])
