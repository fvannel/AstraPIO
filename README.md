# AstraPIO — isolated OUTMSB micro-adaptation candidate

General-purpose programmable digital IO coprocessor for an LPC546xx host, targeting two Tiny Tapeout IHP26b tiles.

**This branch is an unapproved ABI 0x0600 experiment: one PIO context plus the
unchanged timed-I/O engine. Only OUTMSB is added. Submission is authorized only
after every exact-source functional, physical and timing gate passes.**
The qualified ABI-5 source `1b1c911` was accepted as shuttle PR149 on
2026-09-19. These experiments have not replaced it. See the
[micro-adaptation evidence and decisions](docs/micro-studies.md).

The mandatory [WS2812 counter application](docs/ws2812-release.md) captures the
first 24 input bits for the LPC, concurrently substitutes its 24-bit counter,
and relays following words unchanged. Mid-frame counter updates take effect
on the next frame. The release suite runs this application alongside OUTMSB
activity on both RTL and the exact routed netlist; a missing or stale report
blocks qualification. All 29 tests passed on RTL and the routed netlist of
`f9e8b69`, but that layout failed the explicit derated fast-corner hold audit
by 16.380 ps and must NOT be submitted. The 80 ps hold-repair candidate
`4a04464` passes all 29 RTL scenarios but fails post-global-route legalization
after adding 15 delay cells. Both arms of the 75/80 ps placement comparison
also fail. In the bounded density-90/92 study, **density 92 legalizes** after
adding eight hold buffers; density 90 fails. The full density92/hold80 build
`e66a4a8` resolves routing and passes all official jobs, ten prechecks and all
29 RTL/routed scenarios, including WS2812. However, the unchanged audit
rejects it: **fast hold −22.042 ps and two slow-corner slew violations**.
The derating diagnostic confirms that `5.0` activates the intended 5% margin,
but its density92 placement fails after378 post-CTS hold buffers (332 in the
integer control). The next bounded diagnostic tests densities90/91 while
retaining the real 5% margin. No diagnostic can produce a submission artifact.
No failed candidate is approved. RTL, memory, PDK and release criteria stay unchanged.

The extension captures a configurable 1..24-bit prefix, replaces that prefix
on a simultaneously regenerated pulse stream, then relays the remaining bits.
Timing and GPIO routing are programmable; WS2812B V5 is one tested profile.
Atomic host updates, an RX mailbox and error reporting are included. The sole
programmable context remains available concurrently. The earlier two-context
experiment exceeded the two-tile area; this reduction is explicitly approved.
See [native ten-bit architecture and migration](docs/dense-pio-v5.md).

**Historical qualified baseline, not this candidate:** commit `1b1c911`
passed 25 pin-level scenarios and 1,988 bounded differential traces, and
completed the official physical build with zero
Magic/KLayout DRC, LVS, XOR and antenna violations, at 94.5637% standard-cell
utilization. All ten official prechecks and all 25 routed-netlist functional
scenarios pass. The explicit 0.95/1.05 derated timing audit also passes all
three cell corners, with minimum hold slack +4.872 ps. The earlier density-90
candidate remains rejected. The qualified density-91 version was submitted
and merged as [PR149](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/149).
See the [validation ledger](docs/dense-pio-v5.md). Earlier v4
failures remain in the [historical ledger](docs/single-pio-validation.md).

- One context with one instruction slot every four clocks; both output groups remain accessible.
- One 16 × 10-bit latch program store (20 bytes), using unchanged IHP standard cells; no SRAM macro.
- Two-byte TX and RX queues (4 bytes total), plus 24-bit timed RX, active TX and staging registers.
- Same SPI pins and 32-bit framing; new ABI, capacity and firmware APIs.
- Exact shuttle PDK c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c; all checks blocking.

Use `tools/pioasm.py --abi 6` for the candidate's OUTMSB example. The C driver
probes ABI5 or exact ABI6 capability 4 and rejects unsupported hardware before
loading extension instructions. Legacy ABI5 encodings are unchanged; ABI4
binaries remain incompatible. See [current qualification status](design_status.json).

The historical SRAM implementation and its evidence remain on branch `diagnostic/sram-magic` at `f7f5ca6`. Existing SRAM docs, larger examples and test modules are archival unless explicitly selected by the compact test suite. Their passes do not qualify this design. In particular, the previous WS2812 transmitter/relay does not fit unchanged.

## Development

Install the dependencies in `test/requirements.txt`, Icarus Verilog **13**, and the exact IHP standard-cell Verilog models. Icarus 12 does not correctly drive the delayed signals in these latch models; CI uses the same verified version-13 package as the official Tiny Tapeout gate simulation. Set `PDK_ROOT` to the parent of `ihp-sg13g2` (locally defaults to `work/pdk`). Run `make test`. The tests include host tooling, the C driver, FIFO and latch-store unit benches, and pin-level SPI/GPIO application tests.

The manual GDS workflow runs the official Tiny Tapeout physical flow, precheck and gate simulation. It does not merge, publish a viewer or submit a shuttle revision. A successful functional test or synthesis-area estimate is not physical signoff.

## Historical compact revision (superseded by PR149)

The [official compact build at `946648f`](https://github.com/fvannel/AstraPIO/actions/runs/35385953304) completes routing in **1×2 tiles**, with zero Magic/KLayout DRC, LVS, XOR and antenna violations. All ten official prechecks pass. Eleven compact integration tests pass on the exact routed netlist locally (the official build ran the first ten). Final standard-cell utilization is **90.42%**. The PDK and all blocking checks remain unchanged.

That compact commit was submitted as [shuttle PR 142](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/142). Its central submission check and official precheck passed; the PR was merged on 2026-09-19 at 06:26:37 UTC. It does not contain the timed extension later accepted in PR149. See the [validation ledger](docs/compact-validation.md) for historical evidence. A failed or oversized experiment must not replace the qualified submission.
