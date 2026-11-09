"""Slot-together glider: a fuselage, a wing and a tail, all printed flat.

- Fuselage: one continuous side profile with a round nose, a tapering boom and a big fin on the
  tail end. The nose holds a coin as nose weight in a round blind pocket, opened on the top
  face (the side away from the bed) and pressed in flat; the nose is a circle just big enough
  to leave COIN_RIM of material around the pocket, thickened to BOSS_THICKNESS by a round boss.
  The body is FUSELAGE_THICKNESS thick everywhere else, so it prints flat without supports. It
  has two closed slits: a horizontal one for the tail and a slightly tilted one for the wing
  (WING_INCIDENCE). The wing slit's position comes from the center-of-gravity search below.
  In the assembled pose the thin body is centered on the plane of symmetry and the boss and
  coin stick out on one side, which moves the glider's CG sideways by about 0.1 mm.
- Wing: a flat plate with rounded tips that slides sideways through the wing slit. Rounded
  notches in the leading and trailing edge mark its center.
- Tail: a flat plate that slides through the tail slit, with the same center marks.

The wing is placed so that the center of gravity (CG) of the assembled glider lies
STATIC_MARGIN x chord ahead of the neutral point (NP), found by bisection over the wing's X
position. The asserts below fail when the parameters make that impossible or leave the glider
without pitch or yaw stability. Each size uses the smallest coin for which all checks pass.

The design is a frozen ``Design`` of lengths; ``Design.scaled`` scales the planform and the
profile but not the thicknesses, clearances or corner radius, so the 70 % mini version is
built and checked on its own. ``combined.stl`` and ``mini-combined.stl`` show the assembly in
one color per part (the coin in copper): X along the fuselage (nose at X = 0), Y along the wing, Z up.

Run from the repository root: ``python models/glider/generate.py``.
All dimensions are in millimeters and degrees.
"""

import math
import sys
from dataclasses import dataclass, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from manifold3d import CrossSection, JoinType, Manifold
from stlkit import (
    assert_printable,
    assert_rounded,
    center_of_mass,
    extrude,
    layout_on_plate,
    round_corners,
    write_colored_stl,
    write_stl,
)

# Thicknesses, clearances and radii that must stay printable do not scale with the design.
WING_THICKNESS = 0.6
TAIL_THICKNESS = 0.5
FUSELAGE_THICKNESS = 1.6  # eight 0.2 mm layers; stiff enough in test prints
NOTCH_RADIUS = 1.5  # center marks on the wing's and the tail's edges
WING_INCIDENCE = 2.0
SLIT_CLEARANCE = 0.2
SLIT_MARGIN = 2.0  # material kept around each slit
MIN_CORNER_RADIUS = 2.0
STATIC_MARGIN = 0.10
MARGIN_TOLERANCE = 0.01
MIN_TAIL_VOLUME = 0.4
MIN_FIN_VOLUME = 0.04  # vertical tail volume
# The side profile's centroid must lie this far behind the CG (fraction of the fuselage
# length): like a weathercock, the side area behind the CG turns the glider into the wind
# instead of letting a yaw grow into a spiral. The nose and the wing sit near the CG, so the
# centroid of a compact glider like this one is only a few percent of its length behind it,
# and 5 % is the practical floor.
MIN_SIDE_AREA_ARM = 0.05
MAX_MASS = 30.0  # grams
PLA_DENSITY = 1.24  # g/cm3
PLA_GRAMS_PER_METER = 2.98  # 1.75 mm filament
PLATE_GAP = 5.0
CG_TOLERANCE = 1e-3  # mm
# Euro coins as nose weight: name -> (mass in g, diameter in mm). All are 1.67 mm thick.
COINS = {"1 cent": (2.30, 16.25), "2 cent": (3.06, 18.75), "5 cent": (3.92, 21.25)}
COIN_THICKNESS = 1.67
COIN_CLEARANCE = 0.15  # pocket diameter minus coin diameter: a snug press fit
FILLET_RADIUS = 4.0  # blends the nose circle into the body
COIN_RIM = 2.0  # material around the pocket in the side profile and the boss
POCKET_DEPTH = COIN_THICKNESS + 0.1
POCKET_FLOOR = 0.6  # solid material under the coin
BOSS_THICKNESS = math.ceil((POCKET_FLOOR + POCKET_DEPTH) / 0.2 - 1e-9) * 0.2
COLORS = {
    "fuselage": (30, 136, 229),
    "wing": (229, 57, 53),
    "tail": (253, 216, 53),
    "coin": (184, 115, 51),
}
PART_NAMES = ("wing", "fuselage", "tail")
DIR = Path(__file__).parent


