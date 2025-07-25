"""Group Shapely Polygon objects by shared edges for FPP-style quilt patterns.

Provide utilities for grouping, coloring, and visualizing Shapely
Polygon objects, along with geometric adjacency and grouping logic.
"""

from typing import List, Dict, Set

import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

from utils import remove_collinear_points


def polygon_area(poly: Polygon) -> float:
    """Return absolute area of a polygon.

    Args:
        poly: Shapely Polygon object.

    Returns:
        Absolute area as float.
    """
    return abs(poly.area)


def polygons_are_adjacent(p1: Polygon, p2: Polygon) -> bool:
    """Return True if polygons p1 and p2 touch or overlap.

    Args:
        p1: Shapely Polygon object.
        p2: Shapely Polygon object.

    Returns:
        True if polygons intersect, else False.
    """
    return p1.intersects(p2)


def build_polygon_adjacency(polygons: List[Polygon]) -> Dict[int, Set[int]]:
    """Build adjacency dict: key=index, value=set of neighbor indices.

    Args:
        polygons: List of Shapely Polygon objects.

    Returns:
        Dict mapping polygon index to set of adjacent polygon indices.
    """
    n = len(polygons)
    adjacency: Dict[int, Set[int]] = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if polygons_are_adjacent(polygons[i], polygons[j]):
                adjacency[i].add(j)
                adjacency[j].add(i)
    return adjacency


def coords_equal(a, b, tol):
    """Return True if the coordinates a and b are equal within tolerance tol."""
    return np.allclose(a, b, atol=tol)


def find_exact_full_shared_edge(
    poly1: Polygon, poly2: Polygon, tol: float = 1e-6
) -> bool:
    """Return True if poly1 and poly2 share an edge within tolerance tol."""
    coords1 = list(poly1.exterior.coords)
    coords2 = list(poly2.exterior.coords)
    n1 = len(coords1)
    n2 = len(coords2)

    matches = 0
    for i in range(n1 - 1):
        a1, a2 = coords1[i], coords1[i + 1]
        for j in range(n2 - 1):
            b1, b2 = coords2[j], coords2[j + 1]
            if (coords_equal(a1, b2, tol) and coords_equal(a2, b1, tol)) or (
                coords_equal(a1, b1, tol) and coords_equal(a2, b2, tol)
            ):
                matches += 1
    return matches == 1  # Only one shared edge (FPP-style)


def is_concave(polygon: Polygon, tol: float = 1e-2) -> bool:
    """Return True if the polygon is concave based on convex hull area difference."""
    #  if isinstance(polygon, MultiPolygon):
    #      polygon = unary_union(polygon)
    #      if isinstance(polygon, MultiPolygon):
    #          polygon = max(polygon.geoms, key=lambda g: g.area)
    convex = polygon.convex_hull
    if convex.area < polygon.area:
        return False
    return (convex.area / polygon.area - 1) > tol


def grow_group_from_seed(
    seed_idx: int,
    polygons: List[Polygon],
    adjacency: Dict[int, Set[int]],
    already_grouped: Set[int],
    tol: float = 1e-2,
) -> List[int]:
    """Grow a group from a seed polygon index, adding adjacent neighbors.

    Args:
        seed_idx: Polygon index to start grouping from.
        polygons: List of Shapely Polygon objects.
        adjacency: Adjacency dict {index: set of neighbor indices}.
        already_grouped: Set of already grouped polygon indices.
        tol: Rounding tolerance for edge matching.

    Returns:
        List of polygon indices in the group, ordered by addition.
    """
    group_idxs = [seed_idx]
    current_shape = polygons[seed_idx]
    grouped = set([seed_idx]) | already_grouped

    while True:
        candidates = []
        for idx in group_idxs:
            for neighbor in adjacency[idx]:
                if neighbor not in grouped and neighbor not in candidates:
                    candidates.append(neighbor)
        found = False
        for neighbor in candidates:
            neighbor_poly = polygons[neighbor]
            match = find_exact_full_shared_edge(neighbor_poly, current_shape, tol)
            if match:
                merged = current_shape.union(neighbor_poly)
                if is_concave(merged):
                    continue
                current_shape = remove_collinear_points(merged.convex_hull)
                group_idxs.append(neighbor)
                grouped.add(neighbor)
                found = True
                break
        if not found:
            break
    return group_idxs


def group_polygons(polygons: List[Polygon]) -> List[List[int]]:
    """Group polygons by shared edges for FPP grouping.

    Args:
        polygons: List of Shapely Polygon objects.

    Returns:
        List of groups, each a list of polygon indices.
    """
    adjacency = build_polygon_adjacency(polygons)
    already_grouped: Set[int] = set()
    groups: List[List[int]] = []
    n = len(polygons)
    while len(already_grouped) < n:
        candidates = [i for i in range(n) if i not in already_grouped]
        seed = min(candidates, key=lambda idx: polygon_area(polygons[idx]))
        group = grow_group_from_seed(seed, polygons, adjacency, already_grouped)
        groups.append(list(group))
        already_grouped.update(group)
    return groups
