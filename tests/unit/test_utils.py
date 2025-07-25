import pytest
from shapely.geometry import Polygon
from utils import (
    parse_length,
    remove_collinear_points,
    get_distinct_colors,
)


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("1in", 1.0),
        ("25.4mm", 1.0),
        ("2.54cm", 1.0),
        ("72pt", 1.0),
        ("6pc", 1.0),
        ("96px", 1.0),
        ("10", 10 / 96),  # Default to px
    ],
)
def test_parse_length_valid(input_str, expected):
    assert pytest.approx(parse_length(input_str), rel=1e-4) == expected


@pytest.mark.parametrize("invalid_str", ["abc", "10foo", "5%", "20em"])
def test_parse_length_invalid(invalid_str):
    with pytest.raises(ValueError):
        parse_length(invalid_str)


def test_remove_collinear_points_removes_excess_points():
    # Triangle with extra collinear points along edges
    coords = [(0, 0), (0.5, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    polygon = Polygon(coords)
    cleaned = remove_collinear_points(polygon, tol=1e-5)

    # Should still be a rectangle, but fewer points
    assert isinstance(cleaned, Polygon)
    assert len(cleaned.exterior.coords) < len(coords)


def test_remove_collinear_points_does_not_change_simple_shape():
    # Regular triangle
    triangle = Polygon([(0, 0), (1, 0), (0.5, 1), (0, 0)])
    cleaned = remove_collinear_points(triangle)
    assert isinstance(cleaned, Polygon)
    assert cleaned.equals(triangle)


def test_get_distinct_colors_count_and_bounds():
    colors = get_distinct_colors(10, pastel=True)
    assert len(colors) == 10
    for rgb in colors:
        for channel in rgb:
            assert 0 <= channel <= 1
