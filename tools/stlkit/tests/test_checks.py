import pytest
from manifold3d import CrossSection, Manifold
from stlkit import (
    assert_printable,
    assert_rounded,
    assert_supported,
    round_corners,
    worst_unsupported_layer,
)


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


def test_supported_accepts_a_cube_and_a_45_degree_overhang() -> None:
    assert_supported(Manifold.cube((20, 20, 20)))
    wedge = CrossSection([[(0, 0), (10, 0), (10, 10), (-10, 10)]])
    assert_supported(
        Manifold.extrude(wedge, 10).rotate((90, 0, 0)).translate((0, 10, 0))
    )


def test_supported_rejects_a_flat_ledge() -> None:
    post = Manifold.cube((5, 5, 20))
    ledge = Manifold.cube((15, 5, 2)).translate((0, 0, 10))
    with pytest.raises(ValueError, match="unsupported"):
        assert_supported(post + ledge)


def test_supported_ignores_a_short_bridge_only() -> None:
    def arch(gap: float) -> Manifold:
        left = Manifold.cube((5, 5, 10))
        right = Manifold.cube((5, 5, 10)).translate((5 + gap, 0, 0))
        roof = Manifold.cube((10 + gap, 5, 2)).translate((0, 0, 10))
        return left + right + roof

    assert_supported(arch(4))
    with pytest.raises(ValueError, match="unsupported"):
        assert_supported(arch(12))


def _two_posts_and_slab(overhang: float) -> Manifold:
    """Two 3 mm posts, 3 mm apart, under a slab that runs ``overhang`` past them on one side."""
    left = Manifold.cube((3, 3, 5))
    right = Manifold.cube((3, 3, 5)).translate((6, 0, 0))
    slab = Manifold.cube((9, 3 + overhang, 2)).translate((0, 0, 5))
    return left + right + slab


def test_supported_rejects_a_ledge_past_two_posts_on_one_side() -> None:
    # Both posts touch the ledge along the same edge, so it is a cantilever, not a bridge.
    model = _two_posts_and_slab(2)
    _, area = worst_unsupported_layer(model)
    assert area > 5
    with pytest.raises(ValueError, match="unsupported"):
        assert_supported(model)


def test_supported_accepts_a_short_bridge_between_two_posts() -> None:
    # Same posts, but the slab ends flush with them: only the gap between them is bridged.
    assert_supported(_two_posts_and_slab(0))
