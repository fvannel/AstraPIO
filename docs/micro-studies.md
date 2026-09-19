# AstraPIO controlled micro-adaptation studies

Status: experimental; **no approval for a silicon release or shuttle revision**.
Frozen qualified baseline: `1b1c91183a4a9a5ea3516699845336175ffe6d96`.
Worktree starts at documentation commit `2590a99`; release source is unchanged.

## Decision gates

An adaptation must demonstrate a real public-interface benefit, preserve old
behavior when not enabled, retain output ownership and error guards, and pass
the unchanged two-tile physical flow and explicit three-corner timing audit.
Area-only synthesis or initial routing does not constitute approval. No PDK,
clock-period, signoff margin, precheck or DRC/LVS waiver is allowed.

## Independent studies

| Variant | Bit | Demonstrated benefit / scope | Current physical result |
|---|---:|---|---|
| setdir | 1 | Per-pin direction changes preserve accumulator and ownership | Global route only; not approved |
| jin | 2 | All 13 input selectors, both levels, and bounded polling pass | Fails post-CTS legalization |
| outmsb | 4 | 14-instruction mode-0 full-duplex SPI, eight TX/RX byte pairs, 400 ns bit interval | Shared prototype fails post-CTS; minimal candidate tested separately |
| wrap | 8 | End-of-program wrap removes one jump; FIFO stalls remain intact | Fails post-CTS legalization |
| rx4 | 16 | Four RX bytes plus stalled fifth; partial reads preserve ordering | Fails post-CTS legalization |
| event | 32 | Event divider tested at periods 3, 17, 525 with irregular event spacing | Fails post-CTS legalization |
| capture | 64 | Triggered 1/8/16/24-bit capture; unread result protected on overrun | Fails post-CTS legalization |
| burst | 128 | Repeated 16-bit FIFO snapshots; every partial-word length preserves unread data | Global route only; not approved |
| isa | 15 | Combined four instruction/control extensions pass together | Fails post-CTS legalization |

The capture study is deliberately bounded to 1–24 bits. It is not a full
112-bit ADS-B receiver; preamble recognition, longer-frame buffering and
radio front-end work remain outside that implementation. All alternate timed
modes are mutually exclusive with the original pulse-relay mode.

`STUDY_FEATURES` is a compile-time constant. The materializer records exact
source hashes for every variant; default zero preserves the baseline. An
experimental nonzero build reports ABI 0600 and capability bits at register 1A.
New controls occupy 18 (JIN pin), 19 (wrap), 1B (RX/TX capacities), 1C (levels).
Timed register 6D chooses mode 0=original, 1=event divider, 2=sample capture.

Experiments are published only on isolated GitHub study branches for CI; no
study has been submitted to Tiny Tapeout. Matrix 35470009386 checks all eight
individual changes, the combined ISA and a same-source baseline. An older
matrix (35469607163) used the previous prototype source and had an insufficient
observation window in the wrap test; those results are retained, not substituted
for the current-source run.

### Completed same-source matrix

[Run 35470009386](https://github.com/fvannel/AstraPIO/actions/runs/35470009386),
source `df77ab3b12d2c04b48efe4bce4089cc46659fbdd`: all ten variants passed their
functional stage (26 baseline, 27 for each of eight features, 30 combined ISA:
272 **test executions**, not 272 distinct scenarios). All seven physical
failures above are `DPL-0036` during `OpenROAD.ResizerTimingPostCTS`, before
detailed routing or signoff. A failed placement is not evidence that a feature
can never fit, but it does not qualify it under the unchanged constraints.

| Global-route checkpoint | Standard-cell area (µm²) | Core utilization | Overflow |
|---|---:|---:|---:|
| Same-source baseline | 56,921.4 | 94.6965% | 0 |
| SETDIR | 57,271.5 | 95.2791% | 0 |
| SPI burst | 57,267.9 | 95.2730% | 0 |

These are comparable intermediate metrics, NOT final area or timing signoff.
SETDIR costs +350.1 µm² and burst +346.5 µm² at this checkpoint. Neither was
selected for release: SETDIR still needs a compact complete open-drain protocol
application; burst needs end-to-end LPC streaming measurements and a variable-
length transport API. With only two RX slots, two queued bytes use 48 SPI clocks
instead of 64; the asymptotic 2× saving requires continuing production during
the burst. It does not speed up the separate timed-engine mailbox reads.

The event divider can be a building block for line counting, not a complete VGA
controller. Capture mode is not an ADS-B preamble detector or a 112-bit receiver.
Neither adds a second independently usable timed engine.

## OUTMSB full-flow candidate

Branch `codex/pio-outmsb-candidate` fixes the selector to 4. Its exact source is
committed before launching the unchanged official GDS workflow. This is a
physical-verification candidate, not approval or submission. The same 25
legacy pin tests, exact ABI/capability guards, a 14-instruction full-duplex SPI
program and all-14-pin ownership/data-preservation checks pass at RTL. The
gate-level workflow runs these new tests too.

The shared-prototype OUTMSB variant failed post-CTS timing-repair legalization
in matrix 35470009386. Redundant full run 35470584546 was cancelled, not passed.
The final bounded attempt removes ALL unrelated prototype machinery: SPI and
timed RTL are byte-identical to the qualified baseline; only the core's ABI,
capability read at 1A and fourteen OUTMSB encodings differ. Registers 1B/1C and
the other experimental controls are not implemented in this minimal candidate.
All 28 RTL tests pass together. C probe accepts only baseline ABI5 or ABI6 with
capability exactly 4; unsupported extensions fail before stopping the device.
Transport framing remains unchanged. Host tests pass with sanitizers.

The selected minimal RTL source is `456092ecd7256d25b9650145767b28282cc43a73`.
Its [independent test CI](https://github.com/fvannel/AstraPIO/actions/runs/35470811077)
passes all 28 pin scenarios, 1,988 bounded legacy differential traces, FIFO and
latch-store units and host driver tests. The downloaded test XML was checked
again locally with no failures, errors or skips.
Its [strict full build](https://github.com/fvannel/AstraPIO/actions/runs/35470810763)
is separate from the failed shared-prototype run. No memory bytes, instruction
slots, safety checks, clock targets or PDK rules were removed to make room.

SPI application limits: the measured bit interval is 400 ns at a 50 MHz ASIC
clock (2.5 MHz SCK within a byte). The 14-word demonstration toggles CS per byte;
it does not claim arbitrary-length atomic peripheral frames or all four SPI
modes. Host SPI transactions and two-byte FIFOs limit sustained throughput;
the measured SCK frequency is not sustained LPC-to-peripheral bandwidth.

## Mandatory WS2812 release qualification

The user subsequently authorized continuing to a new Tiny Tapeout revision,
conditional on preserving the WS2812 application and passing all qualification
gates. The default suite now contains 29 scenarios, including a dedicated
12-frame / 1,440-bit counter replacement application with concurrent OUTMSB.
All 29 pass locally. Both RTL and official routed CI now require a complete,
source-bound WS2812 report; see [the release contract](ws2812-release.md).

These test/documentation changes do not alter any RTL, PDK or physical setting
from minimal source `456092e`. A final official build must use the same commit
as the expanded suite and accurate ABI6 submission documentation. The earlier
28-test build cannot stand in for that final build.

Full build and, if successful, the explicit three-corner audit remain pending.
The existing follow-up `qualification-astrapio-compact` checks every 10 minutes
when active. It stays quiet on unchanged state. Submission is permitted only
for the exact final qualified commit; no arbitrary merge, skipped check,
reservation change or replacement of accepted PR149 by a failed experiment.
