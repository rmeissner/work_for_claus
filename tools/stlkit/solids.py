"""3D helpers: extrusion and plate layout."""

from collections.abc import Sequence

from manifold3d import CrossSection, Manifold


def extrude(shape: CrossSection, height: float) -> Manifold:
    """Extrude a 2D shape from Z = 0 up to ``height``."""
    return Manifold.extrude(shape, height)


def layout_on_plate(
    parts: Sequence[Manifold], gap: float, *, columns: int | None = None
) -> Manifold:
    """Place parts in rows of ``columns`` (default: one row), ``gap`` apart, on Z = 0.

    Rows run along X and are stacked along Y; the whole plate is centered on the XY origin.
    """
    per_row = columns or len(parts)
    rows = [parts[i : i + per_row] for i in range(0, len(parts), per_row)]
    placed = []
    widths = []
    depths = []
    for row in rows:
        cursor = 0.0
        row_depth = 0.0
        row_parts = []
        for part in row:
            x0, y0, z0, x1, y1, _ = part.bounding_box()
            row_parts.append(part.translate((cursor - x0, -(y0 + y1) / 2, -z0)))
            cursor += (x1 - x0) + gap
            row_depth = max(row_depth, y1 - y0)
        placed.append(row_parts)
        widths.append(cursor - gap)
        depths.append(row_depth)
    total_depth = sum(depths) + gap * (len(rows) - 1)
    result = []
    top = total_depth / 2
    for row_parts, width, depth in zip(placed, widths, depths, strict=True):
        y = top - depth / 2
        result += [p.translate((-width / 2, y, 0)) for p in row_parts]
        top -= depth + gap
    return Manifold.compose(result)
