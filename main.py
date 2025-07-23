from svg_parser import parse_svg
from geometry import lines_to_polygons
from grouping import group_polygons, save_overall_layout_png
from labeling import label_polygons
from seam_allowance import seam_allowance_polygons
from layout import layout_groups
from pdf_writer import pdf_writer
from utils import get_svg_units_per_inch

# ---- Parameters ----
SVG_FILE = "unit_tests/3groupA.svg"
PDF_FILE = "out/pieces.pdf"
PNG_FILE = "out/layout.png"
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11
SEAM_ALLOWANCE_IN = 0.25
SVG_UNITS_PER_IN = get_svg_units_per_inch(SVG_FILE)


def main():
    # Parse SVG to lines
    lines = parse_svg(SVG_FILE)

    # Geometry: lines to polygons
    polygons = lines_to_polygons(lines)

    # Grouping
    groups = group_polygons(polygons)

    # Labeling
    piece_labels, label_positions = label_polygons(polygons, groups)

    # Seam allowance polygons
    seam_allowances = seam_allowance_polygons(
        polygons,
        groups,
        allowance_in_inches=SEAM_ALLOWANCE_IN,
        svg_units_per_inch=SVG_UNITS_PER_IN,
    )

    # Layout
    pages = layout_groups(
        seam_allowances,
        PAGE_WIDTH_IN,
        PAGE_HEIGHT_IN,
        margin_in=0.25,
        svg_units_per_in=SVG_UNITS_PER_IN,
    )

    # Layout export
    save_overall_layout_png(
        polygons,
        piece_labels,
        label_positions,
        PNG_FILE,
        groups=groups,
    )

    # PDF export
    pdf_writer(
        PDF_FILE,
        pages,
        seam_allowances,
        polygons,
        groups,
        piece_labels,
        label_positions,
        page_width_in=PAGE_WIDTH_IN,
        page_height_in=PAGE_HEIGHT_IN,
        svg_units_per_in=SVG_UNITS_PER_IN,
    )


if __name__ == "__main__":
    main()
