# Compact candidate validation ledger — 2026-09-18

This ledger concerns `feature/compact-pio`, not the historical SRAM submission.
All runs use the unchanged shuttle PDK `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`.
No DRC, LVS, timing or official precheck result is waived.

## Functional evidence

- Eleven pin-level RTL scenarios pass locally with Icarus 13: SPI framing,
  all 16 program words and patterns, independent contexts, pin ownership,
  queues/overflow/backpressure, peer events, bounds/faults/restart, a 16-word
  two-context SPI loopback, UART waveform decoding, reset/disable, host/peer
  RX arbitration, late RX arrivals, ALU/branches and both input banks.
- The actual 8-bit, depth-two FIFO is tested with a queue scoreboard and 2,000
  random cycles. Build directories include parameters to avoid stale binaries.
- The latch-store unit performs 200 random writes and checks that bus changes
  and extra requests while busy cannot corrupt stored words.
- The eleven integration scenarios also pass against a locally synthesized
  standard-cell netlist (ten together, the added ALU scenario separately).
  This is zero-delay functional simulation, **not post-route/SDF signoff**.
- The same eleven scenarios pass together on the exact official **routed**
  netlist locally with Icarus 13. The official GL job ran ten scenarios at the
  routed commit; the latest test-only additions do not change RTL or configuration.
  Routed simulation is still functional, **without SDF delay annotation**.
- Local synthesized netlist SHA-256:
  `3908240253a4b58c213a551a64159d072c80282e7cfbfd434039da398eb29ea6`.
- Host C tests use AddressSanitizer and UndefinedBehaviorSanitizer. Structural,
  assembler/protocol and release-policy tests pass. Historical SRAM policy
  tests remain separate and do not qualify compact hardware.

An additional regression exposed an inherited SPI race: `read_busy` previously
ended at bit count 32, one cycle before the host RX pop was consumed. A peer RECV
could duplicate the byte in that cycle. The test reproduced the error by varying
the SPI start across all four scheduler phases. Keeping the lock until CS ends
fixes the original failure and passes all four phases. No arbitration test was
removed or weakened.

