import struct
from pathlib import Path

import numpy as np
from manifold3d import Manifold

from stlkit import extrude, star, write_stl


def read_records(path: Path) -> np.ndarray:
    """Return the 50-byte triangle records, checking the header and file size."""
    data = path.read_bytes()
    (count,) = struct.unpack_from("<I", data, 80)
    assert len(data) == 84 + 50 * count
    return np.frombuffer(data, dtype=np.uint8, offset=84).reshape(count, 50)


def test_writes_valid_binary_stl(tmp_path: Path) -> None:
    solid = extrude(star(5, 45, 22), 3)
    path = tmp_path / "star.stl"
    write_stl(solid, path, "star")
    assert path.read_bytes()[:4] == b"star"
    assert len(read_records(path)) == solid.num_tri()


def test_normals_point_outward(tmp_path: Path) -> None:
    path = tmp_path / "cube.stl"
    write_stl(Manifold.cube((2, 2, 2), center=True), path, "cube")
    records = read_records(path)
    normals = records[:, :12].copy().view("<f4").reshape(-1, 3)
    centroids = records[:, 12:48].copy().view("<f4").reshape(-1, 3, 3).mean(axis=1)
    assert np.all(np.einsum("ij,ij->i", normals, centroids) > 0)


def test_output_is_deterministic(tmp_path: Path) -> None:
    for name in ("a", "b"):
        write_stl(extrude(star(5, 45, 22), 3), tmp_path / f"{name}.stl", "star")
    assert (tmp_path / "a.stl").read_bytes() == (tmp_path / "b.stl").read_bytes()