@dataclass(frozen=True)
class Design:
    """All lengths that scale with the glider's size (millimeters)."""

    wing_span: float = 190.0
    wing_chord: float = 45.0
    wing_tip_radius: float = 15.0
    tail_span: float = 90.0
    tail_chord: float = 32.0
    tail_corner_radius: float = 10.0
    fuselage_length: float = 190.0
    fuselage_height: float = 14.0  # at the nose, tapering to tail_height
    tail_height: float = 7.0
    fin_height: float = 42.0
    fin_chord: float = 44.0
    fin_top_chord: float = 15.0
    fin_radius: float = 5.0
    tail_slit_end_gap: float = 4.0  # material behind the tail slit
    coin: str = "2 cent"  # smallest that passes every check; the coin does not scale

    def scaled(self, factor: float, coin: str) -> "Design":
        """Scale planform and profile lengths, keeping the thicknesses."""
        scale = {
            name: getattr(self, name) * factor
            for name in (
                "wing_span",
                "wing_chord",
                "wing_tip_radius",
                "tail_span",
                "tail_chord",
                "tail_corner_radius",
                "fuselage_length",
                "fuselage_height",
                "tail_height",
                "fin_height",
                "fin_chord",
                "fin_top_chord",
                "fin_radius",
                "tail_slit_end_gap",
            )
        }
        return replace(self, coin=coin, **scale)

    @property
    def wing_slit_length(self) -> float:
        return self.wing_chord + SLIT_CLEARANCE

    @property
    def tail_slit_length(self) -> float:
        return self.tail_chord + SLIT_CLEARANCE

    @property
    def tail_slit_x(self) -> float:
        """Front end of the tail slit."""
        return self.fuselage_length - self.tail_slit_end_gap - self.tail_slit_length

    @property
    def tail_leading_edge(self) -> float:
        return self.tail_slit_x + SLIT_CLEARANCE / 2

    @property
    def coin_mass(self) -> float:
        return COINS[self.coin][0]

    @property
    def pocket_radius(self) -> float:
        return (COINS[self.coin][1] + COIN_CLEARANCE) / 2

    @property
    def nose_radius(self) -> float:
        """The nose circle, which is also the boss and is centered on the pocket."""
        return self.pocket_radius + COIN_RIM


FULL = Design()
MINI = FULL.scaled(0.7, coin="1 cent")


def fin_outline(d: Design) -> CrossSection:
    """Fin profile from the fuselage axis up, with a rounded top."""
    x1 = d.fuselage_length
    fin = CrossSection(
        [
            [
                (x1 - d.fin_chord, 0),
                (x1, 0),
                (x1, d.fin_height),
                (x1 - d.fin_top_chord, d.fin_height),
            ]
        ]
    )
    return round_corners(fin, d.fin_radius)


def fuselage_outline(d: Design) -> CrossSection:
    """Side profile, X along the fuselage (nose at 0), Y up; no slits.

    The nose circle around the coin pocket is blended into the body with concave fillets.
    """
    radius, half_back = d.nose_radius, d.tail_height / 2
    nose = CrossSection.circle(radius, 64).translate((radius, 0))
    half_front = d.fuselage_height / 2
    body = CrossSection(
        [
            [
                (radius, -half_front),
                (d.fuselage_length, -half_back),
                (d.fuselage_length, half_back),
                (radius, half_front),
            ]
        ]
    )
    joined = (nose + body).offset(FILLET_RADIUS, JoinType.Round, 64)
    joined = joined.offset(-FILLET_RADIUS, JoinType.Round, 64)
    return round_corners(joined + fin_outline(d), MIN_CORNER_RADIUS)


def wing_outline(d: Design) -> CrossSection:
    """Planform, X = chord (leading edge at 0), Y = span (centered); no notches."""
    plate = CrossSection.square((d.wing_chord, d.wing_span)).translate(
        (0, -d.wing_span / 2)
    )
    return round_corners(plate, d.wing_tip_radius)


def _notches(chord: float) -> CrossSection:
    """Center marks on the leading and trailing edge."""
    circle = CrossSection.circle(NOTCH_RADIUS, 32)
    return circle + circle.translate((chord, 0))


def tail_outline(d: Design) -> CrossSection:
    plate = CrossSection.square((d.tail_chord, d.tail_span)).translate(
        (0, -d.tail_span / 2)
    )
    return round_corners(plate, d.tail_corner_radius)