The first GitHub RTL run used Ubuntu's Icarus 12 and failed because the old-PDK
latch models' delayed specify signals were undriven. The models were verified
byte-identical locally and remotely. CI now installs the same Icarus 13 package
as the official Tiny Tapeout gate test, checking its SHA-256; the PDK and models
were not patched. [Independent CI passes all eleven scenarios](https://github.com/fvannel/AstraPIO/actions/runs/35386869845)
at `93fb972`, including the exact depth-two FIFO unit and isolated compact harness.

## Physical experiments

| Run / commit | Change | Observed outcome |
|---|---|---|
| [35384252570](https://github.com/fvannel/AstraPIO/actions/runs/35384252570), `f5e8497` | First compact candidate, CTS cluster 7 | Post-CTS area 53,833.2 µm², 89.56% core; 242 hold buffers added; detailed placement fails |
| [35385308221](https://github.com/fvannel/AstraPIO/actions/runs/35385308221), `c8808f8` | CTS cluster 25 | Area 53,664.5 µm², 89.28%; 237 hold buffers; detailed placement still fails |
| [35385953304](https://github.com/fvannel/AstraPIO/actions/runs/35385953304), `946648f` | CTS root buffer `sg13g2_buf_4` instead of `_16`; SPI race fix | **Success**: routed 1×2, strict DRC/LVS/XOR, official precheck and GL tests pass |

The cluster experiment was limited by the unchanged fanout limit of eight.
The successful experiment uses a smaller characterized buffer, without relaxing
fanout, slew, capacitance, uncertainty, derating, setup or hold requirements.
An alternative one-hot program-read expression was also synthesized locally:
it did not reduce the memory area and was discarded.

The current direct synthesis estimate is **45,661.2 µm²**, about 76.0% of the
60,109.3 µm² core. It excludes physical clock/repair overhead. Two tiles occupy
202.08 × 313.74 µm = 63,400.6 µm² overall. Synthesis fit alone is insufficient.

## Successful routed evidence

Final standard-cell area is **54,352.2 µm²**, **90.4223%** of the core, excluding
filler cells. There are no SRAM macros. All of the following report zero:
Magic DRC, KLayout DRC, route DRC, LVS differences, XOR differences, antenna
violations, disconnected pins, negative setup/hold slack and electrical
slew/capacitance/fanout violations. All **10 official precheck tests pass**.

The exact three cell corners were checked with nominal extracted RC, 20 ns
clock period, 0.25 ns uncertainty, 4 ns IO delays and 6 fF output load. These
are block assumptions, not a guarantee for arbitrary board loading or jitter.
The **official** timing results below must not be confused with the stricter
explicit 5% derating audit described afterwards.

| Cell corner | Worst hold slack (ns) | Worst ICG setup / hold (ns) | Maximum latch borrowing (ns) | Minimum unused borrowing window (ns) |
|---|---:|---:|---:|---:|
| Fast, 1.32 V, −40 °C | 0.033246 | 18.646536 / 0.187327 | 0.825907 | 9.014359 |
| Typical, 1.20 V, 25 °C | 0.179283 | 18.034367 / 0.421277 | 1.148550 | 8.598487 |
| Slow, 1.08 V, 125 °C | 0.430798 | 17.016415 / 0.814499 | 1.660457 | 7.903065 |

Each corner's full reports contain all 256 latch-write endpoints and 16 ICG
setup plus 16 ICG hold endpoints. No clocks are reported unpropagated and
`check_setup` reports no unconstrained/no-clock endpoints. Zero setup slack on
transparent latches includes time borrowing; it is not zero remaining latch
window. The resizer's positive target margin still produces warnings, preserved
in the logs, despite zero final negative setup slack. The original placement
failures no longer reproduce with the smaller characterized root buffer.

The official parasitic checker lists 17 `clkload` outputs, whose unused outputs
are excluded by its built-in filter; zero functional nets remain unannotated.
This is the unchanged official flow, not a project filter. The mixed
synchronous/asynchronous reset lint warning remains visible. Intermediate route
estimation and unsupported LEF construct warnings are retained; final independent
geometrical/connectivity checks above pass.

The standard report does not explicitly list minimum pulse-width checks.
An additive [audit](https://github.com/fvannel/AstraPIO/actions/runs/35388572669)
checks the frozen routed netlist/SPEF using LibreLane 3.0.5 and exact PDK
libraries. All three corners pass minimum pulse width. Minimum margins are
9.847138 ns fast, 9.764506 ns typical and 9.616928 ns slow.

**Derating caveat discovered during review:** the official environment exports
`TIME_DERATING_CONSTRAINT` as integer `5`. LibreLane 3.0.5 `base.sdc` evaluates
`5 / 100` with integer Tcl arithmetic, producing zero; early/late factors become
1/1 despite the log announcing 5%. This was reproduced directly in Tcl. The
exported SDC consequently contains no non-unity derate. The supplemental audit
explicitly applies factors **0.95/1.05** without patching the official tools,
PDK or precheck. Its worst reported hold slack is **0.004630 ns (4.63 ps)** at
the fast corner, 0.138137 ns typical and 0.363274 ns slow. The positive fast
margin is small and is recorded as such, not rounded into a comfortable margin.

A [strengthened follow-up audit](https://github.com/fvannel/AstraPIO/actions/runs/35388975455)
also requests all setup/hold, recovery/removal, clock-gating, electrical and
pulse-width violators with the explicit derating: **all three corners pass**.
Its timing tables list 256 exactly zero-slack transparent-latch endpoints per
corner; no negative slack. These entries agree with the reported time borrowing.
No unconstrained/no-clock warning is reported. The CI guard additionally checks
numeric negative slack, not just the `VIOLATED` label, and rejects warnings.
Neither audit replaces or alters the official flow. Both use image digest
`sha256:ecabd075d0ddf6a2bd1cd4a32109c7dbb861ec007f7e4e423a9a081f8d23b8e2`.

Artifact SHA-256:

- GDS: `5682f15e50ffecc84bb0cb396894b23e05485676d072f01f3bfa060015303bea`
- OAS: `91b608d6e358193e903890a2a6155c93fe872a3d127b52e021788364a2cd2616`
- Routed netlist: `a1dcabf881ddd007d66cd62011873539d04906e3c6f2a8339f759aaf57e35a88`

Local evidence is under `work/compact-physical-v3`; the latest routed regression
is `work/compact-routed-test.log` and `test/compact-routed-results.xml`.
Full physical artifacts and checker reports are attached to the linked GitHub run.

## Release status

No merge into `main`, no Pages deployment, no new platform revision. The SRAM
implementation remains on `diagnostic/sram-magic` at `f7f5ca6`.
The compact candidate now passes the official physical and functional flow,
plus the stricter supplemental timing/pulse-width audit. Final release review
(including the small fast hold margin), authorization and exact LPC546xx
board/clock integration remain separate. This is not silicon qualification or
SDF-annotated simulation, and no old SRAM pass is reused as compact evidence.
