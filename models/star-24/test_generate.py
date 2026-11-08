import math
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest
from manifold3d import CrossSection, Error, OpType
from stlkit import assert_printable, load_script

generate = load_script(Path(__file__).with_name("generate.py"))

PART_IDS = list(range(generate.PARTS))


@pytest.fixture(scope="module")
def assembled():
    return generate.assembled()


def test_parts_are_printable():
    for solid in generate.parts():
        assert_printable(solid)
        assert solid.bounding_box()[5] == pytest.approx(generate.THICKNESS)
    assert_printable(generate.build_plate())


def test_plate_fits_the_build_volume():
    x0, y0, z0, x1, y1, z1 = generate.build_plate().bounding_box()
    assert (x1 - x0, y1 - y0, z1 - z0) < (220, 220, 250)


def test_part_is_one_connected_piece():
    part = generate.part_2d()
    assert len(part.decompose()) == 1
    assert len(generate.extrude(part, generate.THICKNESS).decompose()) == 1


def test_slot_width():
    # The planes cross at an angle with cos = 1/3, so sin = sqrt(8/9).
    assert generate.SLOT_WIDTH == pytest.approx(
        generate.THICKNESS * (1 + 1 / 3) / math.sqrt(8 / 9) + generate.SLOT_CLEARANCE
    )
    assert generate.SLOT_WIDTH == pytest.approx(2.0, abs=0.02)


def test_hole_is_closed_and_slits_stay_clear_of_it():
    slits = CrossSection.batch_boolean(
        [
            generate._arm(a, generate.SLOT_DEPTH, generate.OUTER_RADIUS + 5)
            for a in generate.INNER_DIRECTIONS
        ],
        OpType.Add,
    )
    hole = CrossSection.circle(generate.HUB_RADIUS, 48)
    for a in generate.OUTER_DIRECTIONS:
        hole += generate._arm(a, 0, generate.SLOT_DEPTH)
    assert (slits.offset(2.0, 0) ^ hole).area() == pytest.approx(0)
    # Slits reach the edge: the hole is closed, the slits are open.
    assert len(generate.part_2d().decompose()) == 1
    assert (
        len(
            (
                generate.part_2d() ^ CrossSection.circle(generate.OUTER_RADIUS + 1, 96)
            ).decompose()
        )
        == 1
    )


def test_assembled_star_has_24_distinct_points():
    frame = generate.frame()
    directions = []
    for rotation in generate.ROTATIONS:
        for i in range(generate.POINTS):
            # Tips of the flat part (notches are at 30 + 60 * i).
            a = math.radians(60 * i)
            directions.append(
                rotation @ frame @ np.array([math.cos(a), math.sin(a), 0])
            )
    assert len(directions) == 24

    def angle(u, v):
        return math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(u, v))))))

    assert min(angle(u, v) for u, v in combinations(directions, 2)) > 30


def test_inner_directions_are_the_lines_shared_with_other_parts():
    frame = generate.frame()
    for a, expected in zip(
        generate.INNER_DIRECTIONS, [(1, -1, 0), (0, 1, -1), (-1, 0, 1)], strict=False
    ):
        v = frame @ np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0])
        assert v * math.sqrt(2) == pytest.approx(expected, abs=1e-9)


def test_parts_do_not_intersect(assembled):
    for part in assembled:
        assert part.volume() > 0
    for a, b in combinations(assembled, 2):
        assert (a ^ b).volume() == pytest.approx(0, abs=1e-6)


def test_assembled_parts_are_the_same_shape(assembled):
    first = assembled[0]
    for part, rotation in zip(assembled, generate.ROTATIONS, strict=False):
        assert part.volume() == pytest.approx(first.volume())
        expected = first.transform(np.hstack([rotation, np.zeros((3, 1))]))
        assert (part ^ expected).volume() == pytest.approx(part.volume(), rel=1e-6)


def test_combined_parts_are_valid_and_on_z0():
    combined = generate.build_combined()
    assert len(combined) == len(generate.PART_COLORS) == generate.PARTS
    assert len(set(generate.PART_COLORS)) == generate.PARTS
    for part in combined:
        assert part.status() == Error.NoError
        assert part.volume() > 0
    assert min(part.bounding_box()[2] for part in combined) == pytest.approx(0)


def test_combined_stl_has_a_color_per_part(tmp_path):
    path = tmp_path / "combined.stl"
    generate.write_combined(path, "star-24 assembled")
    data = path.read_bytes()
    assert b"COLOR=" in data[:80]
    attrs = np.frombuffer(data[84:], dtype=np.dtype([("f", "<f4", 12), ("a", "<u2")]))[
        "a"
    ]
    assert len(set(attrs.tolist())) == generate.PARTS


@pytest.mark.parametrize("k", PART_IDS)
def test_part_files_are_flat_printable_and_centered(k):
    solid = generate.build_part(k)
    assert_printable(solid)
    x0, y0, z0, x1, y1, _ = solid.bounding_box()
    assert z0 == pytest.approx(0)
    assert (x0 + x1) / 2 == pytest.approx(0)
    assert (y0 + y1) / 2 == pytest.approx(0)


@pytest.mark.parametrize("index", range(2 + generate.PARTS))
def test_committed_stl_is_up_to_date(tmp_path, index):
    path, write = generate.outputs()[index]
    fresh = tmp_path / path.name
    write(fresh)
    assert path.read_bytes() == fresh.read_bytes()
