import json
from pathlib import Path

import numpy as np
import pytest
from manifold3d import CrossSection
from stlkit import assert_printable, load_script, write_stl

generate = load_script(Path(__file__).with_name("generate.py"))

PART_IDS = list(range(generate.PARTS))


def same_shape(a, b):
    return (a - b).area() + (b - a).area() == pytest.approx(0, abs=1e-6)


def material_at(shape, x, y, size=0.02):
    probe = CrossSection.square((size, size)).translate((x - size / 2, y - size / 2))
    return (shape ^ probe).area() > 0


def thickness_at(solid, x, y, size=0.05):
    probe = CrossSection.square((size, size)).translate((x - size / 2, y - size / 2))
    column = solid ^ generate.extrude(probe, 10).translate((0, 0, -1))
    return column.volume() / size**2


def test_parts_are_printable():
    for solid in generate.parts():
        assert_printable(solid)
        assert solid.bounding_box()[5] == pytest.approx(generate.THICKNESS)
    assert_printable(generate.build_plate())


def test_parts_are_five_layers_and_the_fold_keeps_three():
    layer = 0.2
    assert generate.THICKNESS == pytest.approx(5 * layer)
    assert generate.FOLD_THICKNESS == pytest.approx(3 * layer)
    assert generate.FOLD_WIDTH == pytest.approx(1.0)
    # The slits follow the thickness, so the thinner parts still fit snugly.
    assert generate.SLIT_WIDTH == pytest.approx(generate.THICKNESS + 0.3)


def test_plate_fits_the_build_volume():
    x0, y0, z0, x1, y1, z1 = generate.build_plate().bounding_box()
    assert (x1 - x0, y1 - y0, z1 - z0) < (220, 220, 250)


@pytest.mark.parametrize("k", PART_IDS)
def test_each_part_is_one_connected_piece(k):
    assert len(generate.part_2d(k).decompose()) == 1
    assert len(generate.part(k).decompose()) == 1


def test_two_shapes_two_of_each():
    a, b, c, d = (generate.part_2d(k) for k in PART_IDS)
    # B is A turned upside down, without A's hook.
    a_without_hook = a - (generate.hook() - b.rotate(180))
    assert same_shape(a_without_hook.rotate(180), b)
    assert same_shape(c, d)
    assert generate.part(2).volume() == pytest.approx(generate.part(3).volume())


def test_cross_parts_are_slit_from_a_notch_to_the_center():
    a = generate.part_2d(0)
    r = generate.INNER_RADIUS
    assert not material_at(a, 0, -r + 1)
    assert not material_at(a, 0, -0.5)
    assert material_at(a, 0, 0.5)
    assert generate.SLIT_LENGTH == pytest.approx(r)


def test_a_has_a_hook_on_the_point_at_right_angles_to_its_slit():
    a = generate.part_2d(0)
    cx, cy = generate.hook_center()
    assert cy == pytest.approx(0)  # on the X axis; the slit runs along Y
    assert cx > generate.tip_x() - generate.HOOK_OVERLAP
    assert not material_at(a, cx, cy)  # the hole for the thread
    ring_middle = (generate.HOOK_OUTER + generate.HOOK_HOLE) / 2
    assert material_at(a, cx + ring_middle, cy)  # closed beyond the hole
    assert material_at(a, generate.tip_x() - 0.5, 0)  # attached to the tip
    # The hole is clear of the star, so the thread can't jam.
    outline = generate.cross_part_outline()
    assert (outline ^ generate.hook_hole()).area() == pytest.approx(0, abs=1e-9)
    # Only A has a hook.
    assert not material_at(generate.part_2d(1), cx, cy + ring_middle)


def test_fold_part_slit_is_as_wide_and_a_bit_longer_than_twice_and_closed():
    c = generate.part_2d(2)
    half = generate.CENTER_SLIT_LENGTH / 2
    assert generate.SLIT_EXTRA == pytest.approx(0.5)
    assert half == pytest.approx(generate.SLIT_LENGTH + generate.SLIT_EXTRA)
    for y in (-half + 0.2, 0, half - 0.2):
        assert not material_at(c, 0, y)
    for y in (-half - 0.2, half + 0.2):
        assert material_at(c, 0, y)
    # Same width as the cross parts' slit: solid just beside it, empty just inside.
    w = generate.SLIT_WIDTH / 2
    assert not material_at(c, w - 0.05, 5)
    assert material_at(c, w + 0.05, 5)


