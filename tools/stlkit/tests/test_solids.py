import pytest
from manifold3d import Manifold

from stlkit import bar, extrude, layout_on_plate, star


def test_extrude_volume_is_area_times_height() -> None:
    shape = star(5, 45, 22)
    solid = extrude(shape, 3)
    assert solid.status().name == "NoError"
    assert solid.volume() == pytest.approx(shape.area() * 3)


def test_layout_on_plate_places_parts_apart_on_z0() -> None:
    parts = [Manifold.cube((10, 20, 3)).translate((5, 5, 7)), extrude(bar((0, 0), (30, 0), 4), 2)]
    plate = layout_on_plate(parts, 5)
    x0, y0, z0, x1, y1, _ = plate.bounding_box()
    assert z0 == pytest.approx(0)
    assert (x0 + x1, y0 + y1) == pytest.approx((0, 0))
    first, second = sorted(p.bounding_box() for p in plate.decompose())
    assert second[0] - first[3] == pytest.approx(5)
    assert x1 - x0 == pytest.approx(10 + 5 + 30)
