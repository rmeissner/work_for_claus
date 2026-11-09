import pytest
from manifold3d import Manifold
from stlkit import bar, center_of_mass, extrude, layout_on_plate, star


def test_extrude_volume_is_area_times_height() -> None:
    shape = star(5, 45, 22)
    solid = extrude(shape, 3)
    assert solid.status().name == "NoError"
    assert solid.volume() == pytest.approx(shape.area() * 3)


def test_layout_on_plate_places_parts_apart_on_z0() -> None:
    parts = [
        Manifold.cube((10, 20, 3)).translate((5, 5, 7)),
        extrude(bar((0, 0), (30, 0), 4), 2),
    ]
    plate = layout_on_plate(parts, 5)
    x0, y0, z0, x1, y1, _ = plate.bounding_box()
    assert z0 == pytest.approx(0)
    assert (x0 + x1, y0 + y1) == pytest.approx((0, 0))
    first, second = sorted(p.bounding_box() for p in plate.decompose())
    assert second[0] - first[3] == pytest.approx(5)
    assert x1 - x0 == pytest.approx(10 + 5 + 30)


def test_layout_on_plate_with_columns_fills_rows() -> None:
    parts = [Manifold.cube((10 + i, 20, 3)) for i in range(4)]
    plate = layout_on_plate(parts, 5, columns=2)
    x0, y0, z0, x1, y1, _ = plate.bounding_box()
    assert z0 == pytest.approx(0)
    assert (x0 + x1, y0 + y1) == pytest.approx((0, 0))
    assert x1 - x0 == pytest.approx(12 + 5 + 13)
    assert y1 - y0 == pytest.approx(20 + 5 + 20)
    boxes = sorted(
        (p.bounding_box() for p in plate.decompose()), key=lambda b: (-b[1], b[0])
    )
    top, bottom = boxes[:2], boxes[2:]
    assert top[0][1] == pytest.approx(bottom[0][4] + 5)
    for row in (top, bottom):
        assert row[1][0] - row[0][3] == pytest.approx(5)
    for a, b in zip(top, bottom, strict=True):
        assert a[1] > b[4]


def test_layout_on_plate_columns_none_is_one_row() -> None:
    parts = [
        Manifold.cube((10, 20, 3)),
        Manifold.cube((12, 8, 3)),
        Manifold.cube((7, 7, 3)),
    ]
    default = layout_on_plate(parts, 5)
    explicit = layout_on_plate(parts, 5, columns=3)
    assert default.bounding_box() == explicit.bounding_box()
    assert default.volume() == pytest.approx(explicit.volume())
    assert default.bounding_box()[4] - default.bounding_box()[1] == pytest.approx(20)


def test_center_of_mass_of_translated_cube_is_its_center() -> None:
    cube = Manifold.cube((2, 4, 6)).translate((10, -3, 5))
    assert center_of_mass(cube) == pytest.approx((11, -1, 8))


def test_center_of_mass_of_l_shape_matches_analytic_value() -> None:
    # 3x1x1 bar (volume 3, center x=1.5, y=.5) plus 1x1x1 cube on top at x 0..1 (center .5, 1.5).
    l_shape = Manifold.cube((3, 1, 1)) + Manifold.cube((1, 1, 1)).translate((0, 1, 0))
    assert center_of_mass(l_shape) == pytest.approx(
        ((3 * 1.5 + 0.5) / 4, (3 * 0.5 + 1.5) / 4, 0.5)
    )


def test_center_of_mass_of_empty_manifold_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        center_of_mass(Manifold())
