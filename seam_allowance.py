import random

import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union


def group_polygons_to_shape(polygons, group):
    """Return unioned shapely.Polygon for all polygons in the group."""
    return unary_union([Polygon(polygons[idx]) for idx in group])


def clean_and_buffer_group_shape(group_shape, allowance, simplify_tol=1e-9):
    simple = group_shape.convex_hull
    buffered = simple.buffer(allowance, join_style=2)  # join_style=2 for flat corners
    return buffered


def seam_allowance_polygons(
    polygons, groups, allowance_in_inches=0.25, svg_units_per_inch=96
):
    """
    Returns: dict {group_index: seam_allowance_shape (Shapely Polygon)}
    """
    allowance = allowance_in_inches * svg_units_per_inch
    result = {}
    for i, group in enumerate(groups):
        shape = group_polygons_to_shape(polygons, group)
        seam_shape = clean_and_buffer_group_shape(shape, allowance)
        result[i] = seam_shape
    return result
