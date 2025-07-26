"""Unit tests for the png_writer module."""

import os

from shapely.geometry import Polygon

from png_writer import (
    PolygonLayoutConfig,
    LayoutOutputConfig,
    PolygonLayoutPlotter,
    save_overall_layout_png,
)


def simple_polygons():
    # Simple triangles for deterministic testing
    polys = [
        Polygon([(0, 0), (1, 0), (0, 1)]),
        Polygon([(2, 0), (3, 0), (2, 1)]),
    ]
    labels = {0: "A", 1: "B"}
    positions = {0: (0.5, 0.25), 1: (2.5, 0.25)}
    return polys, labels, positions


def test_polygonlayoutconfig_fields():
    polys, labels, positions = simple_polygons()
    config = PolygonLayoutConfig(polys, labels, positions)
    assert config.polygons == polys
    assert config.piece_labels == labels
    assert config.label_positions == positions
    assert config.groups is None
    assert config.figsize == (8, 10)


def test_layoutoutputconfig_defaults():
    out_cfg = LayoutOutputConfig()
    assert out_cfg.out_png == "overall_layout.png"
    assert out_cfg.dpi == 300
    assert out_cfg.title.startswith("FPP Pattern")


def test_polygonlayoutplotter_color_assignment():
    polys, labels, positions = simple_polygons()
    # Explicit colors
    colors = {0: (255, 0, 0), 1: (0, 255, 0)}
    config = PolygonLayoutConfig(polys, labels, positions, polygon_colors=colors)
    plotter = PolygonLayoutPlotter(config)
    poly_colors = plotter.get_polygon_colors()
    assert poly_colors[0] == (1.0, 0.0, 0.0)
    assert poly_colors[1] == (0.0, 1.0, 0.0)


def test_polygonlayoutplotter_save_png(tmp_path):
    polys, labels, positions = simple_polygons()
    config = PolygonLayoutConfig(polys, labels, positions)
    plotter = PolygonLayoutPlotter(config)
    out_cfg = LayoutOutputConfig(out_png=str(tmp_path / "test.png"), dpi=100)
    plotter.save_png(out_cfg)
    assert os.path.isfile(out_cfg.out_png)
    # Optionally: check file size is reasonable (not empty)
    assert os.path.getsize(out_cfg.out_png) > 100


def test_save_overall_layout_png(tmp_path):
    polys, labels, positions = simple_polygons()
    layout_cfg = PolygonLayoutConfig(polys, labels, positions)
    output_cfg = LayoutOutputConfig(out_png=str(tmp_path / "function_api.png"), dpi=72)
    save_overall_layout_png(layout_cfg, output_cfg)
    assert os.path.isfile(output_cfg.out_png)
    assert os.path.getsize(output_cfg.out_png) > 50
