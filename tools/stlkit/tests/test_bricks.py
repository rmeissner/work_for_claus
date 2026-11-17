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
