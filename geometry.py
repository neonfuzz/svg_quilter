import random

import matplotlib.pyplot as plt
import numpy as np
from shapely.ops import polygonize, unary_union
from shapely.geometry import LineString

from utils import remove_collinear_points


def lines_to_polygons(lines, tol=1e-4):
    """
    Given a list of Shapely LineString objects,
    returns all closed polygons as lists of (x, y) tuples.
    Args:
        lines: list of shapely.geometry.LineString objects
        tol: coordinate rounding tolerance (default: 0.0001)
    Returns:
        polygons: list of polygons, each as list of (x, y) tuples
    """
    # Combine all lines, splitting at all intersections
    merged = unary_union(lines)
    polygons = list(polygonize(merged))

    def round_coords(coords):
        return [(round(x, 4), round(y, 4)) for x, y in coords]

    result = []
    for poly in polygons:
        coords = list(poly.exterior.coords)
        if len(coords) < 4:
            continue  # Skip degenerate
        if coords[0] == coords[-1]:
            coords = coords[:-1]  # Remove duplicate close point
        result.append(remove_collinear_points(round_coords(coords)))
    return result


# Example usage:
if __name__ == "__main__":
    import sys
    from svg_parser import parse_svg

    lines = parse_svg(sys.argv[1])
    polys = lines_to_polygons(lines)
    for i, poly in enumerate(polys):
        print(f"Polygon {i+1}: {poly}")
    plot_polygons(polys)
