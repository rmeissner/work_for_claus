"""Board interface, team counts, and symbols shared by RPS Flag Hunt models."""

from manifold3d import CrossSection

from .shapes import bar, ring

FOOT_DIAMETER = 20.0
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
