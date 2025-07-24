"""General utilities for coloring, plotting, SVG parsing, and polygon cleanup."""

import re
from typing import List, Dict, Tuple, Optional
import random
import colorsys
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
from shapely.geometry import Polygon

UNIT_TO_INCH = {
    "in": 1.0,
    "mm": 1.0 / 25.4,
    "cm": 1.0 / 2.54,
    "pt": 1.0 / 72.0,
    "pc": 1.0 / 6.0,
    "px": 1.0 / 96.0,
}


def get_distinct_colors(
    n: int, pastel: bool = True
) -> List[Tuple[float, float, float]]:
    """Generate n visually distinct RGB colors.

    Args:
        n: Number of colors to generate.
        pastel: If True, use pastel palette.

    Returns:
        List of RGB tuples (r, g, b), values in [0, 1].
    """
    hues = [i / n for i in range(n)]
    random.shuffle(hues)
    colors = []
    for h in hues:
        s = 0.5 if pastel else 0.85
        v = 0.85 if pastel else 0.9
        rgb = colorsys.hsv_to_rgb(h, s, v)
        colors.append(rgb)
    return colors


def save_overall_layout_png(
    polygons: List[Polygon],
    piece_labels: Dict[int, str],
    label_positions: Dict[int, Tuple[float, float]],
    out_png: str = "overall_layout.png",
    dpi: int = 300,
    groups: Optional[List[List[int]]] = None,
    figsize: Tuple[int, int] = (8, 10),
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

    if groups is not None:
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

    for idx, label in piece_labels.items():
        x, y = label_positions[idx]
        plt.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=16,
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


def plot_groups(polygons: List[Polygon], groups: List[List[int]]) -> None:
    """Plot groups of polygons, colored by group.

    Args:
        polygons: List of Shapely Polygon objects.
        groups: List of groups, each a list of polygon indices.
    """
    plt.figure(figsize=(8, 8))
    color_choices = [
        (random.random(), random.random(), random.random()) for _ in range(len(groups))
    ]
    for group_idx, group in enumerate(groups):
        color = color_choices[group_idx]
        for poly_idx in group:
            poly = polygons[poly_idx]
            xs, ys = poly.exterior.xy
            plt.fill(xs, ys, alpha=0.5, color=color)
            centroid = poly.centroid
            plt.text(
                centroid.x,
                centroid.y,
                f"{group_idx+1}.{group.index(poly_idx)+1}",
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
            )
    plt.axis("equal")
    plt.axis("off")
    plt.title("FPP Groups (Each color = one group)")
    plt.gca().invert_yaxis()
    plt.show()


def parse_length(length_str: str) -> float:
    """Parse a length string and return the value in inches.

    Args:
        length_str: A string representing a length, e.g., "10cm" or "5in".

    Returns:
        The length converted to inches as a float.
    """
    match = re.fullmatch(r"([\d.]+)([a-z%]*)", length_str.strip())
    if not match:
        raise ValueError(f"Invalid length: {length_str}")
    value, unit = match.groups()
    unit = unit or "px"
    if unit not in UNIT_TO_INCH:
        raise ValueError(f"Unsupported unit: {unit}")
    return float(value) * UNIT_TO_INCH[unit]


def get_svg_units_per_inch(svg_path: str) -> Optional[float]:
    """Get the number of SVG units per inch from an SVG file.

    Args:
        svg_path: The path to the SVG file.

    Returns:
        The number of SVG units per inch as a float, or None if not found.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    width_str = root.get("width")
    viewbox_str = root.get("viewBox")

    if not width_str or not viewbox_str:
        raise ValueError("SVG must have 'width' and 'viewBox' attributes")

    width_in_inches = parse_length(width_str)
    viewbox_values = viewbox_str.strip().split()
    if len(viewbox_values) != 4:
        raise ValueError("Invalid viewBox format")

    viewbox_width = float(viewbox_values[2])

    return viewbox_width / width_in_inches


def remove_collinear_points(poly: Polygon, tol: float = 1e-2) -> Polygon:
    """Remove all intermediate collinear points from a closed polygon ring.

    Args:
        poly: Shapely Polygon object.
        tol: Area tolerance for collinearity.

    Returns:
        Polygon with collinear points removed.
    """
    coords = list(poly.exterior.coords)
    closed = len(coords) > 1 and coords[0] == coords[-1]
    if closed:
        coords = coords[:-1]
    n = len(coords)
    if n <= 3:
        return Polygon(coords)

    def collinear(a, b, c):
        ax, ay = a
        bx, by = b
        cx, cy = c
        area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        return abs(area) < tol

    result = []
    for i in range(n):
        prev = coords[i - 1]
        curr = coords[i]
        nxt = coords[(i + 1) % n]
        if not collinear(prev, curr, nxt):
            result.append(curr)
    if closed:
        result.append(result[0])
    return Polygon(result)


def plot_polygons(polygons: List[Polygon], show_labels: bool = True) -> None:
    """Plot polygons with optional labels at centroid.

    Args:
        polygons: List of Shapely Polygon objects.
        show_labels: Whether to label polygons by index.
    """
    plt.figure(figsize=(8, 8))
    for idx, poly in enumerate(polygons):
        xs, ys = poly.exterior.xy
        color = (random.random(), random.random(), random.random())
        plt.fill(xs, ys, alpha=0.5, color=color, edgecolor="k", linewidth=1)
        if show_labels:
            c = poly.centroid
            plt.text(
                c.x,
                c.y,
                str(idx),
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                color="k",
            )
    plt.axis("equal")
    plt.axis("off")
    plt.title("Detected Polygons")
    plt.gca().invert_yaxis()
    plt.show()


def plot_groups_with_seam_allowance(
    polygons: List[Polygon],
    groups: List[List[int]],
    seam_allowances: Dict[int, Polygon],
    show_labels: bool = True,
) -> None:
    """Plot polygons grouped and overlaid with seam allowance shapes.

    Args:
        polygons: List of Shapely Polygon objects.
        groups: List of groups (each is a list of polygon indices).
        seam_allowances: Dict {group_idx: Polygon} of seam allowance polygons.
        show_labels: Whether to label groups.
    """
    plt.figure(figsize=(8, 8))
    random.seed(42)
    colors = [(random.random(), random.random(), random.random()) for _ in groups]
    for group_idx, group in enumerate(groups):
        seam_poly = seam_allowances[group_idx]
        xs, ys = seam_poly.exterior.xy
        plt.fill(xs, ys, color=colors[group_idx], alpha=0.3, zorder=1)
        plt.plot(xs, ys, color=colors[group_idx], linewidth=2, zorder=2)
    for group_idx, group in enumerate(groups):
        for poly_idx in group:
            poly = polygons[poly_idx]
            xs, ys = poly.exterior.xy
            plt.fill(
                xs, ys, color=colors[group_idx], alpha=0.7, edgecolor="k", zorder=3
            )
    if show_labels:
        for group_idx, seam_poly in seam_allowances.items():
            c = seam_poly.centroid
            plt.text(
                c.x,
                c.y,
                f"Group {group_idx+1}",
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                bbox={"facecolor": "white", "alpha": 0.6, "boxstyle": "round,pad=0.3"},
                zorder=4,
            )
    plt.axis("equal")
    plt.axis("off")
    plt.title("Groups with Seam Allowances")
    plt.gca().invert_yaxis()
    plt.show()
