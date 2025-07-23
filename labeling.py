from shapely.geometry import Polygon


def label_groups(groups, group_prefixes=None):
    """
    Assign group and piece labels.
    """
    if group_prefixes is None:
        # Default: 'A', 'B', ...
        group_prefixes = [chr(ord("A") + i) for i in range(len(groups))]
    piece_labels = {}
    for group_idx, group in enumerate(groups):
        prefix = group_prefixes[group_idx]
        for piece_order, poly_idx in enumerate(group, 1):
            piece_labels[poly_idx] = f"{prefix}{piece_order}"
    return piece_labels


def get_label_positions(polygons, indices=None):
    """
    Return {poly_idx: (x, y)} for label position (centroid).
    """
    if indices is None:
        indices = range(len(polygons))
    return {i: tuple(Polygon(polygons[i]).centroid.coords[0]) for i in indices}


def label_polygons(polygons, groups, group_prefixes=None):
    piece_labels = label_groups(groups, group_prefixes)
    label_positions = get_label_positions(polygons, piece_labels.keys())
    return piece_labels, label_positions
