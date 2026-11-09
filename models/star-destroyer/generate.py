"""Cold-folding Star Destroyer hull and bottom-hooked engine blade.

Run ``python models/star-destroyer/generate.py`` from the repository root.
Millimeters throughout; assembled X runs bow to stern, Y spans the hull, Z is up.
The fan unfolds exactly; preview panels rotate at their radial fold lines.
Real crease bending and retention still require a physical test on Claus.
"""

import math
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from manifold3d import CrossSection, Manifold
from stlkit import (
    assert_printable,
    bar,
    extrude,
    layout_on_plate,
    write_colored_stl,
    write_stl,
)

LENGTH = 148.0
WIDTH = 90.0
HEIGHT = 20.0
SIDE_HEIGHT = 6.0
SHELL = 0.6
FOLD_WIDTH = 2.0
FOLD_LIGAMENT = 0.4  # two 0.2 mm layers; cold-fold performance remains untested
BUILDING_HEIGHTS = (1.2, 1.8)  # total thickness, not additional height
BLADE_X = 144.0
BLADE_THICKNESS = 1.2
FIT_CLEARANCE = 0.2
PANEL_CLEARANCE = 0.15
JOINT_Y = (-20.0, 20.0)
JOINT_WIDTH = 3.0
RETAINING_BORDER = 1.0
TAB_WIDTH = 3.0
TAB_DEPTH = 2.0
ENGINE_DEPTH = 3.6
ENGINE_FLOOR = 0.8
ENGINE_WALL = 0.8
ENGINE_RADII = (4.2, 5.0, 4.2)
ENGINE_Y = (-25.0, 0.0, 25.0)
ENGINE_Z = -0.7
HOLDER_SLOT = (3.2, 2.8)  # reserved for the next phase's 3 mm-thick holder
HOLDER_Z = 6.8
PLATE_GAP = 5.0
PLA_DENSITY = 1.24
FILAMENT_DIAMETER = 1.75
ROOT = Path(__file__)


def polygon(points) -> CrossSection:
    return CrossSection([points])


def rectangle(width: float, height: float, center=(0.0, 0.0)) -> CrossSection:
    return CrossSection.square((width, height), center=True).translate(center)


def stern_vertices() -> np.ndarray:
    """The seam is at the shallow bottom ridge; narrow side facets soften folds."""
    return np.array(
        [
            (LENGTH, 0, -HEIGHT / 2),
            (LENGTH, -WIDTH / 2, -SIDE_HEIGHT / 2),
            (LENGTH, -WIDTH / 2, SIDE_HEIGHT / 2),
            (LENGTH, 0, HEIGHT / 2),
            (LENGTH, WIDTH / 2, SIDE_HEIGHT / 2),
            (LENGTH, WIDTH / 2, -SIDE_HEIGHT / 2),
        ],
        dtype=float,
    )


def net_geometry() -> tuple[list[CrossSection], list[np.ndarray], np.ndarray]:
    vertices = stern_vertices()
    vertices = np.vstack([vertices, vertices[0]])
    radii = np.linalg.norm(vertices, axis=1)
    angles = [
        math.acos(np.dot(a, b) / (ra * rb))
        for a, b, ra, rb in zip(
            vertices[:-1], vertices[1:], radii[:-1], radii[1:], strict=True
        )
    ]
    theta = np.array([0.0, *np.cumsum(angles)]) - sum(angles) / 2
    flat = np.column_stack([radii * np.cos(theta), radii * np.sin(theta)])
    faces, transforms = [], []
    for i in range(6):
        faces.append(polygon([(0, 0), flat[i], flat[i + 1]]))
        u = vertices[i] / radii[i]
        v = vertices[i + 1] - np.dot(vertices[i + 1], u) * u
        v /= np.linalg.norm(v)
        c, s = math.cos(theta[i]), math.sin(theta[i])
        rotation = np.column_stack([u * c - v * s, u * s + v * c, np.cross(u, v)])
        transforms.append(np.column_stack([rotation, np.zeros(3)]))
        if not np.allclose(rotation @ np.r_[flat[i + 1], 0], vertices[i + 1]):
            raise ValueError("unfolded panel does not match its assembled stern edge")
    return faces, transforms, flat


