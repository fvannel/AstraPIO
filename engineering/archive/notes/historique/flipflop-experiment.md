# AstraPIO — dense single-context timed-I/O experiment

**Isolated storage experiment:** `codex/dense-pio10-flop-memory` replaces only
the 16 × 10-bit program payload with synchronous flip-flops. The original
request/busy timing and all capacities are retained. The latch implementation
remains the default for the frozen reference. All 25 local pin-level scenarios
and 1,988 bounded differential traces pass; this is not a formal proof.
The physical comparison failed after clock-tree synthesis and used more area;
this variant is rejected, not a release candidate.

General-purpose programmable digital IO coprocessor for an LPC546xx host, targeting two Tiny Tapeout IHP26b tiles.

**This branch implements ABI 0x0500: one PIO context plus a timed-I/O engine.
It is NOT physically qualified and has NOT replaced the submitted chip.**

The extension captures a configurable 1..24-bit prefix, replaces that prefix
on a simultaneously regenerated pulse stream, then relays the remaining bits.
Timing and GPIO routing are programmable; WS2812B V5 is one tested profile.
Atomic host updates, an RX mailbox and error reporting are included. The sole
programmable context remains available concurrently. The earlier two-context
experiment exceeded the two-tile area; this reduction is explicitly approved.
See [native ten-bit architecture and migration](docs/dense-pio-v5.md).

**Current result:** all 25 pin-level scenarios pass locally in RTL, and 1,988
bounded differential traces match the earlier core cycle by cycle. Encoding-only
commit `8180b33` passes post-hold legalization (96.04% cell utilization); the
shared-SPI variant `57c202f` also passes at 94.49%. Those two physical results
use latch storage and do not qualify this flip-flop variant. No routed or submitted v5 implementation
exists yet. Earlier v4 failures remain in the [historical ledger](docs/single-pio-validation.md).

- One context with one instruction slot every four clocks; both output groups remain accessible.
- One 16 × 10-bit program store (20 bytes), using flip-flops in this isolated experiment and unchanged IHP standard cells; no SRAM macro.
- Two-byte TX and RX queues (4 bytes total), plus 24-bit timed RX, active TX and staging registers.
- Same SPI pins and 32-bit framing; new ABI, capacity and firmware APIs.
- Exact shuttle PDK c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c; all checks blocking.

Use `tools/pioasm.py --abi 5` and the ABI-v5 C driver. Reassemble ABI-v4 source programs; their old binaries are incompatible. See [current qualification status](design_status.json). Historical [compact documentation](docs/compact-v3.md) describes the submitted fallback, not this variant.

The historical SRAM implementation and its evidence remain on branch `diagnostic/sram-magic` at `f7f5ca6`. Existing SRAM docs, larger examples and test modules are archival unless explicitly selected by the compact test suite. Their passes do not qualify this design. In particular, the previous WS2812 transmitter/relay does not fit unchanged.

## Development

Install the dependencies in `test/requirements.txt`, Icarus Verilog **13**, and the exact IHP standard-cell Verilog models. Icarus 12 does not correctly drive the delayed signals in these latch models; CI uses the same verified version-13 package as the official Tiny Tapeout gate simulation. Set `PDK_ROOT` to the parent of `ihp-sg13g2` (locally defaults to `work/pdk`). Run `make test`. The tests include host tooling, the C driver, FIFO and latch-store unit benches, and pin-level SPI/GPIO application tests.

The manual GDS workflow runs the official Tiny Tapeout physical flow, precheck and gate simulation. It does not merge, publish a viewer or submit a shuttle revision. A successful functional test or synthesis-area estimate is not physical signoff.

## Submitted fallback (different RTL)

The [official compact build at `946648f`](https://github.com/fvannel/AstraPIO/actions/runs/35385953304) completes routing in **1×2 tiles**, with zero Magic/KLayout DRC, LVS, XOR and antenna violations. All ten official prechecks pass. Eleven compact integration tests pass on the exact routed netlist locally (the official build ran the first ten). Final standard-cell utilization is **90.42%**. The PDK and all blocking checks remain unchanged.

That compact commit was submitted as [shuttle PR 142](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/142). Its central submission check and official precheck passed; the PR was merged on 2026-09-19 at 06:26:37 UTC. It does not contain this timed extension. See the [validation ledger](docs/compact-validation.md) for timing assumptions, artifacts and limitations. A failed or oversized experiment must not replace this fallback.
