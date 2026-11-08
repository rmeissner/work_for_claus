"""2D shape helpers returning manifold3d ``CrossSection`` objects (millimeters)."""

import math

from manifold3d import CrossSection, JoinType

CIRCLE_SEGMENTS = 64


def _polygon(vertices: list[tuple[float, float]]) -> CrossSection:
    return CrossSection([vertices])


def regular_polygon(sides: int, radius: float) -> CrossSection:
    """Regular polygon centered on the origin with a vertex at +Y."""
    if sides < 3:
        raise ValueError("a polygon needs at least 3 sides")
    angles = [2 * math.pi * i / sides for i in range(sides)]
    return _polygon([(-radius * math.sin(a), radius * math.cos(a)) for a in angles])


def star(points: int, outer_radius: float, inner_radius: float) -> CrossSection:
    """Star with a tip at +Y: ``2 * points`` vertices alternating tip and notch."""
    if points < 3:
        raise ValueError("a star needs at least 3 points")
    if not 0 < inner_radius < outer_radius:
        raise ValueError("inner_radius must be positive and smaller than outer_radius")
    vertices = []
    for i in range(2 * points):
        radius = outer_radius if i % 2 == 0 else inner_radius
        angle = math.pi * i / points
        vertices.append((-radius * math.sin(angle), radius * math.cos(angle)))
    return _polygon(vertices)


def ring(outer: float, inner: float) -> CrossSection:
    """Annulus centered on the origin."""
    if not 0 < inner < outer:
        raise ValueError("inner must be positive and smaller than outer")
    return CrossSection.circle(outer, CIRCLE_SEGMENTS) - CrossSection.circle(inner, CIRCLE_SEGMENTS)


def bar(start: tuple[float, float], end: tuple[float, float], width: float) -> CrossSection:
    """Rectangle of the given width whose centerline runs from ``start`` to ``end``."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length == 0 or width <= 0:
        raise ValueError("bar needs distinct end points and a positive width")
    nx, ny = -dy / length * width / 2, dx / length * width / 2
    return _polygon(
        [
            (start[0] + nx, start[1] + ny),
            (start[0] - nx, start[1] - ny),
            (end[0] - nx, end[1] - ny),
            (end[0] + nx, end[1] + ny),
        ]
    )


def round_corners(shape: CrossSection, radius: float) -> CrossSection:
    """Round convex corners by offsetting inward, then outward by ``radius``."""
    inset = shape.offset(-radius, JoinType.Round, circular_segments=CIRCLE_SEGMENTS)
    return inset.offset(radius, JoinType.Round, circular_segments=CIRCLE_SEGMENTS)
