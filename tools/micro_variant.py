"""Materialize one controlled experimental configuration; never a release."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

VARIANTS = {"baseline": 0, "setdir": 1, "jin": 2, "outmsb": 4,
            "wrap": 8, "rx4": 16, "event": 32, "capture": 64,
            "burst": 128, "isa": 15}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("variant", choices=VARIANTS)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "src/project.v"
    value = VARIANTS[args.variant]
    updated, count = re.subn(r"localparam integer STUDY_FEATURES = \d+;",
                            f"localparam integer STUDY_FEATURES = {value};", source.read_text())
    if count != 1:
        raise SystemExit("Missing or ambiguous experimental selector")
    source.write_text(updated)
    evidence = root / "work/micro" / args.variant
    evidence.mkdir(parents=True, exist_ok=True)
    manifest = {"variant": args.variant, "features": value, "release_approved": False,
                "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted((root / "src").glob("*.v"))}}
    (evidence / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest))

if __name__ == "__main__":
    main()
