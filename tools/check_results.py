"""Fail a test run for missing/empty results, failures, errors or skipped tests."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("test/results.xml")
root = ET.parse(path).getroot()
tests = list(root.iter("testcase"))
bad = [test.attrib.get("name", "?") for test in tests
       if any(test.find(tag) is not None for tag in ("failure", "error", "skipped"))]
if not tests or bad:
    raise SystemExit(f"FAILED: {len(tests)} tests; failing or skipped: {bad}")
print(f"PASS: {len(tests)} RTL tests, no failures/errors/skips.")
