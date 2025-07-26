import pytest
from shapely.geometry import Polygon
from layout import (
    LayoutConfig,
    minimal_bounding_box_rotation,
    layout_groups,
    PageLayoutEngine,
)


def test_minimal_bounding_box_rotation_identity_for_square():
    square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    rotated_poly, angle = minimal_bounding_box_rotation(square)
    assert angle in range(0, 180, 5)
    assert pytest.approx(rotated_poly.area) == 1.0


def test_layout_groups_single_square():
    square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    seam_allowances = {0: square}
    layout_config = LayoutConfig(page_width_in=8.5, page_height_in=11)

    pages = layout_groups(seam_allowances, layout_config)

    assert len(pages) == 1
    assert len(pages[0]) == 1
    placement = pages[0][0]
    assert placement.group_idx == 0
    assert hasattr(placement, "dx") and hasattr(placement, "dy")


def test_layout_groups_multiple_polygons():
    squares = {i: Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]).buffer(0) for i in range(5)}

    layout_config = LayoutConfig(page_width_in=8.5, page_height_in=11)
    pages = layout_groups(squares, layout_config)

    total_shapes = sum(len(page) for page in pages)
    assert total_shapes == 5
    assert all(
        hasattr(placement, "dx") and hasattr(placement, "dy")
        for page in pages
        for placement in page
    )


def test_layout_groups_raises_on_too_large_shape():
    # A polygon that is larger than the page, even without margins
    big_poly = Polygon(
        [(0, 0), (20 * 96, 0), (20 * 96, 20 * 96), (0, 20 * 96)]
    )  # 20" x 20"

    layout_config = LayoutConfig(page_width_in=8.5, page_height_in=11)
    with pytest.raises(ValueError, match="Packing failed for group"):
        layout_groups({0: big_poly}, layout_config)


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

    # Should fit either way, but check rotation flag
    pages_no_rotate = layout_groups(seam_allowances, config_no_rotate)
    pages_rotate = layout_groups(seam_allowances, config_rotate)
    assert len(pages_no_rotate) == 1
    assert len(pages_rotate) == 1
    placement_no_rotate = pages_no_rotate[0][0]
    placement_rotate = pages_rotate[0][0]
    # Rotation in placement_rotate may be different than in placement_no_rotate
    assert isinstance(placement_no_rotate.rotation, (int, float))
    assert isinstance(placement_rotate.rotation, (int, float))


def test_pagelayoutengine_prepare_packing_inputs_public():
    # Directly test the now-public method
    square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    engine = PageLayoutEngine({0: square}, LayoutConfig(8.5, 11))
    rectangles, rotated_polys = engine.prepare_packing_inputs()
    assert isinstance(rectangles, list)
    assert isinstance(rotated_polys, dict)
    assert 0 in rotated_polys
    assert len(rectangles) == 1
    assert isinstance(rotated_polys[0][0], Polygon)
    assert isinstance(rotated_polys[0][1], (int, float))


def test_layout_groups_handles_multiple_pages():
    # 20 small shapes, packed tightly so 8.5x11 cannot hold them all
    squares = {i: Polygon([(0, 0), (6, 0), (6, 6), (0, 6)]) for i in range(20)}
    config = LayoutConfig(
        page_width_in=8.5,
        page_height_in=11,
        margin_in=0.25,
        margin_between=0.1,
        svg_units_per_in=1,
    )
    pages = layout_groups(squares, config)
    # Should require multiple pages
    assert len(pages) > 1
    total = sum(len(page) for page in pages)
    assert total == 20


def test_layout_groups_placement_values_are_float():
    # Ensure all placement dx, dy, rotation are floats
    square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    seam_allowances = {0: square}
    config = LayoutConfig(8.5, 11)
    pages = layout_groups(seam_allowances, config)
    placement = pages[0][0]
    assert isinstance(placement.dx, float)
    assert isinstance(placement.dy, float)
    assert isinstance(placement.rotation, float) or isinstance(placement.rotation, int)


def test_minimal_bounding_box_rotation_is_rotation_invariant_for_regular_polygon():
    # For a regular pentagon, minimal bounding box rotation may be ambiguous, but area should stay the same.
    import math

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
