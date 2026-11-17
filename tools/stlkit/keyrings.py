"""Internally reinforced key-ring passages for hollow interlocking bricks."""

import math
from itertools import pairwise

from manifold3d import Manifold

from .bricks import BODY_HEIGHT

_SEGMENTS = 64
_CLUTCH_CLEARANCE = 2.0  # mating studs reach only 1.8 mm above the bottom
_SLEEVE_WALL = 1.2
_BEND_RADIUS = 3.0


def _sweep(points, radius):
    """Round a polyline with spherical joints, preserving its bore radius."""
    result = Manifold()
    for a, b in pairwise(points):
        dx, dz = b[0] - a[0], b[2] - a[2]
        result += (
            Manifold.cylinder(math.hypot(dx, dz), radius, circular_segments=_SEGMENTS)
            .rotate((0, math.degrees(math.atan2(dx, dz)), 0))
            .translate(a)
        )
    for point in points[1:-1]:
        result += Manifold.sphere(radius, _SEGMENTS).translate(point)
    return result


def with_keyring_passage(brick: Manifold, diameter: float = 5.0) -> Manifold:
    """Connect left-face center to body-top center with a nominal round bore.

    The passage turns upward before the top exit, preserving the top studs.
    An internal 1.2 mm sleeve reinforces it; the bottom 2 mm is left clear so
    receiving studs still fit. Both ports and the whole passage are 5 mm with
    the default diameter. The bent passage is for feeding a split key ring.
    """
    if not 0 < diameter / 2 < BODY_HEIGHT / 2 - _CLUTCH_CLEARANCE:
        raise ValueError("hole would reach the underside clutch clearance")
    x0, y0, _, x1, y1, _ = brick.bounding_box()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    radius = diameter / 2
    margin = radius + _SLEEVE_WALL + 1
    points = [(x0 - margin, cy, BODY_HEIGHT / 2)]
    for step in range(9):
        angle = math.pi / 2 * step / 8
        points.append(
            (
                cx - _BEND_RADIUS + _BEND_RADIUS * math.sin(angle),
                cy,
                BODY_HEIGHT / 2 + _BEND_RADIUS * (1 - math.cos(angle)),
            )
        )
    points.append((cx, cy, BODY_HEIGHT + margin))
    interior = Manifold.cube(
        (x1 - x0, y1 - y0, BODY_HEIGHT - _CLUTCH_CLEARANCE)
    ).translate((x0, y0, _CLUTCH_CLEARANCE))
    reinforced = brick + (_sweep(points, radius + _SLEEVE_WALL) ^ interior)
    result = reinforced - _sweep(points, radius)
    # Where the sleeve meets old clutch tubes, tiny sealed air pockets can
    # form. Fill those enclosed void shells for a solid, printable reinforcement.
    solids = [part for part in result.decompose() if part.volume() > 0]
    if len(solids) != 1:
        raise ValueError("key-ring passage disconnected the brick")
    return solids[0]