def building(face: int, flat: np.ndarray, start: float, end: float) -> CrossSection:
    """A trapezoid well inside a triangular top panel, away from its creases."""
    a, b = flat[face], flat[face + 1]
    return polygon(
        [
            scale * ((1 - across) * a + across * b)
            for scale, across in (
                (start, 0.25),
                (end, 0.25),
                (end, 0.75),
                (start, 0.75),
            )
        ]
    )


def hull_parts() -> tuple[Manifold, list[Manifold]]:
    faces, transforms, flat = net_geometry()
    net = CrossSection.batch_hull(faces)
    grooves = CrossSection()
    for endpoint in flat[1:-1]:
        grooves += bar((0, 0), tuple(endpoint * 1.01), FOLD_WIDTH)
    hull = extrude(net, SHELL)
    hull -= extrude(grooves, SHELL).translate((0, 0, FOLD_LIGAMENT))
    for face in (2, 3):
        for (start, end), height in zip(
            ((0.32, 0.52), (0.60, 0.84)), BUILDING_HEIGHTS, strict=True
        ):
            footprint = building(face, flat, start, end)
            if (footprint ^ grooves.offset(1.0)).area() > 1e-6:
                raise ValueError("a building obstructs a folding groove")
            hull += extrude(footprint, height)
    if not 0 < FOLD_LIGAMENT < SHELL:
        raise ValueError("fold ligament must be positive and thinner than the shell")
    # Rear-open lower slits engage two hooks and hold the bottom seam shut.
    # Two upper-ridge half-cuts form one closed opening for the top tab.
    cuts = Manifold()
    for i in (0, 2, 3, 5):
        locations = JOINT_Y if i in (0, 5) else (0.0,)
        for y in locations:
            width = (
                JOINT_WIDTH + 2 * FIT_CLEARANCE
                if i in (0, 5)
                else TAB_WIDTH + 2 * FIT_CLEARANCE
            )
            end = (
                LENGTH + 1 if i in (0, 5) else BLADE_X + BLADE_THICKNESS + FIT_CLEARANCE
            )
            world = Manifold.cube(
                (end - BLADE_X + FIT_CLEARANCE, width, HEIGHT + 6)
            ).translate((BLADE_X - FIT_CLEARANCE, y - width / 2, -HEIGHT / 2 - 3))
            inverse = np.column_stack([transforms[i][:, :3].T, np.zeros(3)])
            cuts += world.transform(inverse) ^ extrude(faces[i], max(BUILDING_HEIGHTS))
    hull -= cuts
    skin = extrude(net, FOLD_LIGAMENT) - cuts
    if (skin - hull).volume() > 1e-6:
        raise ValueError("a crease cuts through the continuous hinge skin")
    placed = [
        (hull ^ extrude(face, max(BUILDING_HEIGHTS))).transform(transform)
        for face, transform in zip(faces, transforms, strict=True)
    ]
    return hull, placed


def rear_profile() -> CrossSection:
    return polygon(stern_vertices()[::-1, 1:]).scale((BLADE_X / LENGTH,) * 2)


def rear_panel() -> Manifold:
    """Thin blade, two lower hooks, one top tab, and upright raised engine bells."""
    profile = rear_profile().offset(-PANEL_CLEARANCE)
    top = HEIGHT / 2 * BLADE_X / LENGTH
    profile += rectangle(TAB_WIDTH, TAB_DEPTH + 1, (0, top + TAB_DEPTH / 2 - 0.5))
    for y in JOINT_Y:

        def roof(at: float) -> float:
            return HEIGHT / 2 * BLADE_X / LENGTH - (HEIGHT - SIDE_HEIGHT) / WIDTH * abs(
                at
            )

        # Mirror only the hooks onto the underside; engines/mount remain upright.
        for half, low, high in (
            (JOINT_WIDTH / 2, -0.5, SHELL + 0.3),
            (JOINT_WIDTH, SHELL + 0.25, SHELL + 0.25 + RETAINING_BORDER),
        ):
            profile += polygon(
                [
                    (y - half, roof(y - half) + low),
                    (y + half, roof(y + half) + low),
                    (y + half, roof(y + half) + high),
                    (y - half, roof(y - half) + high),
                ]
            ).mirror((0, 1))
    rear = extrude(profile, BLADE_THICKNESS)
    for y, radius in zip(ENGINE_Y, ENGINE_RADII, strict=True):
        boss = Manifold.cylinder(
            ENGINE_DEPTH + ENGINE_FLOOR, radius + ENGINE_WALL, circular_segments=64
        ).translate((y, ENGINE_Z, BLADE_THICKNESS))
        cavity = Manifold.cylinder(
            ENGINE_DEPTH + 0.1, radius - 1.4, radius, circular_segments=64
        ).translate((y, ENGINE_Z, BLADE_THICKNESS + ENGINE_FLOOR))
        rear += boss - cavity
    mount = extrude(
        rectangle(*HOLDER_SLOT, center=(0, HOLDER_Z)),
        BLADE_THICKNESS + ENGINE_DEPTH + ENGINE_FLOOR + 1,
    )
    mount_outline = rectangle(*HOLDER_SLOT, center=(0, HOLDER_Z))
    if (mount_outline.offset(1) - profile).area() > 1e-6:
        raise ValueError("bridge mounting slot has less than 1 mm surrounding wall")
    for y, radius in zip(ENGINE_Y, ENGINE_RADII, strict=True):
        engine = CrossSection.circle(radius, 64).translate((y, ENGINE_Z))
        if (mount_outline ^ engine.offset(1)).area() > 1e-6:
            raise ValueError("bridge mounting slot weakens an engine cavity wall")
    rear -= mount
    if BLADE_THICKNESS + ENGINE_FLOOR < 1.0:
        raise ValueError("engine recess floor is too thin")
    return rear


