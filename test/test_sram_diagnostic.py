"""The diagnostic must never turn a crash or absent report into a DRC pass."""

import unittest

from tools.sram_diagnostic import assess_magic, assess_precheck


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


if __name__ == "__main__":
    unittest.main()
