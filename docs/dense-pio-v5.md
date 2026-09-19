# AstraPIO ABI v5 — native ten-bit instruction experiment

Branch `codex/dense-pio10`. Not physically qualified or submitted. The merged
compact fallback `946648ff` / shuttle PR 142 remains unchanged.

The user approved reducing storage representation and sharing SPI shift storage,
not reducing capabilities. Keep one general PIO, sixteen instruction slots,
two-byte queues in each direction and three 24-bit timed payload banks.

## External interface

Probe ABI register 01 = `0500`; capacity 0F stays `1002` (16 words, depth 2).
The SPI transaction remains command8/address8/data16, mode 0, MSB first, with
six ASIC clocks minimum for every SCK high/low and CS setup/hold/gap. Program
40..4F accepts ten-bit values only; nonzero upper six bits are rejected without
changing memory or length. Reads zero-extend to 16 bits. Invalid ten-bit opcodes
can be read back but fault when executed. All other register semantics are
unchanged from `single-pio-v4.md`; no old binary compatibility is claimed.

Use `pioasm.py --abi 5` / `assemble(..., abi=5)` and `program_frames(..., abi=5)`.
Legacy assembler defaults remain ABI 3 for archival examples. The C driver
requires ABI 5 and validates word width before transport. Reassemble v4 source:
one source instruction still occupies one word. UART/SPI source and four-clock
execution cadence are preserved. The timed engine and its ABI are unchanged.

## Native instruction encoding

Hex values below are zero-extended ten-bit words. No 16-bit expansion register
is synthesized. `k` is byte0..255; `a` is address0..15; `p` is pin index.

- `000..0FF`: LDI k; `100..1FF`: DELAY k; `200..2FF`: XOR k.
- `300..30E`, in order: NOP, DIR, DEC, SHL, SHR, IRQ, HALT, PULL, PUSH,
  AWAIT, CLR_EVENT, IN, IN 1, OUT, OUT 1. `30F` faults.
- `310|a`: JMP; `320|a`: JNZ; `330|a`: JBIT.
- `340|p`: WAIT p,0; `350|p`: WAIT p,1 (input p0..12).
- `360|p`: SET p,0; `370|p`: SET p,1; `380|p`: OUTBIT p (output p0..13).
- `390|p`: INBIT p (input p0..12).
- `3A0|n`: LDX n0..15; `3B0|a`: DJNZ a. Zero counter retains the
  previous sixteen-iteration wrap behavior.
- `3C0..3FF`, and out-of-range pins above, fault and stop the interpreter.

The 944 canonical assembler operation/operand combinations have distinct
encodings. Original noncanonical v4 aliases and arbitrary 16-bit data words
are not part of this format. Bounds, reset, FIFO, event and ownership guards
remain active. A program must be uploaded consecutively while stopped.

## Validation sequence

First, the ABI-5 pin-level tracer failed against v4, then passed after native
ten-bit storage/decode. All 23 pin-level integration scenarios pass locally
before SPI sharing. Assembler checks enumerate all 944 encodings. C driver
checks reject old ABIs and oversized words; sanitizer checks pass.

Physical baseline is diagnostic run 35436643505: v4 passed CTS but failed
post-hold legalization after adding 390 buffers. The planned comparison keeps
the exact PDK, two-tile boundary, clocks, margins, corners and checkers fixed:
first measure encoding alone, then shared SPI. Neither a smaller cell count nor
functional tests qualify a release. Full routing/checks and a new explicit
derated timing audit remain mandatory before any new submission.

