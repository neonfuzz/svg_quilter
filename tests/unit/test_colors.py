import base64
import io
import xml.etree.ElementTree as ET

import pytest
from PIL import Image
from shapely.geometry import Polygon

from colors import (
    extract_image_from_svg,
    svg_to_img_coords,
    average_color,
    closest_color_name,
    sample_polygon_color,
    polygon_color_map,
)


def _make_svg_with_png(pil_img, x=0, y=0, width=None, height=None):
    """Helper to create SVG string with embedded PNG image."""
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    w, h = pil_img.size if width is None or height is None else (width, height)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink">'
        f'<image xlink:href="data:image/png;base64,{b64}" '
        f'x="{x}" y="{y}" width="{w}" height="{h}"/>'
        "</svg>"
    )


def test_extract_image_from_svg_returns_image_and_metadata():
    img = Image.new("RGB", (2, 2), (0, 255, 0))
    svg = _make_svg_with_png(img, x=5, y=10, width=2, height=2)
    tree = ET.ElementTree(ET.fromstring(svg))
    out_img, offset, svg_size = extract_image_from_svg(tree)
    assert out_img.size == (2, 2)
    assert offset == (5, 10)
    assert svg_size == (2, 2)
    assert out_img.getpixel((0, 0)) == (0, 255, 0)


def test_extract_image_from_svg_raises_on_missing_image():
    svg = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    tree = ET.ElementTree(ET.fromstring(svg))
    with pytest.raises(ValueError):
        extract_image_from_svg(tree)


def test_svg_to_img_coords_identity():
    px, py = svg_to_img_coords(
        centroid_x=1,
        centroid_y=1,
        offset=(0, 0),
        svg_size=(2, 2),
        img_size=(2, 2),
    )
    assert (px, py) == (1, 1)


def test_svg_to_img_coords_scaled():
    px, py = svg_to_img_coords(
        centroid_x=10,
        centroid_y=5,
        offset=(0, 0),
        svg_size=(20, 10),
        img_size=(40, 20),
    )
    assert (px, py) == (20, 10)


def test_average_color_simple():
    img = Image.new("RGB", (10, 10), (123, 45, 67))
    poly = Polygon([(2, 2), (8, 2), (8, 8), (2, 8)])
    rgb = average_color(poly, img, offset=(0, 0), svg_size=(10, 10), radius=0)
    assert rgb == (123, 45, 67)


def test_average_color_out_of_bounds():
    img = Image.new("RGB", (4, 4), (1, 2, 3))
    # centroid is outside image bounds
    poly = Polygon([(10, 10), (11, 10), (11, 11), (10, 11)])
    rgb = average_color(poly, img, offset=(0, 0), svg_size=(4, 4), radius=0)
    assert rgb == (0, 0, 0)  # returns black if no pixels sampled


def test_sample_polygon_color_red():
    img = Image.new("RGB", (1, 1), (255, 0, 0))
    svg = _make_svg_with_png(img)
    tree = ET.ElementTree(ET.fromstring(svg))
    image, offset, svg_size = extract_image_from_svg(tree)
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    name, rgb = sample_polygon_color(poly, image, offset, svg_size, radius=0)
    assert rgb == (255, 0, 0)
    assert "red" in name


def test_closest_color_name_exact():
    assert closest_color_name((0, 0, 255)).endswith("blue")


def test_polygon_color_map_multiple_polys():
    img = Image.new("RGB", (5, 5), (100, 100, 0))
    svg = _make_svg_with_png(img, width=5, height=5)
    tree = ET.ElementTree(ET.fromstring(svg))
    polys = [
        Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
        Polygon([(3, 3), (4, 3), (4, 4), (3, 4)]),
    ]
    rgb_map, name_map = polygon_color_map(polys, tree)
    assert rgb_map[0] == (100, 100, 0)
    assert rgb_map[1] == (100, 100, 0)
    assert name_map[0] == name_map[1]
