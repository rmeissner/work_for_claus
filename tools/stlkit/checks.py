"""Sanity checks for models before they are exported."""

from manifold3d import Error, Manifold

DEFAULT_MAX_SIZE = (220.0, 220.0, 250.0)
_TOLERANCE = 1e-6


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
        raise ValueError(f"model must sit on Z = 0, but its lowest point is at Z = {z0}")
    size = (x1 - x0, y1 - y0, z1 - z0)
    if any(s > m + _TOLERANCE for s, m in zip(size, max_size)):
        raise ValueError(f"model size {size} exceeds the maximum {max_size}")
