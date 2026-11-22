"""Small toolkit for generating printable STL models with manifold3d."""

from .checks import (
    DEFAULT_MAX_SIZE,
    assert_printable,
    assert_rounded,
    assert_supported,
    worst_unsupported_layer,
)
from .export import write_colored_stl, write_stl
from .scripts import load_script
from .shapes import bar, regular_polygon, ring, round_corners, star
from .solids import center_of_mass, extrude, layout_on_plate

__all__ = [
    "DEFAULT_MAX_SIZE",
    "assert_printable",
    "assert_rounded",
    "assert_supported",
    "bar",
    "center_of_mass",
    "extrude",
    "layout_on_plate",
    "load_script",
    "regular_polygon",
    "ring",
    "round_corners",
    "star",
    "worst_unsupported_layer",
    "write_colored_stl",
    "write_stl",
]
