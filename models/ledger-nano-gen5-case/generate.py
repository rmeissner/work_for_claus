"""Replacement case for a bare Ledger Nano Gen5 board, in millimeters.

This script builds the bottom tray and the top bezel, both printed without
supports, and an assembled preview. The tray (floor-down) holds the board stack
(board, glued touchscreen and battery) and has the USB-C and side-button openings
plus the channels and grooves the snap hooks of the bezel catch in. The bezel
(face-down, posts and hooks up) is a frame with a window over the screen; it rests
on the screen border and on the tray walls. Four posts on its underside carry the
board, which is screwed to them from the back.

The board is axis-aligned with its long side along X. The USB-C port is on the
short edge at +X and the side button on the long edge at +Y. Every board dimension
below is a placeholder; measure the board with calipers and replace them.
"""

import math
import sys
from pathlib import Path

from manifold3d import CrossSection, Manifold

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import (
    assert_printable,
    assert_supported,
    extrude,
    round_corners,
    write_colored_stl,
    write_stl,
)

# Board stack: the largest outline of board, screen and battery.
BOARD_LENGTH = 76.0  # TODO: measure
BOARD_WIDTH = 50.0  # TODO: measure
BOARD_CORNER_RADIUS = 1.0  # TODO: measure
# From the lowest point (battery or underside parts) to the screen surface.
STACK_HEIGHT = 7.5  # TODO: measure

# Screen: visible area, centred on the board. The bezel window follows in phase 3.
SCREEN_LENGTH = 57.0  # TODO: measure
SCREEN_WIDTH = 43.0  # TODO: measure
SCREEN_BORDER = 2.0  # TODO: measure (glued edge the bezel lip rests on)

# USB-C port on the short edge at +X.
USB_OFFSET = 0.0  # TODO: measure (centre, from the middle of the long edge)
USB_HEIGHT = 3.0  # TODO: measure (centre above the lowest point of the stack)
USB_WIDTH = 12.0  # TODO: measure (plug overmold, along Y)
USB_SIZE_Z = 7.0  # TODO: measure (plug overmold, along Z)

# Side button on the long edge at +Y.
BUTTON_OFFSET = 0.0  # TODO: measure (centre, from the middle of the short edge)
BUTTON_HEIGHT = 4.0  # TODO: measure (centre above the lowest point of the stack)
BUTTON_LENGTH = 8.0  # TODO: measure (along X)
BUTTON_SIZE_Z = 3.0  # TODO: measure (along Z)
BUTTON_ACCESS = 1.0  # Extra room on every side so a fingertip reaches the button.

# Tray.
CLEARANCE = 0.3  # Per side between board stack and pocket.
WALL = 2.0  # Room for the hook channels and grooves with a solid wall behind them.
FLOOR = 1.2
CORNER_RADIUS = 3.0  # Outer corners; a placeholder the user adjusts later.

# Channels and grooves on the inside of the long walls for the bezel's snap hooks.
# Each hook arm hangs in a channel from the wall top; its barb catches in a groove
# below. Depths are measured into the wall from the pocket face.
CHANNEL_DEPTH = 0.8  # Room for a 0.7 mm hook arm plus a 0.1 mm gap.
GROOVE_DEPTH = 1.2  # The barb reaches 0.4 mm past the channel.
GROOVE_HEIGHT = 1.6
GROOVE_TOP_GAP = 4.5  # From the wall top to the groove roof; a long arm flexes easily.
GROOVE_LENGTH = 10.0  # Channel and groove, along the wall.
GROOVE_OFFSET = 20.0  # Centres at +-GROOVE_OFFSET from the middle of the wall.

# Bezel.
BEZEL_THICKNESS = 1.6
WINDOW_LIP = 1.0  # How far the bezel overlaps the glued screen border.
WINDOW_RADIUS = 1.0

# Screw posts: the board is screwed to them from the back (battery side).
SCREW_INSET = (
    3.0  # TODO: measure (hole centres, in from each board corner along X and Y)
)
POST_DIAMETER = 4.0  # TODO: measure
PILOT_HOLE = 1.6  # TODO: measure (M2 self-tapping screw)
BOARD_TOP_BELOW_SCREEN = (
    1.5  # TODO: measure (board top surface below the screen surface)
)

# Snap hooks. The board fills the pocket, so each hook arm lives in a channel in the
# inner face of the long walls and flexes in the room left by the clearance. Dimensions
# are measured into the wall from the pocket face.
HOOK_ARM_THICKNESS = 0.7  # Thin enough to flex, thick enough to print (~2 lines).
HOOK_OVERHANG = 0.4  # How far the barb reaches into the groove.
HOOK_GAP = 0.1  # Between the arm and the back of the channel.
HOOK_TIP = 0.4  # Height of the barb's flat tip; its top and bottom slope at 45°.
HOOK_LENGTH = 9.4  # Along the wall.
HOOK_MAX_STRAIN = 0.02  # PLA breaks beyond roughly 2 % bending strain.

