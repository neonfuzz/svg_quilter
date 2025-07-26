"""Extract and name colors from embedded images in SVG files."""

from __future__ import annotations

import base64
import io
import xml.etree.ElementTree as ET
from typing import Tuple, Dict, List

import matplotlib.colors as mcolors
from PIL import Image
from shapely.geometry import Polygon
import webcolors


def extract_image_from_svg(
    svg_tree: ET.ElementTree,
) -> Tuple[Image.Image, Tuple[float, float], Tuple[float, float]]:
    """Return embedded bitmap image, its offset, and SVG size from an SVG tree.

    Returns:
        Tuple[Image.Image, (x, y), (svg_w, svg_h)]: Decoded image, (x, y) offset,
            and (svg_width, svg_height) from the SVG.

    Raises:
        ValueError: If no base64 image is present in the SVG.
    """
    root = svg_tree.getroot()
    ns = {
        "svg": "http://www.w3.org/2000/svg",
        "xlink": "http://www.w3.org/1999/xlink",
    }
    for image_elem in root.findall(".//svg:image", ns):
        href = image_elem.get("{http://www.w3.org/1999/xlink}href")
        x = float(image_elem.get("x", 0))
        y = float(image_elem.get("y", 0))
        # SVG width/height in user units (often px, but can be mm, etc)
        svg_w = float(image_elem.get("width", 0))
        svg_h = float(image_elem.get("height", 0))
        if href and href.startswith("data:image/") and "base64," in href:
            data = base64.b64decode(href.split(",", 1)[1])
            img = Image.open(io.BytesIO(data)).convert("RGB")
            return img, (x, y), (svg_w, svg_h)
    raise ValueError("No base64-encoded image found in SVG.")


def svg_to_img_coords(
    centroid_x: float,
    centroid_y: float,
    offset: Tuple[float, float],
    svg_size: Tuple[float, float],
    img_size: Tuple[int, int],
) -> Tuple[int, int]:
    """Convert SVG centroid coordinates to image pixel coordinates."""
    svg_x, svg_y = offset
    svg_w, svg_h = svg_size
    img_w, img_h = img_size

    # Handle missing width/height: default to bitmap's pixel size.
    scale_x = img_w / svg_w if svg_w > 0 else 1.0
    scale_y = img_h / svg_h if svg_h > 0 else 1.0

    px = int(round((centroid_x - svg_x) * scale_x))
    py = int(round((centroid_y - svg_y) * scale_y))
    return px, py


def average_color(
    poly: Polygon,
    image: Image.Image,
    offset: Tuple[float, float],
    svg_size: Tuple[float, float],
    radius: int,
) -> Tuple[int, int, int]:
    """Sample average color near polygon centroid, with SVG-image coordinate scaling.

    Args:
        poly: Polygon geometry.
        image: PIL Image.
        offset: (SVG x, y) of the image.
        svg_size: (SVG width, height) of the image in SVG units.
        radius: Sampling radius in pixels.

    Returns:
        Averaged RGB tuple.
    """
    px, py = svg_to_img_coords(
        poly.centroid.x, poly.centroid.y, offset, svg_size, image.size
    )
    img_w, img_h = image.size

    def neighbors() -> Tuple[int, int]:
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                x, y = px + dx, py + dy
                if 0 <= x < img_w and 0 <= y < img_h:
                    yield x, y

    pixels = [image.getpixel((x, y)) for x, y in neighbors()]
    if not pixels:
        return (0, 0, 0)
    n = len(pixels)
    r = sum(p[0] for p in pixels) // n
    g = sum(p[1] for p in pixels) // n
    b = sum(p[2] for p in pixels) // n
    return (r, g, b)


def closest_color_name(rgb: Tuple[int, int, int]) -> str:
    """Return the name of the closest known color for an RGB value."""

    def fix_name(name):
        if name.startswith("xkcd:"):
            return name[5:]
        return name

    try:
        return fix_name(webcolors.rgb_to_name(rgb))
    except ValueError:
        min_colors: Dict[int, str] = {}
        for name, hex_code in mcolors.XKCD_COLORS.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(hex_code)
            rd = (r_c - rgb[0]) ** 2
            gd = (g_c - rgb[1]) ** 2
            bd = (b_c - rgb[2]) ** 2
            min_colors[(rd + gd + bd)] = name
        return fix_name(min_colors[min(min_colors)])


def sample_polygon_color(
    poly: Polygon,
    image: Image.Image,
    offset: Tuple[float, float],
    svg_size: Tuple[float, float],
    radius: int = 6,
) -> Tuple[str, Tuple[int, int, int]]:
    """Sample the bitmap color near a polygon's centroid with scaling."""
    rgb = average_color(poly, image, offset, svg_size, radius)
    name = closest_color_name(rgb)
    return name, rgb


def polygon_color_map(
    polygons: List[Polygon], svg_tree: ET.ElementTree
) -> Tuple[Dict[int, Tuple[int, int, int]], Dict[int, str]]:
    """Return RGB and name maps for polygons if the SVG contains an image."""
    image, offset, svg_size = extract_image_from_svg(svg_tree)
    rgb_map: Dict[int, Tuple[int, int, int]] = {}
    name_map: Dict[int, str] = {}
    for idx, poly in enumerate(polygons):
        name, rgb = sample_polygon_color(poly, image, offset, svg_size)
        rgb_map[idx] = rgb
        name_map[idx] = name
    return rgb_map, name_map
