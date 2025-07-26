"""Arrange seam allowance shapes onto pages for printing or export.

Provide utilities to layout groups with seam allowances on pages,
using translation and rotation to fit within printable areas.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from rectpack import newPacker  # type: ignore[import-untyped]
from shapely.affinity import rotate as shapely_rotate
from shapely.geometry import Polygon


@dataclass
class Placement:
    """Stores placement details for a seam allowance group on a page."""

    group_idx: int
    rotation: float
    dx: float
    dy: float


@dataclass
class LayoutConfig:
    """Configuration for layout of seam allowance polygons."""

    page_width_in: float
    page_height_in: float
    margin_in: float = 0.5
    margin_between: float = 0.1
    svg_units_per_in: float = 96
    allow_rotate: bool = True


@dataclass
class PlacementInputs:
    """Inputs for placing a polygon on the layout."""

    group_idx: int
    x: float
    y: float
    minx: float
    miny: float
    pre_rot_angle: float
    rectpack_rot: int


def minimal_bounding_box_rotation(
    poly: Polygon, step: int = 5
) -> Tuple[Polygon, float]:
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
        self.inner_width = (
            config.page_width_in - 2 * config.margin_in
        ) * config.svg_units_per_in
        self.inner_height = (
            config.page_height_in - 2 * config.margin_in
        ) * config.svg_units_per_in
        self.margin = config.margin_in * config.svg_units_per_in
        self.grow = (config.margin_between / 2) * config.svg_units_per_in

    def layout_groups(self) -> List[List[Placement]]:
        """Arrange seam allowance polygons using rectpack for tight packing."""
        rectangles, rotated_polys = self.prepare_packing_inputs()
        packer = self._run_packer(rectangles)
        self._validate_packing(packer)
        return self._extract_placements_from_packer(packer, rectangles, rotated_polys)

    def prepare_packing_inputs(self):
        """Return rectangles and rotated polygons for each group.

        Returns:
            rectangles: List of (group_idx, width, height, minx, miny)
            rotated_polys: Dict of group_idx to (rotated Polygon, pre-rotation angle)
        """
        rectangles = []
        rotated_polys = {}
        for group_idx, poly in self.seam_allowances.items():
            best_poly, pre_rot_angle = minimal_bounding_box_rotation(poly)
            rotated_polys[group_idx] = (best_poly, pre_rot_angle)
            minx, miny, maxx, maxy = best_poly.bounds
            w = maxx - minx + 2 * self.grow
            h = maxy - miny + 2 * self.grow
            rectangles.append((group_idx, w, h, minx, miny))
        return rectangles, rotated_polys

    def _run_packer(self, rectangles):
        packer = newPacker(rotation=self.config.allow_rotate)
        for group_idx, w, h, _, _ in rectangles:
            packer.add_rect(w, h, group_idx)
        packer.add_bin(self.inner_width, self.inner_height, float("inf"))
        packer.pack()
        return packer

    def _validate_packing(self, packer):
        packed_ids = {rect.rid for abin in packer for rect in abin}
        unpacked_ids = set(self.seam_allowances.keys()) - packed_ids
        if unpacked_ids:
            failed = ", ".join(str(i) for i in sorted(unpacked_ids))
            raise ValueError(
                f"Packing failed for group(s): {failed}. "
                "They may be too large for the page dimensions."
            )

    def _calculate_rectpack_rotation(self, orig_w, orig_h, packed_w, packed_h) -> int:
        return (
            90
            if self.config.allow_rotate and ((packed_w, packed_h) != (orig_w, orig_h))
            else 0
        )

    def _get_transformed_polygon_and_offset(self, rotated_poly, rectpack_rot):
        if rectpack_rot == 90:
            rotated_poly = shapely_rotate(
                rotated_poly, 90, origin="centroid", use_radians=False
            )
        minx, miny, _, _ = rotated_poly.bounds
        return rotated_poly, minx, miny

    def _make_placement(self, inputs: PlacementInputs) -> Placement:
        dx = inputs.x + self.grow + self.margin - inputs.minx
        dy = inputs.y + self.grow + self.margin - inputs.miny
        rotation = (inputs.pre_rot_angle + inputs.rectpack_rot) % 360
        return Placement(
            group_idx=inputs.group_idx,
            rotation=rotation,
            dx=dx,
            dy=dy,
        )

    def _extract_placements_from_packer(self, packer, rectangles, rotated_polys):
        # pylint: disable=too-many-locals
        # The number of locals adds, rather than subtracts, clarity.
        pages: List[List[Placement]] = []
        for abin in packer:
            page_placements: List[Placement] = []
            for rect in abin:
                orig = next(r for r in rectangles if r[0] == rect.rid)
                orig_w, orig_h, minx, miny = orig[1], orig[2], orig[3], orig[4]
                rectpack_rot = self._calculate_rectpack_rotation(
                    orig_w, orig_h, rect.width, rect.height
                )
                rotated_poly, pre_rot_angle = rotated_polys[rect.rid]
                rotated_poly, minx, miny = self._get_transformed_polygon_and_offset(
                    rotated_poly, rectpack_rot
                )
                placement_inputs = PlacementInputs(
                    rect.rid, rect.x, rect.y, minx, miny, pre_rot_angle, rectpack_rot
                )
                placement = self._make_placement(placement_inputs)
                page_placements.append(placement)
            if page_placements:
                pages.append(page_placements)
        return pages


def layout_groups(
    seam_allowances: Dict[int, Polygon], config: LayoutConfig
) -> List[List[Placement]]:
    """Convenience function to use PageLayoutEngine for backward compatibility."""
    return PageLayoutEngine(seam_allowances, config).layout_groups()