EPS = 0.5  # Overlap that makes cuts break cleanly through a face.

POCKET_LENGTH = BOARD_LENGTH + 2 * CLEARANCE
POCKET_WIDTH = BOARD_WIDTH + 2 * CLEARANCE
POCKET_RADIUS = BOARD_CORNER_RADIUS + CLEARANCE
OUTER_LENGTH = POCKET_LENGTH + 2 * WALL
OUTER_WIDTH = POCKET_WIDTH + 2 * WALL
# The walls reach the screen surface, where the bezel sits on them.
TRAY_HEIGHT = FLOOR + STACK_HEIGHT


def _rect(length: float, width: float, radius: float) -> CrossSection:
    return round_corners(CrossSection.square((length, width), center=True), radius)


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Manifold:
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def _wall_points(
    x: float,
    side: int,
    profile: list[tuple[float, float]],
    length: float = GROOVE_LENGTH,
) -> list[tuple[float, float, float]]:
    """Points of a profile (depth into the wall, z) along X, on the wall at ``side`` * Y."""
    face = side * POCKET_WIDTH / 2
    return [
        (x + dx * length / 2, face + side * depth, z)
        for dx in (-1, 1)
        for depth, z in profile
    ]


# Where the groove roof meets the channel; the roof slopes at 45° below it.
GROOVE_ROOF = TRAY_HEIGHT - GROOVE_TOP_GAP


def _groove(x: float, side: int) -> Manifold:
    """A channel from the wall top down to a groove in the inner face of the long wall.

    The groove roof slopes at 45° so the groove prints without supports.
    """
    roof = GROOVE_ROOF
    bottom = roof - GROOVE_HEIGHT
    top = TRAY_HEIGHT + EPS
    channel = Manifold.hull_points(
        _wall_points(
            x,
            side,
            [
                (-EPS, bottom),
                (CHANNEL_DEPTH, bottom),
                (CHANNEL_DEPTH, top),
                (-EPS, top),
            ],
        )
    )
    groove = Manifold.hull_points(
        _wall_points(
            x,
            side,
            [
                (CHANNEL_DEPTH - EPS, bottom),
                (GROOVE_DEPTH, bottom),
                (GROOVE_DEPTH, roof - (GROOVE_DEPTH - CHANNEL_DEPTH)),
                (CHANNEL_DEPTH, roof),
                (CHANNEL_DEPTH - EPS, roof),
            ],
        )
    )
    return channel + groove


def tray() -> Manifold:
    body = extrude(_rect(OUTER_LENGTH, OUTER_WIDTH, CORNER_RADIUS), TRAY_HEIGHT)
    pocket = extrude(_rect(POCKET_LENGTH, POCKET_WIDTH, POCKET_RADIUS), TRAY_HEIGHT)
    body -= pocket.translate((0, 0, FLOOR))

    # Notches cut down from the top edge, so they need no bridging.
    top = TRAY_HEIGHT + EPS
    usb_bottom = max(FLOOR, FLOOR + USB_HEIGHT - USB_SIZE_Z / 2)
    body -= _box(
        POCKET_LENGTH / 2 - EPS,
        OUTER_LENGTH / 2 + EPS,
        USB_OFFSET - USB_WIDTH / 2,
        USB_OFFSET + USB_WIDTH / 2,
        usb_bottom,
        top,
    )
    button_half = BUTTON_LENGTH / 2 + BUTTON_ACCESS
    button_bottom = max(
        FLOOR, FLOOR + BUTTON_HEIGHT - BUTTON_SIZE_Z / 2 - BUTTON_ACCESS
    )
    body -= _box(
        BUTTON_OFFSET - button_half,
        BUTTON_OFFSET + button_half,
        POCKET_WIDTH / 2 - EPS,
        OUTER_WIDTH / 2 + EPS,
        button_bottom,
        top,
    )

    for side in (-1, 1):
        for x in (-GROOVE_OFFSET, GROOVE_OFFSET):
            body -= _groove(x, side)
    return body


