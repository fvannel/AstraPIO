"""Fail-closed evidence validation, separate from actual pin-level simulation."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_ws2812_release import validate_report


class Ws2812EvidenceTest(unittest.TestCase):
    def valid_report(self, mode="rtl"):
        frames = []
        for seed in (0x00FFFE, 0xFFFFFE):
            counter = seed
            for request in (True, False, True, True, False, False):
                following = (counter + int(request)) & 0xFFFFFF
                frames.append({"status": "PASS", "counter_seed_hex": f"{seed:06X}",
                    "din_prefix_hex": "123456", "spi_rx_hex": "123456",
                    "dout_prefix_hex": f"{counter:06X}", "tail_in_hex": "AB"*12,
                    "tail_out_hex": "AB"*12, "increment_requested": request,
                    "next_counter_hex": f"{following:06X}"})
                counter = following
        return {"status": "PASS", "mode": mode, "source_commit": "a"*40,
            "source_sha256": {"source.v": "b"*64}, "expected_abi": 0x600,
            "concurrent_pio_program": "OUTMSB_toggle", "asic_clock_hz": 50000000,
            "frame_count": 12, "checked_output_bits": 1440, "frames": frames,
            "routed_netlist_sha256": "c"*64 if mode == "gl" else None}

    def check(self, data, mode="rtl"):
        validate_report(data, mode, "a"*40, {"source.v": "b"*64},
                        "c"*64 if mode == "gl" else None)

    def test_accepts_complete_exact_evidence(self):
        self.check(self.valid_report())
        self.check(self.valid_report("gl"), "gl")

    def test_rejects_wrong_or_stale_build(self):
        for field, value in (("status", "FAIL"), ("source_commit", "d"*40),
                             ("source_sha256", {}), ("expected_abi", 0x500),
                             ("frame_count", 0), ("checked_output_bits", 1439),
                             ("concurrent_pio_program", "legacy"), ("mode", "gl")):
            data = self.valid_report()
            data[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): self.check(data)
        data = self.valid_report("gl")
        data["routed_netlist_sha256"] = "d"*64
        with self.assertRaises(ValueError): self.check(data, "gl")

    def test_rejects_missing_capture_corrupted_tail_or_counter(self):
        original = self.valid_report()
        for field in ("spi_rx_hex", "tail_out_hex", "dout_prefix_hex", "next_counter_hex"):
            data = copy.deepcopy(original)
            data["frames"][2][field] = "000000"
            with self.subTest(field=field), self.assertRaises(ValueError): self.check(data)
        original["frames"].pop()
        with self.assertRaises(ValueError): self.check(original)
