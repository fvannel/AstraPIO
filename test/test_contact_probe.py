"""Exact geometry guards for a non-production experiment, not physical DRC."""

import struct
import unittest

from tools.diagnostic.contact_probe import recenter, TARGETS, DELAY, CORNER


def record(kind, payload=b"", dtype=0):
    return struct.pack(">HBB", len(payload) + 4, kind, dtype) + payload


def fixture(prefix=""):
    data = bytearray()
    for name, shapes in TARGETS.items():
        encoded = (prefix + name).encode()
        encoded += b"\0" * (len(encoded) % 2)
        data += record(0x06, encoded, 6)
        for (x0, y0, x1, y1), _ in shapes:
            data += record(0x08)
            data += record(0x0D, struct.pack(">h", 6), 2)
            data += record(0x0E, struct.pack(">h", 0), 2)
            data += record(0x10, struct.pack(">10i", x0, y0, x1, y0, x1, y1, x0, y1, x0, y0), 3)
            data += record(0x11)
        data += record(0x07)
    return bytes(data)


class ContactProbeTest(unittest.TestCase):
    def test_individual_experiments_only_touch_target_cell(self):
        for variant, name, count in (("delay", DELAY, 3), ("corner", CORNER, 1)):
            source = fixture()
            changed, edits = recenter(source, variant)
            self.assertEqual(len(edits), count)
            self.assertEqual({e["cell"] for e in edits}, {name})
            self.assertEqual(len(changed), len(source))

    def test_both_is_exact_composition_and_reversible(self):
        source = fixture()
        both, edits = recenter(source, "both")
        delay, _ = recenter(source, "delay")
        combined, _ = recenter(delay, "corner")
        self.assertEqual(both, combined)
        restored = bytearray(both)
        for edit in edits:
            pos = edit["offset"]
            restored[pos:pos + edit["length"]] = bytes.fromhex(edit["before_hex"])
        self.assertEqual(bytes(restored), source)

    def test_prefixed_cells_require_explicit_prefix(self):
        with self.assertRaises(ValueError):
            recenter(fixture("JQ_"), "both")
        self.assertEqual(len(recenter(fixture("JQ_"), "both", "JQ_")[1]), 4)

    def test_reapplying_or_unknown_variant_fails(self):
        changed, _ = recenter(fixture(), "both")
        for data, variant in ((changed, "both"), (fixture(), "skip"), (b"", "both")):
            with self.assertRaises(ValueError):
                recenter(data, variant)

    def test_duplicate_missing_and_malformed_input_fail(self):
        source = fixture()
        for data in (source + source, source[:-1], b"\x00\x02\x06\x06"):
            with self.assertRaises(ValueError):
                recenter(data, "both")

    def test_only_zero_padding_after_endlib_is_accepted_and_preserved(self):
        padded = fixture() + record(0x04) + bytes(100)
        self.assertEqual(recenter(padded, "both")[0][-104:], padded[-104:])
        with self.assertRaises(ValueError):
            recenter(fixture() + record(0x04) + b"junk", "both")


if __name__ == "__main__":
    unittest.main()
