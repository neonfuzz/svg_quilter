"""General utilities for coloring, plotting, SVG parsing, and polygon cleanup."""

from typing import List, Dict, Tuple, Optional

import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from utils import get_distinct_colors


def save_overall_layout_png(
    polygons: List[Polygon],
    piece_labels: Dict[int, str],
    label_positions: Dict[int, Tuple[float, float]],
    out_png: str = "overall_layout.png",
    dpi: int = 300,
    groups: Optional[List[List[int]]] = None,
    figsize: Tuple[int, int] = (8, 10),
    polygon_colors: Optional[Dict[int, Tuple[int, int, int]]] = None,
) -> None:
    """Render and save a PNG with all polygons and labels at SVG positions.

    Args:
        polygons: List of Shapely Polygon objects.
        piece_labels: Dict mapping polygon index to label.
        label_positions: Dict mapping polygon index to (x, y) label position.
        out_png: Output PNG filename.
        dpi: Dots per inch for the saved PNG.
        groups: List of groups, each a list of polygon indices.
        figsize: Figure size (width, height) in inches.
    """
    plt.figure(figsize=figsize, dpi=dpi)
    ax = plt.gca()
    n_polys = len(polygons)
    poly_colors: Dict[int, Tuple[float, float, float]] = {}

    if polygon_colors is not None:
        for idx, rgb in polygon_colors.items():
            poly_colors[idx] = tuple(channel / 255 for channel in rgb)
    elif groups is not None:
        group_count = len(groups)
        group_colors = get_distinct_colors(group_count, pastel=True)
        for gi, group in enumerate(groups):
            for pi in group:
                poly_colors[pi] = group_colors[gi]
    else:
        poly_colors = {i: (0.7, 0.7, 0.95) for i in range(n_polys)}

    for idx, poly in enumerate(polygons):
        color = poly_colors.get(idx, (0.7, 0.7, 0.95))
        xs, ys = poly.exterior.xy
        ax.fill(xs, ys, color=color, alpha=0.85, linewidth=1, edgecolor="k", zorder=2)

    max_area = max((poly.area for poly in polygons), default=1.0)
    for idx, label in piece_labels.items():
        x, y = label_positions[idx]
        poly = polygons[idx]
        area_ratio = poly.area / max_area if max_area else 1.0
        fontsize = max(5, 15 * area_ratio**0.5)
        plt.text(
            x,
            y,
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
    plt.title("FPP Pattern: All Pieces & Labels (Right side)")
    plt.tight_layout()
    plt.gca().invert_yaxis()
    plt.savefig(out_png, bbox_inches="tight", pad_inches=0.1, dpi=dpi)
    plt.close()
