import math
from pathlib import Path

import pytest
from manifold3d import CrossSection, JoinType
from stlkit import assert_printable, load_script, write_stl

generate = load_script(Path(__file__).with_name("generate.py"))

MIN_WALL = 2.0
TIP_ZONE = (
    8.0  # tips taper to a point by nature; walls are only checked outside this radius
)


@pytest.fixture(scope="module", params=["a", "b"])
def part(request):
    return {"a": generate.part_a_2d, "b": generate.part_b_2d}[request.param]()


def strip(part, y, half_width, height=0.1):
    """Area of ``part`` inside a thin horizontal strip around the vertical axis."""
    probe = CrossSection.square((2 * half_width, height)).translate((-half_width, y))
    return (part ^ probe).area()


def test_parts_are_printable():
    for solid in generate.parts():
        assert_printable(solid)
        assert solid.bounding_box()[5] == pytest.approx(generate.THICKNESS)
    assert_printable(generate.build_plate())


def test_plate_fits_the_build_volume():
    x0, y0, z0, x1, y1, z1 = generate.build_plate().bounding_box()
    assert (x1 - x0, y1 - y0, z1 - z0) < (220, 220, 250)


def test_each_part_is_one_connected_piece(part):
    assert len(part.decompose()) == 1
    assert len(generate.extrude(part, generate.THICKNESS).decompose()) == 1


def test_slot_width():
    spine = generate.SPINE_WIDTH / 2 - 0.01
    # A is slotted below the meeting point, B above it; the spine is solid on both sides of the slot.
    for y, part in ((-10, generate.part_a_2d()), (30, generate.part_b_2d())):
        assert strip(part, y, spine) / 0.1 == pytest.approx(
            2 * spine - generate.SLOT_WIDTH
        )
    assert generate.SLOT_WIDTH == pytest.approx(
        generate.THICKNESS + generate.SLOT_CLEARANCE
    )


def test_slot_lengths_add_up_to_the_axis_length():
    def slot_length(part, y0, y1, step=0.25):
        """Length of the axis between y0 and y1 where the part has no material at x = 0."""
        ys = [y0 + step * i for i in range(int((y1 - y0) / step))]
        return sum(step for y in ys if strip(part, y, 0.5, step) == 0)

    top = generate.tip_y()  # the rounded tip is a little lower than OUTER_RADIUS
    a = slot_length(generate.part_a_2d(), -generate.INNER_RADIUS, top)
    b = slot_length(generate.part_b_2d(), -generate.INNER_RADIUS, top)
    assert a == pytest.approx(generate.SLOT_MEETING + generate.INNER_RADIUS, abs=0.3)
    assert b == pytest.approx(top - generate.SLOT_MEETING, abs=0.3)
    assert a + b == pytest.approx(top + generate.INNER_RADIUS, abs=0.5)


def test_parts_slot_together_without_collision():
    a, b = generate.assembled()
    assert a.volume() > 0 and b.volume() > 0
    assert (a ^ b).volume() == pytest.approx(0, abs=1e-6)
    # B really stands at right angles to A, both centered on the vertical axis.
    ax = a.bounding_box()
    bx = b.bounding_box()
    assert ax[1] == pytest.approx(-generate.THICKNESS / 2) and ax[4] == pytest.approx(
        generate.THICKNESS / 2
    )
    assert bx[0] == pytest.approx(-generate.THICKNESS / 2) and bx[3] == pytest.approx(
        generate.THICKNESS / 2
    )


def test_parts_have_no_thin_walls(part):
    """Opening the part by half the minimum wall must only change the tapering tips."""
    r = MIN_WALL / 2 - 0.05
    opened = part.offset(-r, JoinType.Miter).offset(r, JoinType.Miter)
    tips = CrossSection.compose(
        [
            CrossSection.circle(TIP_ZONE, 32).translate(
                (
                    -generate.OUTER_RADIUS
                    * math.sin(math.pi * 2 * i / generate.POINTS),
                    generate.OUTER_RADIUS * math.cos(math.pi * 2 * i / generate.POINTS),
                )
            )
            for i in range(generate.POINTS)
        ]
    )
    assert ((part - opened) - tips).area() == pytest.approx(0, abs=0.5)
    assert len(opened.decompose()) == 1


def test_combined_is_both_parts_standing_on_the_plate_level():
    combined = generate.build_combined()
    part_a, part_b = generate.parts()
    assert combined.volume() == pytest.approx(part_a.volume() + part_b.volume())
    x0, y0, z0, x1, y1, z1 = combined.bounding_box()
    assert z0 == pytest.approx(0)
    assert all(
        size < limit
        for size, limit in zip(
            (x1 - x0, y1 - y0, z1 - z0), (220, 220, 250), strict=True
        )
    )


def test_committed_stls_are_up_to_date(tmp_path):
    part_a, part_b = generate.parts()
    for solid, committed in (
        (generate.build_plate(), generate.OUTPUT),
        (part_a, generate.PART_A_OUTPUT),
        (part_b, generate.PART_B_OUTPUT),
        (generate.build_combined(), generate.COMBINED_OUTPUT),
    ):
        fresh = tmp_path / committed.name
        write_stl(solid, fresh, committed.stem)
        assert committed.read_bytes() == fresh.read_bytes(), committed.name
