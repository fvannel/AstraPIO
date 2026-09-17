"""Block remote hardware workflows until RTL and an explicit release gate allow them."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
status = json.loads((root / "design_status.json").read_text())
if not (
    status["stage"] == "rtl_implemented"
    and status["functional_rtl_implemented"]
    and status["rtl_simulation_passed"]
    and status.get("hardware_workflows_enabled", False)
):
    raise SystemExit(
        "BLOCKED: remote hardware workflows are not enabled. Review the physical "
        "release blockers and authorize publication before changing this gate. "
        "Local development/synthesis remains possible."
    )
print("RTL development gate passed; physical validation is still required.")
