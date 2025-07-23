# FPP SVG to PDF/PNG Pattern Generator

A Python toolkit for turning SVG line drawings into **Foundation Paper Piecing (FPP)** quilt patterns—automatically grouping, labeling, and laying out your quilt pieces for easy printing.

---

## Features

- **SVG → FPP:** Converts SVG paths to precise printable quilt pieces.
- **Automatic Grouping:** Detects groups and shared edges for accurate piecing.
- **Seam Allowance:** Adds customizable seam allowances to each group.
- **Flexible Layout:** Efficiently arranges groups onto printable PDF pages.
- **Visualization:** Outputs a labeled PNG layout preview for quick checks.
- **Easy Labeling:** Groups and pieces are automatically labeled and placed.

---

## Requirements

- Python 3.8+
- Install dependencies:

`pip install -r requirements.txt`

(See below for main libraries.)

---

## Usage

```bash
python main.py [-h] [--pdf PDF_FILE] [--png PNG_FILE]
             [--page-width PAGE_WIDTH_IN] [--page-height PAGE_HEIGHT_IN]
             [--seam-allowance SEAM_ALLOWANCE_IN] [--margin MARGIN_IN]
             svg_file

Example:

`python main.py mypattern.svg --pdf out/pattern.pdf --png out/layout.png --seam-allowance 0.375`

Arguments

    svg_file          Input SVG file (required)

Options
Option	Description	Default
--pdf PDF_FILE	Output PDF file	out/pieces.pdf
--png PNG_FILE	Output PNG layout file	out/layout.png
--page-width PAGE_WIDTH_IN	PDF page width in inches	8.5
--page-height PAGE_HEIGHT_IN	PDF page height in inches	11.0
--seam-allowance SEAM_ALLOWANCE_IN	Seam allowance in inches	0.25
--margin MARGIN_IN	Page margin in inches	0.5
```

Run `python main.py --help` for full usage details.

### Output

    PDF: Pages with all grouped, labeled quilt pieces + seam allowance.

    PNG: Visual layout of all pieces and groups for quick verification.

---

## Main Dependencies

    shapely — for geometry handling

    svgpathtools — for SVG parsing

    matplotlib — for layout/preview visualization

    reportlab — for PDF output

---

## SVG Guidelines

    Use simple SVGs: closed paths/lines for your desired shapes.

    Each "patch" must be a closed shape made of lines or polylines.

    All paths must be in the same SVG file.

    Use Inkscape or similar to prepare SVGs.

---

## Project Structure

main.py
svg_parser.py
geometry.py
grouping.py
labeling.py
seam_allowance.py
layout.py
pdf_writer.py
utils.py

---

## Tips

    Seam allowance and page size are fully customizable.

    For best results, ensure shapes align perfectly in your SVG.

    If you see unexpected grouping, check for tiny gaps or misalignments.

## License

MIT License.
See LICENSE file for details.


*Happy quilting!*