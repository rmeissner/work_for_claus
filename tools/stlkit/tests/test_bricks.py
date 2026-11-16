import pytest
from stlkit import assert_printable
from stlkit.bricks import build_brick


@pytest.mark.parametrize("columns", [2, 4])
def test_bricks_are_connected_and_stack_without_interference(columns):
    brick = build_brick(columns)
    assert_printable(brick)
    assert len(brick.decompose()) == 1
    assert brick.bounding_box() == pytest.approx(
        (-(columns * 8 - 0.2) / 2, -7.9, 0, (columns * 8 - 0.2) / 2, 7.9, 11.4)
    )
    assert abs((brick ^ brick.translate((0, 0, 9.6))).volume()) < 1e-6


def test_looser_fit_preserves_body_bounds_and_reduces_material():
    nominal = build_brick()
    loose = build_brick(fit_adjustment=0.05)
    assert loose.bounding_box() == pytest.approx(nominal.bounding_box())
    assert loose.volume() < nominal.volume()


@pytest.mark.parametrize("columns,adjustment", [(1, 0), (2.5, 0), (4, 1)])
def test_invalid_brick_dimensions_are_rejected(columns, adjustment):
    with pytest.raises(ValueError):
        build_brick(columns, fit_adjustment=adjustment)
