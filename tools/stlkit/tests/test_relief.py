import numpy as np
import pytest
from stlkit import assert_printable
from stlkit.bricks import build_brick
from stlkit.relief import heightfield_solid, photo_front, sample_heightmap


def test_heightfield_is_closed_with_recessed_and_raised_regions():
    heights = np.array([[-0.4, 0], [0.2, 0.9]])
    slab = heightfield_solid(heights, 4, 3)
    assert_printable(slab)
    assert len(slab.decompose()) == 1
    assert slab.bounding_box() == pytest.approx((0, 0, 0, 4, 3, 1.41))
    assert slab.volume() > 0


def test_sampling_preserves_orientation_and_zero_background():
    image = np.array([[0, 1], [2, 3]], dtype=float)
    assert sample_heightmap(
        image, np.array([-1, 0, 1, 2]), np.array([-1, 0, 1, 0]), 2, 2
    ) == pytest.approx([0, 1.5, 3, 0])


@pytest.mark.parametrize("studs_deep", [1, 2])
def test_photo_skin_preserves_studs_and_never_cuts_through_front_wall(studs_deep):
    brick = build_brick(studs_y=studs_deep)
    image = np.full((4, 4), -0.45)
    result = photo_front(brick, (0, 0, 0), image, 40, 10, 9.6)
    assert_printable(result)
    assert len(result.decompose()) == 1
    assert result.slice(10.2).area() == pytest.approx(brick.slice(10.2).area())
    # At maximum recess the front surface is still 1.05 mm from the cavity.
    original_front = -(studs_deep * 8 - 0.2) / 2
    assert result.bounding_box()[1] == pytest.approx(original_front + 0.45)


@pytest.mark.parametrize("values", [[[0]], [[-1, 0], [0, 0]], [[0, np.nan], [0, 0]]])
def test_invalid_heightfield_is_rejected(values):
    with pytest.raises(ValueError):
        heightfield_solid(values, 2, 2)
