#!/usr/bin/env python3
"""Read-only physical diagnostic; NOT a release or a substitute for TT signoff.

Run all independent probes and retain their original logs. Any failure makes
the entire diagnostic fail, even when another checker passes.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET


PDK_VERSION = "5e6d592e4002946a4616f798c357f0f3c06cf3b6"
OLD_PDK = "c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c"
TOOLS_REF = "01d5d2814fa9dd61e9d211e0b235a4a592a9316a"
MACRO = "RM_IHPSG13_1P_256x8_c3_bm_bist"
TOP = "tt_um_fabien_pio"
HASHES = {
    "submitted": "9368dfb687cbaf7a24e27f5b2ca6ca83eac38f7453b46e7047a7975839f3c240",
    "old_macro": "38ccf93cdc4ef0635aa008ef963fd10cabb82e7701f78f66b800b9e81561d634",
    "new_macro": "4aec8f3c5e2d827fcedf8d9967ba6d62b73fdfadb90d221d08c653b633dece08",
    "precheck": "373d64678888bab22b38bbb3751ecb04293d76a4c2a960766f1825f6e85a8c6a",
}


def assess_magic(returncode, report):
    result = {"status": "invalid_report", "returncode": returncode, "errors": None}
    if report is not None:
        lines = report.splitlines()
        if lines and re.fullmatch(r"TOTAL\t\d+", lines[-1]):
            total = int(lines[-1].split("\t")[1])
            categories = [re.fullmatch(r"(\d+)\t[^\t]+", line) for line in lines[:-1]]
            if all(categories) and sum(int(m[1]) for m in categories) == total:
                result["errors"] = total
                if total > 0 and returncode in (0, 1):
                    result["status"] = "violations"
                elif returncode == 0:
                    result["status"] = "pass"
    if returncode not in (0, 1) or (returncode != 0 and result["status"] != "violations"):
        result["status"] = "process_error"
    return result


def assess_magic_staged(returncode, report, log):
    """Require completion evidence, not merely a successful Tcl process exit."""
    result = assess_magic(returncode, report)
    result["stages"] = re.findall(r"^ASTRA_STAGE (\w+) (BEGIN|END) (\S+)$", log, re.M)
    complete = re.findall(r"^ASTRA_DRC_COMPLETE (\d+)$", log, re.M)
    global_count = re.findall(r"^ASTRA_DRC_GLOBAL (\d+)$", log, re.M)
    result["global_error_tiles"] = int(global_count[0]) if len(global_count) == 1 else None
    listed = re.search(r"^ASTRA_STAGE list_results END \d+ms$", log, re.M)
    if result["status"] in ("pass", "violations") and (
        not listed or complete != [str(result["errors"])] or len(global_count) != 1
        or (result["errors"] == 0 and global_count != ["0"])
    ):
        result["status"] = "invalid_report"
    return result


def assess_precheck(returncode, report):
    result = {"status": "invalid_report", "returncode": returncode, "tests": 0}
    if report:
        try:
            root = ET.fromstring(report)
            cases = root.findall(".//testcase")
            result["tests"] = len(cases)
            if any(element.tag in ("failure", "error", "skipped") for element in root.iter()):
                result["status"] = "check_failure"
            elif len(cases) == 10:
                result["status"] = "pass"
        except ET.ParseError:
            pass
    if returncode != 0:
        result["status"] = "process_error"
    return result


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path, expected):
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"Input hash mismatch: {path}: {actual} != {expected}")
    return actual


def read_optional(path):
    return path.read_text() if path.is_file() else None


def invoke(command, cwd, env, logfile, timeout=900):
    started = time.monotonic()
    with logfile.open("w") as log:
        log.write("COMMAND " + json.dumps([str(arg) for arg in command]) + "\n")
        log.flush()
        try:
            process = subprocess.run(command, cwd=cwd, env=env, stdout=log,
                                     stderr=subprocess.STDOUT, timeout=timeout, check=False)
            code = process.returncode
        except subprocess.TimeoutExpired:
            log.write("\nDIAGNOSTIC TIMEOUT: no pass can be inferred.\n")
            code = 124
        except OSError as error:
            log.write(f"\nDIAGNOSTIC START ERROR: {error}\n")
            code = 127
    print(f"{logfile.name}: exit={code}, seconds={time.monotonic() - started:.1f}", flush=True)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    work = args.work.resolve()
    work.relative_to(root)  # Every input is visible under one Docker bind mount.
    out = work / "evidence"
    out.mkdir(parents=True, exist_ok=False)  # Never accept stale reports on a re-run.
    image = os.environ["ASTRA_TOOL_IMAGE"]
    env = dict(os.environ, ASTRA_WORKSPACE=str(root), PDK="ihp-sg13g2",
               PDK_ROOT=str(work / "pdk"))
    env["PATH"] = str(root / "tools/diagnostic/bin") + os.pathsep + env["PATH"]
    pdk = work / "pdk/ihp-sg13g2"
    magic_tech = pdk / "libs.tech/magic"
    precheck = work / "tt/precheck"
    inputs = work / "inputs"
    inputs.mkdir(exist_ok=True)
    submitted_files = list((work / "submission").rglob(TOP + ".gds"))
    if len(submitted_files) != 1:
        raise ValueError(f"Expected one submitted GDS, found {len(submitted_files)}")
    submitted = submitted_files[0]
    old_macro = inputs / (MACRO + ".gds")
    macro_url = f"https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/{OLD_PDK}/ihp-sg13g2/libs.ref/sg13g2_sram/gds/{MACRO}.gds"
    with urllib.request.urlopen(macro_url, timeout=60) as response:
        old_macro.write_bytes(response.read())
    new_macro = pdk / f"libs.ref/sg13g2_sram/gds/{MACRO}.gds"
    checked = {}
    for name, path in (("submitted", submitted), ("old_macro", old_macro),
                       ("new_macro", new_macro), ("precheck", precheck / "precheck.py")):
        checked[name] = {"path": str(path.relative_to(root)), "sha256": verify(path, HASHES[name])}
    for path in (submitted.with_suffix(".lef"), submitted.with_suffix(".v"),
                 root / "info.yaml", magic_tech / "read_sram_gds.tcl",
                 magic_tech / "ihp-sg13g2.tech", magic_tech / "ihp-sg13g2-drc.tech",
                 magic_tech / "ihp-sg13g2.magicrc"):
        checked[str(path.relative_to(root))] = {"sha256": sha256(path)}
    actual_ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=precheck, text=True).strip()
    if actual_ref != TOOLS_REF:
        raise ValueError(f"Unexpected tt-support-tools commit: {actual_ref}")
    subprocess.run(["git", "diff", "--exit-code", "HEAD"], cwd=precheck, check=True)
    provenance = {"scope": "diagnostic only; not a shuttle release or full signoff",
                  "pdk_version": PDK_VERSION, "tools_ref": actual_ref,
                  "image": image, "platform": "linux/amd64", "inputs": checked,
                  "old_macro_url": macro_url,
                  "submission_run": 35328977063, "submission_artifact": 10540429315}
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    if (pdk / "SOURCES").read_text().strip() != f"IHP-Open-PDK {PDK_VERSION}":
        raise ValueError("Ciel SOURCES does not match the pinned PDK")
    shutil.copy2(pdk / "SOURCES", out / "PDK-SOURCES")
    docker = ["docker", "run", "--rm", "--platform", "linux/amd64",
              "--ulimit", "core=0", "--volume", f"{root}:{root}"]
    metadata_code = invoke(docker + [image, "sh", "-c",
                           "set -eu; uname -m; magic --version; klayout -v; ciel --version"],
                           root, env, out / "tool-versions.log", timeout=60)
    results = {"tool_metadata": {"status": "pass" if metadata_code == 0 else "process_error",
                                 "returncode": metadata_code}}
    # Separate processes ensure one Magic crash does not prevent the other probes.
    for name, gds, top in (("old-macro", old_macro, MACRO),
                           ("new-macro", new_macro, MACRO),
                           ("submitted-gds", submitted, TOP)):
        case = out / ("magic-" + name)
        case.mkdir()
        command = docker + ["--workdir", str(case),
                            "--env", f"PDK_ROOT={work / 'pdk'}",
                            "--env", "PDK=ihp-sg13g2",
                            "--env", f"ASTRA_INPUT={gds}", "--env", f"ASTRA_TOP={top}",
                            "--env", f"ASTRA_REPORT={case / 'counts.tsv'}",
                            "--env", f"ASTRA_RAW_REPORT={case / 'violations.tcl'}",
                            "--env", f"ASTRA_FLATGLOB={magic_tech / 'read_sram_gds.tcl'}",
                            image, "timeout", "--kill-after=10", "180", "magic", "-dnull",
                            "-noconsole", "-rcfile", str(magic_tech / "ihp-sg13g2.magicrc"),
                            str(root / "tools/diagnostic/check_magic.tcl")]
        code = invoke(command, root, env, case / "magic.log", timeout=240)
        results["magic-" + name] = assess_magic(code, read_optional(case / "counts.tsv"))
        (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    code = invoke([sys.executable, "precheck.py", "--gds", str(submitted), "--tech", "ihp-sg13g2"],
                  precheck, env, out / "precheck.log")
    reports = precheck / "reports"
    results["precheck-corrected-pdk"] = assess_precheck(code, read_optional(reports / "results.xml"))
    if reports.is_dir():
        shutil.copytree(reports, out / "precheck-reports")
    (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    lines = ["# SRAM diagnostic — Linux x86-64", "", "Diagnostic only. No merge, submission or release.",
             "The full GDS is unchanged; the newer SRAM is a separate witness, not a replacement.",
             "", "| Probe | Result | Exit |", "|---|---|---|"]
    lines.extend(f"| {name} | {value['status']} | {value['returncode']} |" for name, value in results.items())
    summary = "\n".join(lines) + "\n"
    (out / "SUMMARY.md").write_text(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary_file:
            summary_file.write(summary)
    print(json.dumps(results, indent=2), flush=True)
    return 0 if all(result["status"] == "pass" for result in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
