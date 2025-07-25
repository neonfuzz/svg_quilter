import pytest
from shapely.geometry import Polygon
from grouping import (
    polygon_area,
    polygons_are_adjacent,
    build_polygon_adjacency,
    find_exact_full_shared_edge,
    is_concave,
    group_polygons,
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

    groups = group_polygons(polygons)
    assert len(groups) == 1
    assert sorted(groups[0]) == [0, 1, 2]
