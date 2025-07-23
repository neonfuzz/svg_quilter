import matplotlib.pyplot as plt
from shapely.affinity import translate, rotate
from shapely.geometry import box


def apply_transform(geom, rotation=0, dx=0, dy=0):
    g = geom
    if rotation != 0:
        g = rotate(g, rotation, origin="centroid")
    return translate(g, dx, dy)


def get_polygon_bounds(polygon):
    minx, miny, maxx, maxy = polygon.bounds
    return maxx - minx, maxy - miny


def layout_groups(
    seam_allowances,
    page_width_in,
    page_height_in,
    margin_in=0.5,
    svg_units_per_in=96,
    allow_rotate=True,
):
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
        for idx, (group_idx, poly) in enumerate(group_items):
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
                # Find where to place after rotation (we'll apply this later)
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
                # Update for next position
                x += pw + margin
                max_row_height = max(max_row_height, ph)
                if x + pw + margin > page_width:
                    x = margin
                    y += max_row_height + margin
                    max_row_height = 0
        if not page_placements:
            raise ValueError(
                "A group does not fit on the page! Increase page size or decrease margin."
            )
        pages.append(page_placements)
    return pages
