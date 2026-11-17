import pytest
from manifold3d import Manifold
from stlkit import assert_printable
from stlkit.bricks import build_brick
from stlkit.walls import wall_parts, wall_print_plate


def test_four_brick_wall_has_plain_backs_and_separate_printable_parts():
    bricks = wall_parts(
        "Käte", ((4, 2), (2, 4)), ("bottom", "top"), text_width=40, text_height=14
    )
    assert len(bricks) == 4
    widths = [
        round(part.bounding_box()[3] - part.bounding_box()[0], 1)
        for _, part, _, _ in bricks
    ]
    assert widths == [31.8, 15.8, 15.8, 31.8]
    # The full bricks bridge the joints in the opposite courses.
    lower_full = bricks[0]
    upper_full = bricks[3]
    assert lower_full[2][0] - 15.9 < -8 < lower_full[2][0] + 15.9
    assert upper_full[2][0] - 15.9 < 8 < upper_full[2][0] + 15.9
    for _, part, _, _ in bricks:
        assert_printable(part)
        assert len(part.decompose()) == 1
        # No back markings: a patch spanning the whole back remains solid.
        x0, _, _, x1, _, _ = part.bounding_box()
        patch = Manifold.cube((x1 - x0, 0.3, 6)).translate((x0, 7.6, 0))
        assert (patch - part).volume() < 1e-6
    plate = wall_print_plate(bricks)
    assert len(plate.decompose()) == 4
    assert plate.bounding_box() == pytest.approx((-26.3, -18.3, 0, 26.3, 18.3, 11.4))
    for index, (_, a, pa, _) in enumerate(bricks):
        for _, b, pb, _ in bricks[index + 1 :]:
            grip = a.translate(pa) ^ b.translate(pb)
            if pa[2] == pb[2]:
                assert abs(grip.volume()) < 1e-6
            elif not grip.is_empty():
                # The enlarged studs intentionally compress at mating surfaces.
                assert grip.bounding_box()[2] >= max(pa[2], pb[2]) - 1e-6
                assert grip.bounding_box()[5] <= max(pa[2], pb[2]) + 1.8 + 1e-6


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
            "Käte", courses, names, text_width=40, text_height=14, imprint_depth=depth
        )


def test_thin_wall_plate_spacing_uses_the_actual_brick_depth():
    brick = build_brick(2, studs_y=1)
    parts = [(str(index), brick, (0, 0, 0), index // 2) for index in range(4)]
    plate = wall_print_plate(parts)
    assert_printable(plate)
    assert len(plate.decompose()) == 4
    assert plate.bounding_box() == pytest.approx((-18.3, -10.3, 0, 18.3, 10.3, 11.4))
