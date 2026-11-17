import pytest
from manifold3d import CrossSection, Manifold
from stlkit import assert_printable
from stlkit.bricks import build_brick
from stlkit.keyrings import with_keyring_passage
from stlkit.walls import wall_parts


@pytest.mark.parametrize("columns", [2, 4])
def test_passage_has_five_mm_ports_preserves_studs_and_clutch(columns):
    original = build_brick(columns)
    result = with_keyring_passage(original)
    assert_printable(result)
    assert len(result.decompose()) == 1
    assert result.bounding_box() == pytest.approx(original.bounding_box())
    # Both centered openings accept a 5 mm circular section.
    probe = CrossSection.circle(2.5, 64)
    assert (result.slice(9.55) ^ probe).area() < 1e-6
    half_length = (columns * 8 - 0.2) / 2
    side = result.rotate((0, 90, 0)).slice(half_length - 0.05)
    assert (side ^ probe.translate((4.8, 0))).area() < 1e-6
    # The curved path stays clear of the top studs and underside engagement.
    for z in (0.5, 1.8, 10.2, 11.3):
        old, new = original.slice(z), result.slice(z)
        assert (old - new).area() < 1e-6
        assert (new - old).area() < 1e-6
    # A split ring can follow the straight entry leg into the upward bend.
    entry = Manifold.cylinder(half_length - 3, 2.49, circular_segments=64)
    entry = entry.rotate((0, 90, 0)).translate((-half_length, 0, 4.8))
    assert (entry ^ result).volume() < 1e-6


def test_oversized_passage_is_rejected():
    with pytest.raises(ValueError):
        with_keyring_passage(build_brick(), 6)


def test_wall_passage_changes_only_the_upper_left_brick():
    args = ("Carlo", ((4, 4), (2, 4, 2)), ("bottom", "top"))
    original = wall_parts(*args, text_width=54, text_height=14)
    modified = wall_parts(*args, text_width=54, text_height=14, keyring_diameter=5)
    for (name, before, _, _), (_, after, _, _) in zip(original, modified, strict=True):
        difference = (before - after).volume() + (after - before).volume()
        if name == "top-1":
            assert difference > 0
        else:
            assert difference == pytest.approx(0, abs=1e-6)
