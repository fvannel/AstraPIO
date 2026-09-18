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
were not patched. [Independent CI passes after the SPI fix](https://github.com/fvannel/AstraPIO/actions/runs/35385953714)
(ten integration scenarios at commit `946648f`; eleventh added subsequently).

## Physical experiments

| Run / commit | Change | Observed outcome |
|---|---|---|
| [35384252570](https://github.com/fvannel/AstraPIO/actions/runs/35384252570), `f5e8497` | First compact candidate, CTS cluster 7 | Post-CTS area 53,833.2 µm², 89.56% core; 242 hold buffers added; detailed placement fails |
| [35385308221](https://github.com/fvannel/AstraPIO/actions/runs/35385308221), `c8808f8` | CTS cluster 25 | Area 53,664.5 µm², 89.28%; 237 hold buffers; detailed placement still fails |
| [35385953304](https://github.com/fvannel/AstraPIO/actions/runs/35385953304), `946648f` | CTS root buffer `sg13g2_buf_4` instead of `_16`; SPI race fix | In progress; not qualified |

The cluster experiment was limited by the unchanged fanout limit of eight.
The next experiment uses a smaller characterized buffer, without relaxing
fanout, slew, capacitance, uncertainty, derating, setup or hold requirements.
An alternative one-hot program-read expression was also synthesized locally:
it did not reduce the memory area and was discarded.

The current direct synthesis estimate is **45,661.2 µm²**, about 76.0% of the
60,109.3 µm² core. It excludes physical clock/repair overhead. Two tiles occupy
202.08 × 313.74 µm = 63,400.6 µm² overall. Synthesis fit alone is insufficient.

The first reports trace the latch clocks through the ICGs and include clock
gating checks. Zero setup slack on transparent-latch paths includes time
borrowing; the resizer's positive target margin produced warnings despite zero
negative setup slack. These warnings are preserved, not filtered. The fatal
error in both runs was detailed placement after hold repair. Final routed
borrowing limits, hold, pulse widths, electrical checks and unconstrained
endpoints still require review. The mixed synchronous/asynchronous reset lint
warning is also retained, not suppressed.

## Release status

No merge into `main`, no Pages deployment, no new platform revision. The SRAM
implementation remains on `diagnostic/sram-magic` at `f7f5ca6`.
The compact candidate requires successful full routing, strict Magic/KLayout
DRC, LVS, XOR, official precheck, gate simulation and timing review before it can
be considered for submission. Exact LPC546xx board integration remains separate.
