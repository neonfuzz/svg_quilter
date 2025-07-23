"""Arrange seam allowance shapes onto pages for printing or export.

Provide utilities to layout groups with seam allowances on pages,
using translation and rotation to fit within printable areas.
"""

from typing import Dict, List, Any
import matplotlib.pyplot as plt
from shapely.affinity import translate, rotate
from shapely.geometry import Polygon


def apply_transform(
    geom: Polygon, rotation: float = 0, dx: float = 0, dy: float = 0
) -> Polygon:
    """Apply rotation and translation to a geometry.

    Args:
        geom: Shapely Polygon object.
        rotation: Rotation angle in degrees.
        dx: X translation.
        dy: Y translation.

    Returns:
        Transformed Polygon.
    """
    if rotation != 0:
        geom = rotate(geom, rotation, origin="centroid")
    return translate(geom, dx, dy)


def get_polygon_bounds(polygon: Polygon) -> (float, float):
    """Return (width, height) of polygon's bounding box.

    Args:
        polygon: Shapely Polygon object.

    Returns:
        Tuple (width, height).
    """
    minx, miny, maxx, maxy = polygon.bounds
    return maxx - minx, maxy - miny


def layout_groups(
    seam_allowances: Dict[int, Polygon],
    page_width_in: float,
    page_height_in: float,
    margin_in: float = 0.5,
    svg_units_per_in: float = 96,
    allow_rotate: bool = True,
) -> List[List[Dict[str, Any]]]:
    """Arrange seam allowance polygons on pages with margins.

    Args:
        seam_allowances: Dict {group_idx: seam_allowance Polygon}.
        page_width_in: Page width in inches.
        page_height_in: Page height in inches.
        margin_in: Margin size in inches.
        svg_units_per_in: SVG units per inch.
        allow_rotate: Whether to rotate shapes to fit.

    Returns:
        List of pages, each a list of placement dicts with keys:
        group_idx, rotation, dx, dy.
    """
    page_width = page_width_in * svg_units_per_in
    page_height = page_height_in * svg_units_per_in
    margin = margin_in * svg_units_per_in

    placed = set()
    pages = []
    group_items = list(seam_allowances.items())
    group_items.sort(key=lambda item: -item[1].area)

    while len(placed) < len(group_items):
        page_placements = []
        x, y = margin, margin
        max_row_height = 0
        for group_idx, poly in group_items:
            if group_idx in placed:
                continue
            pw, ph = get_polygon_bounds(poly)
            fits_normal = (x + pw + margin <= page_width) and (
                y + ph + margin <= page_height
            )
            fits_rot = (
                allow_rotate
                and (x + ph + margin <= page_width)
                and (y + pw + margin <= page_height)
            )
            if fits_normal or fits_rot:
                rotation = 0
                if fits_rot and ph > pw:
                    rotation = 90
                    pw, ph = ph, pw
                minx, miny, _, _ = rotate(poly, rotation, origin="centroid").bounds
                dx, dy = x - minx, y - miny
                page_placements.append(
                    {
                        "group_idx": group_idx,
                        "rotation": rotation,
                        "dx": dx,
                        "dy": dy,
                    }
                )
                placed.add(group_idx)
                x += pw + margin
                max_row_height = max(max_row_height, ph)
                if x + pw + margin > page_width:
                    x = margin
                    y += max_row_height + margin
                    max_row_height = 0
        if not page_placements:
            raise ValueError(
                "A group does not fit on the page! "
                "Increase page size or decrease margin."
            )
        pages.append(page_placements)
    return pages
