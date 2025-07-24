"""Assign labels and label positions for FPP polygon groups.

Provide utilities to label polygons by group and piece number,
and to extract label positions (using centroids).
"""

from typing import List, Dict, Tuple, Optional
from shapely.geometry import Polygon


def int_to_label(n: int) -> str:
    """Convert an integer to a label using the A1 notation.

    Args:
        n: The integer to convert.

    Returns:
        A string representing the label.
    """
    label = ""
    while n >= 0:
        label = chr(n % 26 + 65) + label
        n = n // 26 - 1
    return label


def label_groups(
    groups: List[List[int]], group_prefixes: Optional[List[str]] = None
) -> Dict[int, str]:
    """Assign group and piece labels to polygon indices.

    Args:
        groups: List of groups, each a list of polygon indices.
        group_prefixes: Optional list of prefixes for each group.

    Returns:
        Dict mapping polygon index to label (e.g., 'A1', 'A2', ...).
    """
    if group_prefixes is None:
        group_prefixes = [int_to_label(i) for i in range(len(groups))]
    piece_labels = {}
    for group_idx, group in enumerate(groups):
        prefix = group_prefixes[group_idx]
        for piece_order, poly_idx in enumerate(group, 1):
            piece_labels[poly_idx] = f"{prefix}{piece_order}"
    return piece_labels


def get_label_positions(
    polygons: List[Polygon], indices: Optional[List[int]] = None
) -> Dict[int, Tuple[float, float]]:
    """Return label positions as {poly_idx: (x, y)} using centroids.

    Args:
        polygons: List of Shapely Polygon objects.
        indices: Optional list of polygon indices to label.

    Returns:
        Dict mapping polygon index to centroid coordinates (x, y).
    """
    if indices is None:
        indices = list(range(len(polygons)))
    return {i: polygons[i].centroid.coords[0] for i in indices}


def label_polygons(
    polygons: List[Polygon],
    groups: List[List[int]],
    group_prefixes: Optional[List[str]] = None,
) -> Tuple[Dict[int, str], Dict[int, Tuple[float, float]]]:
    """Assign labels and label positions for polygons in groups.

    Args:
        polygons: List of Shapely Polygon objects.
        groups: List of groups, each a list of polygon indices.
        group_prefixes: Optional list of prefixes for each group.

    Returns:
        piece_labels: Dict of polygon index to label.
        label_positions: Dict of polygon index to centroid (x, y).
    """
    piece_labels = label_groups(groups, group_prefixes)
    label_positions = get_label_positions(polygons, list(piece_labels.keys()))
    return piece_labels, label_positions
