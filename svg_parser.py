"""Provide a utility to parse SVG files into Shapely LineString objects.

Use svgpathtools to extract only straight line path segments from an
SVG file, returning them as Shapely LineString objects for geometric
operations or further processing.
"""

from typing import List

from shapely.geometry import LineString
from svgpathtools import Line, svg2paths2  # type: ignore[import-untyped]


def parse_svg(svg_filename: str) -> List[LineString]:
    """Parse an SVG file and return a list of Shapely LineString objects.

    Args:
        svg_filename (str): Path to the SVG file.

    Returns:
        List[LineString]: Shapely LineString objects representing
            SVG line segments.
    """
    paths, _, _ = svg2paths2(svg_filename)
    return [
        LineString(
            [
                (segment.start.real, segment.start.imag),
                (segment.end.real, segment.end.imag),
            ]
        )
        for path in paths
        for segment in path
        if isinstance(segment, Line)
    ]
