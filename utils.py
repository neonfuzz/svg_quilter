import random

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


def get_svg_units_per_inch(svg_file):
    tree = ET.parse(svg_file)
    root = tree.getroot()
    width = root.attrib.get("width", "")
    if "in" in width:
        return 1.0
    if "mm" in width:
        return 25.4
    # Assume pixels; check for view_box
    view_box = root.attrib.get("view_box", "")
    if view_box:
        vb_w = float(view_box.split()[2])
        if abs(vb_w - 8.5) < 0.1:
            return 1.0
        if abs(vb_w - 215.9) < 0.5:  # 8.5in in mm
            return 25.4
    # Default: SVG standard is 96 px/in
    return 96.0


def remove_collinear_points(poly, tol=1e-2):
    """
    Remove all intermediate collinear points from a closed polygon ring.
    Handles closed rings (first=last), does NOT remove the first or last.
    Returns a list WITHOUT closure (first != last), so you can close as needed.
    """
    coords = list(poly)
    closed = len(coords) > 1 and coords[0] == coords[-1]
    # Remove closure for processing if present
    if closed:
        coords = coords[:-1]
    n = len(coords)
    if n <= 3:
        return coords  # Already minimal

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
        # Only skip 'curr' if it's *strictly* collinear and not the first point
        if not collinear(prev, curr, nxt):
            result.append(curr)
    if closed:
        result.append(result[0])
    return result


def plot_polygons(polygons, show_labels=True):
    plt.figure(figsize=(8, 8))
    for idx, poly in enumerate(polygons):
        xs, ys = zip(*poly)
        color = (random.random(), random.random(), random.random())
        plt.fill(xs, ys, alpha=0.5, color=color, edgecolor="k", linewidth=1)
        if show_labels:
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            plt.text(
                cx,
                cy,
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
    plt.gca().invert_yaxis()  # Flip y-axis to match SVG
    plt.show()


def plot_groups_with_seam_allowance(
    polygons, groups, seam_allowances, show_labels=True
):
    """
    polygons: list of polygons (list of (x,y))
    groups: list of groups (each is a list of polygon indices)
    seam_allowances: dict {group_idx: shapely Polygon} from seam_allowance_polygons()
    """
    plt.figure(figsize=(8, 8))
    random.seed(42)  # Consistent colors across runs
    colors = [(random.random(), random.random(), random.random()) for _ in groups]
    # Draw seam allowance polygons first (so they don't cover the interiors)
    for group_idx, group in enumerate(groups):
        seam_poly = seam_allowances[group_idx]
        xs, ys = seam_poly.exterior.xy
        plt.fill(xs, ys, color=colors[group_idx], alpha=0.3, zorder=1)
        plt.plot(xs, ys, color=colors[group_idx], linewidth=2, zorder=2)
    # Draw original group interiors
    for group_idx, group in enumerate(groups):
        for poly_idx in group:
            xs, ys = zip(*polygons[poly_idx])
            plt.fill(
                xs, ys, color=colors[group_idx], alpha=0.7, edgecolor="k", zorder=3
            )
    # Add group labels at centroid of seam allowance
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
                bbox=dict(facecolor="white", alpha=0.6, boxstyle="round,pad=0.3"),
                zorder=4,
            )
    plt.axis("equal")
    plt.axis("off")
    plt.title("Groups with Seam Allowances")
    plt.gca().invert_yaxis()
    plt.show()
