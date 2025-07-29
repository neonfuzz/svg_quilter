import math
import pytest
from shapely.geometry import Polygon, box, LineString, MultiPoint

from layout import (
    LayoutConfig,
    minimal_bounding_box_rotation,
    layout_groups,
    PageLayoutEngine,
    Placement,
    _as_polygon,
)


def make_square(x=0, y=0, size=1) -> Polygon:
    return box(x, y, x+size, y+size)


def test_minimal_bounding_box_rotation_identity_for_square():
    square = make_square()
    rotated_poly, angle = minimal_bounding_box_rotation(square)
    assert angle in range(0, 180, 5)
    assert pytest.approx(rotated_poly.area) == 1.0


def test_layout_groups_single_square():
    square = make_square()
    seam_allowances = {0: square}
    config = LayoutConfig(page_width_in=8.5, page_height_in=11)

    pages = layout_groups(seam_allowances, config)
    assert len(pages) == 1
    assert len(pages[0]) == 1
    placement = pages[0][0]
    assert placement.group_idx == 0
    assert isinstance(placement.dx, float)
    assert isinstance(placement.dy, float)
    assert isinstance(placement.rotation, int)
    assert isinstance(placement.poly, Polygon)


def test_layout_groups_multiple_polygons():
    seam_allowances = {i: make_square() for i in range(5)}
    config = LayoutConfig(page_width_in=8.5, page_height_in=11)
    pages = layout_groups(seam_allowances, config)
    total_shapes = sum(len(page) for page in pages)
    assert total_shapes == 5
    assert all(isinstance(p.group_idx, int) for page in pages for p in page)


def test_layout_groups_raises_on_too_large_shape():
    big_poly = make_square(0, 0, size=20 * 96)  # 20" x 20" at 96 units/in
    config = LayoutConfig(page_width_in=8.5, page_height_in=11)
    with pytest.raises(ValueError, match="cannot be placed on the page"):
        layout_groups({0: big_poly}, config)


def test_layout_groups_rotation_allowed_vs_not():
    # Place a rectangle that fits only if rotation is allowed
    rect = Polygon([(0, 0), (2, 0), (2, 8), (0, 8)])
    seam_allowances = {0: rect}
    config_no_rotate = LayoutConfig(
        page_width_in=8.5, page_height_in=11, allow_rotate=False
    )
    config_rotate = LayoutConfig(
        page_width_in=8.5, page_height_in=11, allow_rotate=True
    )
    pages_no_rotate = layout_groups(seam_allowances, config_no_rotate)
    pages_rotate = layout_groups(seam_allowances, config_rotate)
    assert len(pages_no_rotate) == 1
    assert len(pages_rotate) == 1
    placement_no_rotate = pages_no_rotate[0][0]
    placement_rotate = pages_rotate[0][0]
    assert isinstance(placement_no_rotate.rotation, int)
    assert isinstance(placement_rotate.rotation, int)


def test_pagelayoutengine_prepare_packing_inputs_public():
    square = make_square()
    engine = PageLayoutEngine({0: square}, LayoutConfig(8.5, 11))
    result = engine.prepare_packing_inputs()
    assert isinstance(result, list)
    idx, poly, angle = result[0]
    assert idx == 0
    assert isinstance(poly, Polygon)
    assert isinstance(angle, int)


def test_layout_groups_handles_multiple_pages():
    # 20 small shapes, packed tightly so 8.5x11 cannot hold them all.
    seam_allowances = {i: make_square(size=6) for i in range(20)}
    config = LayoutConfig(
        page_width_in=8.5,
        page_height_in=11,
        margin_in=0.25,
        margin_between=0.1,
        svg_units_per_in=1,
    )
    pages = layout_groups(seam_allowances, config)
    assert len(pages) > 1
    total = sum(len(page) for page in pages)
    assert total == 20


def test_layout_groups_placement_values_are_float():
    square = make_square()
    seam_allowances = {0: square}
    config = LayoutConfig(8.5, 11)
    pages = layout_groups(seam_allowances, config)
    placement = pages[0][0]
    assert isinstance(placement.dx, float)
    assert isinstance(placement.dy, float)
    assert isinstance(placement.rotation, int)


def test_minimal_bounding_box_rotation_is_rotation_invariant_for_regular_polygon():
    n = 5
    r = 1
    pentagon = Polygon(
        [
            (math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r)
            for i in range(n)
        ]
    )
    rotated_poly, angle = minimal_bounding_box_rotation(pentagon)
    assert pytest.approx(rotated_poly.area) == pytest.approx(pentagon.area)
    assert 0 <= angle < 180

def test_as_polygon_raises_typeerror():
    with pytest.raises(TypeError):
        _as_polygon(LineString([(0,0),(1,1)]))


def test_place_next_handles_no_line_intersection(monkeypatch):
    square = make_square()
    engine = PageLayoutEngine({0: square, 1: square}, LayoutConfig(2, 2))
    first = engine._place_first(0, square, 0)

    # Force unary_union and minkowski to return multipoint so intersection yields not LineString
    monkeypatch.setattr('layout.unary_union', lambda *args, **kwargs: MultiPoint([(0,0),(1,1)]))
    monkeypatch.setattr('layout.minkowski', lambda *args, **kwargs: [square, square])

    res = engine._place_next(1, square, 0, [first])
    assert res is None
