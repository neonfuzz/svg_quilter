#!/usr/bin/env python3

"""Main entry point for FPP SVG to PDF/PNG pattern pipeline.

Reads SVG, extracts geometry, groups pieces, labels, adds seam allowances,
lays out for pages, and outputs both PNG and PDF for printing.
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# pylint: disable=import-outside-toplevel
# For CLI tool speed, it makes the most sense to use local imports.

DEFAULT_PDF: str = "out/pieces.pdf"
DEFAULT_PNG: str = "out/layout.png"
DEFAULT_PAGE_WIDTH_IN: float = 8.5
DEFAULT_PAGE_HEIGHT_IN: float = 11.0
DEFAULT_SEAM_ALLOWANCE_IN: float = 0.25
DEFAULT_MARGIN_IN: float = 0.5


@dataclass
class PipelineConfig:
    """Configuration for the pipeline."""

    page_width_in: float
    page_height_in: float
    seam_allowance_in: float
    margin_in: float
    pdf_file: str
    png_file: str


@dataclass
class PipelineState:
    """State of the pipeline during execution."""

    svg_file: str
    lines: Any = None
    polygons: Any = None
    svg_units_per_in: Optional[float] = None
    svg_tree: Any = None
    polygon_colors: Any = None
    color_names: Any = None
    groups: Any = None
    piece_labels: Any = None
    label_positions: Any = None
    seam_allowances: Any = None
    pages: Any = None


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
        default=DEFAULT_PDF,
        help="Output PDF file",
    )
    parser.add_argument(
        "--png",
        dest="png_file",
        type=str,
        default=DEFAULT_PNG,
        help="Output PNG layout file",
    )
    parser.add_argument(
        "--page-width",
        dest="page_width_in",
        type=float,
        default=DEFAULT_PAGE_WIDTH_IN,
        help="PDF page width in inches",
    )
    parser.add_argument(
        "--page-height",
        dest="page_height_in",
        type=float,
        default=DEFAULT_PAGE_HEIGHT_IN,
        help="PDF page height in inches",
    )
    parser.add_argument(
        "--seam-allowance",
        dest="seam_allowance_in",
        type=float,
        default=DEFAULT_SEAM_ALLOWANCE_IN,
        help="Seam allowance in inches",
    )
    parser.add_argument(
        "--margin",
        dest="margin_in",
        type=float,
        default=DEFAULT_MARGIN_IN,
        help="Page margin in inches",
    )
    return parser.parse_args()


def ensure_output_dirs(config: PipelineConfig) -> None:
    """Ensure that output directories for PDF and PNG files exist."""
    for output_path in [config.pdf_file, config.png_file]:
        output_dir = Path(output_path).parent
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)


def parse_svg_and_geometry(state: PipelineState) -> PipelineState:
    """Parse SVG file and extract geometric structures."""
    import xml.etree.ElementTree as ET

    from geometry import lines_to_polygons
    from svg_parser import parse_svg
    from utils import get_svg_units_per_inch

    state.svg_units_per_in = get_svg_units_per_inch(state.svg_file)
    state.svg_tree = ET.parse(state.svg_file)
    state.lines = parse_svg(state.svg_file)
    state.polygons = lines_to_polygons(state.lines)
    return state


def get_polygon_colors(state: PipelineState) -> PipelineState:
    """Assign colors to polygons, handling missing color mapping."""
    from colors import polygon_color_map

    try:
        state.polygon_colors, state.color_names = polygon_color_map(
            state.polygons, state.svg_tree
        )
    except ValueError:
        state.polygon_colors, state.color_names = None, None
    return state


def group_polygons_step(state: PipelineState) -> PipelineState:
    """Group polygons based on geometry."""
    from grouping import group_polygons

    state.groups = group_polygons(state.polygons, state.lines)
    return state


def label_polygons_step(state: PipelineState) -> PipelineState:
    """Label each polygon for identification and placement."""
    from labeling import label_polygons

    state.piece_labels, state.label_positions = label_polygons(
        state.polygons, state.groups
    )
    return state


def compute_seam_allowances(
    state: PipelineState, config: PipelineConfig
) -> PipelineState:
    """Generate seam allowance polygons."""
    from seam_allowance import seam_allowance_polygons

    if state.svg_units_per_in is None:
        raise ValueError("SVG units per inch not set.")

    state.seam_allowances = seam_allowance_polygons(
        state.polygons,
        state.groups,
        allowance_in_inches=config.seam_allowance_in,
        svg_units_per_inch=state.svg_units_per_in,
    )
    return state


def compute_layout(state: PipelineState, config: PipelineConfig) -> PipelineState:
    """Compute page layouts for seam allowance polygons."""
    from layout import LayoutConfig, layout_groups

    if state.svg_units_per_in is None:
        raise ValueError("SVG units per inch not set.")

    layout_config = LayoutConfig(
        page_width_in=config.page_width_in,
        page_height_in=config.page_height_in,
        margin_in=config.margin_in,
        svg_units_per_in=state.svg_units_per_in,
    )
    state.pages = layout_groups(state.seam_allowances, layout_config)
    return state


def export_png(state: PipelineState, config: PipelineConfig) -> None:
    """Export the pattern layout as a PNG image."""
    from png_writer import (
        LayoutOutputConfig,
        PolygonLayoutConfig,
        save_overall_layout_png,
    )

    poly_layout_config = PolygonLayoutConfig(
        state.polygons,
        state.piece_labels,
        state.label_positions,
        groups=state.groups,
        polygon_colors=state.polygon_colors,
    )
    save_overall_layout_png(poly_layout_config, LayoutOutputConfig(config.png_file))


def export_pdf(state: PipelineState, config: PipelineConfig) -> None:
    """Export the pattern layout as a PDF file."""
    from pdf_writer import PDFWriterArgs, pdf_writer

    if state.svg_units_per_in is None:
        raise ValueError("SVG units per inch not set.")

    pdf_writer_args = PDFWriterArgs(
        config.pdf_file,
        state.pages,
        state.seam_allowances,
        state.polygons,
        state.groups,
        state.piece_labels,
        state.label_positions,
        color_names=state.color_names,
        page_width_in=config.page_width_in,
        page_height_in=config.page_height_in,
        svg_units_per_in=state.svg_units_per_in,
    )
    pdf_writer(pdf_writer_args)


def print_results(config: PipelineConfig) -> None:
    """Print the results of output file generation."""
    print("Done! Output written to:")
    print(f" - {config.pdf_file}")
    print(f" - {config.png_file}")


def run_pipeline(args: argparse.Namespace) -> None:
    """Run the full pipeline from SVG to PDF/PNG pattern."""
    svg_path: Path = Path(args.svg_file)
    if not svg_path.is_file():
        print(f"Error: SVG file not found: {svg_path}", file=sys.stderr)
        sys.exit(1)

    config = PipelineConfig(
        page_width_in=args.page_width_in,
        page_height_in=args.page_height_in,
        seam_allowance_in=args.seam_allowance_in,
        margin_in=args.margin_in,
        pdf_file=args.pdf_file,
        png_file=args.png_file,
    )
    ensure_output_dirs(config)
    state = PipelineState(svg_file=args.svg_file)

    state = parse_svg_and_geometry(state)
    state = get_polygon_colors(state)
    state = group_polygons_step(state)
    state = label_polygons_step(state)
    state = compute_seam_allowances(state, config)
    state = compute_layout(state, config)
    export_png(state, config)
    export_pdf(state, config)
    print_results(config)


def main() -> None:
    """Main program entry point."""
    args = parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
