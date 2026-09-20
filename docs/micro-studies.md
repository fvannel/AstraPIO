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
was cancelled in favor of the final 29-test source below, not passed. No memory bytes, instruction
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

Every new physical candidate requires a full build and explicit three-corner audit.
The existing follow-up `qualification-astrapio-compact` checks every 10 minutes
when active. It stays quiet on unchanged state. Submission is permitted only
for the exact final qualified commit; no arbitrary merge, skipped check,
reservation change or replacement of accepted PR149 by a failed experiment.

### Final exact-source verification

Source `f9e8b69f90cfacd1fafebe9513a5b294ed691fb0` includes the mandatory WS2812
scenario and correct ABI6 submission documentation. Independent RTL CI
[35472246586](https://github.com/fvannel/AstraPIO/actions/runs/35472246586)
and docs CI 35472246583 succeed. The entire official
[GDS run 35472253033](https://github.com/fvannel/AstraPIO/actions/runs/35472253033)
succeeds: zero final Magic/KLayout DRC, LVS, XOR, antenna and routing errors;
all ten official prechecks and all 29 routed pin-level scenarios pass.
Downloaded results were independently checked for failures, errors and skips.

The WS2812 report passes both its CI gate and a local source/netlist-bound
recheck: 12 frames, 1,440 bits, host prefix capture, atomic next-frame counter
replacement, intact tail and concurrent OUTMSB. Observed rise latency in both
CI runs is 682–699 ns. The local RTL run measured 680–697 ns at its phases;
both are inside the unchanged 680–700 ns assertion. No SDF is used.

Final standard-cell area is **57,400.4 µm² (95.4934%)**, compared with
56,841.5 µm² (94.5637%) for qualified baseline 1b1c911. The increase is
558.9 µm², with unchanged memory, timed engine and constraints. This is a
completed two-tile layout, not yet approval of its derated timing margins.

Exact routed netlist SHA256:
`de4a388ce1ab062ae44cfd8c3a4b51d82db5e16dd28761cda36964f3a02210b1`.
PDK remains `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`; LibreLane is 3.0.5.
The explicit three-corner 0.95/1.05 audit was launched once as
[35481178961](https://github.com/fvannel/AstraPIO/actions/runs/35481178961).
It **failed** on one fast-corner hold path: `core.instruction[8]` (`_4779_`)
through `_3031_`, `_3032_`, `_3033_` to `core.accumulator[6]` (`_5048_`).
The required time is 0.791058 ns and arrival 0.774678 ns, giving
**−0.016380 ns**. Typical hold is +0.117166 ns and slow +0.345912 ns; minimum
pulse-width checks pass at all three corners. This failure disqualifies
`f9e8b69` despite its successful official flow and functional simulations.

Diagnosis checked three hypotheses: a real fast short path, mismatched
artifacts, or a report/parser problem. The audit netlist, SDC and SPEF hashes
match the official build. The full path report and all-violators summary
independently contain the same negative slack, while latch time-borrowing zeros
are not treated as violations. Thus this is a real hold-margin deficit under
the required derating, not a test to waive. The frozen-netlist audit is the
regression harness; ordinary RTL tests cannot reproduce a routed hold deficit.

## Corrective physical candidate: GRT hold target 80 ps

Only `GRT_RESIZER_HOLD_SLACK_MARGIN` changes from 0.02 to 0.08 ns. This asks
OpenROAD to insert enough physical delay to aim for a larger positive hold
margin; it does NOT relax a signoff rule or change the audit's 0.95/1.05
derating. See [LibreLane timing closure](https://librelane.readthedocs.io/en/latest/usage/timing_closure/index.html).
Post-CTS margin stays 0.02 ns. RTL, memory, timed engine, 20 ns clock, PDK,
placement density, setup constraints and all official checks stay unchanged.

Prediction: extra post-global-route hold repair should remove the observed
fast short path while preserving setup, legality and the two-tile boundary.
The physical regression is a NEW complete official build, all 29 routed tests
including the source-bound WS2812 application, and the identical strict
three-corner audit. No acceptance is inferred from increasing the setting.
The failed `f9e8b69` artifacts are retained; accepted baseline PR149 is untouched.
No new shuttle revision has been submitted.

### Hold80 result and bounded diagnostic

Source `4a044644455181e3053fe15fc3d3ba170b501c30`: RTL CI
[35481475673](https://github.com/fvannel/AstraPIO/actions/runs/35481475673)
and docs CI 35481475694 succeed. Downloaded XMLs contain 29 pin scenarios,
the differential scenario group (1,988 traces), FIFO/latch units and no
failures or skips. The WS2812 report is bound to this exact source and all six
RTL hashes; all 12 frames / 1,440 bits pass.

Official [GDS 35481481220](https://github.com/fvannel/AstraPIO/actions/runs/35481481220)
**fails** in `OpenROAD.ResizerTimingPostGRT`: `DPL-0036` after inserting 15
hold buffers (+0.4% cell area at the repair step). Precheck and routed tests are
skipped, not passed. No timing audit or shuttle submission is justified.

The prior 20 ps build has identical setup-repair log entries at this step,
inserts no hold buffers and legalizes. At 80 ps, the repair starts with a
60 ps worst endpoint, reaches 74 ps at `_5048_/D` after ten buffers, then
80 ps after fifteen. The failing placement lists `input18`, `_4652_`,
`_4869__378` twice and `_4878__369`. This supports a repair-induced local
placement bottleneck; it does not prove total area is physically impossible.

Ranked falsifiable hypotheses: (1) fewer inserted delay cells at 75 ps may
legalize while still repairing the 74 ps critical endpoint; (2) a different
initial distribution at the same capacity may accommodate the 80 ps repair;
(3) OUTMSB's physical overhead cannot be accommodated without sacrificing
required capacity, in which case retain PR149. A 60 ps target was not selected:
it might leave the observed critical endpoint untouched.

The first experiment compares **only** GRT repair target 75 vs 80 ps, keeping
density 91, post-CTS target 20 ps, clock 20 ns and the frozen PDK. The existing
diagnostic workflow stops after post-global-route timing repair/legalization,
preserves failure status, and cannot create a submission artifact. The 80 ps
arm is a reproduction control, not an attempt to rerun a failed release until
green. If 75 ps legalizes, its extracted final timing is still unknown: a new
official full build plus all 29 routed tests and the unchanged three-corner
0.95/1.05 audit are mandatory. No signoff acceptance threshold is changed.

### Repair-target comparison rejected; distribution study

The bounded [comparison 35482376886](https://github.com/fvannel/AstraPIO/actions/runs/35482376886)
on `9ddea8e35030b6192bb16d0e118fc663965b0e8a` fails in both arms:

| GRT repair target | New hold buffers | Pre-legalization estimated minimum hold | Placement result |
|---|---:|---:|---|
| 75 ps | 13 | 77 ps | DPL-0036, `_2641_` |
| 80 ps control | 15 | 80 ps | DPL-0036, `_4649_`, `input18` twice |

These are global-route estimates, NOT final extracted/derated signoff slacks.
Both arms start the repair step at 57,340.5 µm². The resolved configurations
match the failed official hold80 build numerically except the intended 75 ps
target; paths differ because this diagnostic runs directly inside the same
LibreLane 3.0.5 image. The 80 ps control reproduces the failure class and repair
counts, but the list of unplaced instances is not identical to the official
build. Do not claim bit-identical placement across those invocation paths.
Both runs' frozen-condition assertions pass. Same-source RTL CI 35482377042
and documentation CI 35482376934 succeed. No release build was run at 75 ps.

This falsifies the prediction that reducing the repair target to 75 ps alone
would legalize the current distribution. The next bounded experiment tests
the second hypothesis: `PL_TARGET_DENSITY_PCT` 90 or 92 with GRT target fixed
at 80 ps. Only the initial-placement density target varies; neither the tile
boundary nor the logical circuit, memory, PDK, clocks or checkers change.
This is a [placement target](https://librelane.readthedocs.io/en/latest/reference/step_config_vars.html#global-placement),
not permission to enlarge the two tiles or a claim about final utilization.
The same stop-after-post-GRT diagnostic is used, with both failures preserved.
Any legal result still needs a fresh exact-source full official flow and the
unchanged supplemental audit before it can be selected for submission.

### Density92 selected for full reconstruction, not release

The [distribution diagnostic 35483136903](https://github.com/fvannel/AstraPIO/actions/runs/35483136903)
uses source `5ccf2984b52b4090f46058666a85945ef556c788`. The overall matrix is
failed because density90 fails; **only the density92 job succeeds**. Frozen
condition assertions pass for both. Same-source RTL CI 35483136845 and docs
CI 35483136874 also succeed; those are not the next full-build source.

Density90 fails post-GRT legalization (`_4327_`, `fanout256`). Its repair log
reports a net count of one hold buffer and +0.5% area; the iterative repair
also removes/replaces buffers, so that final count is not a gross insertion
count. This failed arm is retained and cannot qualify a release.

Density92 inserts eight hold buffers and legalizes. The estimated pre-placement
minimum hold reaches 81 ps; after legalization, global routing ends with
**40 overflow units**, including Metal2/3/4/5/TopMetal1. Intermediate cell area
is 57,498.3 µm² and utilization 95.6564%; these are not final signoff metrics.
The placement displacement maximum is 227.1 µm, within the unchanged 500/350 µm
limits. The valid output state and netlist are preserved in the diagnostic.
This supports the distribution hypothesis, but not a claim that final timing
or detailed routing will pass. Global congestion is explicitly unresolved.

The next candidate changes **only** `PL_TARGET_DENSITY_PCT` from 91 to 92 in
the physical config, retaining the existing 80 ps GRT hold target. All RTL,
program/FIFO capacity, WS2812 behaviour, two-tile boundary, clocks, PDK and
official/supplemental acceptance gates remain unchanged. The existing
`GRT_ALLOW_CONGESTION` setting is not changed; it allows the normal detailed
router to attempt closure, not a waiver of final DRC or routed timing.

The regression harness is the same full official GDS, all 29 routed scenarios
and source-bound WS2812 evidence, then the exact frozen-netlist three-corner
early0.95/late1.05 audit. Diagnostic success alone does not authorize submission.
No checker or safety override was introduced. Accepted PR149 stays intact.
