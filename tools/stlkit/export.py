"""Binary STL export."""

from collections.abc import Sequence
from pathlib import Path

import numpy as np
from manifold3d import Manifold

_HEADER_SIZE = 80
_TRIANGLE_DTYPE = np.dtype(
    [("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attr", "<u2")]
)

# Default color (RGBA) for facets without their own: neutral gray, opaque.
_COLOR_MARKER = b"COLOR=" + bytes((176, 180, 186, 255))


def _facets(manifold: Manifold, attr: int = 0) -> np.ndarray:
    """Return the STL facet records of ``manifold``, all with attribute ``attr``."""
    mesh = manifold.to_mesh()
    vertices = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    corners = vertices[np.asarray(mesh.tri_verts, dtype=np.int64)]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, lengths, out=np.zeros_like(normals), where=lengths > 0)

    triangles = np.zeros(len(corners), dtype=_TRIANGLE_DTYPE)
    triangles["normal"] = normals
    triangles["vertices"] = corners
    triangles["attr"] = attr
    return triangles


def _write(path: str | Path, header: bytes, triangles: np.ndarray) -> None:
    header = header[:_HEADER_SIZE].ljust(_HEADER_SIZE, b"\0")
    Path(path).write_bytes(
        header + np.uint32(len(triangles)).tobytes() + triangles.tobytes()
    )


def write_stl(manifold: Manifold, path: str | Path, name: str) -> None:
    """Write ``manifold`` as a deterministic binary STL with per-facet normals."""
    _write(path, name.encode("ascii", "replace"), _facets(manifold))


def _facet_color(rgb: tuple[int, int, int]) -> int:
    """Pack 0-255 RGB into the 15-bit facet color (bit 15 clear = facet color)."""
    r, g, b = (round(channel * 31 / 255) for channel in rgb)
    return r | g << 5 | b << 10


def write_colored_stl(
    parts: Sequence[tuple[Manifold, tuple[int, int, int]]],
    path: str | Path,
    name: str,
) -> None:
    """Write ``parts`` as one binary STL, each part in its own 0-255 RGB color.

    Uses the "Materialise Magics" convention read by three.js's ``STLLoader``:
    the header ends in ``COLOR=`` plus a default RGBA, and each facet's
    attribute holds a 15-bit color (R in bits 0-4, G in 5-9, B in 10-14).
    """
    triangles = np.concatenate(
        [_facets(manifold, _facet_color(rgb)) for manifold, rgb in parts]
    )
    # STLLoader scans the first 70 header bytes for COLOR=, so the name is cut
    # to leave room for the 10-byte marker at the very end.
    prefix = name.encode("ascii", "replace")[: _HEADER_SIZE - len(_COLOR_MARKER)]
    header = prefix.ljust(_HEADER_SIZE - len(_COLOR_MARKER), b"\0") + _COLOR_MARKER
    _write(path, header, triangles)
