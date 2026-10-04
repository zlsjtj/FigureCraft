"""Original SVG/PDF/PNG drawing; all dimensions below are millimetres.

Only two members are modelled. The exploded view lifts B by 70 mm for
explanation. The assembly view uses the exact supplied bounds. The section
enlarges the central 20 x 16 mm region at y = 0; it is not a third member.
No new dependencies are required: ReportLab and the supplied pdftoppm render
the same vector primitives that are written to the editable SVG.
"""
from pathlib import Path
from collections import defaultdict
import argparse
import html
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parent
FONT = None
PDFTOPPM = None
W, H = 160.0, 100.0
PT = 72 / 25.4
INK = "#24343B"
MUTED = "#52646B"
EDGE = "#36525B"
PALETTE = {
    "A": {0: "#278C93", 1: "#369FA5", 2: "#62BDC0"},
    "B": {0: "#C77C38", 1: "#D9934D", 2: "#F0B971"},
}


class Drawing:
    def __init__(self, out):
        self.out = out
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="100mm" viewBox="0 0 160 100">',
            '<title>Cross-lap members: complementary half-depth notches</title>',
            '<desc>Constructed geometry demonstration. The same two members are shown separated, assembled, and in an enlarged section through the crossing. A occupies the lower half and B the upper half at the centre.</desc>',
            '<rect x="0" y="0" width="160" height="100" fill="#FFFFFF"/>']
        pdfmetrics.registerFont(TTFont("FigureArial", str(FONT)))
        self.pdf = canvas.Canvas(str(out / "figure.pdf"), pagesize=(W * PT, H * PT))
        self.pdf.setTitle("Cross-lap members: constructed geometry demonstration")
        self.pdf.setAuthor("")

    def group(self, name):
        self.parts.append(f'<g id="{name}">')

    def endgroup(self):
        self.parts.append('</g>')

    def polygon(self, points, fill, stroke=EDGE, width=0.20):
        pts = " ".join(f"{x:.4f},{y:.4f}" for x, y in points)
        self.parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"/>')
        p = self.pdf.beginPath()
        p.moveTo(points[0][0] * PT, (H - points[0][1]) * PT)
        for x, y in points[1:]:
            p.lineTo(x * PT, (H - y) * PT)
        p.close()
        self.pdf.setFillColor(HexColor(fill))
        self.pdf.setStrokeColor(HexColor(stroke))
        self.pdf.setLineWidth(width * PT)
        self.pdf.setLineJoin(1)
        self.pdf.drawPath(p, fill=1, stroke=1)

    def line(self, points, color=MUTED, width=0.23, dash=None):
        pts = " ".join(f"{x:.4f},{y:.4f}" for x, y in points)
        dashed = ' stroke-dasharray="1.4 1.1"' if dash else ''
        self.parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{dashed}/>')
        p = self.pdf.beginPath()
        p.moveTo(points[0][0] * PT, (H - points[0][1]) * PT)
        for x, y in points[1:]:
            p.lineTo(x * PT, (H - y) * PT)
        self.pdf.setStrokeColor(HexColor(color))
        self.pdf.setLineWidth(width * PT)
        self.pdf.setDash([1.4 * PT, 1.1 * PT] if dash else [])
        self.pdf.drawPath(p, fill=0, stroke=1)
        self.pdf.setDash([])

    def text(self, x, y, value, size=3.0, color=INK, anchor="start"):
        self.parts.append(f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}">{html.escape(value)}</text>')
        self.pdf.setFillColor(HexColor(color))
        self.pdf.setFont("FigureArial", size * PT)
        function = {"start": self.pdf.drawString, "middle": self.pdf.drawCentredString, "end": self.pdf.drawRightString}[anchor]
        function(x * PT, (H - y) * PT, value)

    def arrow(self, x, y0, y1):
        self.line([(x, y0), (x, y1)], width=0.34)
        self.polygon([(x, y1), (x - 1.05, y1 + 2.1), (x + 1.05, y1 + 2.1)], MUTED, MUTED, 0.1)

    def finish(self):
        self.parts.append('</svg>')
        (self.out / "figure.svg").write_text("\n".join(self.parts) + "\n", encoding="utf-8")
        self.pdf.showPage()
        self.pdf.save()