Encoding-only commit `8180b33` passes the same controlled diagnostic in
[run 35438406460](https://github.com/fvannel/AstraPIO/actions/runs/35438406460).
Post-CTS cells: 51,801.1 square micrometers. After 363 hold-repair buffers,
legalized cells: 57,728.8 square micrometers (96.0397% of the core).
The exact settings are root buffer 2, density target 97, Y legalization search
350 micrometers. No routing or signoff follows this diagnostic's stop point.

The second change shares the SPI read/write shift storage, since the protocol
selects one direction per transaction. Read snapshots replace header storage
at the original falling-edge boundary; subsequent read MOSI is ignored. MISO
timing, complete-read consumption and aborted-frame semantics are unchanged.
24 pin-level tests pass after sharing, including every 0..31-bit abort length,
all twenty input-clock phase offsets at the specified minimum SPI timing,
arbitrary read MOSI and alternating read/write transactions. Timing constraints
are not relaxed. The separate physical comparison is recorded below.

`make differential` compares the new core with a frozen v4 reference from
`9ac64fb` at public bus/pin ports: all 944 operations in two accumulator states,
plus 100 random programs, match on every observed cycle (1,988 traces).
Long delays are observed for 1,100 cycles. The reference is test-only and never
part of the ASIC source list. This is bounded dynamic equivalence, not formal
proof. The latch-store unit bench also passes at both widths (10 and legacy 16).

The shared-SPI comparison `57c202f` passes
[run 35438677326](https://github.com/fvannel/AstraPIO/actions/runs/35438677326):
56,798.0 square micrometers after 328 hold buffers, 94.4912% utilization,
930.8 square micrometers less than the encoding-only trial. These are legalized
post-CTS figures, not final routed results. The same three placement/clock
settings are now selected in the official build config for the full-flow test.
Synthesis contains exactly 160 program latches and sixteen row clock gates.

The suite now has 25 pin-level scenarios, including rejection of all 80
reserved ten-bit codes and each of the upper six transport bits. The SPI phase
sweep explicitly aligns simulation time to each phase 0..19 before transfer.
No confidence is inferred for new RTL from historical fallback checks.

Commit `8819b92660527db107a6639ac1193156d1c1f6d8` passes the independent
[25-scenario RTL CI](https://github.com/fvannel/AstraPIO/actions/runs/35438879956).
The same 25 scenarios also pass locally against the exact post-hold placed
netlist from run 35438677326, SHA256
`0d0d72e7bc181b3aa7547b4ff1ab663b9d25c939343e08e59f64b60913430f0c`.
That simulation has no SDF and is not a routed timing qualification. Local
checks additionally pass 52 Python tests, both sanitizer-enabled C test
binaries, the FIFO unit bench and both latch-store widths.

The first official full-flow trial is frozen at `8819b92660527db107a6639ac1193156d1c1f6d8`
in [run 35438884203](https://github.com/fvannel/AstraPIO/actions/runs/35438884203).
It was cancelled, not passed or classified as a signoff failure, after the
density-90 comparison advanced further. Its retained log records 2,148 global
overflow units at 11:35 UTC during post-global timing repair. It never reached
final routing or signoff. No new revision was submitted from this trial.

The density-97 official trial develops routing congestion. A separate
[density-90 diagnostic](https://github.com/fvannel/AstraPIO/actions/runs/35440167471)
on the same RTL passes post-hold legalization and the first global routing
stage: 56,788.9 square micrometers, 94.4761% utilization, 325 hold buffers,
zero overflow on every routing layer. It changes only the initial placement
density target, not the boundary, timing margins, PDK or checkers. The target
is now 90 for a new full-flow trial. This diagnostic stops before post-route
timing repair, detailed routing and signoff; it cannot qualify a submission.

The new complete official trial is
[run 35440371045](https://github.com/fvannel/AstraPIO/actions/runs/35440371045),
frozen at `83ef6b7d8e96dd90e14fa3d22ad8585309dd1a03`. Its RTL is identical
to `8819b92`; only the placement density changed in the physical config.
[Independent functional CI](https://github.com/fvannel/AstraPIO/actions/runs/35440371601)
passes on that exact commit. Downloaded XML evidence confirms 25 pin-level
scenarios plus the differential, FIFO and two program-width benches with no
failure, error or skip. Complete routing, official precheck and explicit derated
timing must still pass before any promotion.

Density 90 reaches detailed routing; Metal2 spacing markers persist through
multiple repair passes (reduced to one at an intermediate observation). They
are blocking until repaired; the run is not qualified.
To test whether the conflict depends on local placement, the adjacent target
91 was measured separately in
[run 35442518158](https://github.com/fvannel/AstraPIO/actions/runs/35442518158):
56,743.5 square micrometers, 94.4007% utilization, 327 hold buffers and zero
initial global overflow. No capacity, RTL, boundary or checking rule changes.
Its complete official trial is
[run 35442726541](https://github.com/fvannel/AstraPIO/actions/runs/35442726541)
on `1b1c91183a4a9a5ea3516699845336175ffe6d96`. Both complete trials are still
unqualified until their results and the supplemental audit are reviewed.

At 13:04 UTC on 2026-09-19, the density-90 physical build completes. Its final
metrics record 56,859.7 um2 standard-cell area (94.5939% utilization), zero
Magic/KLayout DRC, LVS, XOR and antenna violations. All ten official prechecks
pass with no failure, error or skip. The final routed netlist SHA256 is
`68601a53d42b98c47013c1ebe57f53303c69d4d89d95a011fd8e0ca608ac4357`.
Submission metadata confirms source `83ef6b7d8e96dd90e14fa3d22ad8585309dd1a03`,
the unchanged shuttle PDK and LibreLane 3.0.5. The standard fast-corner hold
slack is 0.030340 ns; it does not replace the explicit derated audit.
At 13:13 UTC, all 25 routed-netlist functional scenarios pass with no failures
or skips, and the entire official workflow succeeds. This simulation has no
SDF. The supplemental audit remains pending. Its workflow is frozen to this
exact successful run, source commit, netlist hash, PDK, final SDC and nominal
SPEF, and checks all three cell corners with explicit early 0.95 / late 1.05.
No new revision is submitted before that additional gate passes.

An isolated flip-flop alternative was also measured, without changing the
sixteen ten-bit words, instruction cadence or host contract. All 25 local
pin-level scenarios, 1,988 differential traces and both storage-width unit
benches pass. However, [physical run 35443893374](https://github.com/fvannel/AstraPIO/actions/runs/35443893374)
at `3d296921ff7011b5353b11f66549c1629fe1b35f` fails post-CTS legalization
(`DPL-0036`) before hold repair. Pre-CTS area rises from 49,424.3 to 55,335.6
um2 at the same placement target 91. Post-CTS area is already 57,654.4 um2
(95.916%). This alternative is rejected and remains isolated on
`codex/dense-pio10-flop-memory`; it is not merged into this latch candidate.

The repository has no separate agent glossary/ADR configuration; existing
`compact-v3.md`, `single-pio-v4.md` and their validation ledgers remain the
domain references. No issue-tracker setup, label or external issue is created.
