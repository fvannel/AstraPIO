# Timed PIO experiment — not a submitted revision

The validated compact candidate `946648ff` / shuttle PR 142 remains the fallback.
This experiment adds one shared, configurable pulse-I/O engine beside the two
unchanged compact contexts. No WS2812-specific constants are built into its
protocol: input/output selection, idle qualification, prefix length, sample
delay, output delay and both pulse widths are registers. Existing PIO programs
and ABI 0x0300 remain supported; the extension has its own identity/version.

## Acceptance scope

At a 50 MHz ASIC clock the initial application profile is WS2812B V5:
idle >=300 us; bit periods 1240..1300 ns; legal input highs/lows within the
manufacturer's V5 table; output high 320/640 ns. Both paths use the same delayed
output scheduling, including the first relayed bit. No instantaneous mux splice.
The LPC's 24-bit counter is prepared before a frame; an explicit commit becomes
active at the next frame. The completed RX prefix is frozen until acknowledged.
If the LPC is late, keep the old RX result, flag overrun, and continue the relay.

The 24-bit maximum is an area-conscious prototype choice, not a WS2812 decoder:
all prefix lengths 1..24 are programmable, as are pulse timing and idle duration.
Only one output is owned by this shared engine. A core context may not claim it
at the same time. Configuration changes require the engine disabled; staged
payload updates are allowed while a frame runs, with commit locking the staging
register until the next frame consumes it. Output is zero when disabled/reset.

## Implemented experimental host map, page 0x60

| Address | Function |
|---|---|
| 60 | Identity 0x5449 |
| 61 | Control: enable bit0, output enable bit1, replace prefix bit2; write pulses ACK RX bit8, COMMIT bit9, clear errors bit10 |
| 62 | Pins: DIN selector bits3:0 (0..12), DOUT bits7:4 (0..13) |
| 63 | Continuous-low qualification, ASIC cycles, 1..65535 |
| 64 | Sample delay bits5:0; output delay bits13:8; 1 <= sample < output <=63 |
| 65 | Zero high cycles bits5:0; one high cycles bits13:8; nonzero |
| 66 | Prefix length, 1..24 |
| 67/68 | Staging payload low16/high8; writes rejected while a commit is pending |
| 69/6A | Completed RX prefix low16/high8, zero if invalid; MSB first on wire |
| 6B | Status: armed, frame, RX valid, commit pending, active TX valid, config/host error, RX overrun, timing error |
| 6C | Extension version/capacity 0x0118 |

Bits outside these encodings are rejected. Disabling aborts the current frame
and releases output ownership; a new qualified idle is required on re-enable.
The received word is right-aligned. Only its configured low N bits are sent.
Read/ack is not an implicit destructive read; a completed word is stable across
two SPI reads until ACK. The engine must not stall serial timing for host access.

## Validation gates

Implement/test vertical slices via SPI and GPIO only: RX prefix and idle,
independent injected TX and tail relay, atomic updates/late host, reset and
configuration conflicts, randomized timings and length. Run all old compact
regressions too. Then measure synthesis and routing in 1x2 on the exact shuttle
PDK. Preserve all DRC/LVS/timing/precheck guards and run explicit derating audit.
No new platform revision unless every required gate passes. No automatic main
merge is needed for a commit-specific submission.

Existing domain references: `compact-v3.md`, `compact-validation.md`; no repository
agent configuration or issue workflow exists. The autonomous experiment uses
these existing docs and this local ledger, without creating issues or labels.

## Result, 2026-09-19 (Europe/Zurich)

**Functional concept demonstrated; two-tile physical integration FAILED.
No new Tiny Tapeout revision was submitted.** The submitted compact fallback
`946648ff` / PR 142 remains unchanged, with successful central checks and an open
PR. The new source lives only on `feature/timed-pio`; `main` is unchanged.

The test-driven sequence exposed and fixed acceptance of an uninitialized TX
payload. Both staging halves must be initialized before the first commit.
Independent input sampling and output pulse counters prevent a new DIN edge
from truncating the preceding DOUT pulse. The countdown refactor removes a
wide compare/subtract combination without changing the external behavior.

### Functional evidence

