import math

import pytest
from stlkit import bar, regular_polygon, ring, round_corners, star


def test_star_vertices_alternate_between_radii() -> None:
    shape = star(5, 45, 22)
    vertices = shape.to_polygons()[0]
    assert len(vertices) == 10
    radii = sorted(math.hypot(x, y) for x, y in vertices)
    assert radii[:5] == pytest.approx([22] * 5)
    assert radii[5:] == pytest.approx([45] * 5)
    assert shape.bounds()[3] == pytest.approx(45)  # tip at +Y


def test_star_rejects_bad_radii() -> None:
    with pytest.raises(ValueError):
        star(5, 10, 20)


def test_regular_polygon_area() -> None:
    assert regular_polygon(6, 10).area() == pytest.approx(3 * math.sqrt(3) / 2 * 100)


def test_ring_area() -> None:
    assert ring(4, 2).area() == pytest.approx(math.pi * 12, rel=0.01)


def test_bar_has_expected_length_and_width() -> None:
    shape = bar((0, 0), (30, 40), 2)
    assert shape.area() == pytest.approx(50 * 2)
    x0, y0, x1, y1 = shape.bounds()
    assert (x1 - x0, y1 - y0) == pytest.approx((30 + 2 * 0.8, 40 + 2 * 0.6))


def test_round_corners_keeps_area_within_tolerance() -> None:
    shape = star(5, 45, 22)
    rounded = round_corners(shape, 1.0)
    assert rounded.area() < shape.area()
    assert rounded.area() == pytest.approx(shape.area(), rel=0.03)
