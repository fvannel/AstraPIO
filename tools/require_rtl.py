"""Block hardware workflows until the complete intended RTL is explicitly enabled."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
status = json.loads((root / "design_status.json").read_text())
if not (
    status["stage"] == "rtl_implemented"
    and status["functional_rtl_implemented"]
    and status["rtl_simulation_passed"]
):
    raise SystemExit(
        "BLOCKED: incomplete PIO prototype. Complete and verify the intended RTL "
        "before enabling hardware workflows. Local development/synthesis remains possible."
    )
print("RTL development gate passed; physical validation is still required.")
