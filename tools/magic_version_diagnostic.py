#!/usr/bin/env python3
"""Compare unmodified Magic versions. Diagnostic only, never a release gate override."""

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import urllib.request

from tools.diagnostic.make_control import write_control
from tools.sram_diagnostic import (
    HASHES, MACRO, OLD_PDK, PDK_VERSION, TOP, assess_magic_staged,
    invoke, read_optional, sha256, verify,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--ref", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    work = args.work.resolve()
    work.relative_to(root)
    out = work / "evidence"
    out.mkdir(parents=True, exist_ok=False)
    inputs = work / "inputs"
    inputs.mkdir(exist_ok=True)
    binary, source = args.binary.resolve(), args.source.resolve()
    env = dict(os.environ, PDK_ROOT=str(work / "pdk"), PDK="ihp-sg13g2")
    pdk = work / "pdk/ihp-sg13g2"
    tech = pdk / "libs.tech/magic"
    if (pdk / "SOURCES").read_text().strip() != f"IHP-Open-PDK {PDK_VERSION}":
        raise ValueError("Unexpected Ciel PDK")
    version = subprocess.check_output([str(binary), "--version"], env=env, text=True).strip()
    source_ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if version != args.version or source_ref != args.ref:
        raise ValueError(f"Unexpected Magic version/source: {version} / {source_ref}")
    subprocess.run(["git", "diff", "--exit-code", "HEAD"], cwd=source, check=True)
    submitted_files = list((work / "submission").rglob(TOP + ".gds"))
    if len(submitted_files) != 1:
        raise ValueError("Expected exactly one submitted GDS")
    submitted = submitted_files[0]
    old_macro = inputs / (MACRO + ".gds")
    url = f"https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/{OLD_PDK}/ihp-sg13g2/libs.ref/sg13g2_sram/gds/{MACRO}.gds"
    with urllib.request.urlopen(url, timeout=60) as response:
        old_macro.write_bytes(response.read())
    new_macro = pdk / f"libs.ref/sg13g2_sram/gds/{MACRO}.gds"
    checked = {}
    for name, path in (("submitted", submitted), ("old_macro", old_macro), ("new_macro", new_macro)):
        checked[name] = {"path": str(path.relative_to(root)), "sha256": verify(path, HASHES[name])}
    controls = []
    for name, negative in (("control-positive", False), ("control-negative", True)):
        gds = inputs / f"{name}.gds"
        write_control(gds, negative=negative)
        checked[name] = {"sha256": sha256(gds)}
        controls.append((name, gds, "astra_metal_control", "violations" if negative else "pass"))
    for name in ("read_sram_gds.tcl", "ihp-sg13g2.tech", "ihp-sg13g2-drc.tech", "ihp-sg13g2.magicrc"):
        checked[name] = {"sha256": sha256(tech / name)}
    provenance = {"scope": "Magic version diagnostic; not signoff or submission",
                  "magic_version": version, "magic_source": source_ref,
                  "platform": platform.platform(), "machine": platform.machine(),
                  "pdk": PDK_VERSION, "inputs": checked,
                  "submission_run": 35328977063, "submission_artifact": 10540429315}
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    cases = controls + [("old-macro", old_macro, MACRO, "pass"),
                        ("new-macro", new_macro, MACRO, "pass"),
                        ("submitted-gds", submitted, TOP, "pass")]
    results = {}
    for name, gds, top, expected in cases:
        case = out / name
        case.mkdir()
        case_env = dict(env, ASTRA_INPUT=str(gds), ASTRA_TOP=top,
                        ASTRA_REPORT=str(case / "counts.tsv"),
                        ASTRA_RAW_REPORT=str(case / "violations.tcl"),
                        ASTRA_FLATGLOB=str(tech / "read_sram_gds.tcl"))
        print(f"BEGIN Magic {version}: {name} (expected {expected})", flush=True)
        command = ["/usr/bin/time", "-v", "-o", str(case / "resources.txt"),
                   "timeout", "--kill-after=10", "180", str(binary), "-dnull", "-noconsole",
                   "-rcfile", str(tech / "ihp-sg13g2.magicrc"),
                   str(root / "tools/diagnostic/check_magic.tcl")]
        code = invoke(command, case, case_env, case / "magic.log", timeout=220)
        result = assess_magic_staged(code, read_optional(case / "counts.tsv"),
                                     (case / "magic.log").read_text())
        result["expected_status"] = expected
        result["expectation_met"] = result["status"] == expected
        results[name] = result
        (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        print(f"END {name}: {result['status']}, errors={result['errors']}", flush=True)
    lines = [f"# Magic {version} — independent diagnostic", "",
             "Unchanged rules and GDS; no merge, submission, exclusions or checker bypass.",
             "The negative control is intentionally invalid; real layouts must have zero errors.", "",
             "| Circuit | Status | Errors | Expected |", "|---|---|---|---|"]
    lines.extend(f"| {name} | {r['status']} | {r['errors']} | {r['expected_status']} |"
                 for name, r in results.items())
    summary = "\n".join(lines) + "\n"
    (out / "SUMMARY.md").write_text(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as stream:
            stream.write(summary)
    return 0 if all(r["expectation_met"] for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
