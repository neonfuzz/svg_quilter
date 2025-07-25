"""Group Shapely Polygon objects by shared edges for FPP-style quilt patterns.

Uses seam order logic for correct seed selection.

Provide utilities for grouping, coloring, and visualizing Shapely
Polygon objects, along with geometric adjacency and grouping logic.
"""

from typing import List, Dict, Set

import numpy as np
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

from utils import collinear, remove_collinear_points


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


def seam_is_collinear_with_bbox_edge(
    seam: LineString, bbox: Polygon, tol: float = 1e1
) -> bool:
    """Check if a seam is collinear with any edge of the bounding box.

    Args:
        seam (LineString): The seam to check.
        bbox (Polygon): The bounding box.
        tol (float, optional): Tolerance for collinearity check. Defaults to 1e-1.

    Returns:
        bool: True if the seam is collinear with any edge of the bounding box,
            False otherwise.
    """
    bbox_edges = list(
        zip(list(bbox.exterior.coords)[:-1], list(bbox.exterior.coords)[1:])
    )
    seam_coords = list(seam.coords)
    for edge in bbox_edges:
        a, b = edge
        # Check both endpoints of seam for collinearity with the bbox edge
        # If both seam endpoints are collinear with the edge (a,b),
        # we consider the seam collinear with the bbox edge
        if collinear(a, b, seam_coords[0], tol) and collinear(
            a, b, seam_coords[1], tol
        ):
            return True
    return False


def classify_seams(
    lines: List[LineString], bounding_box: Polygon, tol: float = 1e1
) -> dict:
    """Assign order to each seam.

    0 = collinear with bbox edge
    1 = crosses bbox edge in two places (primary)
    2 = crosses primary (secondary)
    etc.
    """
    seam_orders = {}
    seams = list(lines)
    n = len(seams)

    # 0th order: collinear with bbox edge
    for i, seam in enumerate(seams):
        if seam_is_collinear_with_bbox_edge(seam, bounding_box, tol):
            seam_orders[i] = 0

    # 1st order: crosses TWO 0th order seams
    for i, seam in enumerate(seams):
        if i in seam_orders:
            continue
        crosses_edge = sum(
            seam.intersects(seams[j]) for j, order in seam_orders.items() if order == 0
        )
        if crosses_edge == 2:
            seam_orders[i] = 1

    # Higher order: crosses previous order
    current_order = 2
    while len(seam_orders) < n:
        for i, seam in enumerate(seams):
            if i in seam_orders:
                continue
            crosses_prev = any(
                seam.intersects(seams[j])
                for j, order in seam_orders.items()
                if order == current_order - 1
            )
            if crosses_prev:
                seam_orders[i] = current_order
        current_order += 1
        if current_order > 10:
            break
    return seam_orders


def polygon_max_seam_order(
    poly: Polygon,
    seams: List[LineString],
    seam_orders: Dict[int, int],
    tol: float = 1e1,
) -> int:
    """Return the highest seam order used by the edges of this polygon.

    Args:
        poly (Polygon): Polygon to check.
        seams (List[LineString]): List of LineStrings (seams).
        seam_orders (Dict[int, int]): Mapping seam index to order.
        tol (float): Tolerance for collinearity.

    Returns:
        int: Maximum seam order present among the edges (or -1 if none match).
    """
    max_order = -1
    poly_edges = list(
        zip(list(poly.exterior.coords)[:-1], list(poly.exterior.coords)[1:])
    )
    for edge in poly_edges:
        a, b = edge
        for i, seam in enumerate(seams):
            sc = list(seam.coords)
            # Only check seam if it is a 2-point LineString
            if len(sc) == 2:
                c, d = sc
                # Edges are considered equal if both endpoints are collinear
                if (collinear(a, b, c, tol) and collinear(a, b, d, tol)) or (
                    collinear(c, d, a, tol) and collinear(c, d, b, tol)
                ):
                    max_order = max(max_order, seam_orders.get(i, -1))
    return max_order


def group_polygons(polygons: List[Polygon], lines: List[LineString]) -> List[tuple]:
    """Group polygons for FPP, using seam order logic to choose correct seed.

    Args:
        polygons: List of Shapely Polygon objects
        lines: List of Shapely LineString seams

    Returns:
        List of groups (list of polygon indices)
    """
    bounding_box = unary_union(polygons).convex_hull
    seam_orders = classify_seams(lines, bounding_box)
    polygon_orders = [polygon_max_seam_order(p, lines, seam_orders) for p in polygons]

    adjacency = build_polygon_adjacency(polygons)
    already_grouped: Set[int] = set()
    groups: List[List[int]] = []
    n = len(polygons)
    while len(already_grouped) < n:
        candidates = [i for i in range(n) if i not in already_grouped]
        # Find the highest order present among ungrouped polygons
        highest_order = max(polygon_orders[i] for i in candidates)
        # Filter to only those with that order
        seed_candidates = [i for i in candidates if polygon_orders[i] == highest_order]
        # Of these, pick the smallest area as seed
        seed = min(seed_candidates, key=lambda idx: polygon_area(polygons[idx]))
        group = grow_group_from_seed(seed, polygons, adjacency, already_grouped)
        groups.append(list(group))
        already_grouped.update(group)
    return groups
