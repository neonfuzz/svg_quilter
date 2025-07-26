"""General utilities for coloring, plotting, SVG parsing, and polygon cleanup."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from utils import get_distinct_colors

matplotlib.use("Agg")


@dataclass
class PolygonLayoutConfig:
    """Configuration for arranging polygons in a layout."""

    polygons: List[Polygon]
    piece_labels: Dict[int, str]
    label_positions: Dict[int, Tuple[float, float]]
    groups: Optional[List[List[int]]] = None
    polygon_colors: Optional[Dict[int, Tuple[int, int, int]]] = None
    figsize: Tuple[int, int] = (8, 10)


@dataclass
class LayoutOutputConfig:
    """Configuration for saving the layout output."""

    out_png: str = "overall_layout.png"
    dpi: int = 300
    title: str = "FPP Pattern: All Pieces & Labels (Right side)"


class PolygonLayoutPlotter:
    """Class for rendering and saving polygon layouts with labels."""

    def __init__(self, layout_cfg: PolygonLayoutConfig):
        """Initialize the PolygonLayoutPlotter class.

        Args:
            layout_cfg: PolygonLayoutConfig instance with polygons, labels, etc.
        """
        self.layout_cfg = layout_cfg

    def get_polygon_colors(self) -> Dict[int, Tuple[float, ...]]:
        """Compute the color mapping for polygons."""
        n_polys = len(self.layout_cfg.polygons)
        poly_colors: Dict[int, Tuple[float, ...]] = {}

        if self.layout_cfg.polygon_colors is not None:
            for idx, rgb in self.layout_cfg.polygon_colors.items():
                poly_colors[idx] = tuple(channel / 255 for channel in rgb)
        elif self.layout_cfg.groups is not None:
            group_count = len(self.layout_cfg.groups)
            group_colors = get_distinct_colors(group_count, pastel=True)
            for gi, group in enumerate(self.layout_cfg.groups):
                for pi in group:
                    poly_colors[pi] = group_colors[gi]
        else:
            poly_colors = {i: (0.7, 0.7, 0.95) for i in range(n_polys)}

        return poly_colors

    def save_png(self, output_cfg: LayoutOutputConfig) -> None:
        """Render and save a PNG with all polygons and labels.

        Args:
            output_cfg: LayoutOutputConfig with output filename, dpi, and title.
        """
        plt.figure(figsize=self.layout_cfg.figsize, dpi=output_cfg.dpi)
        ax = plt.gca()
        poly_colors = self.get_polygon_colors()

        for idx, poly in enumerate(self.layout_cfg.polygons):
            color = poly_colors.get(idx, (0.7, 0.7, 0.95))
            xs, ys = poly.exterior.xy
            ax.fill(
                xs, ys, color=color, alpha=0.85, linewidth=1, edgecolor="k", zorder=2
            )

        max_area = max((poly.area for poly in self.layout_cfg.polygons), default=1.0)
        for idx, label in self.layout_cfg.piece_labels.items():
            poly = self.layout_cfg.polygons[idx]
            area_ratio = poly.area / max_area if max_area else 1.0
            fontsize = max(5, 15 * area_ratio**0.5)
            plt.text(
                self.layout_cfg.label_positions[idx][0],
                self.layout_cfg.label_positions[idx][1],
                label,
                ha="center",
                va="center",
                fontsize=fontsize,
                fontweight="bold",
                bbox={"facecolor": "white", "alpha": 0.7, "boxstyle": "round,pad=0.2"},
                zorder=3,
            )

        plt.axis("equal")
        plt.axis("off")
        plt.title(output_cfg.title)
        plt.tight_layout()
        plt.gca().invert_yaxis()
        plt.savefig(
            output_cfg.out_png, bbox_inches="tight", pad_inches=0.1, dpi=output_cfg.dpi
        )
        plt.close()


def save_overall_layout_png(
    layout_cfg: PolygonLayoutConfig,
    output_cfg: Optional[LayoutOutputConfig] = None,
) -> None:
    """Render and save a PNG with all polygons and labels at SVG positions.

    Args:
        layout_cfg: Configuration for the polygons, labels, and layout.
        output_cfg: Configuration for the output file and rendering options.
    """
    if output_cfg is None:
        output_cfg = LayoutOutputConfig()
    plotter = PolygonLayoutPlotter(layout_cfg)
    plotter.save_png(output_cfg)
