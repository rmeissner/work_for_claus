import pytest
from manifold3d import Manifold
from stlkit import assert_printable


def test_accepts_cube_on_the_bed() -> None:
    assert_printable(Manifold.cube((20, 20, 20)))


def test_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        assert_printable(Manifold())


def test_rejects_part_below_the_bed() -> None:
    with pytest.raises(ValueError, match="Z = 0"):
        assert_printable(Manifold.cube((5, 5, 5)).translate((0, 0, -1)))


def test_rejects_part_floating_above_the_bed() -> None:
    with pytest.raises(ValueError, match="Z = 0"):
        assert_printable(Manifold.cube((5, 5, 5)).translate((0, 0, 1)))


def test_rejects_oversized_part() -> None:
    assert_printable(Manifold.cube((50, 5, 5)), max_size=(50, 50, 50))
    with pytest.raises(ValueError, match="exceeds"):
        assert_printable(Manifold.cube((51, 5, 5)), max_size=(50, 50, 50))
