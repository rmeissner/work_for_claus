"""Sanity checks for models before they are exported."""

from manifold3d import CrossSection, Error, JoinType, Manifold

from .shapes import round_corners

DEFAULT_MAX_SIZE = (220.0, 220.0, 250.0)
_TOLERANCE = 1e-6
_SHARP_CORNER_AREA = 0.01


def assert_printable(
    manifold: Manifold, *, max_size: tuple[float, float, float] = DEFAULT_MAX_SIZE
) -> None:
    """Raise ``ValueError`` unless the model is non-empty, watertight, on Z = 0 and fits ``max_size``."""
    if manifold.is_empty():
        raise ValueError("model is empty")
    if manifold.status() != Error.NoError:
        raise ValueError(f"model is not a valid manifold: {manifold.status()}")
    x0, y0, z0, x1, y1, z1 = manifold.bounding_box()
    if abs(z0) > _TOLERANCE:
        raise ValueError(
            f"model must sit on Z = 0, but its lowest point is at Z = {z0}"
        )
    size = (x1 - x0, y1 - y0, z1 - z0)
    if any(s > m + _TOLERANCE for s, m in zip(size, max_size, strict=True)):
        raise ValueError(f"model size {size} exceeds the maximum {max_size}")


def assert_rounded(shape: CrossSection, radius: float) -> None:
    """Raise ``ValueError`` if any convex corner of ``shape`` is sharper than ``radius``.

    Rounding the shape with ``radius`` removes one small piece per sharp corner (about
    0.21 * radius² for a right angle). Each piece is checked on its own, so one sharp corner
    on a large outline is not hidden; faceting slivers of the circle arcs are far smaller.
    """
    removed = shape - round_corners(shape, radius)
    for piece in removed.decompose():
        if piece.area() > _SHARP_CORNER_AREA * radius**2:
            x, y = piece.bounds()[:2]
            raise ValueError(
                f"shape has a convex corner sharper than radius {radius} near ({x:.1f}, {y:.1f})"
            )


def _unsupported_area(
    layer: CrossSection, below: CrossSection, reach: float, bridge: float
) -> float:
    """Area of ``layer`` that neither ``below`` grown by ``reach`` nor a short bridge holds."""
    held = below.offset(reach, JoinType.Round)
    area = 0.0
    for part in (layer - held).decompose():
        rim = part.offset(0.05, JoinType.Round) - part
        # A bridge is short and its supports bracket it: the hull of the places where it
        # touches the layer below covers it. Two patches on the same edge (a cantilever)
        # or a single one leave the far side uncovered.
        contacts = rim - (rim - held)
        bracketed = (
            not contacts.is_empty()
            and (part - contacts.hull().offset(0.05, JoinType.Round)).area() < 0.01
        )
        if bracketed and (part - held.offset(bridge / 2)).area() < 0.01:
            continue
        area += part.area()
    return area


def worst_unsupported_layer(
    manifold: Manifold,
    *,
    layer_height: float = 0.2,
    reach: float = 0.25,
    bridge: float = 5.0,
) -> tuple[float, float]:
    """Slice ``manifold`` mid-layer and return the (z, area) of the worst unsupported layer.

    Each layer is compared with the one below, grown outward by ``reach``; a
    reach of 0.25 mm per 0.2 mm layer is about 51° from vertical. Bridges
    shorter than ``bridge`` are ignored. The first layer sits on the bed.
    """
    top = manifold.bounding_box()[5]
    worst = (0.0, 0.0)
    # Slice just off mid-layer, so a face on a layer boundary is not ambiguous.
    nudge = 0.01
    below = manifold.slice(layer_height / 2 + nudge)
    z = layer_height * 1.5 + nudge
    while z < top:
        layer = manifold.slice(z)
        area = _unsupported_area(layer, below, reach, bridge)
        if area > worst[1]:
            worst = (z, area)
        below = layer
        z += layer_height
    return worst


def assert_supported(
    manifold: Manifold,
    *,
    max_area: float = 0.5,
    bridge: float = 5.0,
    layer_height: float = 0.2,
    reach: float = 0.25,
) -> tuple[float, float]:
    """Raise ``ValueError`` unless every layer is supported; return the worst layer."""
    z, area = worst_unsupported_layer(
        manifold, layer_height=layer_height, reach=reach, bridge=bridge
    )
    if area > max_area:
        raise ValueError(
            f"{area:.1f} mm² of the layer at Z = {z:.1f} is unsupported"
            f" (more than {max_area} mm²)"
        )
    return z, area
