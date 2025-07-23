"""Generate seam allowance shapes for grouped FPP polygons.

Buffer the union of grouped polygons to create seam allowance regions.
"""

from typing import List, Dict, Union
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

from utils import remove_collinear_points


def group_polygons_to_shape(
    polygons: List[Polygon], group: List[int]
) -> Union[Polygon, MultiPolygon]:
    """Return unioned Shapely Polygon or MultiPolygon for group indices.

    Args:
        polygons: List of Shapely Polygon objects.
        group: List of polygon indices to union.

    Returns:
        Unioned shape as Polygon or MultiPolygon.
    """
    group_shapes = [polygons[idx] for idx in group]
    return unary_union(group_shapes)


def clean_and_buffer_group_shape(
    group_shape: Union[Polygon, MultiPolygon],
    allowance: float,
) -> Union[Polygon, MultiPolygon]:
    """Convex hull, then buffer group shape for seam allowance.

    Args:
        group_shape: The unioned Polygon or MultiPolygon for the group.
        allowance: Buffer distance (SVG units).

    Returns:
        Buffered shape as Polygon or MultiPolygon.
    """
    simple = remove_collinear_points(group_shape.convex_hull)
    buffered = simple.buffer(allowance, join_style=2)  # Flat corners
    return buffered


def seam_allowance_polygons(
    polygons: List[Polygon],
    groups: List[List[int]],
    allowance_in_inches: float = 0.25,
    svg_units_per_inch: float = 96,
) -> Dict[int, Union[Polygon, MultiPolygon]]:
    """Compute seam allowance shapes for each group.

    Args:
        polygons: List of Shapely Polygon objects.
        groups: List of groups, each a list of polygon indices.
        allowance_in_inches: Seam allowance width (inches).
        svg_units_per_inch: SVG units per inch.

    Returns:
        Dict {group_index: buffered shape (Polygon or MultiPolygon)}.
    """
    allowance = allowance_in_inches * svg_units_per_inch
    result: Dict[int, Union[Polygon, MultiPolygon]] = {}
    for i, group in enumerate(groups):
        shape = group_polygons_to_shape(polygons, group)
        seam_shape = clean_and_buffer_group_shape(shape, allowance)
        result[i] = seam_shape
    return result
