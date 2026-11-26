"""Replacement case for a bare Ledger Nano Gen5 board, in millimeters.

This script builds the bottom tray, printed floor-down without supports. The tray
holds the board stack (board, glued touchscreen and battery) and has the USB-C and
side-button openings plus the channels and grooves the snap hooks of the top bezel catch in.

The board is axis-aligned with its long side along X. The USB-C port is on the
short edge at +X and the side button on the long edge at +Y. Every board dimension
below is a placeholder; measure the board with calipers and replace them.
"""

import sys
from pathlib import Path

from manifold3d import CrossSection, Manifold

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import assert_printable, assert_supported, extrude, round_corners, write_stl

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
    x: float, side: int, profile: list[tuple[float, float]]
) -> list[tuple[float, float, float]]:
    """Points of a profile (depth into the wall, z) along X, on the wall at ``side`` * Y."""
    face = side * POCKET_WIDTH / 2
    return [
        (x + dx * GROOVE_LENGTH / 2, face + side * depth, z)
        for dx in (-1, 1)
        for depth, z in profile
    ]


def _groove(x: float, side: int) -> Manifold:
    """A channel from the wall top down to a groove in the inner face of the long wall.

    The groove roof slopes at 45° so the groove prints without supports.
    """
    roof = TRAY_HEIGHT - GROOVE_TOP_GAP
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


def main() -> None:
    part = tray()
    assert_printable(part)
    if len(part.decompose()) != 1:
        raise ValueError("the tray must be one connected solid")
    assert_supported(part)
    check_fit(part)
    write_stl(part, Path(__file__).with_name("tray.stl"), "ledger-nano-gen5-tray")


if __name__ == "__main__":
    main()
