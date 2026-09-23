"""Check retained file identities, not functionality or physical signoff."""

import hashlib
import json
import sys
from pathlib import Path


# Exact editorial edits, not a general comment-stripping or hash exemption.
# Original copies retain the unchanged manifest hashes. Replaying only these
# replacements must reproduce every byte of each current source file.
EDITORIAL_UPDATES = {
    "info.yaml": (
        ('  author:       "Fabien" # Confirm public attribution before publishing.\n',
         '  author:       "Fabien"\n'),
        ('  description:  "General-purpose programmable IO prototype; not ready for tapeout"\n',
         '  description:  "Programmable PIO and autonomous timed I/O coprocessor (ABI 5)"\n'),
        ('  clock_hz:     50000000 # Exploratory target, not verified.\n',
         '  clock_hz:     50000000 # Reference clock; board and silicon characterization pending.\n'),
        ('  # Two-tile area target; final fit must be measured with the IHP flow.\n',
         '  # Accepted block allocation: 1x2 tiles.\n'),
        ('  top_module:  "tt_um_fabien_pio" # Provisional; confirm uniqueness before submission.\n',
         '  top_module:  "tt_um_fabien_pio" # Top module of the accepted ABI 5 layout.\n'),
    ),
    "src/project.v": (
        ('// General-purpose PIO prototype. The target frequency and tile fit are unproven.\n',
         '// AstraPIO ABI 5: programmable PIO and independent timed pulse-I/O engine.\n'),
    ),
    "src/pio_spi.v": (
        ('// Oversampling, not a separate SCK clock domain. See docs/compact-v3.md for limits.\n',
         '// Oversampling, not a separate SCK clock domain. See docs/reference.md for limits.\n'),
    ),
    "firmware/pio_timed.h": (
        ('/* EXPERIMENTAL: requires timed extension identity 0x5449 / version 0x0118.\n'
         ' * This extension is NOT present in the submitted compact 946648ff chip.\n',
         '/* AstraPIO ABI 5 timed engine: identity 0x5449 / version 0x0118.\n'
         " * Configure pulse timing and routing for the application's input stream.\n"),
    ),
}


def bounded_path(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Invalid path: {name}")
    return path


def check(root):
    manifest = json.loads((root / "release/manifest.json").read_text())
    if manifest["schema_version"] != 1:
        raise ValueError("Unsupported release manifest")
    if not EDITORIAL_UPDATES.keys() <= manifest["reference_files"].keys():
        raise ValueError("Editorial originals missing from frozen reference manifest")
    count = 0
    for section in ("reference_files", "artifacts", "vendor_files"):
        entries = manifest[section]
        if not entries:
            raise ValueError(f"Empty manifest section: {section}")
        for name, expected in entries.items():
            path = bounded_path(root, name)
            editorial = section == "reference_files" and name in EDITORIAL_UPDATES
            reference = (bounded_path(root, "release/reference-text/" + name)
                         if editorial else path)
            original = reference.read_bytes()
            actual = hashlib.sha256(original).hexdigest()
            if actual != expected:
                raise ValueError(f"File differs from frozen release: {name}")
            if editorial:
                reconstructed = original
                for before, after in EDITORIAL_UPDATES[name]:
                    before, after = before.encode(), after.encode()
                    if reconstructed.count(before) != 1:
                        raise ValueError(f"Editorial replacement is not unique: {name}")
                    reconstructed = reconstructed.replace(before, after, 1)
                if path.read_bytes() != reconstructed:
                    raise ValueError(f"File differs from exact editorial update: {name}")
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
    print(f"PASS: {count} frozen identities verified; source {manifest['reference_commit']}.")
    print(f"PASS: {len(EDITORIAL_UPDATES)} current files match their exact editorial updates.")
    print("Identity check only: no new simulation, physical signoff or submission.")


if __name__ == "__main__":
    try:
        check(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
