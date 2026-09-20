"""Check retained file identities, not functionality or physical signoff."""

import hashlib
import json
import sys
from pathlib import Path


def check(root):
    manifest = json.loads((root / "release/manifest.json").read_text())
    if manifest["schema_version"] != 1:
        raise ValueError("Unsupported release manifest")
    count = 0
    for section in ("reference_files", "artifacts", "vendor_files"):
        entries = manifest[section]
        if not entries:
            raise ValueError(f"Empty manifest section: {section}")
        for name, expected in entries.items():
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError(f"Invalid path: {name}")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError(f"File differs from frozen release: {name}")
            count += 1
    provenance = json.loads((root / "release/commit_id.json").read_text())
    pdk = json.loads((root / "release/pdk.json").read_text())
    status = json.loads((root / "design_status.json").read_text())
    if provenance["commit"] != manifest["reference_commit"]:
        raise ValueError("Submission/source mismatch")
    if pdk["PDK_VERSION"] != manifest["pdk_version"]:
        raise ValueError("PDK mismatch")
    if status["source_commit"] != manifest["reference_commit"]:
        raise ValueError("Status/source mismatch")
    print(f"PASS: {count} frozen files verified; source {manifest['reference_commit']}.")
    print("Identity check only: no new simulation, physical signoff or submission.")


if __name__ == "__main__":
    try:
        check(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
