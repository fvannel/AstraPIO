"""Cross-library audit of the flat diagnostic witness, not a DRC waiver."""
import math
from pathlib import Path
import tempfile
import unittest
import gdstk
from tools.diagnostic.flatten_probe import flatten_verified


class FlattenProbeTest(unittest.TestCase):
    def test_array_paths_marker_layers_and_rotated_labels_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            lib = gdstk.Library(unit=1e-6, precision=1e-9)
            child = lib.new_cell("leaf")
            child.add(gdstk.rectangle((0, 0), (2, 2), layer=25))
            child.add(gdstk.FlexPath([(0.2, 0.4), (1.4, 0.4)], 0.2, layer=8))
            child.add(gdstk.Label("well", (0.3, 0.4), rotation=math.pi, layer=8, texttype=25))
            top = lib.new_cell("top")
            top.add(gdstk.Reference(child, rotation=math.pi * 1.5,
                                    columns=3, rows=2, spacing=(5, 4)))
            source, target = folder / "source.gds", folder / "flat.gds"
            lib.write_gds(source)
            original = source.read_bytes()
            result = flatten_verified(source, target, "top")
            self.assertEqual(result["result"], "pass")
            self.assertEqual(sum(x["label_count"] for x in result["layers"]), 6)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(len(gdstk.read_gds(target).cells), 1)


if __name__ == "__main__":
    unittest.main()
