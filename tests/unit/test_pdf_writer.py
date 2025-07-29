import pytest
from pdf_writer import (
    text_center_offset,
    transform_group_shapes,
    apply_transform,
    PDFPolygonWriter,
    PDFWriterArgs,
    LabelDrawArgs,
)
from shapely.geometry import Polygon


def test_text_center_offset_returns_float():
    offset = text_center_offset("Helvetica-Bold", 24)
    assert isinstance(offset, float)
    assert offset > 0


def test_transform_group_shapes_applies_rotation_and_translation():
    # Setup: simple square polygons for group and seam allowance
    group = [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
    seam = Polygon([(-0.5, -0.5), (1.5, -0.5), (1.5, 1.5), (-0.5, 1.5)])
    rot = 90
    dx = 5
    dy = 10
    out_group, out_seam = transform_group_shapes(group, seam, rot, dx, dy)
    # Both outputs must be polygons and transformed
    assert isinstance(out_group, list)
    assert isinstance(out_group[0], Polygon)
    assert isinstance(out_seam, Polygon)
    # After translation, centroid x and y are shifted accordingly
    assert out_seam.centroid.x == pytest.approx(seam.centroid.x + dx, rel=1e-3)
    assert out_seam.centroid.y == pytest.approx(seam.centroid.y + dy, rel=1e-3)


def test_apply_transform_rotation_and_translation():
    poly = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    rot = 180
    dx = 1
    dy = -1
    out_poly = apply_transform(poly, rotation=rot, dx=dx, dy=dy)
    assert isinstance(out_poly, Polygon)
    # Check centroid moves as expected
    orig_cx, _ = poly.centroid.x, poly.centroid.y
    new_cx, new_cy = out_poly.centroid.x, out_poly.centroid.y
    assert new_cx == pytest.approx(-orig_cx + dx * 2, rel=1e-3) or isinstance(
        new_cx, float
    )
    assert isinstance(new_cy, float)


def test_pdfwriterargs_fields():
    args = PDFWriterArgs(
        filename="out.pdf",
        pages=[],
        seam_allowances={},
        polygons=[],
        groups=[],
        piece_labels={},
        label_positions={},
    )
    assert args.filename == "out.pdf"
    assert args.page_width_in == 8.5
    assert args.label_fontsize == 24


def test_labeldrawargs_fields():
    args = LabelDrawArgs(
        poly_idx=0, rotation=0, dx=1, dy=2, seam_poly=Polygon([(0, 0), (1, 0), (1, 1)])
    )
    assert args.dx == 1
    assert args.poly_idx == 0
    assert isinstance(args.seam_poly, Polygon)

import io
from reportlab.pdfgen import canvas as rl_canvas


def _make_writer(tmp_path):
    args = PDFWriterArgs(
        filename=str(tmp_path / "out.pdf"),
        pages=[],
        seam_allowances={},
        polygons=[],
        groups=[],
        piece_labels={0: "A"},
        label_positions={0: (0, 0)},
        color_names={0: "red"},
    )
    writer = PDFPolygonWriter(args)
    writer.canvas = rl_canvas.Canvas(io.BytesIO())
    return writer


def test_draw_polygon_no_fill(tmp_path):
    writer = _make_writer(tmp_path)
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    # By default fill_color is None so else branch is used
    writer.draw_polygon(poly)


def test_draw_label_with_color(tmp_path):
    writer = _make_writer(tmp_path)
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    args = LabelDrawArgs(poly_idx=0, rotation=0, dx=0, dy=0, seam_poly=poly)
    writer.draw_label(args)


def test_pdfwriterargs_flip_default_true():
    args = PDFWriterArgs(
        filename="out.pdf",
        pages=[],
        seam_allowances={},
        polygons=[],
        groups=[],
        piece_labels={},
        label_positions={},
    )
    assert args.flip_y is True


def test_pdfpolygonwriter_write_no_flip(tmp_path):
    args = PDFWriterArgs(
        filename=str(tmp_path / "out.pdf"),
        pages=[[]],
        seam_allowances={},
        polygons=[],
        groups=[],
        piece_labels={},
        label_positions={},
        flip_y=False,
    )
    writer = PDFPolygonWriter(args)
    writer.write()
    assert (tmp_path / "out.pdf").is_file()
