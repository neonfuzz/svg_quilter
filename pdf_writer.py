from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, HexColor
from shapely.affinity import rotate as shapely_rotate, translate as shapely_translate
from shapely.geometry import Polygon, Point


def transform_group_shapes(group_polys, seam_poly, rotation, dx, dy):
    # group_polys: list of shapely Polygons for this group
    # seam_poly: shapely Polygon for the group seam allowance
    # rotation: degrees (0 or 90, etc)
    # dx, dy: translation in SVG units
    # Always rotate around the centroid of the seam_poly!
    origin = seam_poly.centroid
    seam_poly_rot = shapely_rotate(seam_poly, rotation, origin=origin)
    group_polys_rot = [shapely_rotate(p, rotation, origin=origin) for p in group_polys]
    # After rotation, translate
    seam_poly_final = shapely_translate(seam_poly_rot, dx, dy)
    group_polys_final = [shapely_translate(p, dx, dy) for p in group_polys_rot]
    return group_polys_final, seam_poly_final


def draw_polygon(
    c,
    poly,
    svg_units_per_in,
    fill_color=None,
    stroke_color=black,
    alpha=1.0,
    linewidth=1,
):
    pts = [
        (x / svg_units_per_in * 72, y / svg_units_per_in * 72)
        for x, y in poly.exterior.coords
    ]
    path = c.beginPath()
    path.moveTo(*pts[0])
    for pt in pts[1:]:
        path.lineTo(*pt)
    path.close()
    if fill_color:
        c.setFillColor(fill_color, alpha=alpha)
    else:
        c.setFillColorRGB(1, 1, 1, alpha=0.0)
    c.setStrokeColor(stroke_color)
    c.setLineWidth(linewidth)
    c.drawPath(path, fill=1 if fill_color else 0, stroke=1)


def apply_transform(geom, rotation=0, dx=0, dy=0):
    if rotation != 0:
        geom = shapely_rotate(geom, rotation, origin="centroid")
    geom = shapely_translate(geom, dx, dy)
    return geom


def pdf_writer(
    filename,
    pages,
    seam_allowances,
    polygons,
    groups,
    piece_labels,
    label_positions,
    page_width_in=8.5,
    page_height_in=11,
    svg_units_per_in=96,
    label_fontsize=18,
):
    c = canvas.Canvas(filename, pagesize=(page_width_in * 72, page_height_in * 72))
    gray = HexColor("#888888")
    light = HexColor("#eeeeee")
    for page_num, placements in enumerate(pages, 1):
        for placement in placements:
            group_idx = placement["group_idx"]
            rotation = placement["rotation"]
            dx = placement["dx"]
            dy = placement["dy"]
            seam_poly = seam_allowances[group_idx]
            group_poly_idxs = groups[group_idx]
            group_polys = [Polygon(polygons[pi]) for pi in group_poly_idxs]

            # --- Transform group seam and polygons together
            group_polys_final, seam_poly_final = transform_group_shapes(
                group_polys, seam_poly, rotation, dx, dy
            )

            # Draw seam allowance
            draw_polygon(
                c,
                seam_poly_final,
                svg_units_per_in,
                fill_color=gray,
                stroke_color=gray,
                alpha=1.0,
                linewidth=3,
            )

            # Draw polygons and labels (using the correctly transformed positions)
            for poly, poly_idx in zip(group_polys_final, group_poly_idxs):
                draw_polygon(
                    c,
                    poly,
                    svg_units_per_in,
                    fill_color=light,
                    stroke_color=black,
                    alpha=1.0,
                    linewidth=1,
                )
                # Transform label position the same way:
                from shapely.geometry import Point

                orig_x, orig_y = label_positions[poly_idx]
                pt = Point(orig_x, orig_y)
                pt_rot = shapely_rotate(pt, rotation, origin=seam_poly.centroid)
                pt_tr = shapely_translate(pt_rot, dx, dy)
                lx, ly = (
                    pt_tr.x / svg_units_per_in * 72,
                    pt_tr.y / svg_units_per_in * 72,
                )
                c.setFont("Helvetica-Bold", label_fontsize)
                c.setFillColor(black)
                c.drawCentredString(lx, ly, piece_labels[poly_idx])
        c.showPage()
    c.save()
    print(f"Saved PDF to {filename}")
