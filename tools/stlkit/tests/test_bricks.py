import pytest
from manifold3d import Manifold
from stlkit import assert_printable
from stlkit.bricks import build_brick


@pytest.mark.parametrize("columns", [2, 4])
def test_bricks_are_connected_with_compensated_grip_at_studs_only(columns):
    brick = build_brick(columns)
    assert_printable(brick)
    assert len(brick.decompose()) == 1
    assert brick.bounding_box() == pytest.approx(
        (-(columns * 8 - 0.2) / 2, -7.9, 0, (columns * 8 - 0.2) / 2, 7.9, 11.4)
    )
    grip = brick ^ brick.translate((0, 0, 9.6))
    assert grip.volume() > 0
    assert grip.bounding_box()[2] >= 9.6 - 1e-6
    assert grip.bounding_box()[5] <= 11.4 + 1e-6


def test_larger_studs_preserve_the_tested_underside():
    original = build_brick(stud_diameter=4.8)
    enlarged = build_brick()
    body_region = Manifold.cube((40, 20, 9.6)).translate((-20, -10, 0))
    old_body, new_body = original ^ body_region, enlarged ^ body_region
    assert (old_body - new_body).is_empty()
    assert (new_body - old_body).is_empty()
    assert abs((original ^ original.translate((0, 0, 9.6))).volume()) < 1e-6
    studs = enlarged.slice(10.2).decompose()
    assert len(studs) == 8
    for stud in studs:
        x0, y0, x1, y1 = stud.bounds()
        assert (x1 - x0, y1 - y0) == pytest.approx((5.0, 5.0))


def test_looser_fit_preserves_body_bounds_and_reduces_material():
    nominal = build_brick()
    loose = build_brick(fit_adjustment=0.05)
    assert loose.bounding_box() == pytest.approx(nominal.bounding_box())
    assert loose.volume() < nominal.volume()


@pytest.mark.parametrize("columns,adjustment", [(1, 0), (2.5, 0), (4, 1)])
def test_invalid_brick_dimensions_are_rejected(columns, adjustment):
    with pytest.raises(ValueError):
        build_brick(columns, fit_adjustment=adjustment)


@pytest.mark.parametrize("columns", [2, 4])
def test_thin_bricks_have_one_stud_row_and_solid_clutch_pins(columns):
    brick = build_brick(columns, studs_y=1)
    assert_printable(brick)
    assert len(brick.decompose()) == 1
    assert brick.bounding_box() == pytest.approx(
        (-(columns * 8 - 0.2) / 2, -3.9, 0, (columns * 8 - 0.2) / 2, 3.9, 11.4)
    )
    studs = sorted(brick.slice(10.2).decompose(), key=lambda s: s.bounds()[0])
    assert len(studs) == columns
    for index, stud in enumerate(studs):
        x0, y0, x1, y1 = stud.bounds()
        assert (x1 - x0, y1 - y0) == pytest.approx((5, 5))
        assert (x0 + x1) / 2 == pytest.approx((index - (columns - 1) / 2) * 8)
        assert y0 + y1 == pytest.approx(0)
    # A lower section contains the shell and N-1 separate solid support pins.
    sections = brick.slice(1).decompose()
    assert len(sections) == columns
    pins = sorted(sections, key=lambda s: s.area())[:-1]
    assert len(pins) == columns - 1
    for pin in pins:
        assert len(pin.to_polygons()) == 1  # no bore in a one-row support
        x0, y0, x1, y1 = pin.bounds()
        assert (x1 - x0, y1 - y0) == pytest.approx((3.2, 3.2))
    nominal = build_brick(columns, studs_y=1, stud_diameter=4.8)
    assert abs((nominal ^ nominal.translate((0, 0, 9.6))).volume()) < 1e-6


@pytest.mark.parametrize("depth", [0, 3, 1.5])
def test_invalid_stud_depth_is_rejected(depth):
    with pytest.raises(ValueError):
        build_brick(studs_y=depth)