def member_at(x, y, z, lift):
    inside_a = -50 < x < 50 and -10 < y < 10 and 0 < z < 16
    notch_a = -10 < x < 10 and 8 < z < 16
    inside_b = -10 < x < 10 and -40 < y < 40 and lift < z < lift + 16
    notch_b = -10 < y < 10 and lift < z < lift + 8
    a = inside_a and not notch_a
    b = inside_b and not notch_b
    assert not (a and b), "The two members must not overlap."
    return "A" if a else "B" if b else None


def plane_contours(rectangles):
    """Cancel shared grid edges, retaining only the true material boundary.

    This avoids artificial seams where the voxel grid splits one solid face.
    The input faces have no holes; disconnected top faces produce separate
    contours. All construction uses the exact fixture coordinate grid.
    """
    edges = set()
    for u0, u1, v0, v1 in rectangles:
        vertices = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        for a, b in zip(vertices, vertices[1:] + vertices[:1]):
            if (b, a) in edges:
                edges.remove((b, a))
            else:
                edges.add((a, b))
    contours = []
    while edges:
        a, b = min(edges)
        edges.remove((a, b))
        loop = [a, b]
        while loop[-1] != loop[0]:
            candidates = sorted(edge for edge in edges if edge[0] == loop[-1])
            assert len(candidates) == 1
            edge = candidates[0]
            edges.remove(edge)
            loop.append(edge[1])
        loop.pop()
        simplified = []
        for i, point in enumerate(loop):
            previous, following = loop[i - 1], loop[(i + 1) % len(loop)]
            if (point[0] - previous[0]) * (following[1] - point[1]) != (point[1] - previous[1]) * (following[0] - point[0]):
                simplified.append(point)
        contours.append(simplified)
    return contours


def surfaces(lift):
    axes = [[-50, -10, 10, 50], [-40, -10, 10, 40], sorted(set([0, 8, 16, lift, lift + 8, lift + 16]))]
    cells = {}
    volumes = defaultdict(float)
    for i in range(len(axes[0]) - 1):
        for j in range(len(axes[1]) - 1):
            for k in range(len(axes[2]) - 1):
                index = (i, j, k)
                bounds = [(axes[d][index[d]], axes[d][index[d] + 1]) for d in range(3)]
                material = member_at(*[(a + b) / 2 for a, b in bounds], lift)
                if material:
                    cells[index] = material
                    volumes[material] += (bounds[0][1] - bounds[0][0]) * (bounds[1][1] - bounds[1][0]) * (bounds[2][1] - bounds[2][0])
    assert dict(volumes) == {"A": 28800.0, "B": 22400.0}
    plane_rects = defaultdict(list)
    for index, material in cells.items():
        for direction in range(3):
            neighbor = list(index)
            neighbor[direction] += 1
            if tuple(neighbor) in cells:
                continue
            uv = [d for d in range(3) if d != direction]
            a, b = uv
            coord = axes[direction][index[direction] + 1]
            plane_rects[(material, direction, coord)].append((axes[a][index[a]], axes[a][index[a] + 1], axes[b][index[b]], axes[b][index[b] + 1]))
    faces = []
    for (material, direction, coord), rectangles in plane_rects.items():
        uv = [d for d in range(3) if d != direction]
        for contour in plane_contours(rectangles):
            poly = []
            for u, v in contour:
                xyz = [0, 0, 0]
                xyz[direction] = coord
                xyz[uv[0]], xyz[uv[1]] = u, v
                poly.append(xyz)
            depth = sum(0.75609756 * x + y + 0.784120 * z for x, y, z in poly) / len(poly)
            faces.append((depth, material, direction, poly))
    return sorted(faces, key=lambda face: face[0])


def project(point, cx, cy, scale):
    x, y, z = point
    return (cx + scale * (0.82 * x - 0.62 * y), cy + scale * (0.34 * x + 0.48 * y - 0.94 * z))


