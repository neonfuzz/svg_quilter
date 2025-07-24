"""Provide utilities for converting Shapely lines to convex hull polygons.

Offer a function to extract convex hull polygons from a list of Shapely
LineString objects using shapely's polygonize, unary_union, and convex_hull.
"""

from typing import List
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

from utils import remove_collinear_points


def lines_to_polygons(
    lines: List[LineString],
    snap_tol: float = 1e-3,
    min_area: float = 1e-1,
) -> List[Polygon]:
    """Convert list of LineString objects to polygons, snapping endpoints.

    Args:
        lines: List of shapely.geometry.LineString objects.
        snap_tol: Snapping tolerance (default 0.001 units).
        min_area: Minimum polygon area to keep (default 1e-6).

    Returns:
        List of convex hull polygons as shapely.geometry.Polygon objects.
    """

    def snap_line(line: LineString, tol: float = 1e-3) -> LineString:
        def snap(v):
            return round(v / tol) * tol

        return LineString([(snap(x), snap(y)) for x, y in line.coords])

    snapped_lines = [snap_line(line, tol=snap_tol) for line in lines]
    merged = unary_union(snapped_lines)
    polygons = polygonize(merged)
    return [
        remove_collinear_points(poly)
        for poly in polygons
        if len(poly.exterior.coords) > 3 and poly.area > min_area
    ]
