import subprocess
from pathlib import Path
import pytest

from shapely.geometry import LineString, Polygon

from utils import get_svg_units_per_inch
from svg_parser import parse_svg
from geometry import lines_to_polygons
from grouping import group_polygons
from seam_allowance import seam_allowance_polygons
from layout import LayoutConfig, layout_groups


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
def test_full_pipeline_stages(filename):
    svg_path = f"tests/e2e/fixtures/{filename}"

    # Step 1: Parse SVG to LineStrings
    lines = parse_svg(svg_path)
    assert isinstance(lines, list)
    assert all(isinstance(line, LineString) for line in lines)
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
    layout_config = LayoutConfig(page_width_in=8.5, page_height_in=11)
    pages = layout_groups(allowances, layout_config)
    assert isinstance(pages, list)
    assert len(pages) == 1, f"{filename} produced {len(pages)} pages"
    assert sum(len(page) for page in pages) == len(groups)


def test_pipeline_cli_e2e(tmp_path: Path):
    """
    E2E test: Run the entire pipeline as a CLI command on a sample SVG file.
    Checks that the PDF and PNG outputs are produced.
    """
    # Adjust the paths as needed for your project structure
    project_root = Path(__file__).parent.parent.parent
    main_py = project_root / "main.py"
    input_svg = project_root / "tests" / "e2e" / "fixtures" / "1groupA.svg"
    output_pdf = tmp_path / "out/pieces.pdf"
    output_png = tmp_path / "out/layout.png"

    result = subprocess.run(
        [
            "python",
            str(main_py),
            str(input_svg),
            "--pdf",
            str(output_pdf),
            "--png",
            str(output_png),
            "--page-width",
            "8.5",
            "--page-height",
            "11",
            "--seam-allowance",
            "0.25",
            "--margin",
            "0.5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Print outputs for debugging if needed
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    assert result.returncode == 0, "Pipeline CLI did not complete successfully"

    # Check that outputs exist and are non-empty
    assert output_pdf.exists() and output_pdf.stat().st_size > 0, (
        "PDF output not created"
    )
    assert output_png.exists() and output_png.stat().st_size > 0, (
        "PNG output not created"
    )

    assert "Done! Output written to:" in result.stdout


def test_pipeline_cli_no_flip(tmp_path: Path):
    project_root = Path(__file__).parent.parent.parent
    main_py = project_root / "main.py"
    input_svg = project_root / "tests" / "e2e" / "fixtures" / "1groupA.svg"
    output_pdf = tmp_path / "out/pieces.pdf"
    output_png = tmp_path / "out/layout.png"

    result = subprocess.run(
        [
            "python",
            str(main_py),
            str(input_svg),
            "--pdf",
            str(output_pdf),
            "--png",
            str(output_png),
            "--no-flip",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    assert result.returncode == 0
    assert output_pdf.exists() and output_pdf.stat().st_size > 0
    assert output_png.exists() and output_png.stat().st_size > 0
