from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "src" / "my_world" / "worlds" / "indoor.world"


def load_box_spans():
    world = ET.parse(WORLD).getroot().find("world")
    spans = {}
    for model in world.findall("model"):
        name = model.attrib["name"]
        box = model.find(".//collision/geometry/box")
        if box is None:
            continue

        pose = [float(value) for value in model.findtext("pose").split()]
        size = [float(value) for value in box.findtext("size").split()]
        x, y = pose[0], pose[1]
        sx, sy = size[0], size[1]
        spans[name] = {
            "x": (x - sx / 2.0, x + sx / 2.0),
            "y": (y - sy / 2.0, y + sy / 2.0),
        }
    return spans


def axis_gap(first_span, second_span):
    if first_span[1] < second_span[0]:
        return second_span[0] - first_span[1]
    if second_span[1] < first_span[0]:
        return first_span[0] - second_span[1]
    return 0.0


class WorldGeometryTest(unittest.TestCase):
    def test_staggered_channel_corner_wall_segments_are_joined(self):
        spans = load_box_spans()
        connected_corners = [
            ("heng_top_a", "heng_right"),
            ("heng_top_b", "heng_left"),
            ("heng_bottom_a", "heng_right"),
            ("heng_bottom_b", "heng_left"),
        ]

        for horizontal, vertical in connected_corners:
            with self.subTest(horizontal=horizontal, vertical=vertical):
                x_gap = axis_gap(spans[horizontal]["x"], spans[vertical]["x"])
                y_gap = axis_gap(spans[horizontal]["y"], spans[vertical]["y"])

                self.assertLessEqual(x_gap, 0.001)
                self.assertLessEqual(y_gap, 0.001)


if __name__ == "__main__":
    unittest.main()
