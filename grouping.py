import random

import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString, Polygon

from utils import remove_collinear_points


def get_distinct_colors(n, pastel=True):
    """Generate n visually distinct colors."""
    import colorsys

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
    polygons,
    piece_labels,
    label_positions,
    out_png="overall_layout.png",
    dpi=300,
    groups=None,
    figsize=(8, 10),
):
    """
    Renders a PNG with all polygons and labels in original SVG positions.
    Each group will have a unique, visually distinct color.
    """
    plt.figure(figsize=figsize, dpi=dpi)
    ax = plt.gca()

    n_polys = len(polygons)
    poly_colors = {}

    if groups is not None:
        group_count = len(groups)
        group_colors = get_distinct_colors(group_count, pastel=True)
        for gi, group in enumerate(groups):
            for pi in group:
                poly_colors[pi] = group_colors[gi]
    else:
        # All polygons: same color
        poly_colors = {i: (0.7, 0.7, 0.95) for i in range(n_polys)}

    # Draw all polygons (filled, black outline)
    for idx, poly_pts in enumerate(polygons):
        poly = Polygon(poly_pts)
        color = poly_colors.get(idx, (0.7, 0.7, 0.95))
        xs, ys = poly.exterior.xy
        ax.fill(xs, ys, color=color, alpha=0.85, linewidth=1, edgecolor="k", zorder=2)

    # Draw labels at provided positions
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
            bbox=dict(facecolor="white", alpha=0.7, boxstyle="round,pad=0.2"),
            zorder=3,
        )

    plt.axis("equal")
    plt.axis("off")
    plt.title("FPP Pattern: All Pieces & Labels")
    plt.tight_layout()
    plt.gca().invert_yaxis()
    plt.savefig(out_png, bbox_inches="tight", pad_inches=0.1, dpi=dpi)
    plt.close()
    print(f"Saved overall layout PNG to {out_png}")


def plot_groups(polygons, groups):
    plt.figure(figsize=(8, 8))
    color_choices = []
    for _ in range(len(groups)):
        color_choices.append((random.random(), random.random(), random.random()))
    for group_idx, group in enumerate(groups):
        color = color_choices[group_idx]
        for poly_idx in group:
            poly = polygons[poly_idx]
            xs, ys = zip(*poly)
            plt.fill(xs, ys, alpha=0.5, color=color)
            # Label the polygon with its index in the group
            centroid_x = sum(xs) / len(xs)
            centroid_y = sum(ys) / len(ys)
            plt.text(
                centroid_x,
                centroid_y,
                f"{group_idx+1}.{group.index(poly_idx)+1}",
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
            )
    plt.axis("equal")
    plt.axis("off")
    plt.title("FPP Groups (Each color = one group)")
    plt.gca().invert_yaxis()  # Flip y-axis to match SVG
    plt.show()


def polygon_area(poly):
    return abs(Polygon(poly).area)


def polygons_are_adjacent(p1, p2):
    return Polygon(p1).intersects(Polygon(p2))


def build_polygon_adjacency(polygons, tol=1e-2):
    n = len(polygons)
    adjacency = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if polygons_are_adjacent(polygons[i], polygons[j]):
                adjacency[i].add(j)
                adjacency[j].add(i)
    return adjacency


def edges_from_coords(coords):
    # Returns a set of all edges (as sorted tuples) for a closed ring
    n = len(coords)
    return {
        tuple(sorted((tuple(coords[i]), tuple(coords[(i + 1) % n]))))
        for i in range(n - 1)  # -1 because shapely closes polygons
    }


def find_exact_full_shared_edge(neighbor_poly, group_boundary, tol=1e-2):
    """
    Returns True if the neighbor_poly and group boundary have an identical edge (by endpoints).
    """

    # For both, build edge sets using sorted, rounded endpoints.
    def rounded(pt):
        round_factor = int(-np.log10(tol))
        return (round(pt[0], round_factor), round(pt[1], round_factor))

    # Get all edges as sets of sorted endpoint pairs (order-insensitive)
    neighbor_edges = set()
    n = len(neighbor_poly)
    for i in range(n):
        a = rounded(neighbor_poly[i])
        b = rounded(neighbor_poly[(i + 1) % n])
        neighbor_edges.add(tuple(sorted((a, b))))
    group_edges = set()
    gb = group_boundary
    m = len(gb)
    for i in range(m):
        a = rounded(gb[i])
        b = rounded(gb[(i + 1) % m])
        group_edges.add(tuple(sorted((a, b))))
    # Return True if there is any *identical* edge in both sets
    shared = neighbor_edges & group_edges
    return len(shared) == 1  # Must be *exactly one* matching edge to add FPP-style


def grow_group_from_seed(seed_idx, polygons, adjacency, already_grouped, tol=1e-2):
    group_idxs = [seed_idx]
    current_shape = Polygon(polygons[seed_idx])
    grouped = set([seed_idx]) | already_grouped

    while True:
        candidates = []
        for idx in group_idxs:
            for neighbor in adjacency[idx]:
                if neighbor not in grouped and neighbor not in candidates:
                    candidates.append(neighbor)
        found = False
        for neighbor in candidates:
            neighbor_poly = polygons[neighbor]
            match = find_exact_full_shared_edge(
                neighbor_poly, list(current_shape.exterior.coords), tol
            )
            if match:
                # Only add if the shared edge is exact
                neighbor_shape = Polygon(neighbor_poly)
                current_shape = current_shape.union(neighbor_shape)
                current_shape = Polygon(
                    remove_collinear_points(list(current_shape.exterior.coords))
                )
                group_idxs.append(neighbor)
                grouped.add(neighbor)
                found = True
                break  # Only one per iteration
        if not found:
            break
    return group_idxs  # Ordered


def group_polygons(polygons):
    """
    Main grouping function: returns list of groups,
    each a list of polygon indices (ordered by addition).
    """
    adjacency = build_polygon_adjacency(polygons)
    already_grouped = set()
    groups = []
    n = len(polygons)

    while len(already_grouped) < n:
        # Find the smallest ungrouped polygon
        candidates = [i for i in range(n) if i not in already_grouped]
        seed = min(candidates, key=lambda idx: polygon_area(polygons[idx]))
        group = grow_group_from_seed(seed, polygons, adjacency, already_grouped)
        groups.append(list(group))
        already_grouped.update(group)
    return groups


# Example usage (needs polygons from geometry.py):
if __name__ == "__main__":
    import sys
    from geometry import lines_to_polygons
    from svg_parser import parse_svg

    lines = parse_svg(sys.argv[1])
    polygons = lines_to_polygons(lines)
    groups = group_polygons(polygons)
    for i, group in enumerate(groups):
        print(f"Group {i+1}: polygons {group}")
    plot_groups(polygons, groups)
