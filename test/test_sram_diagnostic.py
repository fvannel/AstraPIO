"""The diagnostic must never turn a crash or absent report into a DRC pass."""

import unittest
import contextlib
import io
from pathlib import Path

from tools.sram_diagnostic import assess_magic, assess_magic_staged, assess_precheck
from tools.magic_version_diagnostic import parse_args


class MagicResultTest(unittest.TestCase):
    def test_complete_zero_is_pass(self):
        self.assertEqual(assess_magic(0, "TOTAL\t0\n")["status"], "pass")

    def test_crash_overrides_even_a_zero_report(self):
        for code in (139, -11, 124, 137, 1):
            with self.subTest(code=code):
                self.assertNotEqual(assess_magic(code, "TOTAL\t0\n")["status"], "pass")

    def test_missing_or_malformed_report_is_not_zero(self):
        for report in (None, "", "TOTAL\t-1\n", "TOTAL\t0\nTOTAL\t0\n", "junk\nTOTAL\t0\n"):
            with self.subTest(report=report):
                self.assertNotEqual(assess_magic(0, report)["status"], "pass")

    def test_violations_fail_even_if_process_returns_zero(self):
        for code in (0, 1):
            result = assess_magic(code, "2\tCnt.c\nTOTAL\t2\n")
            self.assertEqual(result["status"], "violations")
            self.assertEqual(result["errors"], 2)

    def test_inconsistent_counts_fail(self):
        self.assertNotEqual(assess_magic(0, "2\tCnt.c\nTOTAL\t0\n")["status"], "pass")


class PrecheckResultTest(unittest.TestCase):
    @staticmethod
    def report(count=10, extra=""):
        return '<testsuites><testsuite>' + ''.join(
            f'<testcase name="check-{i}">{extra if i == 0 else ""}</testcase>'
            for i in range(count)
        ) + '</testsuite></testsuites>'

    def test_ten_completed_tests_pass(self):
        self.assertEqual(assess_precheck(0, self.report())["status"], "pass")

    def test_incomplete_crashed_or_failed_checks_fail(self):
        for code, report in (
            (1, self.report()), (124, self.report()), (0, None), (0, ""),
            (0, self.report(9)), (0, self.report(extra="<failure/>")),
            (0, self.report(extra="<error/>")), (0, self.report(extra="<skipped/>")),
        ):
            with self.subTest(code=code, report=report):
                self.assertNotEqual(assess_precheck(code, report)["status"], "pass")


class InstrumentedMagicTest(unittest.TestCase):
    def test_completed_check_is_required(self):
        complete = "ASTRA_STAGE list_results END 2ms\nASTRA_DRC_GLOBAL 0\nASTRA_DRC_COMPLETE 0\n"
        self.assertEqual(assess_magic_staged(0, "TOTAL\t0\n", complete)["status"], "pass")
        for log in ("", "ASTRA_STAGE drc_catchup BEGIN 123\n",
                    "ASTRA_STAGE list_results END 2ms\n",
                    "ASTRA_STAGE list_results END 2ms\nASTRA_DRC_COMPLETE 1\n"):
            with self.subTest(log=log):
                self.assertNotEqual(assess_magic_staged(0, "TOTAL\t0\n", log)["status"], "pass")

    def test_stage_progress_does_not_hide_crash_or_violations(self):
        log = "ASTRA_STAGE list_results END 2ms\nASTRA_DRC_GLOBAL 1\nASTRA_DRC_COMPLETE 2\n"
        self.assertEqual(assess_magic_staged(1, "2\tCnt.c\nTOTAL\t2\n", log)["status"], "violations")
        self.assertEqual(assess_magic_staged(139, None, log)["status"], "process_error")

    def test_global_error_cannot_be_hidden_by_report_window(self):
        for count in (None, 1):
            log = "ASTRA_STAGE list_results END 2ms\nASTRA_DRC_COMPLETE 0\n"
            if count is not None:
                log += f"ASTRA_DRC_GLOBAL {count}\n"
            self.assertNotEqual(assess_magic_staged(0, "TOTAL\t0\n", log)["status"], "pass")


class DiagnosticBudgetTest(unittest.TestCase):
    BASE = ["--work", "work/probe", "--binary", "magic", "--source", "source",
            "--version", "8.3.684", "--ref", "pinned-ref"]

    def test_default_comparison_is_preserved(self):
        args = parse_args(self.BASE)
        self.assertEqual(args.timeout_seconds, 180)
        self.assertEqual(args.target, "all")

    def test_ten_minute_targeted_probe(self):
        args = parse_args(self.BASE + ["--timeout-seconds", "600", "--target", "submitted-gds"])
        self.assertEqual(args.timeout_seconds, 600)
        self.assertEqual(args.target, "submitted-gds")

    def test_unbounded_budget_and_unknown_target_are_rejected(self):
        for extra in (["--timeout-seconds", "0"], ["--timeout-seconds", "3600"],
                      ["--target", "unknown"]):
            with self.subTest(extra=extra), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    parse_args(self.BASE + extra)

    def test_workflow_does_not_override_magics_build_variables(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/magic-version-diagnostic.yaml").read_text()
        self.assertNotRegex(workflow, r"(?m)^\s+MAGIC_VERSION:")
        self.assertIn("ASTRA_MAGIC_VERSION:", workflow)


if __name__ == "__main__":
    unittest.main()
