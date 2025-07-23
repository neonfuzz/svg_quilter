from svgpathtools import svg2paths2
from shapely.geometry import LineString


def parse_svg(svg_filename):
    """
    Reads all paths from SVG and returns a list of Shapely LineString segments
    for all straight lines and line-like path segments.
    """
    paths, attributes, svg_attr = svg2paths2(svg_filename)
    shapely_lines = []
    for path in paths:
        for segment in path:
            # Only handle straight lines (Line) segments.
            if segment.__class__.__name__ == "Line":
                start = segment.start
                end = segment.end
                shapely_lines.append(
                    LineString([(start.real, start.imag), (end.real, end.imag)])
                )
            # Optionally: Approximate curves as lines for quilt patterns
            # elif segment.__class__.__name__ == "CubicBezier":
            #     # You could use segment.approximate_arcs_with_quads() or similar, or interpolate
            #     pass
    return shapely_lines


if __name__ == "__main__":
    import sys

    lines = parse_svg(sys.argv[1])
    for i, line in enumerate(lines):
        print(f"LineString {i+1}: {list(line.coords)}")
