"""Binary STL export."""

from pathlib import Path

import numpy as np
from manifold3d import Manifold

_HEADER_SIZE = 80
_TRIANGLE_DTYPE = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attr", "<u2")])


def write_stl(manifold: Manifold, path: str | Path, name: str) -> None:
    """Write ``manifold`` as a deterministic binary STL with per-facet normals."""
    mesh = manifold.to_mesh()
    vertices = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    corners = vertices[np.asarray(mesh.tri_verts, dtype=np.int64)]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, lengths, out=np.zeros_like(normals), where=lengths > 0)

    triangles = np.zeros(len(corners), dtype=_TRIANGLE_DTYPE)
    triangles["normal"] = normals
    triangles["vertices"] = corners
    header = name.encode("ascii", "replace")[:_HEADER_SIZE].ljust(_HEADER_SIZE, b"\0")
    Path(path).write_bytes(header + np.uint32(len(triangles)).tobytes() + triangles.tobytes())
