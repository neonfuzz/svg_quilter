import textwrap
import matplotlib
import matplotlib.pyplot as plt
import pytest
from shapely.geometry import Polygon
from utils import (
    get_svg_units_per_inch,
    plot_groups,
    plot_polygons,
    plot_groups_with_seam_allowance,
)

matplotlib.use("Agg")


def simple_polygons():
    polys = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
    ]
    groups = [[0], [1]]
    seam_allowances = {0: polys[0].buffer(0.1), 1: polys[1].buffer(0.1)}
    return polys, groups, seam_allowances


def test_get_svg_units_per_inch_valid(tmp_path):
    svg = '<svg width="96px" viewBox="0 0 96 100"></svg>'
    path = tmp_path / "test.svg"
    path.write_text(svg)
    assert get_svg_units_per_inch(str(path)) == pytest.approx(96.0)


def test_get_svg_units_per_inch_invalid(tmp_path):
    svg_missing = '<svg width="96px"></svg>'
    path_missing = tmp_path / "missing.svg"
    path_missing.write_text(svg_missing)
    with pytest.raises(ValueError):
        get_svg_units_per_inch(str(path_missing))

    svg_bad_vb = '<svg width="1in" viewBox="0 0 100"></svg>'
    path_bad_vb = tmp_path / "bad.svg"
    path_bad_vb.write_text(svg_bad_vb)
    with pytest.raises(ValueError):
        get_svg_units_per_inch(str(path_bad_vb))


def test_plot_functions(monkeypatch):
    show_calls = []
    monkeypatch.setattr(plt, "show", lambda: show_calls.append(True))
    polys, groups, seam_allowances = simple_polygons()

    plot_groups(polys, groups)
    plot_polygons(polys, show_labels=True)
    plot_groups_with_seam_allowance(polys, groups, seam_allowances)

    assert len(show_calls) == 3
