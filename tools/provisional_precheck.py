"""Authorized submission policy, NOT a passing DRC result or foundry waiver.

Only the exact SRAM violation signatures from official run 35322726665 may be
nonblocking. The official action, JUnit XML and DRC reports remain unchanged.
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


EXPECTED_CHECKS = {
    "KLayout pin label overlapping drawing", "KLayout SG13G2 DRC",
    "KLayout zero area", "KLayout Checks", "Pin check", "Boundary check",
    "Layer check", "Cell name check", "Analog pin check", "Verilog syntax check",
}
EXPECTED_CATEGORIES = Counter({"'Sdiod.d'": 796, "'Sdiod.e'": 796,
                               "'Cnt.c.digibnd'": 176})
# Hash of sorted (category, cell, multiplicity, sorted geometry values).
# The tested GDS's SHA256 and original reports are recorded in the docs.
EXPECTED_SIGNATURE = "6e3e0f139182f47cd77e9cb095f350294e30e247d211040dfba8d281229a5aad"


def evaluate(junit, drc, outcome):
    """Return 'passed' or 'authorized_sram_exception'; reject all other states."""
    if outcome not in {"success", "failure"}:
        raise ValueError("Official precheck did not finish with a usable outcome")
    if junit.tag != "testsuites" or drc.tag != "report-database":
        raise ValueError("Unexpected report format")
    cases = junit.findall(".//testcase")
    names = [case.get("name") for case in cases]
    if len(names) != len(EXPECTED_CHECKS) or set(names) != EXPECTED_CHECKS:
        raise ValueError("Missing, duplicate or unexpected precheck tests")
    if junit.findall(".//skipped"):
        raise ValueError("Skipped prechecks are not permitted")
    failures = [(case.get("name"), child) for case in cases for child in case
                if child.tag in {"error", "failure"}]
    if len(failures) != len(junit.findall(".//error") + junit.findall(".//failure")):
        raise ValueError("Unexpected suite-level error")
    if drc.findtext("top-cell") != "tt_um_fabien_pio":
        raise ValueError("DRC report is for a different top module")
    items = drc.findall("items/item")
    if not failures:
        if outcome != "success" or items:
            raise ValueError("Official action and reports disagree")
        return "passed"
    if outcome != "failure" or len(failures) != 1:
        raise ValueError("Only the single documented SRAM failure is authorized")
    name, failure = failures[0]
    if (name != "KLayout SG13G2 DRC" or
            failure.get("message") != "Klayout sg13g2 failed with 1768 DRC violations"):
        raise ValueError("Failure is not the documented SRAM DRC result")
    if Counter(i.findtext("category") for i in items) != EXPECTED_CATEGORIES:
        raise ValueError("DRC counts/categories differ from the authorized baseline")
    signatures = sorted((i.findtext("category"), i.findtext("cell"),
                         i.findtext("multiplicity"),
                         tuple(sorted(v.text or "" for v in i.findall("values/value"))))
                        for i in items)
    fingerprint = hashlib.sha256(json.dumps(
        signatures, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()
    if fingerprint != EXPECTED_SIGNATURE:
        raise ValueError("DRC cell/geometry signatures differ from the authorized baseline")
    return "authorized_sram_exception"


def main():
    try:
        reports, outcome = Path(sys.argv[1]), sys.argv[2]
        result = evaluate(ET.parse(reports / "results.xml").getroot(),
                          ET.parse(reports / "drc_sg13g2.xml").getroot(), outcome)
    except (IndexError, OSError, ET.ParseError, ValueError, TypeError) as error:
        print(f"::error::Provisional submission blocked: {error}")
        return 1
    if result == "authorized_sram_exception":
        message = ("OFFICIAL PRECHECK FAILED: 1768 known SRAM violations. "
                   "User-authorized provisional nonblocking exception only. "
                   "9 other checks passed. NOT qualified for fabrication. "
                   "See the unchanged precheck_reports artifact and docs/provisional-submission.md.")
        print(f"::warning::{message}")
    else:
        message = "Official precheck passed; provisional SRAM exception was not used."
        print(message)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write("\n## Provisional submission policy\n\n" + message + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
