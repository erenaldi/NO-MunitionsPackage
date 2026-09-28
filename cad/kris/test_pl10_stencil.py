"""Regression tests for compare_pl10_stencil.compare().

Synthetic tiny images and traces only; no CAD sources or real renders.
The render is stored as the reference silhouette rotated 90 degrees CCW,
because compare() rotates the snapshot render clockwise (ROTATE_270) to put
the nose at right before masking.
"""

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from compare_pl10_stencil import compare

TEMP_PARENT = Path(r"C:\Users\erena\AppData\Local\Temp\opencode")


def make_trace(body_top, body_bottom, length=160, nose=20, canvas=(220, 100)):
    """Horizontal missile trace: rectangular body + triangular nose, nose right."""
    x0, y0 = 20, body_top
    x1 = x0 + length
    center = (y0 + body_bottom) // 2
    body = [[x0, y0], [x1, y0], [x1, body_bottom], [x0, body_bottom]]
    nose_poly = [[x1, y0], [x1 + nose, center], [x1, body_bottom]]
    return {
        "canvas": list(canvas),
        "axis": [[x0, center], [x1, center]],
        "silhouette_polygons": {"body": body, "nose": nose_poly},
        "feature_lines": {},
        "uncertainty_pixels": 3,
    }


def draw_silhouette(trace):
    image = Image.new("L", tuple(trace["canvas"]), 255)
    draw = ImageDraw.Draw(image)
    for polygon in trace["silhouette_polygons"].values():
        draw.polygon([tuple(p) for p in polygon], fill=0)
    return image


def make_render(trace, path):
    """Snapshot-camera-style render: silhouette vertical, nose up."""
    draw_silhouette(trace).transpose(Image.Transpose.ROTATE_90).convert("RGB").save(path)
    return path


class ComparePl10StencilTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=TEMP_PARENT)

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_silhouette_yields_iou_near_one(self):
        trace = make_trace(body_top=40, body_bottom=60)
        render_path = Path(self.tmp.name) / "render.png"
        output_path = Path(self.tmp.name) / "overlay.png"
        make_render(trace, render_path)

        result = compare(str(render_path), trace, str(output_path))

        self.assertGreaterEqual(result["manual_trace_iou"], 0.99)
        self.assertTrue(output_path.exists())
        self.assertGreater(output_path.stat().st_size, 0)
        self.assertEqual(result["overlay"], str(output_path))

    def test_incorrect_body_thickness_is_penalized(self):
        trace = make_trace(body_top=40, body_bottom=60)
        thick_trace = make_trace(body_top=35, body_bottom=65)
        render_path = Path(self.tmp.name) / "thick_render.png"
        output_path = Path(self.tmp.name) / "thick_overlay.png"
        make_render(thick_trace, render_path)

        result = compare(str(render_path), trace, str(output_path))

        # Uniform width scaling cannot hide a 50% thicker body: IoU must drop.
        self.assertLess(result["manual_trace_iou"], 0.8)
        self.assertTrue(output_path.exists())
        self.assertGreater(output_path.stat().st_size, 0)

    def test_empty_render_is_rejected(self):
        trace = make_trace(body_top=40, body_bottom=60)
        render_path = Path(self.tmp.name) / "blank.png"
        Image.new("RGB", (100, 100), "white").save(render_path)

        with self.assertRaisesRegex(ValueError, "No CAD silhouette"):
            compare(str(render_path), trace, str(Path(self.tmp.name) / "unused.png"))

    def test_empty_trace_is_rejected(self):
        trace = make_trace(body_top=40, body_bottom=60)
        trace["silhouette_polygons"] = {}
        render_path = Path(self.tmp.name) / "render.png"
        make_render(make_trace(body_top=40, body_bottom=60), render_path)

        with self.assertRaisesRegex(ValueError, "Empty manual reference trace"):
            compare(str(render_path), trace, str(Path(self.tmp.name) / "unused.png"))


if __name__ == "__main__":
    unittest.main()