def _hook(x: float, side: int) -> Manifold:
    """A snap hook in the assembled position: it hangs from the bezel underside.

    The barb's catch face matches the groove roof (45°, contact along the slope);
    its bottom has a 45° lead-in chamfer for snapping on.
    """
    t = HOOK_ARM_THICKNESS
    # The roof, extended to the arm's outer face, is where the catch face starts.
    catch = GROOVE_ROOF + (CHANNEL_DEPTH - t)
    tip_top = catch - HOOK_OVERHANG
    tip_bottom = tip_top - HOOK_TIP
    arm_bottom = tip_bottom - HOOK_OVERHANG
    arm = Manifold.hull_points(
        _wall_points(
            x,
            side,
            [(0, arm_bottom), (t, arm_bottom), (t, TRAY_HEIGHT), (0, TRAY_HEIGHT)],
            HOOK_LENGTH,
        )
    )
    barb = Manifold.hull_points(
        _wall_points(
            x,
            side,
            [
                (t - 0.1, arm_bottom),
                (t, arm_bottom),
                (t + HOOK_OVERHANG, tip_bottom),
                (t + HOOK_OVERHANG, tip_top),
                (t, catch),
                (t - 0.1, catch),
            ],
            HOOK_LENGTH,
        )
    )
    return arm + barb


def _posts() -> Manifold:
    """Four posts hanging from the plate underside to the board's top surface.

    The pilot hole runs the full post length but stops at the plate, so the visible
    face of the bezel stays closed.
    """
    bottom = TRAY_HEIGHT - BOARD_TOP_BELOW_SCREEN
    post = Manifold.cylinder(
        BOARD_TOP_BELOW_SCREEN, POST_DIAMETER / 2, circular_segments=48
    )
    hole = Manifold.cylinder(
        BOARD_TOP_BELOW_SCREEN + EPS, PILOT_HOLE / 2, circular_segments=32
    )
    post -= hole.translate((0, 0, -EPS))
    posts = Manifold()
    for x, y in _post_centres():
        posts += post.translate((x, y, bottom))
    return posts


def _post_centres() -> list[tuple[float, float]]:
    x = BOARD_LENGTH / 2 - SCREW_INSET
    y = BOARD_WIDTH / 2 - SCREW_INSET
    return [(sx * x, sy * y) for sx in (-1, 1) for sy in (-1, 1)]


def hook_strain() -> float:
    """Peak bending strain of a hook arm (cantilever) while the barb passes the channel."""
    arm_length = TRAY_HEIGHT - (GROOVE_ROOF - 2 * HOOK_OVERHANG - HOOK_TIP + HOOK_GAP)
    deflection = HOOK_ARM_THICKNESS + HOOK_OVERHANG - CHANNEL_DEPTH
    return 1.5 * HOOK_ARM_THICKNESS * deflection / arm_length**2


def _hooks() -> Manifold:
    hooks = Manifold()
    for side in (-1, 1):
        for x in (-GROOVE_OFFSET, GROOVE_OFFSET):
            hooks += _hook(x, side)
    return hooks


def bezel_assembled() -> Manifold:
    """The bezel in place on the tray: the plate on top of the walls, hooks hanging down."""
    plate = extrude(_rect(OUTER_LENGTH, OUTER_WIDTH, CORNER_RADIUS), BEZEL_THICKNESS)
    plate = plate.translate((0, 0, TRAY_HEIGHT))
    window_length = SCREEN_LENGTH + 2 * (SCREEN_BORDER - WINDOW_LIP)
    window_width = SCREEN_WIDTH + 2 * (SCREEN_BORDER - WINDOW_LIP)
    window = extrude(
        _rect(window_length, window_width, WINDOW_RADIUS), BEZEL_THICKNESS + 2
    )
    plate -= window.translate((0, 0, TRAY_HEIGHT - 1))

    # Keep the tray's notches open from above: the USB-C plug and a fingertip for the button.
    z0, z1 = TRAY_HEIGHT - 1, TRAY_HEIGHT + BEZEL_THICKNESS + 1
    plate -= _box(
        POCKET_LENGTH / 2,
        OUTER_LENGTH / 2 + EPS,
        USB_OFFSET - USB_WIDTH / 2,
        USB_OFFSET + USB_WIDTH / 2,
        z0,
        z1,
    )
    button_half = BUTTON_LENGTH / 2 + BUTTON_ACCESS
    plate -= _box(
        BUTTON_OFFSET - button_half,
        BUTTON_OFFSET + button_half,
        POCKET_WIDTH / 2,
        OUTER_WIDTH / 2 + EPS,
        z0,
        z1,
    )
    return plate + _hooks() + _posts()


def bezel_printed(assembled: Manifold) -> Manifold:
    """Turn the bezel face-down: the visible side on the bed, hooks pointing up."""
    flipped = assembled.rotate((180, 0, 0))
    return flipped.translate((0, 0, -flipped.bounding_box()[2]))


