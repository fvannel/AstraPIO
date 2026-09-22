# Single PIO + timed I/O: validation ledger, 2026-09-19

## Outcome

The approved reduction from two general PIO contexts to one is implemented
on `feature/single-pio-timed`, ABI `0x0400`. The 16 x 16-bit program store,
two-byte TX and RX queues, and 24-bit timed RX/active TX/staging registers
remain intact. All 22 pin-level functional tests pass, including concurrent
PIO activity and prefix replacement/tail relay. **This candidate is not
physically qualified and has not been submitted.**

The previously qualified compact commit `946648ff304834c2c34deca6c4b14031f191dd39`
remains the submitted design. [Shuttle PR 142](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/142)
is merged, timestamp 2026-09-19T06:26:37Z, verified again during this work.
Its passing results apply only to that different RTL, without the timed engine.
Neither main nor the platform revision was replaced.

## Functional evidence

- First identity/capacity test failed against ABI `0x0300` and passed after
  implementation of ABI `0x0400`; assembler/profile and C-driver changes were
  likewise checked with failing-then-passing regression tests.
- Local RTL: 22 scenarios in `work/single-22.xml`, all pass.
- Independent [RTL CI 35436643502](https://github.com/fvannel/AstraPIO/actions/runs/35436643502):
  success at diagnostic commit `a363df8`.
- Exact AREA-2 globally placed netlist from
  [placement run 35435713981](https://github.com/fvannel/AstraPIO/actions/runs/35435713981):
  22 scenarios pass in `work/single-placed.xml`. SHA-256:
  `92ed410d21d36a4a9b8f4b524a813fe925caa9e508db5b67fb430e1a6f80b19d`.
  This is a pre-CTS functional simulation **without SDF**, not routed timing proof.
- Two memory/FIFO unit benches, 49 Python tool/policy tests, and two C test
  binaries under address/undefined-behavior sanitizers also pass. The policy
  tests guard against historical bypasses; they do not waive physical checks.
- Coverage includes all 14 output indices, both input banks, FIFO overflow and
  backpressure, aborted/empty SPI reads, program initialization and bounds,
  reset/deselection, removed-context rejection, ALU/branches/events, SPI/UART
  waveforms, 24 timed prefix lengths, 20 input phases, atomic payload commits,
  late host updates, malformed input and ownership conflicts.
- Official Verilator 5.044 reports zero errors, with the existing unsuppressed
  `SYNCASYNCNET` reset warning. Local Verilator 5.052 additionally rejects PDK
  `specify` constructs through `SPECIFYIGN` warnings; this local lint result
  is not represented as a pass and the PDK models were not patched.

These are bounded tests, not exhaustive verification or silicon qualification.

## Reproducible physical experiment

All runs use the existing two-tile geometry and exact shuttle PDK
`c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`, LibreLane 3.0.5 and Tiny Tapeout
tools `01d5d2814fa9dd61e9d211e0b235a4a592a9316a`. Core area is
60,109.258 square micrometers. There is no SRAM macro in this design.

Initial AREA-2 global placement has 51,657.8 square micrometers of actual
cells (85.94% utilization), before signal/clock/hold repair. The placer's
pin-density-adjusted utilization is 93.741%; these are different quantities.

[Official full run 35435903552](https://github.com/fvannel/AstraPIO/actions/runs/35435903552)
adds 360 signal-repair buffers and 153 clock buffers, reaches 57,059.25 square
micrometers, then fails CTS detailed placement (`DPL-0036`, 20 reported entries).
It produces no qualified submission artifact and does not reach routed checks.

Controlled trials keep failures blocking and stop after post-CTS timing repair:

- [35436128695](https://github.com/fvannel/AstraPIO/actions/runs/35436128695):
  reproduced baseline; root buffer 2 saves area but still fails CTS;
  AREA 1 fails earlier; placement density target 97 reduces the failed entries.
- [35436388861](https://github.com/fvannel/AstraPIO/actions/runs/35436388861):
  combining root buffer 2 and density 97 reaches 56,496.79 square micrometers
  and one failed tie-cell entry. The alternative NF mapper is larger.
- [35436572402](https://github.com/fvannel/AstraPIO/actions/runs/35436572402):
  density targets 98/99 and removal of buffer-8 from the CTS candidate list
  do not solve legalization; the smaller CTS candidate list increases area.
- [35436643505](https://github.com/fvannel/AstraPIO/actions/runs/35436643505):
  root buffer 2, density 97 and `PL_MAX_DISPLACEMENT_Y=350` **pass CTS
  legalization**. The default search is 100 micrometers, versus a core about
  306 micrometers high. Expanding the legalizer's search does not change
  legal placement rules or electrical/timing constraints.

The last trial then finds **328 hold endpoints**, inserts **390 hold buffers**
(+11.3% cell area reported, rounded), and fails the next detailed placement
with **184 reported entries**. On the pre-repair area, this implies roughly
62,900 square micrometers, already above the 60,109-square-micrometer core.
This is an estimate from the repair log, not a final routed utilization metric.
The listed entries are the tool's output count, not necessarily unique cells.

The minimum-path report includes an input synchronizer path with only about
1.25 ps of clock skew but a -58.4 ps hold slack at the typical corner. Thus
clock imbalance alone is not an adequate explanation: short data paths also
need real delay under the unchanged 250 ps clock uncertainty. The repair
achieves its 20 ps target before legalization fails; that temporary estimated
timing result cannot qualify an unplaceable design. The setup repair also
reports 256 latch endpoints at zero slack against its requested positive
margin; this warning remains visible and is not treated as signoff.

Local evidence is under `work/single-physical-v1/`,
`work/single-cts-v1/`, `work/single-cts-v2-combined/`,
`work/single-cts-v2-nf/` and `work/single-cts-y350/`; the v3 run log is
`work/single-cts-v3.log`. Downloadable CI artifacts are linked above.

## Safety and qualification boundary

No timing uncertainty, setup/hold margin, corner, DRC/LVS check or official
precheck was removed or made nonblocking. No PDK edit/update, custom SDC,
extra tile or provisional SRAM exception was introduced. The diagnostic
settings have not been promoted to `src/config.json` as a working release.

A future candidate still needs complete placement/routing, timing, DRC, LVS,
antenna/XOR checks, unmodified official precheck, and the 22 functional tests
on its exact routed netlist. It also needs a new frozen-netlist timing audit
with explicit 0.95/1.05 derating: the documented LibreLane 3.0.5 base-SDC
integer-division issue and the fallback's separate audit must not be hidden
or inherited as evidence for new RTL. Board voltage translation, host SPI
limits and the actual LPC546xx board remain to be qualified.

## Next capacity decision — not implemented

The approved one-context reduction alone is insufficient in the measured flow.
Further program/FIFO/payload reductions are not silently included.

Removing four program words (16 to 12) removes 64 characterized latches and
four row clock gates: 2,082.93 square micrometers of bare cells. Removing eight
words (16 to 8) removes 4,165.86 square micrometers. These arithmetic estimates
use 30.8448 per `sg13g2_dlhq_1` and 27.216 per `sg13g2_lgcp_1` from the pinned
library, excluding changed muxes, buffers and routing. They are not measured
post-route savings or fit guarantees.

Of those two memory-only experiments, eight words offers the larger useful
margin, while leaving the timed stream engine and its 24-bit values intact.
It substantially reduces the general PIO's program capacity: the current UART
example is 14 instructions and the SPI transmitter test is nine. Neither fits
unchanged. Splitting initialization from the running program may help some
applications, but requires reprogramming and new tests; no such port is claimed
complete. The 12-word reduction alone is smaller than the current estimated
post-hold excess before any routing margin. Reducing both queues to one byte
would be another separate throughput/backpressure tradeoff, not a demonstrated
solution. User choice is needed before cutting these capacities further.
