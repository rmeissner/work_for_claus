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
DECK_WIDTH = 8.0
LOWER_FACES = (0, 6)
UPPER_FACES = (2, 4)
DECK_FACE = 3
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
TAB_DEPTH = 2.1  # compact tab retains at least 0.3 mm above the dovetail channel
ENGINE_DEPTH = 3.6
ENGINE_FLOOR = 0.8
ENGINE_WALL = 0.8
ENGINE_RADII = (4.2, 5.0, 4.2)
ENGINE_Y = (-25.0, 0.0, 25.0)
ENGINE_Z = -0.7
HOLDER_FRONT = 136.0
HOLDER_BACK = 148.0
HOLDER_WIDTH = 7.2
HOLDER_BASE = 8.0
HOLDER_TOP = (8.0, 8.0)
HOLDER_LOCK_BACK = 146.0
HOLDER_LOCK_TOP = 12.4
RAIL_X = 138.6
RAIL_LENGTH = 3.9
RAIL_NECK = 3.6
RAIL_HEAD = 4.6
RAIL_RISE = 0.6
RAIL_TOP = 1.0
BRIDGE_X = 138.5
BRIDGE_BOTTOM = 16.0
BRIDGE_HEIGHT = 4.0
BRIDGE_WIDTH = 30.0
BRIDGE_DEPTH = 10.0
BRIDGE_PEG = (2.0, 3.0, 3.0)
BRIDGE_SOCKET = (2.2, 3.2, 3.2)
SHIELD_Y = (-9.0, 9.0)
SHIELD_RADIUS = 2.5
SHIELD_STEM = 0.9
SHIELD_STEM_HEIGHT = 3.0
SHIELD_SOCKET_RADIUS = 1.0
SHIELD_SOCKET_DEPTH = 2.2
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
            (LENGTH, -DECK_WIDTH / 2, HEIGHT / 2),
            (LENGTH, DECK_WIDTH / 2, HEIGHT / 2),
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
    for i in range(len(vertices) - 1):
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
    for face in UPPER_FACES:
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
    # The center deck has one closed opening for the engine blade's top tab.
    cuts = Manifold()
    for i in (*LOWER_FACES, DECK_FACE):
        locations = JOINT_Y if i in LOWER_FACES else (0.0,)
        for y in locations:
            width = (
                JOINT_WIDTH + 2 * FIT_CLEARANCE
                if i in LOWER_FACES
                else TAB_WIDTH + 2 * FIT_CLEARANCE
            )
            end = (
                LENGTH + 1
                if i in LOWER_FACES
                else BLADE_X + BLADE_THICKNESS + FIT_CLEARANCE
            )
            world = Manifold.cube(
                (end - BLADE_X + FIT_CLEARANCE, width, HEIGHT + 6)
            ).translate((BLADE_X - FIT_CLEARANCE, y - width / 2, -HEIGHT / 2 - 3))
            inverse = np.column_stack([transforms[i][:, :3].T, np.zeros(3)])
            cuts += world.transform(inverse) ^ extrude(faces[i], max(BUILDING_HEIGHTS))
    hull -= cuts
    inverse = np.column_stack([transforms[DECK_FACE][:, :3].T, np.zeros(3)])
    hull += deck_rail().transform(inverse)
    skin = extrude(net, FOLD_LIGAMENT) - cuts
    if (skin - hull).volume() > 1e-6:
        raise ValueError("a crease cuts through the continuous hinge skin")
    placed = [
        (hull ^ extrude(face, hull.bounding_box()[5] + 1)).transform(transform)
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

        # Mirror only the hooks onto the underside; engines remain upright.
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
    # Bearing shoulders follow the deck pitch through the blade thickness.
    half = DECK_WIDTH * BLADE_X / LENGTH / 2 - FIT_CLEARANCE
    rear += Manifold.hull_points(
        [
            (y, z, t)
            for t in (0, BLADE_THICKNESS)
            for y in (-half, half)
            for z in (top - 0.3, top + HEIGHT / (2 * LENGTH) * t)
        ]
    )
    for y, radius in zip(ENGINE_Y, ENGINE_RADII, strict=True):
        boss = Manifold.cylinder(
            ENGINE_DEPTH + ENGINE_FLOOR, radius + ENGINE_WALL, circular_segments=64
        ).translate((y, ENGINE_Z, BLADE_THICKNESS))
        cavity = Manifold.cylinder(
            ENGINE_DEPTH + 0.1, radius - 1.4, radius, circular_segments=64
        ).translate((y, ENGINE_Z, BLADE_THICKNESS + ENGINE_FLOOR))
        rear += boss - cavity
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
        if any(
            (moving ^ panel).volume() > 1e-5
            for i, panel in enumerate(placed)
            if i not in LOWER_FACES
        ):
            raise ValueError("engine blade jams during staged insertion from below")


def deck_rail(
    clearance: float = 0.0, length: float = RAIL_LENGTH, start: float = RAIL_X
) -> Manifold:
    """Dovetail along the flat deck; its flared head prints at less than 45 degrees."""
    a = HEIGHT / (2 * LENGTH)
    normal = np.array([-a, 0, 1]) / math.sqrt(1 + a * a)
    tangent = np.array([1, 0, a]) / math.sqrt(1 + a * a)
    profile = polygon(
        [
            (-RAIL_NECK / 2, -0.05),
            (RAIL_NECK / 2, -0.05),
            (RAIL_HEAD / 2, RAIL_RISE),
            (RAIL_HEAD / 2, RAIL_TOP),
            (-RAIL_HEAD / 2, RAIL_TOP),
            (-RAIL_HEAD / 2, RAIL_RISE),
        ]
    )
    if (RAIL_HEAD - RAIL_NECK) / 2 > RAIL_RISE:
        raise ValueError("deck rail flare exceeds a 45-degree overhang")
    origin = np.array([start, 0, a * start]) + SHELL * normal
    frame = np.column_stack([[0, 1, 0], normal, tangent, origin])
    return extrude(
        profile.offset(clearance) if clearance else profile, length
    ).transform(frame)


def bridge_holder() -> Manifold:
    """Flat-footed tower with a sliding dovetail, printed inverted, groove up."""
    front, back, half = HOLDER_FRONT, HOLDER_BACK, HOLDER_WIDTH / 2
    foot = [
        (front, -half + 1),
        (front + 2, -half),
        (back, -half),
        (back, half),
        (front + 2, half),
        (front, half - 1),
    ]
    top = [
        (BRIDGE_X + x, y)
        for x in (-HOLDER_TOP[0] / 2, HOLDER_TOP[0] / 2)
        for y in (-HOLDER_TOP[1] / 2, HOLDER_TOP[1] / 2)
    ]
    body = Manifold.hull_points(
        [(x, y, HOLDER_BASE) for x, y in foot]
        + [(x, y, BRIDGE_BOTTOM) for x, y in top]
        + [(HOLDER_LOCK_BACK, y, HOLDER_LOCK_TOP) for y in (-3, 3)]
    )
    a = HEIGHT / (2 * LENGTH)
    offset = SHELL * math.sqrt(1 + a * a)
    # The seventh facet is flat across Y and follows the hull's pitch along X.
    roof = Manifold.hull_points(
        [
            (x, y, z)
            for x in (front - 1, back + 1)
            for y, z in [(-20, 0), (20, 0), (20, a * x + offset), (-20, a * x + offset)]
        ]
    )
    body -= roof
    body -= deck_rail(
        FIT_CLEARANCE / 2, HOLDER_BACK - RAIL_X + 2, RAIL_X - FIT_CLEARANCE
    )
    tab_top = HEIGHT / 2 * BLADE_X / LENGTH + TAB_DEPTH + FIT_CLEARANCE
    body -= Manifold.cube(
        (BLADE_THICKNESS + 2 * FIT_CLEARANCE, TAB_WIDTH + 2 * FIT_CLEARANCE, tab_top)
    ).translate((BLADE_X - FIT_CLEARANCE, -TAB_WIDTH / 2 - FIT_CLEARANCE, 0))
    body -= extrude(
        rectangle(*BRIDGE_SOCKET[:2], center=(BRIDGE_X, 0)), BRIDGE_SOCKET[2] + 0.1
    ).translate((0, 0, BRIDGE_BOTTOM - BRIDGE_SOCKET[2]))
    channel_top = (
        a * (BRIDGE_X + BRIDGE_SOCKET[0] / 2)
        + offset
        + (RAIL_TOP + FIT_CLEARANCE / 2) * math.sqrt(1 + a * a)
    )
    tab_gap = max(
        BLADE_X - FIT_CLEARANCE - BRIDGE_X - BRIDGE_SOCKET[0] / 2,
        BRIDGE_BOTTOM - BRIDGE_SOCKET[2] - tab_top,
    )
    if min(BRIDGE_BOTTOM - BRIDGE_SOCKET[2] - channel_top, tab_gap) < 0.8:
        raise ValueError("tower sockets must retain at least 0.8 mm between them")
    engagement = (
        tab_top
        - FIT_CLEARANCE
        - (
            a * (BLADE_X + BLADE_THICKNESS)
            + offset
            + (RAIL_TOP + FIT_CLEARANCE / 2) * math.sqrt(1 + a * a)
        )
    )
    if engagement < 0.3:
        raise ValueError("locking tab must extend at least 0.3 mm above the channel")
    height = BRIDGE_BOTTOM - HOLDER_BASE
    if (
        max(
            BRIDGE_X - HOLDER_TOP[0] / 2 - front,
            back - BRIDGE_X - HOLDER_TOP[0] / 2,
            (HOLDER_WIDTH - HOLDER_TOP[1]) / 2,
        )
        > height
    ):
        raise ValueError("inverted tower flare exceeds a 45-degree overhang")
    if (
        HOLDER_LOCK_BACK - BRIDGE_X - HOLDER_TOP[0] / 2
        > BRIDGE_BOTTOM - HOLDER_LOCK_TOP
    ):
        raise ValueError("rear locking haunch exceeds a 45-degree overhang")
    return body.rotate((180, 0, 0)).translate((0, 0, BRIDGE_BOTTOM))


def place_holder(holder: Manifold) -> Manifold:
    return holder.translate((0, 0, -BRIDGE_BOTTOM)).rotate((180, 0, 0))


def bridge() -> Manifold:
    """Volumetric bridge, underside peg, and two blind shield sockets."""
    if SHIELD_SOCKET_DEPTH >= BRIDGE_HEIGHT:
        raise ValueError("shield sockets must retain a solid floor")
    x, y = BRIDGE_DEPTH / 2, BRIDGE_WIDTH / 2
    outline = polygon(
        [
            (-x, -y + 4),
            (-x + 2, -y),
            (x - 2, -y),
            (x, -y + 4),
            (x, y - 4),
            (x - 2, y),
            (-x + 2, y),
            (-x, y - 4),
        ]
    )
    body = Manifold.extrude(outline, BRIDGE_HEIGHT, scale_top=(0.85, 0.85))
    body += extrude(rectangle(*BRIDGE_PEG[:2]), BRIDGE_PEG[2]).translate(
        (0, 0, -BRIDGE_PEG[2])
    )
    for y in SHIELD_Y:
        body -= Manifold.cylinder(
            SHIELD_SOCKET_DEPTH + 0.1, SHIELD_SOCKET_RADIUS, circular_segments=48
        ).translate((0, y, BRIDGE_HEIGHT - SHIELD_SOCKET_DEPTH))
    return body.rotate((180, 0, 0)).translate((0, 0, BRIDGE_HEIGHT))


def shield() -> Manifold:
    """Round globe with a 45-degree lower transition, so its stem prints upright."""
    join_radius = SHIELD_RADIUS / math.sqrt(2)
    join_height = SHIELD_STEM_HEIGHT + join_radius - SHIELD_STEM
    center = join_height + join_radius
    arc = [
        (SHIELD_RADIUS * math.cos(a), center + SHIELD_RADIUS * math.sin(a))
        for a in np.linspace(-math.pi / 4, math.pi / 2, 37)
    ]
    profile = polygon(
        [
            (0, 0),
            (SHIELD_STEM, 0),
            (SHIELD_STEM, SHIELD_STEM_HEIGHT),
            *arc,
            (0, center + SHIELD_RADIUS),
        ]
    )
    if not 0 < SHIELD_STEM < join_radius:
        raise ValueError("shield stem must be narrower than its 45-degree transition")
    if (
        not 0 < SHIELD_SOCKET_DEPTH < SHIELD_STEM_HEIGHT
        or SHIELD_SOCKET_RADIUS <= SHIELD_STEM
    ):
        raise ValueError("shield socket must fit its stem below the globe transition")
    return Manifold.revolve(profile, circular_segments=64)


def accessory_assembly(parts: list[Manifold]) -> list[Manifold]:
    holder, command, globe = parts
    return [
        place_holder(holder),
        command.translate((0, 0, -BRIDGE_HEIGHT))
        .rotate((180, 0, 0))
        .translate((BRIDGE_X, 0, BRIDGE_BOTTOM)),
        *[
            globe.translate(
                (BRIDGE_X, y, BRIDGE_BOTTOM + BRIDGE_HEIGHT - SHIELD_SOCKET_DEPTH)
            )
            for y in SHIELD_Y
        ],
    ]


def validate_accessories(
    hull: list[Manifold], rear: Manifold, extras: list[Manifold]
) -> None:
    assembled = [*hull, rear, *extras]
    for a, b in combinations(assembled, 2):
        if (a ^ b).volume() > 1e-5:
            raise ValueError("assembled bridge kit parts intersect")
    holder, command, *globes = extras
    turned = (
        command.translate((-BRIDGE_X, 0, 0))
        .rotate((0, 0, 90))
        .translate((BRIDGE_X, 0, 0))
    )
    if (turned ^ holder).volume() < 1e-5:
        raise ValueError("bridge socket must reject a quarter-turn")
    a = HEIGHT / (2 * LENGTH)
    # Slide along the pitched deck before installing the blade as a locking pin.
    for distance in np.linspace(-14, 0, 57):
        moving = holder.translate((float(distance), 0, a * float(distance)))
        if any((moving ^ fixed).volume() > 1e-5 for fixed in hull):
            raise ValueError("tower cannot slide onto the deck rail")
    for distance in np.linspace(0, HEIGHT + TAB_DEPTH + 2, 121):
        moving = rear.translate((0, 0, -float(distance)))
        if any(
            (moving ^ fixed).volume() > 1e-5
            for fixed in [
                holder,
                *[part for i, part in enumerate(hull) if i not in LOWER_FACES],
            ]
        ):
            raise ValueError("engine blade cannot lock the tower through the deck")
    obstacles = [*hull, rear]
    for distance in np.linspace(0, 8, 33):
        if any(
            (command.translate((0, 0, float(distance))) ^ fixed).volume() > 1e-5
            for fixed in [*obstacles, holder]
        ):
            raise ValueError("bridge cannot lower onto its holder")
        if any(
            (globe.translate((0, 0, float(distance))) ^ command).volume() > 1e-5
            for globe in globes
        ):
            raise ValueError("a shield cannot lower into its bridge socket")
    if (holder.translate((0, 0, -0.05)) ^ hull[DECK_FACE]).volume() < 0.5:
        raise ValueError("tower must bear on at least 10 mm2 of the mounting strip")
    if (holder.translate((0, 0, 0.3)) ^ hull[DECK_FACE]).volume() < 1e-5:
        raise ValueError("deck dovetail must prevent the tower lifting off")
    if (holder.translate((-0.4, 0, -a * 0.4)) ^ rear).volume() < 1e-5:
        raise ValueError("engine blade tab must prevent reverse sliding")
    if (holder.translate((0.4, 0, a * 0.4)) ^ hull[DECK_FACE]).volume() < 1e-5:
        raise ValueError("tower channel needs a closed end stop")
    if (rear.translate((0, 0, 0.05)) ^ hull[DECK_FACE]).volume() < 0.15:
        raise ValueError("engine blade must support at least 3 mm2 beneath the strip")


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
    accessories = [bridge_holder(), bridge(), shield()]
    parts = [hull, rear, *accessories]
    for name, part in zip(
        ("hull", "rear", "holder", "bridge", "shield"), parts, strict=True
    ):
        assert_printable(part)
        if len(part.decompose()) != 1:
            raise ValueError(f"{name} is not one connected printable part")
        write_stl(part, ROOT.with_name(f"part-{name}.stl"), name)
    assembled_rear = place_rear(rear)
    validate(placed, assembled_rear)
    extras = accessory_assembly(accessories)
    validate_accessories(placed, assembled_rear, extras)
    plate = layout_on_plate(parts[:2], PLATE_GAP, columns=1)
    assert_printable(plate)
    if len(plate.decompose()) != 2:
        raise ValueError("print plate must have two separate parts")
    write_stl(plate, ROOT.with_name("star-destroyer.stl"), "Star Destroyer plate")
    report("plate", [plate])
    accessory_plate = layout_on_plate(
        [*accessories, accessories[-1]], PLATE_GAP, columns=2
    )
    assert_printable(accessory_plate)
    if len(accessory_plate.decompose()) != 4:
        raise ValueError("accessory plate must contain holder, bridge, and two shields")
    write_stl(
        accessory_plate, ROOT.with_name("accessories.stl"), "Star Destroyer accessories"
    )
    report("accessory plate", [accessory_plate])
    lowest = min(part.bounding_box()[2] for part in [*placed, assembled_rear, *extras])
    colored = [(p.translate((0, 0, -lowest)), (170, 182, 196)) for p in placed]
    colored.append((assembled_rear.translate((0, 0, -lowest)), (95, 114, 137)))
    colored.extend(
        (part.translate((0, 0, -lowest)), color)
        for part, color in zip(
            extras,
            [(130, 145, 160), (155, 166, 180), (113, 151, 179), (113, 151, 179)],
            strict=True,
        )
    )
    write_colored_stl(
        colored, ROOT.with_name("combined.stl"), "Star Destroyer assembled"
    )
    report("assembled", [*placed, assembled_rear, *extras])
    volume = sum(part.volume() for part in [*parts, accessories[-1]])
    mass = volume / 1000 * PLA_DENSITY
    filament = volume / (math.pi * (FILAMENT_DIAMETER / 2) ** 2) / 1000
    print(f"solid PLA estimate: {mass:.1f} g, {filament:.1f} m of 1.75 mm filament")


if __name__ == "__main__":
    main()