def check_snap(part: Manifold, bezel: Manifold) -> None:
    """Hooks must flex within PLA's limit and parts touch only where intended."""
    # The hooks must fit the tray's channels and grooves.
    if not math.isclose(HOOK_ARM_THICKNESS + HOOK_GAP, CHANNEL_DEPTH):
        raise ValueError("the hook arm does not match the channel depth")
    if not math.isclose(CHANNEL_DEPTH + HOOK_OVERHANG, GROOVE_DEPTH):
        raise ValueError("the hook overhang does not match the groove depth")
    if HOOK_LENGTH > GROOVE_LENGTH:
        raise ValueError("the hooks are longer than the channels")
    strain = hook_strain()
    if strain > HOOK_MAX_STRAIN:
        raise ValueError(f"the hook arms bend too far: {strain:.1%} strain")
    # The bezel rests on the tray walls and the barbs on the groove roofs. These are
    # contacts of coincident faces, so the shared volume is zero up to float rounding;
    # allow 1e-3 mm3 (a 0.01 mm cube) for that rounding.
    shared = (part ^ bezel).volume()
    if shared > 1e-3:
        raise ValueError(f"the bezel and the tray intersect by {shared:.4f} mm3")
    # The board stack is the board up to its top surface plus the screen with its glued
    # border above it. The hooks, posts and plate may touch it, but not enter it: the
    # posts reach the board's top surface and stop there.
    board_top = STACK_HEIGHT - BOARD_TOP_BELOW_SCREEN
    board = extrude(_rect(BOARD_LENGTH, BOARD_WIDTH, BOARD_CORNER_RADIUS), board_top)
    screen = extrude(
        _rect(
            SCREEN_LENGTH + 2 * SCREEN_BORDER, SCREEN_WIDTH + 2 * SCREEN_BORDER, 0.01
        ),
        STACK_HEIGHT,
    )
    stack = (board + screen).translate((0, 0, FLOOR))
    if (stack ^ bezel).volume() > 1e-3:
        raise ValueError("the bezel intersects the board stack")
    # Each post must stand on the board outside the screen window and the glued border.
    for x, y in _post_centres():
        r = POST_DIAMETER / 2
        if abs(x) + r > BOARD_LENGTH / 2 or abs(y) + r > BOARD_WIDTH / 2:
            raise ValueError("a screw post is not inside the board outline")
        if abs(x) - r < SCREEN_LENGTH / 2 + SCREEN_BORDER and (
            abs(y) - r < SCREEN_WIDTH / 2 + SCREEN_BORDER
        ):
            raise ValueError("a screw post is in the way of the screen")
    # The posts reach the board's top surface, the plate sits on the screen surface.
    if (_posts() ^ part).volume() > 1e-3:
        raise ValueError("the screw posts intersect the tray")
    if (_posts() ^ _hooks()).volume() > 1e-3:
        raise ValueError("the screw posts intersect the hooks")


def check_fit(part: Manifold) -> None:
    """The board stack plus the clearance on every side must not touch the tray."""
    # Shrink the margin a hair so the exactly touching pocket walls do not count.
    margin = CLEARANCE - 0.001
    stack = extrude(
        _rect(
            BOARD_LENGTH + 2 * margin,
            BOARD_WIDTH + 2 * margin,
            BOARD_CORNER_RADIUS + margin,
        ),
        STACK_HEIGHT,
    ).translate((0, 0, FLOOR))
    if (stack ^ part).volume() > 1e-3:
        raise ValueError("the board stack does not fit the pocket with the clearance")
    if SCREEN_LENGTH + 2 * SCREEN_BORDER > BOARD_LENGTH:
        raise ValueError("the screen and its border are longer than the board")
    if SCREEN_WIDTH + 2 * SCREEN_BORDER > BOARD_WIDTH:
        raise ValueError("the screen and its border are wider than the board")


def _single_solid(part: Manifold, name: str) -> None:
    assert_printable(part)
    if len(part.decompose()) != 1:
        raise ValueError(f"the {name} must be one connected solid")
    assert_supported(part)


def main() -> None:
    folder = Path(__file__).parent
    part = tray()
    _single_solid(part, "tray")
    check_fit(part)

    in_place = bezel_assembled()
    bezel = bezel_printed(in_place)
    _single_solid(bezel, "bezel")
    check_snap(part, in_place)

    write_colored_stl(
        [(part, (176, 180, 186)), (in_place, (58, 62, 70))],
        folder / "assembled.stl",
        "ledger-nano-gen5-case",
    )
    write_stl(part, folder / "tray.stl", "ledger-nano-gen5-tray")
    write_stl(bezel, folder / "bezel.stl", "ledger-nano-gen5-bezel")


if __name__ == "__main__":
    main()
