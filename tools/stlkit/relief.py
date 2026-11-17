"""Watertight grayscale height fields and shallow relief on brick fronts."""

import math

import numpy as np
from manifold3d import Error, Manifold, Mesh

from .bricks import BODY_HEIGHT


def heightfield_solid(heights, width, height, *, base_depth=0.51):
    """A closed XY slab whose top Z is base_depth plus a 2D height array.

    Array row zero is the bottom edge. Negative heights engrave the slab;
    positive heights emboss it. The back remains planar at Z = 0.
    """
    values = np.asarray(heights, dtype=float)
    if (
        values.ndim != 2
        or min(values.shape) < 2
        or not np.isfinite(values).all()
        or width <= 0
        or height <= 0
        or base_depth + values.min() <= 0
    ):
        raise ValueError("height field needs a finite grid and positive slab thickness")
    rows, columns = values.shape
    x, y = np.meshgrid(np.linspace(0, width, columns), np.linspace(0, height, rows))
    count = rows * columns
    top = np.column_stack((x.ravel(), y.ravel(), (base_depth + values).ravel()))
    bottom = np.column_stack((x.ravel(), y.ravel(), np.zeros(count)))
    vertices = np.concatenate((top, bottom)).astype(np.float32)
    triangles = []
    for row in range(rows - 1):
        for col in range(columns - 1):
            a = row * columns + col
            b, c, d = a + 1, a + columns, a + columns + 1
            triangles.extend(((a, b, d), (a, d, c)))
            triangles.extend(
                ((a + count, d + count, b + count), (a + count, c + count, d + count))
            )
    # Follow the perimeter counter-clockwise, then close its vertical skirt.
    boundary = list(range(columns))
    boundary += [row * columns + columns - 1 for row in range(1, rows)]
    boundary += list(range(count - 2, count - columns - 1, -1))
    boundary += [row * columns for row in range(rows - 2, 0, -1)]
    for a, b in zip(boundary, boundary[1:] + boundary[:1], strict=True):
        triangles.extend(((a, a + count, b + count), (a, b + count, b)))
    solid = Manifold(Mesh(vertices, np.asarray(triangles, dtype=np.uint32)))
    if solid.status() != Error.NoError or solid.is_empty():
        raise ValueError(f"invalid height-field mesh: {solid.status()}")
    return solid


def sample_heightmap(values, x, y, width, height):
    """Bilinearly sample a centered height map; outside the image is flat zero."""
    values = np.asarray(values)
    gx = (np.asarray(x) / width + 0.5) * (values.shape[1] - 1)
    gy = (np.asarray(y) / height + 0.5) * (values.shape[0] - 1)
    inside = (
        (gx >= 0)
        & (gx <= values.shape[1] - 1)
        & (gy >= 0)
        & (gy <= values.shape[0] - 1)
    )
    gx, gy = np.clip(gx, 0, values.shape[1] - 1), np.clip(gy, 0, values.shape[0] - 1)
    ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int)
    jx, jy = (
        np.minimum(ix + 1, values.shape[1] - 1),
        np.minimum(iy + 1, values.shape[0] - 1),
    )
    tx, ty = gx - ix, gy - iy
    result = (1 - ty) * ((1 - tx) * values[iy, ix] + tx * values[iy, jx])
    result += ty * ((1 - tx) * values[jy, ix] + tx * values[jy, jx])
    return np.where(inside, result, 0)


def photo_front(
    brick, position, image, image_width, image_height, wall_height, *, spacing=0.35
):
    """Replace the front skin; preserve studs, underside supports and other faces."""
    if spacing <= 0 or np.min(image) < -0.45 or np.max(image) > 0.90001:
        raise ValueError(
            "relief must stay within -0.45 to +0.9 mm and use positive spacing"
        )
    x0, y0, _, x1, _, _ = brick.bounding_box()
    width = x1 - x0
    columns, rows = math.ceil(width / spacing) + 1, math.ceil(BODY_HEIGHT / spacing) + 1
    xs = np.linspace(x0 + position[0], x1 + position[0], columns)
    zs = np.linspace(position[2], position[2] + BODY_HEIGHT, rows) - wall_height / 2
    x, z = np.meshgrid(xs, zs)
    heights = sample_heightmap(image, x, z, image_width, image_height)
    skin = heightfield_solid(heights, width, BODY_HEIGHT)
    skin = skin.rotate((90, 0, 0)).translate((x0, y0 + 0.51, 0))
    # Leave 0.01 mm overlap between the replacement skin and original body.
    old_face = Manifold.cube((width + 0.02, 0.6, BODY_HEIGHT + 0.02)).translate(
        (x0 - 0.01, y0 - 0.1, -0.01)
    )
    return (brick - old_face) + skin