def view(d, name, lift, cx, cy, scale):
    d.group(name)
    for _, material, direction, points in surfaces(lift):
        d.polygon([project(p, cx, cy, scale) for p in points], PALETTE[material][direction])
    d.endgroup()


def draw(out):
    d = Drawing(out)
    d.group("heading-and-member-key")
    d.text(8, 8, "Cross-lap: complementary half-depth notches", 4.0)
    d.text(152, 8, "DEMO", 2.8, MUTED, "end")
    d.polygon([(8, 12), (11, 12), (11, 15), (8, 15)], PALETTE["A"][2], PALETTE["A"][0], 0.16)
    d.text(13, 14.7, "A   100 × 20 × 16 mm", 3.0)
    d.polygon([(86, 12), (89, 12), (89, 15), (86, 15)], PALETTE["B"][2], PALETTE["B"][0], 0.16)
    d.text(91, 14.7, "B   80 × 20 × 16 mm", 3.0)
    d.line([(8, 19), (152, 19)], "#D8E2E5", 0.25)
    d.text(8, 25, "(a) Separated for explanation", 3.3)
    d.text(86, 25, "(b) Assembled", 3.3)
    d.endgroup()
    view(d, "separated-same-members", 70, 40, 84, 0.50)
    view(d, "assembled-same-members", 0, 120, 47, 0.57)
    d.group("separation-guide")
    # One illustrative assembly-motion arrow, kept clear of the members.
    d.arrow(73, 69, 48)
    d.text(76, 75, "Lift B", 3.0, MUTED, "end")
    d.endgroup()
    d.group("centre-section-same-joint")
    d.text(86, 68.5, "(c) Same joint: centre section", 3.3)
    d.text(86, 73, "Crossing only · y = 0", 2.9, MUTED)
    left, right, top, middle, bottom = 87, 114.5, 76, 87, 98
    d.polygon([(left, middle), (right, middle), (right, bottom), (left, bottom)], PALETTE["A"][2])
    d.polygon([(left, top), (right, top), (right, middle), (left, middle)], PALETTE["B"][2])
    d.text((left + right) / 2, 83, "B", 4.0, INK, "middle")
    d.text((left + right) / 2, 94, "A", 4.0, INK, "middle")
    for y in (top, middle, bottom):
        d.line([(right, y), (119, y)], EDGE, 0.23)
    d.text(121, 77, "Flush top · z = 16", 2.9)
    d.text(121, 88, "Contact · z = 8", 2.9)
    d.text(121, 99, "Flush base · z = 0", 2.9)
    d.endgroup()
    d.finish()
    caption = (
        "Constructed geometry demonstration of a perpendicular cross-lap joint. "
        "The same two members appear in all three views: A (teal), 100 mm along x, and B (ochre), 80 mm along y; both are 20 mm wide and 16 mm thick. "
        "(a) B is raised vertically only to expose the complementary through-width notches: the central upper 8 mm is removed from A and the central lower 8 mm from B. "
        "(b) In assembly, the overall top and bottom surfaces of both members are flush at z = 16 and z = 0 mm. "
        "(c) An enlarged section through the 20 mm crossing at y = 0 shows A occupying z = 0–8 mm and B occupying z = 8–16 mm, meeting at z = 8 mm without volume overlap. "
        "Ideal contact has zero clearance; manufacturing tolerances are unspecified. Projections are not to scale. This fixture specifies geometry only and provides no test or strength evidence.\n"
    )
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    subprocess.run([str(PDFTOPPM), "-png", "-singlefile", "-r", "300", str(out / "figure.pdf"), str(out / "figure")], check=True)
    print(f"Wrote original editable SVG, PDF, 300 dpi PNG, and caption to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--pdftoppm", type=Path, required=True)
    args = parser.parse_args()
    FONT, PDFTOPPM = args.font, args.pdftoppm
    destination = args.out
    destination.mkdir(exist_ok=False)
    draw(destination)
