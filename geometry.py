"""Provide utilities for converting Shapely lines to convex hull polygons.

Offer a function to extract convex hull polygons from a list of Shapely
LineString objects using shapely's polygonize, unary_union, and convex_hull.
"""

from typing import List
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

from utils import remove_collinear_points


def lines_to_polygons(lines: List[LineString]) -> List[Polygon]:
    """Convert a list of Shapely LineString objects to convex hull polygons.

    Args:
        lines: List of shapely.geometry.LineString objects.

    Returns:
        List of convex hull polygons as shapely.geometry.Polygon objects.
    """
    merged = unary_union(lines)
    polygons = polygonize(merged)
    return [
        remove_collinear_points(poly)
        for poly in polygons
        if len(poly.exterior.coords) > 3
    ]
