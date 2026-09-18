"""Fail closed if the known provisional DRC bypasses return to the release flow.

These are configuration guardrails, not physical verification or a general YAML
security analyzer. The official checkers must still run on the produced layout.
"""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleasePolicyTest(unittest.TestCase):
    def test_magic_errors_are_fatal(self):
        config = json.loads((ROOT / "src/config.json").read_text())
        self.assertIs(config.get("ERROR_ON_MAGIC_DRC"), True)
        for key, value in config.items():
            if key.startswith("ERROR_ON_"):
                with self.subTest(setting=key):
                    self.assertNotEqual(value, False)

    def test_precheck_cannot_continue_after_failure(self):
        workflow = (ROOT / ".github/workflows/gds.yaml").read_text()
        self.assertNotRegex(workflow, r"(?m)^\s*continue-on-error\s*:")
        self.assertIn("uses: TinyTapeout/tt-gds-action/precheck@ttihp26b", workflow)
        self.assertNotIn("tools/provisional_precheck.py", workflow)

    def test_release_checks_its_policy_before_building(self):
        workflow = (ROOT / ".github/workflows/gds.yaml").read_text()
        gate = "python3 -m unittest discover -s test -p test_release_policy.py"
        self.assertIn(gate, workflow)
        self.assertLess(workflow.index(gate), workflow.index("name: Build GDS"))

    def test_future_exceptions_are_not_authorized(self):
        status = json.loads((ROOT / "design_status.json").read_text())
        self.assertIs(status.get("magic_drc_nonblocking_authorized"), False)
        self.assertIs(status.get("provisional_sram_precheck_nonblocking_authorized"), False)

    def test_compact_build_has_no_sram_or_custom_timing_deck(self):
        config = json.loads((ROOT / "src/config.json").read_text())
        for key in ("MACROS", "PNR_SDC_FILE", "SIGNOFF_SDC_FILE", "EXTRA_SDC_FILES"):
            self.assertNotIn(key, config)
        sources = (ROOT / "info.yaml").read_text()
        self.assertNotIn('"pio_sram.v"', sources)
        self.assertNotIn('"sram_blackbox.v"', sources)
        for key in ("RUN_KLAYOUT_DRC", "RUN_KLAYOUT_XOR", "RUN_CTS"):
            self.assertTrue(config[key], key)
        workflow = (ROOT / ".github/workflows/gds.yaml").read_text()
        self.assertIn("tools-ref: 01d5d2814fa9dd61e9d211e0b235a4a592a9316a", workflow)
        self.assertNotIn("deploy-pages", workflow)

    def test_cell_models_and_status_use_exact_shuttle_pdk(self):
        expected = "c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c"
        status = json.loads((ROOT / "design_status.json").read_text())
        self.assertEqual(status["pdk_version"], expected)
        workflow = (ROOT / ".github/workflows/test.yaml").read_text()
        self.assertIn("ref: " + expected, workflow)
        self.assertIn("iverilog_13.0-1_amd64.deb", workflow)


if __name__ == "__main__":
    unittest.main()
