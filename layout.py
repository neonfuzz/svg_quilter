"""Arrange seam allowance shapes onto pages for printing or export.

Provide utilities to layout groups with seam allowances on pages,
using translation and rotation to fit within printable areas.
"""

from typing import Dict, List, Any

from rectpack import newPacker
from shapely.affinity import rotate as shapely_rotate
from shapely.geometry import Polygon


def minimal_bounding_box_rotation(poly: Polygon, step: int = 5) -> (Polygon, float):
    """Rotate a polygon to minimize its bounding box area.

    Args:
        poly (Polygon): The input polygon.
        step (int, optional): The angle step for rotation. Defaults to 5.

    Returns:
        Tuple[Polygon, float]: A tuple containing the rotated polygon and
            the best angle of rotation.
    """
    min_area = float("inf")
    best_angle = 0
    best_poly = poly
    for angle in range(0, 180, step):
        rotated = shapely_rotate(poly, angle, origin="centroid", use_radians=False)
        minx, miny, maxx, maxy = rotated.bounds
        area = (maxx - minx) * (maxy - miny)
        if area < min_area:
            min_area = area
            best_angle = angle
            best_poly = rotated
    return best_poly, best_angle


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
        margin_between: Margin between shapes in inches.
        svg_units_per_in: SVG units per inch.
        allow_rotate: Allow 90-degree rotation for packing.

    Returns:
        List of pages, each a list of placement dicts for each group.

    Raises:
        ValueError: If any group fails to pack.
    """
    inner_width = (page_width_in - 2 * margin_in) * svg_units_per_in
    inner_height = (page_height_in - 2 * margin_in) * svg_units_per_in
    margin = margin_in * svg_units_per_in
    grow = (margin_between / 2) * svg_units_per_in

    packer = newPacker(rotation=allow_rotate)
    rectangles = []
    rotated_polys = {}

    # Add each polygon's bounding box as a rectangle to the packer
    for group_idx, poly in seam_allowances.items():
        best_poly, pre_rot_angle = minimal_bounding_box_rotation(poly)
        rotated_polys[group_idx] = (best_poly, pre_rot_angle)
        minx, miny, maxx, maxy = best_poly.bounds
        w = maxx - minx + 2 * grow
        h = maxy - miny + 2 * grow
        packer.add_rect(w, h, group_idx)
        rectangles.append((group_idx, w, h, minx, miny))

    # Add a bin (page) of inner dimensions (many bins allowed)
    packer.add_bin(inner_width, inner_height, float("inf"))
    packer.pack()

    packed_ids = {rect.rid for abin in packer for rect in abin}
    unpacked_ids = set(seam_allowances.keys()) - packed_ids
    if unpacked_ids:
        failed = ", ".join(str(i) for i in sorted(unpacked_ids))
        raise ValueError(
            f"Packing failed for group(s): {failed}. "
            "They may be too large for the page dimensions."
        )

    pages = []
    for abin in packer:
        page_placements = []
        for rect in abin:
            group_idx = rect.rid
            x, y = rect.x, rect.y
            w, h = rect.width, rect.height
            orig = next(r for r in rectangles if r[0] == group_idx)
            orig_w, orig_h, minx, miny = orig[1], orig[2], orig[3], orig[4]
            # Rotation detection: rectpack swaps w/h if rotated
            rectpack_rot = 90 if allow_rotate and ((w, h) != (orig_w, orig_h)) else 0

            rotated_poly, pre_rot_angle = rotated_polys[group_idx]
            if rectpack_rot == 90:
                rotated_poly = shapely_rotate(
                    rotated_poly, 90, origin="centroid", use_radians=False
                )
                minx, miny, _, _ = rotated_poly.bounds

            dx = x + grow + margin - minx
            dy = y + grow + margin - miny

            page_placements.append(
                {
                    "group_idx": group_idx,
                    "rotation": (pre_rot_angle + rectpack_rot) % 360,
                    "dx": dx,
                    "dy": dy,
                }
            )
        if page_placements:
            pages.append(page_placements)

    return pages
