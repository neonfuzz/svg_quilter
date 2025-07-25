import pytest
from shapely.geometry import LineString, Polygon
from utils import get_svg_units_per_inch
from svg_parser import parse_svg  # Your SVG → LineString parser
from geometry import lines_to_polygons
from grouping import group_polygons
from seam_allowance import seam_allowance_polygons
from layout import layout_groups


@pytest.mark.parametrize(
    "filename",
    [
        "1groupA.svg",
        "1groupB.svg",
        "2groupA.svg",
        "2groupB.svg",
        "3groupA.svg",
        "3groupB.svg",
        "2converging.svg",
        "1big_seed.svg",
        "2big_seed.svg",
    ],
)
def test_full_pipeline_on_svg(filename):
    svg_path = f"tests/e2e/fixtures/{filename}"

    # Step 1: Parse SVG to LineStrings
    lines = parse_svg(svg_path)
    assert isinstance(lines, list)
    assert all(isinstance(l, LineString) for l in lines)
    assert len(lines) > 0

    # Step 2: Convert LineStrings to Polygons
    polygons = lines_to_polygons(lines)
    assert all(isinstance(p, Polygon) for p in polygons)
    assert len(polygons) > 0

    # Step 3: Group Polygons
    ngroups = int(filename[0])
    groups = group_polygons(polygons, lines)
    assert len(groups) == ngroups
    assert isinstance(groups, list)
    assert sum(len(g) for g in groups) == len(polygons)

    # Step 4: Seam Allowances
    svg_units = get_svg_units_per_inch(svg_path)
    allowances = seam_allowance_polygons(
        polygons, groups, allowance_in_inches=0.25, svg_units_per_inch=svg_units
    )
    assert len(allowances) == len(groups)

    # Step 5: Layout
    pages = layout_groups(allowances, 8.5, 11)
    assert isinstance(pages, list)
    assert len(pages) == 1, f"{filename} produced {len(pages)} pages"
    assert sum(len(page) for page in pages) == len(groups)
