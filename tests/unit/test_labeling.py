import pytest
from shapely.geometry import Polygon
from labeling import int_to_label, label_groups, get_label_positions, label_polygons


def test_int_to_label():
    assert int_to_label(0) == "A"
    assert int_to_label(25) == "Z"
    assert int_to_label(26) == "AA"
    assert int_to_label(27) == "AB"
    assert int_to_label(51) == "AZ"
    assert int_to_label(52) == "BA"
    assert int_to_label(701) == "ZZ"
    assert int_to_label(702) == "AAA"


def test_label_groups_default_prefixes():
    groups = [[0, 1], [2]]
    result = label_groups(groups)
    expected = {0: "A1", 1: "A2", 2: "B1"}
    assert result == expected


def test_label_groups_custom_prefixes():
    groups = [[3, 4], [5]]
    prefixes = ["X", "Y"]
    result = label_groups(groups, prefixes)
    expected = {3: "X1", 4: "X2", 5: "Y1"}
    assert result == expected


def test_get_label_positions():
    polygons = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),  # centroid (0.5, 0.5)
        Polygon([(2, 2), (4, 2), (3, 4)]),  # centroid (3.0, 2.666...)
    ]
    result = get_label_positions(polygons)
    assert result[0] == (0.5, 0.5)
    assert pytest.approx(result[1][0]) == 3.0
    assert pytest.approx(result[1][1]) == pytest.approx(2.6666666666666665)


def test_label_polygons_combined():
    polygons = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        Polygon([(2, 2), (4, 2), (3, 4)]),
        Polygon([(5, 5), (6, 5), (6, 6), (5, 6)]),
    ]
    groups = [[0, 1], [2]]
    labels, positions = label_polygons(polygons, groups)

    assert labels == {0: "A1", 1: "A2", 2: "B1"}
    assert positions[0] == (0.5, 0.5)
    assert pytest.approx(positions[1][0]) == 3.0
    assert pytest.approx(positions[1][1]) == pytest.approx(2.6666666666666665)
    assert positions[2] == (5.5, 5.5)