def place_rear(rear: Manifold) -> Manifold:
    return rear.transform(
        np.array(
            [
                [0, 0, 1, BLADE_X],
                [1, 0, 0, 0],
                [0, 1, 0, 0],
            ],
            dtype=float,
        )
    )


def validate(placed: list[Manifold], rear: Manifold) -> None:
    if LENGTH - BLADE_X - BLADE_THICKNESS - FIT_CLEARANCE < 1:
        raise ValueError("top tab hole needs at least 1 mm of closed stern web")
    for a, b in combinations(placed, 2):
        if (a ^ b).volume() > 1e-5:
            raise ValueError("folded hull panels intersect")
    for panel in placed:
        if (panel ^ rear).volume() > 1e-5:
            raise ValueError("engine blade intersects the hull")
    # Raise the blade from below while the lower faces are still open. Its top
    # tab enters the ridge hole; lower slits then engage the two retaining hooks.
    for distance in np.linspace(0, HEIGHT + TAB_DEPTH + 2, 121):
        moving = rear.translate((0, 0, -float(distance)))
        if any((moving ^ placed[i]).volume() > 1e-5 for i in (1, 2, 3, 4)):
            raise ValueError("engine blade jams during staged insertion from below")


def report(label: str, solids: list[Manifold]) -> None:
    bounds = Manifold.compose(solids).bounding_box()
    print(
        f"{label}: "
        + " x ".join(f"{bounds[i + 3] - bounds[i]:.1f}" for i in range(3))
        + " mm"
    )


def main() -> None:
    hull, placed = hull_parts()
    rear = rear_panel()
    parts = [hull, rear]
    for name, part in zip(("hull", "rear"), parts, strict=True):
        assert_printable(part)
        if len(part.decompose()) != 1:
            raise ValueError(f"{name} is not one connected printable part")
        write_stl(part, ROOT.with_name(f"part-{name}.stl"), name)
    assembled_rear = place_rear(rear)
    validate(placed, assembled_rear)
    plate = layout_on_plate(parts, PLATE_GAP, columns=1)
    assert_printable(plate)
    if len(plate.decompose()) != 2:
        raise ValueError("print plate must have two separate parts")
    write_stl(plate, ROOT.with_name("star-destroyer.stl"), "Star Destroyer plate")
    report("plate", [plate])
    lowest = min(part.bounding_box()[2] for part in [*placed, assembled_rear])
    colored = [(p.translate((0, 0, -lowest)), (170, 182, 196)) for p in placed]
    colored.append((assembled_rear.translate((0, 0, -lowest)), (95, 114, 137)))
    write_colored_stl(
        colored, ROOT.with_name("combined.stl"), "Star Destroyer folding hull"
    )
    report("assembled", [*placed, assembled_rear])
    volume = sum(part.volume() for part in parts)
    mass = volume / 1000 * PLA_DENSITY
    filament = volume / (math.pi * (FILAMENT_DIAMETER / 2) ** 2) / 1000
    print(f"solid PLA estimate: {mass:.1f} g, {filament:.1f} m of 1.75 mm filament")


if __name__ == "__main__":
    main()
