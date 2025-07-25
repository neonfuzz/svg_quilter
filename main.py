#!/usr/bin/env python3

"""Main entry point for FPP SVG to PDF/PNG pattern pipeline.

Reads SVG, extracts geometry, groups pieces, labels, adds seam allowances,
lays out for pages, and outputs both PNG and PDF for printing.
"""

import argparse
import os

from svg_parser import parse_svg
from geometry import lines_to_polygons
from grouping import group_polygons
from labeling import label_polygons
from seam_allowance import seam_allowance_polygons
from layout import layout_groups
from pdf_writer import pdf_writer
from png_writer import save_overall_layout_png
from utils import get_svg_units_per_inch


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for main pipeline."""
    parser = argparse.ArgumentParser(
        description="FPP SVG to PDF/PNG pattern generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("svg_file", type=str, help="Input SVG file")
    parser.add_argument(
        "--pdf",
        dest="pdf_file",
        type=str,
        default="out/pieces.pdf",
        help="Output PDF file",
    )
    parser.add_argument(
        "--png",
        dest="png_file",
        type=str,
        default="out/layout.png",
        help="Output PNG layout file",
    )
    parser.add_argument(
        "--page-width",
        dest="page_width_in",
        type=float,
        default=8.5,
        help="PDF page width in inches",
    )
    parser.add_argument(
        "--page-height",
        dest="page_height_in",
        type=float,
        default=11.0,
        help="PDF page height in inches",
    )
    parser.add_argument(
        "--seam-allowance",
        dest="seam_allowance_in",
        type=float,
        default=0.25,
        help="Seam allowance in inches",
    )
    parser.add_argument(
        "--margin",
        dest="margin_in",
        type=float,
        default=0.5,
        help="Page margin in inches",
    )
    return parser.parse_args()


def main() -> None:
    """Run the full pipeline from SVG to PDF/PNG pattern."""
    args = parse_args()

    if not os.path.exists(args.svg_file):
        raise FileNotFoundError(f"SVG file not found: {args.svg_file}")
    pdf_dir = os.path.dirname(args.pdf_file)
    if pdf_dir:
        os.makedirs(pdf_dir, exist_ok=True)
    png_dir = os.path.dirname(args.pdf_file)
    if png_dir:
        os.makedirs(png_dir, exist_ok=True)

    svg_units_per_in = get_svg_units_per_inch(args.svg_file)

    # Parse SVG to lines
    lines = parse_svg(args.svg_file)

    # Geometry: lines to polygons
    polygons = lines_to_polygons(lines)

    # Grouping
    groups = group_polygons(polygons, lines)

    # Labeling
    piece_labels, label_positions = label_polygons(polygons, groups)

    # Seam allowance polygons
    seam_allowances = seam_allowance_polygons(
        polygons,
        groups,
        allowance_in_inches=args.seam_allowance_in,
        svg_units_per_inch=svg_units_per_in,
    )

    # Layout
    pages = layout_groups(
        seam_allowances,
        args.page_width_in,
        args.page_height_in,
        margin_in=args.margin_in,
        svg_units_per_in=svg_units_per_in,
    )

    # Layout export (PNG)
    save_overall_layout_png(
        polygons,
        piece_labels,
        label_positions,
        args.png_file,
        groups=groups,
    )

    # PDF export
    pdf_writer(
        args.pdf_file,
        pages,
        seam_allowances,
        polygons,
        groups,
        piece_labels,
        label_positions,
        page_width_in=args.page_width_in,
        page_height_in=args.page_height_in,
        svg_units_per_in=svg_units_per_in,
    )

    print("Done! Output written to:")
    print(f" - {args.pdf_file}")
    print(f" - {args.png_file}")


if __name__ == "__main__":
    main()
