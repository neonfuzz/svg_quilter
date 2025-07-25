import pytest
from shapely.geometry import Polygon, MultiPolygon
from seam_allowance import (
    group_polygons_to_shape,
    clean_and_buffer_group_shape,
    seam_allowance_polygons,
)


def test_group_polygons_to_shape_single_and_multi():
    square1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    square2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
    square3 = Polygon([(10, 10), (11, 10), (11, 11), (10, 11)])
    polygons = [square1, square2, square3]

    # Group with touching shapes → single polygon
    shape1 = group_polygons_to_shape(polygons, [0, 1])
    assert isinstance(shape1, Polygon)

    # Group with disjoint shapes → MultiPolygon
    shape2 = group_polygons_to_shape(polygons, [0, 2])
    assert isinstance(shape2, MultiPolygon)


def test_clean_and_buffer_group_shape_returns_buffered_shape():
    square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    allowance = 0.1
    buffered = clean_and_buffer_group_shape(square, allowance)

    assert isinstance(buffered, Polygon)
    assert buffered.area > square.area
    # Area should increase with buffer
    assert buffered.area - square.area > 0.01


def test_seam_allowance_polygons_basic_grouping_and_buffer():
    square1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    square2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
    square3 = Polygon([(3, 0), (4, 0), (4, 1), (3, 1)])
    polygons = [square1, square2, square3]
    groups = [[0, 1], [2]]

    result = seam_allowance_polygons(
        polygons, groups, allowance_in_inches=0.25, svg_units_per_inch=96
    )

    assert isinstance(result, dict)
    assert set(result.keys()) == {0, 1}
    assert all(isinstance(shape, (Polygon, MultiPolygon)) for shape in result.values())

    area_0 = result[0].area
    area_1 = result[1].area
    # Area of buffered group should be > than unbuffered union area
    assert area_0 > 2.0
    assert area_1 > 1.0
