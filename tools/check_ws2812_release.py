"""Require current, complete WS2812 counter evidence before a release proceeds."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

SOURCES = ("project.v", "pio_spi.v", "pio_single_core.v", "pio_program.v", "pio_fifo.v", "pio_timed.v")
APPLICATION = "lpc_counter_on_demand_replaces_prefix_and_relays_tail"
PDK = "c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_report(report, mode, source_commit, source_hashes, netlist_sha=None):
    expected = {"status": "PASS", "mode": mode, "source_commit": source_commit,
                "source_sha256": source_hashes, "expected_abi": 0x600,
                "concurrent_pio_program": "OUTMSB_toggle", "asic_clock_hz": 50000000,
                "frame_count": 12, "checked_output_bits": 1440,
                "routed_netlist_sha256": netlist_sha}
    for key, value in expected.items():
        require(report.get(key) == value, f"Wrong/stale WS2812 evidence: {key}")
    require(mode in ("rtl", "gl"), "Unknown simulation mode")
    if mode == "gl":
        require(isinstance(netlist_sha, str) and len(netlist_sha) == 64,
                "Routed evidence requires a verified netlist hash")
    frames = report.get("frames", [])
    require(len(frames) == 12, "Missing application frames")
    for sequence, seed in enumerate((0x00FFFE, 0xFFFFFE)):
        counter = seed
        for offset, request in enumerate((True, False, True, True, False, False)):
            frame = frames[sequence*6+offset]
            following = (counter + int(request)) & 0xFFFFFF
            require(frame.get("status") == "PASS", "Application frame failed")
            require(frame.get("counter_seed_hex") == f"{seed:06X}", "Wrong counter seed")
            require(frame.get("increment_requested") is request, "Wrong update sequence")
            require(frame.get("dout_prefix_hex") == f"{counter:06X}", "Counter output corrupted")
            require(frame.get("next_counter_hex") == f"{following:06X}", "Counter update corrupted")
            prefix, tail = frame.get("din_prefix_hex", ""), frame.get("tail_in_hex", "")
            require(len(prefix) == 6 and frame.get("spi_rx_hex") == prefix, "Lost captured prefix")
            require(len(tail) == 24 and frame.get("tail_out_hex") == tail, "Corrupted relayed tail")
            counter = following


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("rtl", "gl"), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    tests = list(ET.parse(root/"test/results.xml").getroot().iter("testcase"))
    require(len(tests) >= 29, "Full release suite was not run")
    require(all(not any(test.find(tag) is not None for tag in ("failure", "error", "skipped"))
                for test in tests), "Release suite contains failed/skipped tests")
    require(sum(test.get("name") == APPLICATION and test.get("classname") == "test_ws2812_counter"
                for test in tests) == 1, "WS2812 counter application was not tested exactly once")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    hashes = {name: digest(root/"src"/name) for name in SOURCES}
    netlist_sha = None
    if args.mode == "gl":
        artifact = root/"tt_submission"
        require(json.loads((artifact/"commit_id.json").read_text())["commit"] == commit,
                "Routed artifact belongs to another source commit")
        require(json.loads((artifact/"pdk.json").read_text())["PDK_VERSION"] == PDK,
                "Routed artifact uses another PDK")
        netlist_sha = digest(root/"test/gate_level_netlist.v")
        require(netlist_sha == digest(artifact/"tt_um_fabien_pio.v"),
                "Simulated netlist differs from submission artifact")
    report = json.loads((root/f"test/output/ws2812-counter-{args.mode}.json").read_text())
    validate_report(report, args.mode, commit, hashes, netlist_sha)
    print(f"PASS: exact {args.mode} WS2812 counter application; 12 frames / 1440 bits; "
          f"capture, atomic counter replacement and tail relay; {len(tests)} suite tests.")
    print("Functional verification only; SDF, physical timing and real LPC hardware are separate.")


if __name__ == "__main__":
    main()