def _slit(x: float, length: float, height: float, angle: float) -> CrossSection:
    """Closed slit starting at X = ``x``, centered on Y = 0, tilted about its center."""
    cx = x + length / 2
    box = CrossSection.square((length, height)).translate((-length / 2, -height / 2))
    return box.rotate(angle).translate((cx, 0))


def wing_slit(d: Design, x_wing: float) -> CrossSection:
    """Slit for a wing whose leading edge sits at ``x_wing`` (leading edge up)."""
    return _slit(
        x_wing - SLIT_CLEARANCE / 2,
        d.wing_slit_length,
        WING_THICKNESS + SLIT_CLEARANCE,
        -WING_INCIDENCE,
    )


def tail_slit(d: Design) -> CrossSection:
    return _slit(
        d.tail_slit_x, d.tail_slit_length, TAIL_THICKNESS + SLIT_CLEARANCE, 0.0
    )


def fuselage_2d(d: Design, x_wing: float) -> CrossSection:
    outline = fuselage_outline(d)
    slits = [wing_slit(d, x_wing), tail_slit(d)]
    for slit in slits:
        if (slit.offset(SLIT_MARGIN) - outline).area() > 1e-6:
            raise ValueError("a slit has less than SLIT_MARGIN of material around it")
    return outline - slits[0] - slits[1]


def pocket_floor_z() -> float:
    """Z of the pocket's floor in the flat fuselage."""
    return BOSS_THICKNESS - POCKET_DEPTH


def fuselage(d: Design, x_wing: float) -> Manifold:
    """Flat on Z = 0: the thin body, a round boss around the pocket, the coin pocket."""
    boss = CrossSection.circle(d.nose_radius, 64).translate((d.nose_radius, 0))
    solid = extrude(fuselage_2d(d, x_wing), FUSELAGE_THICKNESS) + extrude(
        boss, BOSS_THICKNESS
    )
    pocket = CrossSection.circle(d.pocket_radius, 64).translate((d.nose_radius, 0))
    return solid - extrude(pocket, POCKET_DEPTH + 1).translate((0, 0, pocket_floor_z()))


def wing_2d(d: Design) -> CrossSection:
    """Planform with the notches; the notch edges are rounded too."""
    shape = wing_outline(d) - _notches(d.wing_chord)
    return round_corners(shape, MIN_CORNER_RADIUS)


def wing(d: Design) -> Manifold:
    """Flat wing on Z = 0."""
    return extrude(wing_2d(d), WING_THICKNESS)


def tail_2d(d: Design) -> CrossSection:
    shape = tail_outline(d) - _notches(d.tail_chord)
    return round_corners(shape, MIN_CORNER_RADIUS)


def tail(d: Design) -> Manifold:
    return extrude(tail_2d(d), TAIL_THICKNESS)


def parts(d: Design, x_wing: float) -> list[Manifold]:
    """Wing, fuselage and tail flat for printing; wing and tail turned to lie along X."""
    return [
        wing(d).rotate((0, 0, 90)),
        fuselage(d, x_wing),
        tail(d).rotate((0, 0, 90)),
    ]


# Assembled pose: X along the fuselage, Y along the wing, Z up.


def _place_fuselage(d: Design, x_wing: float) -> Manifold:
    return _upright(fuselage(d, x_wing))


def _upright(flat: Manifold) -> Manifold:
    """Flat fuselage frame to the assembled pose.

    The thin body is centered on the middle plane; the boss and the coin stick out to one
    side.
    """
    flat = flat.translate((0, 0, -FUSELAGE_THICKNESS / 2))
    return flat.rotate((90, 0, 0))  # (x, y, z) -> (x, -z, y)


def _placed_coin(d: Design) -> Manifold:
    """The coin lying on the pocket's floor."""
    radius = COINS[d.coin][1] / 2
    disc = Manifold.cylinder(COIN_THICKNESS, radius, circular_segments=64)
    return _upright(disc.translate((d.nose_radius, 0, pocket_floor_z())))


def _placed_wing(d: Design, x_wing: float) -> Manifold:
    flat = wing(d).translate((-d.wing_chord / 2, 0, -WING_THICKNESS / 2))
    tilted = flat.rotate((0, WING_INCIDENCE, 0))  # leading edge up
    return tilted.translate((x_wing + d.wing_chord / 2, 0, 0))


def _placed_tail(d: Design) -> Manifold:
    flat = tail(d).translate((0, 0, -TAIL_THICKNESS / 2))
    return flat.translate((d.tail_leading_edge, 0, 0))


