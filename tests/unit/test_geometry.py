import pytest
from shapely.geometry import LineString, Polygon
from geometry import lines_to_polygons


def test_lines_to_polygons_simple_square():
    # Define square using 4 lines
    lines = [
        LineString([(0, 0), (1, 0)]),
        LineString([(1, 0), (1, 1)]),
        LineString([(1, 1), (0, 1)]),
        LineString([(0, 1), (0, 0)]),
    ]

    polygons = lines_to_polygons(lines)

    assert len(polygons) == 1
    poly = polygons[0]

    assert isinstance(poly, Polygon)
    assert pytest.approx(poly.area) == 1.0
    # Should be roughly square
    assert set(poly.exterior.coords) >= set([(0, 0), (1, 0), (1, 1), (0, 1)])


def test_lines_to_polygons_ignores_small_area():
    # Very tiny triangle (area < 0.1)
    lines = [
        LineString([(0, 0), (0.01, 0)]),
        LineString([(0.01, 0), (0, 0.01)]),
        LineString([(0, 0.01), (0, 0)]),
    ]

    polygons = lines_to_polygons(lines, min_area=0.1)
    assert polygons == []


def test_lines_to_polygons_multiple_polygons():
    square1 = [
        LineString([(0, 0), (1, 0)]),
        LineString([(1, 0), (1, 1)]),
        LineString([(1, 1), (0, 1)]),
        LineString([(0, 1), (0, 0)]),
    ]
    square2 = [
        LineString([(2, 2), (3, 2)]),
        LineString([(3, 2), (3, 3)]),
        LineString([(3, 3), (2, 3)]),
        LineString([(2, 3), (2, 2)]),
    ]

    polygons = lines_to_polygons(square1 + square2)

    assert len(polygons) == 2
    areas = sorted([poly.area for poly in polygons])
    assert all(pytest.approx(a) == 1.0 for a in areas)
