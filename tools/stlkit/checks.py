"""Sanity checks for models before they are exported."""

from manifold3d import CrossSection, Error, Manifold

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