def test_fold_groove_runs_across_the_slit_and_is_not_too_thin():
    c = generate.part(2)
    assert generate.FOLD_THICKNESS >= 0.6
    for x in (-10, -3, 3, 10):
        assert thickness_at(c, x, 0) == pytest.approx(generate.FOLD_THICKNESS, abs=1e-3)
        assert thickness_at(c, x, 2) == pytest.approx(generate.THICKNESS, abs=1e-3)
    for k in (0, 1):
        assert thickness_at(generate.part(k), 10, 0) == pytest.approx(
            generate.THICKNESS, abs=1e-3
        )


def test_project_json_lists_the_files_in_order():
    project = json.loads(Path(__file__).with_name("project.json").read_text())
    assert [f["file"] for f in project["files"]] == [
        "combined.stl",
        "star-24.stl",
        "part-a.stl",
        "part-b.stl",
        "part-c.stl",
        "part-d.stl",
    ]
    listed = {f["file"] for f in project["files"]}
    on_disk = {p.name for p in Path(__file__).parent.glob("*.stl")}
    assert listed == on_disk


@pytest.mark.parametrize("index", range(1 + generate.PARTS))
def test_committed_stl_is_up_to_date(tmp_path, index):
    solid, path, name = generate.outputs()[index]
    fresh = tmp_path / path.name
    write_stl(solid, fresh, name)
    assert path.read_bytes() == fresh.read_bytes()


@pytest.fixture(scope="module")
def assembled():
    return generate.assembled()


def test_assembled_parts_do_not_intersect(assembled):
    for i in PART_IDS:
        for j in PART_IDS[i + 1 :]:
            overlap = (assembled[i] ^ assembled[j]).volume()
            assert overlap == pytest.approx(0, abs=1e-6), (i, j)


def _half_direction(half):
    """Direction (Y, Z) of a folded half seen along X, from the hinge to its middle."""
    _, y0, z0, _, y1, z1 = half.bounding_box()
    center = np.array([(y0 + y1) / 2, (z0 + z1) / 2])
    hinge = np.array([np.sign(center[0]) * generate.HINGE_OFFSET, 0.0])
    v = center - hinge
    return np.degrees(np.arctan2(v[1], v[0]))


@pytest.mark.parametrize(("k", "side"), [(2, 1), (3, -1)])
def test_fold_parts_make_three_equal_angles_with_a(k, side):
    upper, lower = generate.folded_halves(k, side)
    # Seen along X, A's halves point along +Z (90 degrees) and -Z (270 degrees); the folded
    # halves split one side of A into three 60 degree angles.
    angles = sorted(_half_direction(h) % 360 for h in (upper, lower))
    expected = [30, 330] if side > 0 else [150, 210]
    assert angles == pytest.approx(expected, abs=1)


@pytest.mark.parametrize(("k", "side"), [(2, 1), (3, -1)])
def test_fold_part_slits_lie_in_b_plane(k, side):
    for half in generate.folded_halves(k, side):
        x0, _, _, x1, _, _ = half.bounding_box()
        assert (x0 + x1) / 2 == pytest.approx(0, abs=1e-3)  # centered on B (X = 0)
    # B (the YZ plane) passes through the slits without touching C or D.
    b = generate.assembled()[1]
    for half in generate.folded_halves(k, side):
        assert (b ^ half).volume() == pytest.approx(0, abs=1e-6)


def test_combined_has_one_color_per_part(tmp_path):
    path = tmp_path / "combined.stl"
    generate.write_colored_stl(generate.build_combined(), path, "star-24 assembled")
    data = path.read_bytes()
    assert b"COLOR=" in data[:80]
    record = np.dtype([("f", "<f4", 12), ("attr", "<u2")])
    assert len(set(np.frombuffer(data[84:], dtype=record)["attr"].tolist())) == 4
    assert min(p.bounding_box()[2] for p, _ in generate.build_combined()) == (
        pytest.approx(0)
    )


def test_committed_combined_stl_is_up_to_date(tmp_path):
    fresh = tmp_path / "combined.stl"
    generate.write_colored_stl(generate.build_combined(), fresh, "star-24 assembled")
    assert generate.COMBINED_OUTPUT.read_bytes() == fresh.read_bytes()
