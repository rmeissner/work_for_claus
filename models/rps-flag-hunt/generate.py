"""Recessed-role cylinders for RPS Flag Hunt, in millimeters.

Print and play with the circular base at Z = 0. The engraved side faces -Y.
"""

import sys
from pathlib import Path

from manifold3d import CrossSection, Manifold

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from stlkit import assert_printable, bar, extrude, layout_on_plate, ring, write_stl

BODY_DIAMETER = 20.0
BODY_HEIGHT = 50.0
FOOT_HEIGHT = 10.0
FLAT_Y = -4.0
MARK_Z = 30.0
MARK_SCALE = 1.5
ENGRAVING_DEPTH = 0.8

TEAM_COUNTS = {"rock": 4, "paper": 4, "scissors": 4, "bomb": 1, "flag": 1}


def role_marks() -> dict[str, CrossSection]:
    rock = CrossSection(
        [
            [
                (-3.6, -1.1),
                (-1.8, -2.7),
                (1.8, -2.6),
                (3.4, -0.9),
                (2.2, 2.0),
                (-0.1, 3.1),
                (-2.6, 1.3),
            ]
        ]
    )
    paper = (
        CrossSection([[(-2.5, -3.3), (2.5, -3.3), (2.5, 1.5), (0.9, 3.3), (-2.5, 3.3)]])
        - bar((-1.4, -1.4), (1.4, -1.4), 0.8)
        - bar((-1.4, 0.2), (1.4, 0.2), 0.8)
    )

    scissors = (
        ring(1.5, 0.6).translate((-1.55, -2.0))
        + ring(1.5, 0.6).translate((1.55, -2.0))
        + bar((-1.25, -0.9), (2.0, 3.2), 1.0)
        + bar((1.25, -0.9), (-2.0, 3.2), 1.0)
    )
    bomb = (
        CrossSection.circle(2.45, 48).translate((-0.5, -0.9))
        + bar((-0.3, 1.2), (0.2, 2.5), 1.0)
        + bar((-0.05, 2.3), (1.65, 3.1), 1.0)
    )
    flag = bar((-2.1, -3.3), (-2.1, 3.0), 1.0) + CrossSection(
        [[(-2.1, -0.4), (2.9, 1.5), (-2.1, 3.4)]]
    )
    return {
        "rock": rock,
        "paper": paper,
        "scissors": scissors,
        "bomb": bomb,
        "flag": flag,
    }


def blank_piece() -> Manifold:
    radius = BODY_DIAMETER / 2
    cylinder = Manifold.cylinder(BODY_HEIGHT, radius, circular_segments=96)
    # Remove a circular segment above the foot to expose a vertical face.
    cut = Manifold.cube(
        (BODY_DIAMETER + 2, radius + FLAT_Y + 1, BODY_HEIGHT - FOOT_HEIGHT + 1)
    ).translate((-radius - 1, -radius - 1, FOOT_HEIGHT))
    return cylinder - cut


def main() -> None:
    blank = blank_piece()

    team = []
    for role, mark in role_marks().items():
        engraving = (
            extrude(mark.scale((MARK_SCALE, MARK_SCALE)), ENGRAVING_DEPTH + 1)
            .rotate((90, 0, 0))
            .translate((0, FLAT_Y + ENGRAVING_DEPTH, MARK_Z))
        )
        piece = blank - engraving
        assert_printable(piece)
        if len(piece.decompose()) != 1:
            raise ValueError(f"{role} must be one connected solid")
        write_stl(piece, Path(__file__).with_name(f"{role}.stl"), role)
        team.extend([piece] * TEAM_COUNTS[role])

    plate = layout_on_plate(team, gap=4, columns=4)
    assert_printable(plate)
    if len(plate.decompose()) != sum(TEAM_COUNTS.values()):
        raise ValueError("each team piece must be separate on the print plate")
    write_stl(plate, Path(__file__).with_name("team-plate.stl"), "rps-flag-hunt-team")


if __name__ == "__main__":
    main()
