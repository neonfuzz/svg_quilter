"""Write grouped FPP polygons and seam allowances to PDF using ReportLab."""

from typing import List, Dict, Any, Tuple, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, HexColor
from reportlab.pdfbase import pdfmetrics
from shapely.affinity import rotate as shapely_rotate, translate as shapely_translate
from shapely.geometry import Polygon, Point


def text_center_offset(fontname: str, fontsize: float) -> float:
    """Return baseline offset so text is centered vertically."""
    ascent = pdfmetrics.getAscent(fontname)
    descent = pdfmetrics.getDescent(fontname)
    return (ascent + descent) / 2000 * fontsize


def transform_group_shapes(
    group_polys: List[Polygon],
    seam_poly: Polygon,
    rotation: float,
    dx: float,
    dy: float,
) -> Tuple[List[Polygon], Polygon]:
    """Rotate and translate group polygons and seam allowance.

    Args:
        group_polys: List of Shapely Polygon objects.
        seam_poly: Seam allowance Polygon for the group.
        rotation: Rotation angle in degrees.
        dx: X translation (SVG units).
        dy: Y translation (SVG units).

    Returns:
        (transformed group polygons, transformed seam polygon)
    """
    origin = seam_poly.centroid
    seam_poly_rot = shapely_rotate(seam_poly, rotation, origin=origin)
    group_polys_rot = [shapely_rotate(p, rotation, origin=origin) for p in group_polys]
    seam_poly_final = shapely_translate(seam_poly_rot, dx, dy)
    group_polys_final = [shapely_translate(p, dx, dy) for p in group_polys_rot]
    return group_polys_final, seam_poly_final


def draw_polygon(
    c: canvas.Canvas,
    poly: Polygon,
    svg_units_per_in: float,
    fill_color: Any = None,
    stroke_color: Any = black,
    alpha: float = 1.0,
    linewidth: float = 1,
) -> None:
    """Draw a single polygon on a ReportLab canvas.

    Args:
        c: ReportLab canvas.
        poly: Shapely Polygon object.
        svg_units_per_in: Conversion factor (SVG units to inches).
        fill_color: Fill color for polygon.
        stroke_color: Stroke color for polygon.
        alpha: Fill opacity.
        linewidth: Line width (points).
    """
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


def apply_transform(
    geom: Polygon,
    rotation: float = 0,
    dx: float = 0,
    dy: float = 0,
) -> Polygon:
    """Rotate and translate a geometry (polygon or point).

    Args:
        geom: Shapely geometry (Polygon or Point).
        rotation: Rotation angle in degrees.
        dx: X translation.
        dy: Y translation.

    Returns:
        Transformed geometry.
    """
    if rotation != 0:
        geom = shapely_rotate(geom, rotation, origin="centroid")
    return shapely_translate(geom, dx, dy)


def pdf_writer(
    filename: str,
    pages: List[List[Dict[str, Any]]],
    seam_allowances: Dict[int, Polygon],
    polygons: List[Polygon],
    groups: List[List[int]],
    piece_labels: Dict[int, str],
    label_positions: Dict[int, Tuple[float, float]],
    color_names: Optional[Dict[int, str]] = None,
    page_width_in: float = 8.5,
    page_height_in: float = 11,
    svg_units_per_in: float = 96,
    label_fontsize: int = 24,
) -> None:
    """Write seam allowance layouts and labels to PDF pages.

    Args:
        filename: Output PDF file path.
        pages: List of pages, each as list of placement dicts.
        seam_allowances: Dict {group_idx: seam allowance Polygon}.
        polygons: List of Shapely Polygon objects.
        groups: List of groups, each a list of polygon indices.
        piece_labels: Dict {poly_idx: label string}.
        label_positions: Dict {poly_idx: (x, y)} original label positions.
        polygon_colors: Optional mapping of polygon index to RGB fill color.
        color_names: Optional mapping of polygon index to color name.
        page_width_in: PDF page width (inches).
        page_height_in: PDF page height (inches).
        svg_units_per_in: SVG units per inch.
        label_fontsize: Font size for labels.
    """
    c = canvas.Canvas(filename, pagesize=(page_width_in * 72, page_height_in * 72))
    gray = HexColor("#888888")
    light = HexColor("#eeeeee")

    for placements in pages:
        for placement in placements:
            group_idx = placement["group_idx"]
            rotation = placement["rotation"]
            dx = placement["dx"]
            dy = placement["dy"]
            seam_poly = seam_allowances[group_idx]
            group_poly_idxs = groups[group_idx]
            group_polys = [polygons[pi] for pi in group_poly_idxs]

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
                linewidth=0,
            )

            # Draw polygons and labels (transformed positions)
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
                # Transform label position with same rotation/translation
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
                # Center text both horizontally and vertically
                offset = text_center_offset("Helvetica-Bold", label_fontsize)
                c.drawCentredString(lx, ly - offset, piece_labels[poly_idx])
                if color_names and poly_idx in color_names:
                    c.setFont("Helvetica", label_fontsize * 0.5)
                    c.drawCentredString(
                        lx, ly - offset - label_fontsize * 0.75, color_names[poly_idx]
                    )
        c.showPage()
    c.save()
