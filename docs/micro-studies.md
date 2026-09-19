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

| Variant | Bit | Hypothesis | Initial verdict |
|---|---:|---|---|
| setdir | 1 | Preserve data while changing one owned bidirectional pin's direction | Untested |
| jin | 2 | Branch on a configured synchronized input without consuming the accumulator | Untested |
| outmsb | 4 | Non-destructive output simplifies uniform-cadence full-duplex SPI | Untested |
| wrap | 8 | Optional end-of-program loop removes a branch instruction | Untested |
| rx4 | 16 | RX-only depth four doubles the byte buffering reserve | Untested |
| event | 32 | Reuse timed counters to divide external events | Untested |
| capture | 64 | Reuse the 24-bit bank for externally triggered periodic sampling | Untested |
| burst | 128 | Read repeated 16-bit FIFO snapshots after one SPI header | Untested |
| isa | 15 | Measure the combined four instruction/control extensions | Untested |

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

## OUTMSB full-flow candidate

Branch `codex/pio-outmsb-candidate` fixes the selector to 4. Its exact source is
committed before launching the unchanged official GDS workflow. This is a
physical-verification candidate, not approval or submission. The same 25
legacy pin tests, exact ABI/capability guards, a 14-instruction full-duplex SPI
program and all-14-pin ownership/data-preservation checks pass at RTL. The
gate-level workflow runs these new tests too. C host ABI-6 support is still a
release blocker.
