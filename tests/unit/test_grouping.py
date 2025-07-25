import pytest
from shapely.geometry import Polygon, LineString
from grouping import (
    build_polygon_adjacency,
    classify_seams,
    find_exact_full_shared_edge,
    group_polygons,
    is_concave,
    polygon_area,
    polygon_max_seam_order,
    polygons_are_adjacent,
    seam_is_collinear_with_bbox_edge,
)


def test_polygon_area_returns_positive():
    square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    reversed_square = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
    assert polygon_area(square) == 1.0
    assert polygon_area(reversed_square) == 1.0


def test_polygons_are_adjacent_true_and_false():
    p1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    p2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])  # Touches p1
    p3 = Polygon([(2, 0), (3, 0), (3, 1), (2, 1)])  # Does not touch p1

    assert polygons_are_adjacent(p1, p2)
    assert not polygons_are_adjacent(p1, p3)


def test_build_polygon_adjacency():
    p1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    p2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
    p3 = Polygon([(2, 0), (3, 0), (3, 1), (2, 1)])
    polygons = [p1, p2, p3]

    adjacency = build_polygon_adjacency(polygons)
    assert adjacency == {
        0: {1},
        1: {0, 2},
        2: {1},
    }


def test_find_exact_full_shared_edge_true_and_false():
    p1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    p2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])  # Shares one edge
    p3 = Polygon([(2, 0), (3, 0), (3, 1), (2, 1)])  # Doesn't share

    assert find_exact_full_shared_edge(p1, p2)
    assert not find_exact_full_shared_edge(p1, p3)


def test_is_concave_identifies_concave_shapes():
    convex = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    concave = Polygon([(0, 0), (2, 0), (1, 1), (2, 2), (0, 2)])  # Has inward dent

    assert not is_concave(convex)
    assert is_concave(concave)


def test_group_polygons_basic_merge():
    square1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    square2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])  # Shares edge with square1
    square3 = Polygon([(2, 0), (3, 0), (3, 1), (2, 1)])  # Adjacent to square2

    polygons = [square3, square1, square2]  # Intentionally shuffled

    # Collect all unique edges as lines
    def polygon_edges(poly):
        coords = list(poly.exterior.coords)
        return [LineString([coords[i], coords[i + 1]]) for i in range(len(coords) - 1)]

    edge_set = set()
    for poly in polygons:
        for edge in polygon_edges(poly):
            # Use tuple for hashability, directionless
            key = tuple(sorted(edge.coords))
            edge_set.add(key)
    lines = [LineString(edge) for edge in edge_set]

    groups = group_polygons(polygons, lines)
    assert len(groups) == 1
    assert sorted(groups[0]) == [0, 1, 2]


def test_seam_is_collinear_with_bbox_edge_true_and_false():
    bbox = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    # Seam exactly along bottom edge
    seam1 = LineString([(0, 0), (2, 0)])
    # Seam along a diagonal (not collinear)
    seam2 = LineString([(0, 0), (2, 2)])
    # Seam almost collinear, but offset
    seam3 = LineString([(0, 0.1), (2, 0.1)])
    assert seam_is_collinear_with_bbox_edge(seam1, bbox, tol=1e-6)
    assert not seam_is_collinear_with_bbox_edge(seam2, bbox, tol=1e-6)
    assert not seam_is_collinear_with_bbox_edge(seam3, bbox, tol=1e-6)


def test_classify_seams_simple():
    bbox = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    seams = [
        LineString([(0, 0), (2, 0)]),  # seam 0: bottom edge
        LineString([(0, 2), (2, 2)]),  # seam 1: top edge
        LineString([(1, -0.1), (1, 2.1)]),  # seam 2: vertical, crosses both edge seams
        LineString([(-0.1, 1), (1.1, 1)]),  # seam 3: horizontal, crosses seam 2
    ]
    orders = classify_seams(seams, bbox, tol=1e-6)
    assert orders[0] == 0  # edge
    assert orders[1] == 0  # edge
    assert orders[2] == 1  # crosses two 0th order seams
    assert orders[3] == 2  # crosses 1st order seam


def test_polygon_max_seam_order():
    poly = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    seam1 = LineString([(0, 0), (2, 0)])  # bottom edge
    seam2 = LineString([(1, 0), (1, 2)])  # vertical through middle
    seams = [seam1, seam2]
    seam_orders = {0: 0, 1: 1}
    # Both seams touch the polygon, so max order is 1
    assert polygon_max_seam_order(poly, seams, seam_orders) == 1
    # Remove the vertical seam: only edge seam left
    assert polygon_max_seam_order(poly, [seam1], {0: 0}) == 0
    # No seams at all
    assert polygon_max_seam_order(poly, [], {}) == -1
