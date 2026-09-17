"""Dependency-free structural checks. This does NOT simulate or synthesize RTL."""

import ast
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
info = (root / "info.yaml").read_text()
top = re.search(r'^\s+top_module:\s+"([^"]+)"', info, re.M).group(1)
assert re.fullmatch(r"tt_um_[a-zA-Z0-9_]+", top)
rtl = (root / "src/project.v").read_text()
tb = (root / "test/tb.v").read_text()
assert re.search(rf"\bmodule\s+{top}\s*\(", rtl)
assert re.search(rf"\b{top}\s+user_project\s*\(", tb)
assert len(re.findall(r"^  (?:ui|uo|uio)\[\d\]:", info, re.M)) == 24
for group in ("ui", "uo", "uio"):
    for index in range(8):
        assert len(re.findall(rf"^  {group}\[{index}\]:", info, re.M)) == 1
assert re.search(r'^\s+tiles:\s+"1x2"', info, re.M)
assert '"project.v"' in info
assert "PROJECT_SOURCES = project.v" in (root / "test/Makefile").read_text()
status = json.loads((root / "design_status.json").read_text())
assert status["stage"] == "scaffold"
assert not status["functional_rtl_implemented"]
for source in list((root / "test").glob("*.py")) + list((root / "tools").glob("*.py")):
    ast.parse(source.read_text(), filename=str(source))
for name in ("gds", "fpga"):
    workflow = (root / f".github/workflows/{name}.yaml").read_text()
    assert "tools/require_rtl.py" in workflow
    assert "@ttihp26b" in workflow
    assert not re.search(r"^  push:", workflow, re.M)
print("PASS: scaffold structure, module names, 24 pin labels, Python syntax and hardware guards.")
print("NOT CHECKED: RTL simulation, PIO behavior, memory capacity, area, timing or GDS.")
