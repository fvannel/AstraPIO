"""Avoid building/publishing fabrication artifacts for an inert scaffold."""

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
        "BLOCKED: inert scaffold. Implement and verify the PIO before building hardware."
    )
print("RTL development gate passed; physical validation is still required.")
