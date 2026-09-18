"""Fail-closed tests for the explicitly authorized provisional SRAM exception."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from provisional_precheck import evaluate


class ProvisionalPrecheckTest(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).parent / "fixtures" / "precheck"
        self.junit = ET.parse(base / "results.xml").getroot()
        self.drc = ET.parse(base / "drc_sg13g2.xml").getroot()

    def check(self, outcome="failure"):
        return evaluate(self.junit, self.drc, outcome)

    def test_exact_official_baseline_is_nonblocking_not_passed(self):
        self.assertEqual(self.check(), "authorized_sram_exception")

    def test_item_order_is_irrelevant(self):
        items = self.drc.find("items")
        items[:] = list(reversed(items))
        self.assertEqual(self.check(), "authorized_sram_exception")

    def test_generated_sram_namespace_changes_between_identical_builds(self):
        # Real run 35326459266 differs from the baseline ONLY by RT_ -> YH_.
        # Exercise the complete report, including every geometry and orientation.
        for cell in self.drc.findall("items/item/cell"):
            self.assertTrue(cell.text.startswith("RT_"))
            cell.text = "YH_" + cell.text[3:]
        self.assertEqual(self.check(), "authorized_sram_exception")

    def test_mixed_sram_namespaces_are_blocking(self):
        cell = self.drc.find("items/item/cell")
        cell.text = "YH_" + cell.text[3:]
        with self.assertRaises(ValueError):
            self.check()

    def test_real_cell_name_change_stays_blocking(self):
        cell = self.drc.find("items/item/cell")
        cell.text += "_CHANGED"
        with self.assertRaises(ValueError):
            self.check()

    def test_other_check_failure_is_blocking(self):
        ET.SubElement(self.junit.find(".//testcase"), "error", message="new failure")
        with self.assertRaises(ValueError):
            self.check()

    def test_changed_geometry_is_blocking(self):
        value = self.drc.find("items/item/values/value")
        value.text += " CHANGED"
        with self.assertRaises(ValueError):
            self.check()

    def test_changed_cell_is_blocking(self):
        self.drc.find("items/item/cell").text = "different_cell"
        with self.assertRaises(ValueError):
            self.check()

    def test_changed_category_is_blocking(self):
        self.drc.find("items/item/category").text = "'Other.rule'"
        with self.assertRaises(ValueError):
            self.check()

    def test_changed_count_is_blocking(self):
        self.drc.find("items").remove(self.drc.find("items/item"))
        with self.assertRaises(ValueError):
            self.check()

    def test_missing_test_is_blocking(self):
        self.junit.find("testsuite").remove(self.junit.find(".//testcase"))
        with self.assertRaises(ValueError):
            self.check()

    def test_duplicate_test_is_blocking(self):
        cases = self.junit.findall(".//testcase")
        cases[0].set("name", cases[1].get("name"))
        with self.assertRaises(ValueError):
            self.check()

    def test_skipped_test_is_blocking(self):
        ET.SubElement(self.junit.find(".//testcase"), "skipped")
        with self.assertRaises(ValueError):
            self.check()

    def test_missing_or_inconsistent_outcome_is_blocking(self):
        for outcome in ("", "skipped", "cancelled", "success"):
            with self.subTest(outcome=outcome), self.assertRaises(ValueError):
                self.check(outcome)

    def test_legitimate_all_pass_does_not_use_exception(self):
        failed = self.junit.find(".//testcase/error/..")
        failed.remove(failed.find("error"))
        self.drc.find("items").clear()
        self.assertEqual(self.check("success"), "passed")
        with self.assertRaises(ValueError):
            self.check("failure")

    def test_wrong_module_is_blocking(self):
        self.drc.find("top-cell").text = "another_project"
        with self.assertRaises(ValueError):
            self.check()


if __name__ == "__main__":
    unittest.main()