def assembled(d: Design, x_wing: float) -> list[Manifold]:
    """Wing, fuselage, tail and coin in place, in PART_NAMES order plus the coin."""
    return [
        _placed_wing(d, x_wing),
        _place_fuselage(d, x_wing),
        _placed_tail(d),
        _placed_coin(d),
    ]


def _aspect_lift_slope(aspect_ratio: float) -> float:
    """Helmbold lift slope per radian."""
    return 2 * math.pi * aspect_ratio / (2 + math.sqrt(aspect_ratio**2 + 4))


def _centroid_x(shape: CrossSection) -> float:
    return center_of_mass(extrude(shape, 1.0))[0]


def fin_area_and_centroid(d: Design) -> tuple[float, float]:
    """Area and centroid X of the fin above the boom."""
    above = CrossSection.square((d.fuselage_length, d.fin_height + 1)).translate(
        (0, d.tail_height / 2)
    )
    fin = fin_outline(d) ^ above
    return fin.area(), _centroid_x(fin)


def flight_properties(d: Design, x_wing: float) -> dict[str, float]:
    """CG, NP and friends for the wing's leading edge at ``x_wing`` (X from the nose)."""
    placed = assembled(d, x_wing)
    masses = [p.volume() / 1000 * PLA_DENSITY for p in placed[:-1]] + [d.coin_mass]
    cg_x = sum(
        center_of_mass(p)[0] * m for p, m in zip(placed, masses, strict=True)
    ) / sum(masses)
    wing_area = d.wing_span * d.wing_chord
    ar_wing = d.wing_span / d.wing_chord
    a_wing = _aspect_lift_slope(ar_wing)
    a_tail = _aspect_lift_slope(d.tail_span / d.tail_chord)
    downwash = 2 * a_wing / (math.pi * ar_wing)
    arm = (d.tail_leading_edge + d.tail_chord / 4) - (x_wing + d.wing_chord / 4)
    tail_volume = d.tail_span * d.tail_chord * arm / (wing_area * d.wing_chord)
    np_rel = (0.25 + tail_volume * (a_tail / a_wing) * (1 - downwash)) * d.wing_chord
    fin_area, fin_x = fin_area_and_centroid(d)
    mass = sum(masses)  # with the coin
    return {
        "cg": cg_x - x_wing,  # from the wing's leading edge
        "np": np_rel,
        "margin": (np_rel - (cg_x - x_wing)) / d.wing_chord,
        "tail_volume": tail_volume,
        "fin_volume": fin_area * (fin_x - cg_x) / (wing_area * d.wing_span),
        "side_area_arm": _centroid_x(fuselage_outline(d)) - cg_x,
        "mass": mass,
        "filament": (mass - d.coin_mass) / PLA_GRAMS_PER_METER,  # m, without the coin
        "wing_loading": mass / (wing_area / 10000),  # g/dm2
    }


def find_wing_position(d: Design, steps: int = 24) -> float:
    """X of the wing's leading edge that gives STATIC_MARGIN, by scan and bisection.

    The margin first rises as the wing moves back, peaks, then falls (the tail arm shrinks).
    The first upward crossing of the target is used: it has the largest tail volume.
    """

    def error(x_wing: float) -> float:
        return flight_properties(d, x_wing)["margin"] - STATIC_MARGIN

    low = 2 * d.nose_radius + SLIT_MARGIN + 1.0
    high = d.tail_slit_x - SLIT_MARGIN - d.wing_slit_length - 3.0
    xs = [low + (high - low) * i / steps for i in range(steps + 1)]
    errors = [error(x) for x in xs]
    for i in range(steps):
        if errors[i] < 0 <= errors[i + 1]:
            low, high, f_low = xs[i], xs[i + 1], errors[i]
            break
    else:
        raise ValueError(
            f"no wing position gives the static margin (best error {max(errors):.3f})"
        )
    while high - low > CG_TOLERANCE:
        mid = (low + high) / 2
        f_mid = error(mid)
        if f_mid * f_low > 0:
            low, f_low = mid, f_mid
        else:
            high = mid
    return (low + high) / 2


def check_outlines(d: Design) -> None:
    for outline in (fuselage_outline(d), wing_2d(d), tail_2d(d)):
        assert_rounded(outline, MIN_CORNER_RADIUS)


def check_assembly(d: Design, x_wing: float) -> None:
    wing_p, fuselage_p, tail_p, coin_p = assembled(d, x_wing)
    for name, a, b in (
        ("coin", coin_p, fuselage_p),
        ("wing", wing_p, fuselage_p),
        ("tail", tail_p, fuselage_p),
        ("wing", wing_p, tail_p),
    ):
        if (a ^ b).volume() > 1e-3:
            raise ValueError(f"the {name} intersects another part when assembled")


