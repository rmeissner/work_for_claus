import pytest
from manifold3d import CrossSection
from stlkit.text import text_shape


def test_text_fits_box_without_distorting_letters():
    wide = text_shape("Meissner", width=84, height=20)
    x0, y0, x1, y1 = wide.bounds()
    assert (x0 + x1, y0 + y1) == pytest.approx((0, 0))
    assert x1 - x0 == pytest.approx(84)
    assert 10 < y1 - y0 < 20
    small = text_shape("Meissner", width=42, height=10)
    assert small.area() == pytest.approx(wide.area() / 4)


def test_text_keeps_letter_counters_open():
    letter = text_shape("O", width=10, height=10)
    center = CrossSection.square((0.2, 0.2), center=True)
    assert (letter ^ center).is_empty()
    assert len(letter.decompose()) == 1


@pytest.mark.parametrize(
    "text,width,height", [(" ", 10, 10), ("a", 0, 10), ("a", 10, -1), ("Ж", 10, 10)]
)
def test_text_rejects_invalid_input(text, width, height):
    with pytest.raises(ValueError):
        text_shape(text, width=width, height=height)


def test_umlaut_keeps_both_dots_above_the_letter():
    letter = text_shape("ä", width=10, height=10)
    pieces = sorted(letter.decompose(), key=lambda p: p.area())
    assert len(pieces) == 3
    dot_a, dot_b, body = pieces
    assert dot_a.area() == pytest.approx(dot_b.area(), rel=0.03)
    assert min(dot_a.bounds()[1], dot_b.bounds()[1]) > body.bounds()[3]
