"""Write grouped FPP polygons and seam allowances to PDF using ReportLab."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib.colors import HexColor, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as rl_canvas
from shapely.affinity import rotate as shapely_rotate
from shapely.affinity import translate as shapely_translate
from shapely.geometry import Point, Polygon


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


def apply_transform(
    geom: Polygon,
    rotation: float = 0,
    dx: float = 0,
    dy: float = 0,
) -> Polygon:
    """Rotate and translate a geometry (polygon or point)."""
    if rotation != 0:
        geom = shapely_rotate(geom, rotation, origin="centroid")
    return shapely_translate(geom, dx, dy)


@dataclass
class PDFWriterArgs:
    """Dataclass for all arguments required by PDFPolygonWriter and pdf_writer."""

    filename: str
    pages: List[List[Any]]
    seam_allowances: Dict[int, Polygon]
    polygons: List[Polygon]
    groups: List[List[int]]
    piece_labels: Dict[int, str]
    label_positions: Dict[int, Tuple[float, float]]
    color_names: Optional[Dict[int, str]] = None
    page_width_in: float = 8.5
    page_height_in: float = 11.0
    svg_units_per_in: float = 96.0
    label_fontsize: int = 24


@dataclass
class LabelDrawArgs:
    """Arguments for drawing a label on the canvas."""

    poly_idx: int
    rotation: float
    dx: float
    dy: float
    seam_poly: Polygon


class PDFPolygonWriter:
    """Class to write grouped polygons and seam allowances to a PDF using ReportLab."""

    def __init__(self, args: PDFWriterArgs) -> None:
        """Initialize PDFPolygonWriter from a PDFWriterArgs dataclass."""
        self.args = args
        self.gray = HexColor("#888888")
        self.light = HexColor("#eeeeee")
        self.canvas: Optional[rl_canvas.Canvas] = None
        # Drawing style attributes (set per shape in write())
        self.fill_color: Any = None
        self.stroke_color: Any = black
        self.alpha: float = 1.0
        self.linewidth: float = 1.0

    def draw_polygon(self, poly: Polygon) -> None:
        """Draw a polygon on the instance's canvas using instance drawing attributes."""
        assert self.canvas is not None, "Canvas must be initialized before drawing."
        pts = [
            (x / self.args.svg_units_per_in * 72, y / self.args.svg_units_per_in * 72)
            for x, y in poly.exterior.coords
        ]
        path = self.canvas.beginPath()
        path.moveTo(*pts[0])
        for pt in pts[1:]:
            path.lineTo(*pt)
        path.close()
        if self.fill_color:
            self.canvas.setFillColor(self.fill_color, alpha=self.alpha)
        else:
            self.canvas.setFillColorRGB(1, 1, 1, alpha=0.0)
        self.canvas.setStrokeColor(self.stroke_color)
        self.canvas.setLineWidth(self.linewidth)
        self.canvas.drawPath(path, fill=1 if self.fill_color else 0, stroke=1)

    def draw_label(self, args: LabelDrawArgs) -> None:
        """Draw a label on the canvas for the given polygon index."""
        assert self.canvas is not None, "Canvas must be initialized before drawing."
        orig_x, orig_y = self.args.label_positions[args.poly_idx]
        pt = Point(orig_x, orig_y)
        pt_rot = shapely_rotate(pt, args.rotation, origin=args.seam_poly.centroid)
        pt_tr = shapely_translate(pt_rot, args.dx, args.dy)
        lx, ly = (
            pt_tr.x / self.args.svg_units_per_in * 72,
            pt_tr.y / self.args.svg_units_per_in * 72,
        )
        self.canvas.setFont("Helvetica-Bold", self.args.label_fontsize)
        self.canvas.setFillColor(black)
        offset = text_center_offset("Helvetica-Bold", self.args.label_fontsize)
        self.canvas.drawCentredString(
            lx, ly - offset, self.args.piece_labels[args.poly_idx]
        )
        if self.args.color_names and args.poly_idx in self.args.color_names:
            self.canvas.setFont("Helvetica", self.args.label_fontsize * 0.5)
            self.canvas.drawCentredString(
                lx,
                ly - offset - self.args.label_fontsize * 0.75,
                self.args.color_names[args.poly_idx],
            )

    def write(self) -> None:
        """Write the polygons and labels to a PDF file."""
        self.canvas = rl_canvas.Canvas(
            self.args.filename,
            pagesize=(self.args.page_width_in * 72, self.args.page_height_in * 72),
        )
        for placements in self.args.pages:
            for placement in placements:
                group_idx = placement.group_idx
                rotation = placement.rotation
                dx = placement.dx
                dy = placement.dy
                seam_poly = self.args.seam_allowances[group_idx]
                group_poly_idxs = self.args.groups[group_idx]
                group_polys = [self.args.polygons[pi] for pi in group_poly_idxs]
                group_polys_final, seam_poly_final = transform_group_shapes(
                    group_polys, seam_poly, rotation, dx, dy
                )
                # Draw seam allowance with seam style
                self.fill_color = self.gray
                self.stroke_color = self.gray
                self.alpha = 1.0
                self.linewidth = 0
                self.draw_polygon(seam_poly_final)
                # Draw polygons and labels (transformed positions)
                self.fill_color = self.light
                self.stroke_color = black
                self.alpha = 1.0
                self.linewidth = 1
                for poly, poly_idx in zip(group_polys_final, group_poly_idxs):
                    self.draw_polygon(poly)
                    label_args = LabelDrawArgs(
                        poly_idx=poly_idx,
                        rotation=rotation,
                        dx=dx,
                        dy=dy,
                        seam_poly=seam_poly,
                    )
                    self.draw_label(label_args)
            self.canvas.showPage()
        self.canvas.save()


def pdf_writer(args: PDFWriterArgs) -> None:
    """Create PDF using PDFPolygonWriter class and PDFWriterArgs."""
    writer = PDFPolygonWriter(args)
    writer.write()