def check_flight(d: Design, props: dict[str, float]) -> None:
    if abs(props["margin"] - STATIC_MARGIN) > MARGIN_TOLERANCE:
        raise ValueError(f"static margin {props['margin']:.3f} is off the target")
    if props["tail_volume"] < MIN_TAIL_VOLUME:
        raise ValueError(
            f"tail volume {props['tail_volume']:.2f} is below {MIN_TAIL_VOLUME}"
        )
    if props["fin_volume"] < MIN_FIN_VOLUME:
        raise ValueError(
            f"fin volume {props['fin_volume']:.3f} is below {MIN_FIN_VOLUME}"
        )
    min_arm = MIN_SIDE_AREA_ARM * d.fuselage_length
    if props["side_area_arm"] < min_arm:
        raise ValueError(
            f"the side area is only {props['side_area_arm']:.1f} mm behind the CG, "
            f"less than {min_arm:.1f} mm"
        )
    if props["mass"] > MAX_MASS:
        raise ValueError(f"mass {props['mass']:.1f} g is above {MAX_MASS} g")


def verify(d: Design) -> tuple[float, dict[str, float]]:
    """Run every check; return the wing position and the flight properties."""
    check_outlines(d)
    x_wing = find_wing_position(d)
    check_assembly(d, x_wing)
    props = flight_properties(d, x_wing)
    check_flight(d, props)
    return x_wing, props


def build_plate(d: Design, x_wing: float) -> Manifold:
    plate = layout_on_plate(parts(d, x_wing), PLATE_GAP, columns=1)
    assert_printable(plate)
    return plate


def build_part(solid: Manifold) -> Manifold:
    """A part alone, flat and centered on the XY origin."""
    assert_printable(solid)
    x0, y0, _, x1, y1, _ = solid.bounding_box()
    return solid.translate((-(x0 + x1) / 2, -(y0 + y1) / 2, 0))


def build_combined(
    d: Design, x_wing: float
) -> list[tuple[Manifold, tuple[int, int, int]]]:
    """The assembled glider, one color per part, lowest point on Z = 0. Viewing only."""
    placed = assembled(d, x_wing)
    lowest = min(p.bounding_box()[2] for p in placed)
    return [
        (p.translate((0, 0, -lowest)), COLORS[name])
        for p, name in zip(placed, (*PART_NAMES, "coin"), strict=True)
    ]


def outputs(x_wing: float, mini_x_wing: float) -> list[tuple[Manifold, Path, str]]:
    """Every plain generated file: ``(solid, path, name)``."""
    files = [(build_plate(FULL, x_wing), DIR / "glider.stl", "glider")]
    for name, solid in zip(PART_NAMES, parts(FULL, x_wing), strict=True):
        files.append((build_part(solid), DIR / f"part-{name}.stl", name))
    files.append((build_plate(MINI, mini_x_wing), DIR / "mini-glider.stl", "mini"))
    return files


def report(label: str, d: Design, x_wing: float, props: dict[str, float]) -> None:
    print(f"{label}: wing leading edge at X = {x_wing:.1f} mm, coin: {d.coin}")
    print(f"  CG {props['cg']:.1f} mm, NP {props['np']:.1f} mm behind it")
    print(f"  static margin {props['margin'] * 100:.1f} % of the chord")
    print(f"  tail volume {props['tail_volume']:.2f}, fin {props['fin_volume']:.3f}")
    print(f"  side area {props['side_area_arm']:.1f} mm behind the CG")
    print(
        f"  mass {props['mass']:.1f} g with the coin, wing loading {props['wing_loading']:.1f} g/dm2"
    )
    print(f"  filament {props['filament']:.1f} m (1.75 mm PLA, without the coin)")


def main() -> None:
    x_wing, props = verify(FULL)
    report("glider", FULL, x_wing, props)
    mini_x_wing, mini_props = verify(MINI)
    report("mini", MINI, mini_x_wing, mini_props)
    for d, x, name, label in (
        (FULL, x_wing, "combined.stl", "glider assembled"),
        (MINI, mini_x_wing, "mini-combined.stl", "mini glider assembled"),
    ):
        write_colored_stl(build_combined(d, x), DIR / name, label)
        print(f"wrote {DIR / name}")
    for solid, path, name in outputs(x_wing, mini_x_wing):
        write_stl(solid, path, name)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
