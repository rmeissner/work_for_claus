import pytest
from manifold3d import CrossSection, Manifold
from stlkit import assert_printable, assert_rounded, round_corners


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


def test_assert_rounded_accepts_rounded_square() -> None:
    square = CrossSection.square((30, 30))
    assert_rounded(round_corners(square, 3), 3)


def test_assert_rounded_rejects_plain_square() -> None:
    with pytest.raises(ValueError, match="sharper"):
        assert_rounded(CrossSection.square((30, 30)), 3)


def test_assert_rounded_rejects_smaller_radius() -> None:
    square = CrossSection.square((30, 30))
    with pytest.raises(ValueError, match="sharper"):
        assert_rounded(round_corners(square, 1), 3)


def test_assert_rounded_catches_one_sharp_corner_on_a_large_outline() -> None:
    rect = CrossSection.square((200, 50))
    corner = CrossSection.square((2, 2))
    rounded = round_corners(rect, 2)
    assert_rounded(rounded, 2)
    # Put the sharp corner back at the origin only.
    one_sharp = rounded + corner
    with pytest.raises(ValueError, match="sharper"):
        assert_rounded(one_sharp, 2)
