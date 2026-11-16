"""Split recessed lettering across separate interlocking bricks and lay them out."""

from . import assert_printable, extrude, layout_on_plate
from .bricks import BODY_HEIGHT, PITCH, WALL_THICKNESS, build_brick
from .text import text_shape


def wall_parts(
    text,
    courses,
    row_names,
    *,
    text_width,
    text_height,
    imprint_depth=0.6,
    fit_adjustment=0.0,
):
    """Return (filename stem, printable part, assembled position, row) tuples."""
    wall_studs = sum(courses[0])
    if len(row_names) != len(courses):
        raise ValueError("one row name is required per course")
    if not 0 < imprint_depth < WALL_THICKNESS - fit_adjustment:
        raise ValueError("imprint must leave material behind the front face")
    front_y = -(2 * PITCH - 0.2) / 2
    imprint = (
        extrude(
            text_shape(text, width=text_width, height=text_height), imprint_depth + 0.1
        )
        .rotate((90, 0, 0))
        .translate((0, front_y + imprint_depth, len(courses) * BODY_HEIGHT / 2))
    )
    result = []
    for row, columns in enumerate(courses):
        if sum(columns) != wall_studs:
            raise ValueError("each course must be the same stud width")
        cursor = -wall_studs * PITCH / 2
        for index, width in enumerate(columns, start=1):
            position = (cursor + width * PITCH / 2, 0, row * BODY_HEIGHT)
            brick = build_brick(width, fit_adjustment=fit_adjustment)
            placed = brick.translate(position) - imprint
            local = placed.translate(tuple(-p for p in position))
            assert_printable(local)
            if len(local.decompose()) != 1:
                raise ValueError("engraving disconnected a brick")
            name = f"{row_names[row]}-{index}"
            result.append((name, local, position, row))
            cursor += width * PITCH
    return result


def wall_print_plate(bricks, *, gap=5.0):
    """Keep each assembled course in its own row, each row centered on the bed."""
    row_count = max(row for _, _, _, row in bricks) + 1
    rows = []
    for row in range(row_count):
        course = [part for _, part, _, r in bricks if r == row]
        line = layout_on_plate(course, gap)
        rows.append(line.translate((0, ((row_count - 1) / 2 - row) * (15.8 + gap), 0)))
    plate = rows[0]
    for row in rows[1:]:
        plate += row
    assert_printable(plate)
    return plate
