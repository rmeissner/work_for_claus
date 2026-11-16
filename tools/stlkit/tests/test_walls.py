import pytest
from manifold3d import Manifold
from stlkit import assert_printable
from stlkit.walls import wall_parts, wall_print_plate


def test_four_brick_wall_has_plain_backs_and_separate_printable_parts():
    bricks = wall_parts(
        "Käte", ((4, 4), (4, 4)), ("bottom", "top"), text_width=54, text_height=14
    )
    assert len(bricks) == 4
    for _, part, _, _ in bricks:
        assert_printable(part)
        assert len(part.decompose()) == 1
        # No back markings: a patch spanning the whole back remains solid.
        patch = Manifold.cube((31.8, 0.3, 6)).translate((-15.9, 7.6, 0))
        assert (patch - part).volume() < 1e-6
    plate = wall_print_plate(bricks)
    assert len(plate.decompose()) == 4
    assert plate.bounding_box() == pytest.approx((-34.3, -18.3, 0, 34.3, 18.3, 11.4))
    for index, (_, a, pa, _) in enumerate(bricks):
        for _, b, pb, _ in bricks[index + 1 :]:
            assert abs((a.translate(pa) ^ b.translate(pb)).volume()) < 1e-6


@pytest.mark.parametrize(
    "courses,names,depth",
    [
        (((4, 4), (4,)), ("bottom", "top"), 0.6),
        (((4, 4),), (), 0.6),
        (((4, 4),), ("bottom",), 1.5),
    ],
)
def test_invalid_wall_geometry_is_rejected(courses, names, depth):
    with pytest.raises(ValueError):
        wall_parts(
            "Käte", courses, names, text_width=54, text_height=14, imprint_depth=depth
        )
