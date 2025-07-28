"""Arrange seam allowance shapes onto pages for printing or export.

Provide utilities to layout groups with seam allowances on pages,
using translation and rotation to fit within printable areas.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union, cast

from pyclipper import MinkowskiSum  # type: ignore[import-untyped]
from shapely import unary_union
from shapely.affinity import rotate as shapely_rotate
from shapely.affinity import translate as shapely_translate
from shapely.geometry import LineString, MultiLineString, Polygon, box
from shapely.geometry.base import BaseGeometry
from tqdm import tqdm

from utils import remove_collinear_points


@dataclass
class Placement:
    """Stores placement details for a seam allowance group on a page."""

    group_idx: int
    rotation: int
    dx: float
    dy: float
    poly: Polygon


@dataclass
class LayoutConfig:
    """Configuration for layout of seam allowance polygons."""

    page_width_in: float
    page_height_in: float
    margin_in: float = 0.5
    margin_between: float = 0.1
    svg_units_per_in: float = 96
    allow_rotate: bool = True


def _as_polygon(geom: BaseGeometry) -> Polygon:
    """Safely cast BaseGeometry to Polygon, or raise informative error."""
    if not isinstance(geom, Polygon):
        raise TypeError(f"Expected Polygon, got {type(geom).__name__}")
    return geom


def _polygon_exterior_coords(geom: BaseGeometry) -> List[Tuple[float, ...]]:
    """Get exterior coords from a Polygon, raise if not Polygon.

    Ensures each coord is a 2-tuple of floats.
    """
    poly = _as_polygon(geom.normalize())
    return [cast(Tuple[float, ...], (c[0], c[1])) for c in poly.exterior.coords]


def minimal_bounding_box_rotation(poly: Polygon, step: int = 5) -> Tuple[Polygon, int]:
    """Rotate a polygon to minimize its bounding box area."""
    min_area = float("inf")
    best_angle = 0
    best_poly = poly
    for angle in range(0, 180, step):
        rotated = shapely_rotate(poly, angle, origin="centroid", use_radians=False)
        minx, miny, maxx, maxy = rotated.bounds
        area = (maxx - minx) * (maxy - miny)
        if area < min_area:
            min_area = area
            best_angle = angle
            best_poly = rotated
    return best_poly, best_angle


def minkowski(
    poly1: Polygon, poly2: Polygon, diff: bool = False, scale: int = 100000
) -> List[Polygon]:
    """Compute the Minkowski sum of two polygons.

    Args:
        poly1: The first polygon.
        poly2: The second polygon.
        diff: If True, compute the difference instead of the sum. Defaults to False.
        scale: Scale factor for pyclipper coordinates. Defaults to 100000.

    Returns:
        List[Polygon]: A list of polygons representing the Minkowski sum or difference.
    """
    coords1 = _polygon_exterior_coords(poly1)[:-1]
    coords1 = [(int(x * scale), int(y * scale)) for x, y in coords1]

    coords2 = _polygon_exterior_coords(poly2)[:-1]
    x0, y0 = coords2[0]
    coords2 = [(x - x0, y - y0) for x, y in coords2]
    if not diff:
        # Reflect poly2 about the origin
        coords2 = [(-x, -y) for x, y in coords2]
    coords2 = [(int(x * scale), int(y * scale)) for x, y in coords2]

    mink_raw = MinkowskiSum(coords1, coords2, True)
    mink = [Polygon([(x / scale, y / scale) for (x, y) in poly]) for poly in mink_raw]
    return mink


def score_placements(placements: List[Placement]) -> float:
    """Calculate a score for a list of placements.

    The score can be customized as needed. This version computes
    the total area of the bounding box used by all polygons
    (after placement).

    Args:
        placements: List of Placement objects.

    Returns:
        A float score; lower is better (less area used).
    """
    return unary_union([p.poly for p in placements]).convex_hull.area


class PageLayoutEngine:
    """Engine to arrange seam allowance polygons onto pages."""

    def __init__(self, seam_allowances: Dict[int, Polygon], config: LayoutConfig):
        """Initialize the PageLayoutEngine.

        Args:
            seam_allowances: A dictionary where keys are unique identifiers
                for each seam allowance polygon and values are the corresponding
                Polygon objects.
            config: The layout configuration object containing page dimensions,
                margins, and other relevant settings.
        """
        self.seam_allowances = seam_allowances
        self.config = config
        self.grow = (config.margin_between / 2) * config.svg_units_per_in

        inner_width = (
            config.page_width_in - 2 * config.margin_in
        ) * config.svg_units_per_in
        inner_height = (
            config.page_height_in - 2 * config.margin_in
        ) * config.svg_units_per_in
        margin = config.margin_in * config.svg_units_per_in
        # Normalize, ensure always Polygon
        self.box: Polygon = _as_polygon(
            _as_polygon(box(margin, margin, inner_width, inner_height)).normalize()
        )

    def layout_groups(self) -> List[List[Placement]]:
        """Place groups of polygons across multiple pages.

        Returns:
            A list of pages. Each page is a list of `Placement`s.
        """
        pages: List[List[Placement]] = []
        for idx, poly, angle in tqdm(
            self.prepare_packing_inputs(), desc="Placing groups"
        ):
            placed_on_existing = False
            # Try to place on any existing page
            for page in pages:
                next_placement = self._place_next(idx, poly, angle, page)
                if next_placement is not None:
                    page.append(next_placement)
                    placed_on_existing = True
                    break
            if not placed_on_existing:
                # Can't fit: start new page and place as first piece
                placement = self._place_first(idx, poly, angle)
                pages.append([placement])
        return pages

    def _place_first(
        self, idx: int, poly: Polygon, angle: int, tol: float = 1e-6
    ) -> Placement:
        """Attempt to place the first polygon on the page, trying basic rotations.

        If it does not fit at any rotation, raise an error.
        """
        for ang in [0, 90, 45, 135]:
            rotated = shapely_rotate(poly, ang, origin="centroid").normalize()
            rotated = _as_polygon(rotated)
            x0, y0, _, _ = rotated.bounds
            x1, y1 = self.box.exterior.coords[0]
            dx, dy = x1 - x0, y1 - y0
            rotated_t = shapely_translate(rotated, xoff=dx, yoff=dy)
            rotated_t = _as_polygon(rotated_t)
            if self.box.contains(rotated_t.buffer(-tol)):
                return Placement(
                    group_idx=idx, rotation=angle + ang, dx=dx, dy=dy, poly=rotated_t
                )
        raise ValueError(f"Largest piece (group {idx}) cannot be placed on the page.")

    def _place_next(
        self, idx: int, poly: Polygon, angle: int, placed: List[Placement]
    ) -> Optional[Placement]:
        """Find the best placement for a polygon given existing placements.

        Minimizes by `score_placements`.
        """

        def candidate_placements_for_rotation(
            rotated: Polygon, ang: int
        ) -> List[Placement]:
            nfp_parts = [unary_union(minkowski(p.poly, rotated)) for p in placed]
            nfp = unary_union(nfp_parts).boundary
            ifp_raw = minkowski(self.box, rotated)
            if len(ifp_raw) == 1:
                return []
            ifp = _as_polygon(ifp_raw[1])
            valid = ifp.intersection(nfp)
            # Accept only if valid is LineString or MultiLineString
            if isinstance(valid, (LineString, MultiLineString)):
                coords = self._extract_coords(valid)
            else:
                coords = []
            candidates = []
            x0, y0 = rotated.exterior.coords[0]
            for coord in coords:
                dx, dy = coord[0] - x0, coord[1] - y0
                candidates.append(
                    Placement(
                        group_idx=idx,
                        rotation=angle + ang,
                        dx=dx,
                        dy=dy,
                        poly=shapely_translate(rotated, xoff=dx, yoff=dy),
                    )
                )
            return candidates

        best: Optional[Placement] = None
        for ang in [0, 45, 90, 135, 180, 225, 270, 315]:
            rotated = shapely_rotate(poly, ang, origin="centroid").normalize()
            rotated = _as_polygon(rotated)
            candidates = candidate_placements_for_rotation(rotated, ang)
            for candidate in candidates:
                score = score_placements(placed + [candidate])
                if best is None or score < score_placements(placed + [best]):
                    best = candidate
        return best

    def _extract_coords(
        self, valid: Union[LineString, MultiLineString]
    ) -> List[Tuple[float, ...]]:
        if isinstance(valid, LineString):
            return [cast(Tuple[float, ...], c) for c in valid.coords]
        # MultiLineString.geoms: sequence of LineString
        coords: List[Tuple[float, ...]] = []
        for line in valid.geoms:
            coords.extend([cast(Tuple[float, ...], c) for c in line.coords])
        return coords

    def prepare_packing_inputs(self) -> List[Tuple[int, Polygon, int]]:
        """Prepare the inputs for packing.

        Sort polygons by area, rotating them to minimize bounding box size,
        and applying a buffer for inter-piece margin.
        """
        to_pack: List[Tuple[int, Polygon, int]] = []
        for idx, poly in sorted(self.seam_allowances.items(), key=lambda x: -x[1].area):
            poly, angle = minimal_bounding_box_rotation(poly)
            poly = poly.buffer(self.grow, join_style="mitre")
            poly = remove_collinear_points(poly)
            poly = _as_polygon(poly.normalize())
            to_pack.append((idx, poly, angle))
        return to_pack


def layout_groups(
    seam_allowances: Dict[int, Polygon], config: LayoutConfig
) -> List[List[Placement]]:
    """Convenience function to use PageLayoutEngine for backward compatibility."""
    return PageLayoutEngine(seam_allowances, config).layout_groups()
