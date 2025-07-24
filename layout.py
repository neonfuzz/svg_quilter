"""Arrange seam allowance shapes onto pages for printing or export.

Provide utilities to layout groups with seam allowances on pages,
using translation and rotation to fit within printable areas.
"""

from typing import Dict, List, Any

from rectpack import newPacker
from shapely.affinity import rotate as shapely_rotate
from shapely.geometry import Polygon


def layout_groups(
    seam_allowances: Dict[int, Polygon],
    page_width_in: float,
    page_height_in: float,
    margin_in: float = 0.5,
    margin_between: float = 0.1,
    svg_units_per_in: float = 96,
    allow_rotate: bool = True,
) -> List[List[Dict[str, Any]]]:
    """Arrange seam allowance polygons using rectpack for tight packing.

    Args:
        seam_allowances: Dict {group_idx: Polygon} for each group.
        page_width_in: Page width in inches.
        page_height_in: Page height in inches.
        margin_in: Page margin in inches.
        margin_in: Margin between shapes in inches.
        svg_units_per_in: SVG units per inch.
        allow_rotate: Allow 90-degree rotation for packing.

    Returns:
        List of pages, each a list of placement dicts for each group.
    """
    inner_width = (page_width_in - 2 * margin_in) * svg_units_per_in
    inner_height = (page_height_in - 2 * margin_in) * svg_units_per_in
    margin = margin_in * svg_units_per_in
    grow = (margin_between / 2) * svg_units_per_in

    packer = newPacker(rotation=allow_rotate)
    rectangles = []
    # Add each polygon's bounding box as a rectangle to the packer
    for group_idx, poly in seam_allowances.items():
        minx, miny, maxx, maxy = poly.bounds
        w = maxx - minx + 2*grow
        h = maxy - miny + 2*grow
        packer.add_rect(w, h, group_idx)
        rectangles.append((group_idx, w, h, minx, miny))

    # Add a bin (page) of inner dimensions (many bins allowed)
    packer.add_bin(inner_width, inner_height, float("inf"))
    packer.pack()

    pages = []
    for abin in packer:
        page_placements = []
        for rect in abin:
            group_idx = rect.rid
            x, y = rect.x, rect.y
            w, h = rect.width, rect.height
            orig = next(r for r in rectangles if r[0] == group_idx)
            orig_w, orig_h = orig[1], orig[2]
            minx, miny = orig[3], orig[4]
            # Rotation detection: rectpack swaps w/h if rotated
            rotation = 90 if allow_rotate and ((w, h) != (orig_w, orig_h)) else 0
            if rotation == 90:
                poly = seam_allowances[group_idx]
                poly = shapely_rotate(poly, 90, origin="centroid")
                minx, miny, _, _ = poly.bounds
            dx = x + grow + margin - minx
            dy = y + grow + margin - miny

            page_placements.append(
                {
                    "group_idx": group_idx,
                    "rotation": rotation,
                    "dx": dx,
                    "dy": dy,
                }
            )
        if page_placements:
            pages.append(page_placements)
    return pages