- All 22 top-level pin-only scenarios pass on RTL and on the optimized AREA 2
  synthesized netlist. Eleven preserve compact behavior; eleven cover timed IO.
- The timing sweep checks all 24 prefix lengths (1,836 output bits) and all
  twenty one-nanosecond input phases (1,920 further output bits). Output pulse
  widths and inter-pulse lows are checked, not just decoded payloads. Measured
  first-edge latency is 680..700 ns for the default profile at 50 MHz.
- Concurrent compact programs, host traffic, counter carry across bytes,
  frame-boundary commit, pending-write rejection, frozen RX/late host, malformed
  input recovery, partial frames and mid-frame ACK are covered.
- A second timing profile uses different input/output pins, a 7-bit prefix and
  60/120 ns output pulses at a 400 ns bit period. It is not a WS2812-only decoder.
- The byte FIFO and program-latch unit benches pass. All 48 Python helper/policy
  tests pass (some are historical SRAM diagnostic helpers, not SRAM signoff).
- Both portable C host drivers pass with address/undefined-behavior sanitizers.
  The timed driver probes its own extension identity and rejects the old chip.
  Failed SPI transactions stop immediately, including an ambiguous error after
  commit; it does not silently retry them.

Synthesized netlist SHA-256:
`9489f6b73d2de1030b7bad5c238d5ee050a7cba37ae68b36103e5f44c5b9d74b`.
It was built from `7a90da4`; its RTL matches `2656afa` and placement candidate
`95d6f8f`. Netlist simulation is functional, **not routed and not SDF annotated**.
This is bounded test coverage, not a claim of exhaustive formal verification.

### Area and placement evidence

Exact shuttle PDK `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`, LibreLane 3.0.5,
TT support tools `01d5d2814fa9dd61e9d211e0b235a4a592a9316a`, clock 20 ns,
unchanged 202.08 × 313.74 um die and 60,109.258 um² usable core.

| Optimized RTL mapping | Synthesis area, um² (ICGs excluded) |
|---|---:|
| AREA 0, NF false | 62,401.7142 |
| AREA 0, NF true | 62,400.0132 |
| AREA 1, NF false | 62,004.8898 |
| AREA 2, NF false | 61,733.2590 |
| AREA 3, NF false | 69,590.7450 |

Yosys omits the 16 explicit clock gates in these area totals. OpenROAD's actual
AREA 2 cell area is **62,181.302 um²**, already above the available core. Its
pin-density adjustment adds 6,623.107 um² for placement, giving **114.466%**
effective utilization (AREA 0: **116.329%**). This adjustment is not an invented
buffer area. Both runs stop with `GPL-0301` at global placement. There is no
routed layout, CTS signoff, DRC/LVS result or official precheck for this extension.

[Synthesis sweep](https://github.com/fvannel/AstraPIO/actions/runs/35399857434)
and [strict placement failures](https://github.com/fvannel/AstraPIO/actions/runs/35400396916)
preserve the reports. Only synthesis strategies were varied. No PDK, tile count,
clock relaxation, checker exception, DRC filtering or release-flow bypass was
introduced. Diagnostic runs intentionally stop before fabrication signoff and
never produce a `tt_submission` release artifact.

### Host integration and remaining decision

`firmware/pio_timed.h` / `.c` provide configure, stage/commit, control and stable
receive operations using the existing serialized SPI callback. Configure and
stage the initial 24-bit value before enabling mode 7. A successful later
`pio_timed_stage()` schedules the new value for the next qualified frame; it
does not change the word already transmitting. `PIO_EFULL` means a prior commit
is pending. Read the frozen RX word, then explicitly ACK with mode 7 retained.
Handle overrun visibly. A transport error after commit has an uncertain effect;
reconcile/reset rather than blindly incrementing and retrying the counter.
The exact LPC board transport, DMA, electrical levels and clock remain untested.

The next useful architecture step is to **share storage/state with the compact
engine instead of adding an independent bank**, with explicit rules for which
PIO programs/resources can operate simultaneously. Alternatively, reduce a
capacity or context count. These are real capability tradeoffs; none was
silently applied to obtain a passing build. Extra tiles are outside the agreed
two-tile target. The current completed physical fallback remains the release.
