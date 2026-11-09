import math
from itertools import combinations
from pathlib import Path

import pytest
from manifold3d import CrossSection
from stlkit import assert_printable, load_script, write_stl

generate = load_script(Path(__file__).with_name("generate.py"))

PART_IDS = list(range(generate.PARTS))


@pytest.fixture(scope="module")
def assembled():
    return generate.assembled()


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


@pytest.mark.parametrize("k", PART_IDS)
def test_each_part_is_one_connected_piece(k):
    part = generate.part_2d(k)
    assert len(part.decompose()) == 1
    assert len(generate.extrude(part, generate.THICKNESS).decompose()) == 1


def test_slot_width():
    assert generate.SLOT_WIDTH == pytest.approx(
        generate.THICKNESS / math.tan(math.radians(22.5)) + generate.SLOT_CLEARANCE
    )
    assert generate.SLOT_WIDTH == pytest.approx(7.54, abs=0.01)
    half = generate.SLOT_WIDTH / 2 + 3
    # Part B is slotted above and below its segment; the rest of the strip stays solid.
    top, bottom = generate.segment_edges(1)
    for y in (top + 3, bottom - 3):
        assert strip(generate.part_2d(1), y, half) / 0.1 == pytest.approx(
            2 * half - generate.SLOT_WIDTH
        )


def test_every_axis_point_belongs_to_exactly_one_part():
    step = 0.25
    parts = [generate.part_2d(k) for k in PART_IDS]
    y = -generate.INNER_RADIUS  # windows [y, y + step] line up with the segment edges
    while y < generate.INNER_RADIUS:
        owners = [k for k, p in enumerate(parts) if strip(p, y, 0.5, step) > 0]
        expected = min(
            int((generate.INNER_RADIUS - y - step / 2) // generate.SEGMENT),
            generate.PARTS - 1,
        )
        assert owners == [expected], (y, owners)
        y += step


def test_assembled_star_has_24_distinct_points():
    directions = []
    for k in PART_IDS:
        turn = math.radians(generate.PLANE_ANGLE * k)
        for i in range(generate.POINTS):
            # Tip i of the flat part (notch on the axis), standing up and turned about Z.
            a = math.pi / generate.POINTS + 2 * math.pi * i / generate.POINTS
            x, y = -math.sin(a), math.cos(a)
            directions.append((x * math.cos(turn), x * math.sin(turn), y))
    assert len(directions) == 24

    def angle(u, v):
        return math.degrees(
            math.acos(
                max(-1.0, min(1.0, sum(p * q for p, q in zip(u, v, strict=True))))
            )
        )

    assert min(angle(u, v) for u, v in combinations(directions, 2)) > 20


def test_parts_slot_together_without_collision(assembled):
    for part in assembled:
        assert part.volume() > 0
    for a, b in combinations(assembled, 2):
        assert (a ^ b).volume() == pytest.approx(0, abs=1e-6)


@pytest.mark.parametrize("k", [1, 2, 3])
def test_part_slides_in_from_below(assembled, k):
    for step in range(1, int(2 * generate.OUTER_RADIUS) + 2):
        moved = assembled[k].translate((0, 0, -float(step)))
        for other in assembled[:k]:
            assert (moved ^ other).volume() == pytest.approx(0, abs=1e-6), (k, step)


def test_committed_stl_is_up_to_date(tmp_path):
    fresh = tmp_path / "star-24.stl"
    write_stl(generate.build_plate(), fresh, "star-24")
    assert generate.OUTPUT.read_bytes() == fresh.read_bytes()
