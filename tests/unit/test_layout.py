import pytest
from shapely.geometry import Polygon
from layout import minimal_bounding_box_rotation, layout_groups


def test_minimal_bounding_box_rotation_identity_for_square():
    square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    rotated_poly, angle = minimal_bounding_box_rotation(square)
    assert angle in range(0, 180, 5)
    assert pytest.approx(rotated_poly.area) == 1.0


def test_layout_groups_single_square():
    square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    seam_allowances = {0: square}
    page_width = 8.5
    page_height = 11

    pages = layout_groups(
        seam_allowances,
        page_width_in=page_width,
        page_height_in=page_height,
    )

    assert len(pages) == 1
    assert len(pages[0]) == 1
    placement = pages[0][0]
    assert placement["group_idx"] == 0
    assert 0 <= placement["rotation"] <= 360
    assert isinstance(placement["dx"], float)
    assert isinstance(placement["dy"], float)


def test_layout_groups_multiple_polygons():
    squares = {i: Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]).buffer(0) for i in range(5)}

    pages = layout_groups(
        squares,
        page_width_in=8.5,
        page_height_in=11,
        margin_in=0.25,
        margin_between=0.1,
        svg_units_per_in=96,
    )

    total_shapes = sum(len(page) for page in pages)
    assert total_shapes == 5
    assert all(
        "dx" in placement and "dy" in placement for page in pages for placement in page
    )


def test_layout_groups_raises_on_too_large_shape():
    # A polygon that is larger than the page, even without margins
    big_poly = Polygon(
        [(0, 0), (20 * 96, 0), (20 * 96, 20 * 96), (0, 20 * 96)]
    )  # 20" x 20"

    with pytest.raises(ValueError, match="Packing failed for group"):
        layout_groups(
            {0: big_poly},
            page_width_in=8.5,
            page_height_in=11,
        )
