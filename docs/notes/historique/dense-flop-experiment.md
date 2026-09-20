# Isolated synchronous program-store experiment

Branch: `codex/dense-pio10-flop-memory`, based on `1b1c911`.

The payload is still sixteen ten-bit instructions, with identical ISA, host
registers, initialized-length protection, request/busy contract and interpreter
cadence. Only payload storage changes: synchronous flip-flops replace 160
latches and their sixteen row-clock gates. The default latch implementation
remains selectable for the frozen reference and unit tests.

Hypothesis: larger bit cells may be offset by simpler clock distribution and
fewer hold-repair buffers. This is not an area claim until physical measurement.
The comparison uses density 91, the same pinned PDK, clock and margins, with all
blocking checks unchanged. No signoff waiver is permitted.

## Local evidence before the physical run

`make test` completed successfully on 2026-09-19:

- 52 Python unit tests and both sanitized C-driver binaries.
- FIFO unit bench and both 10/16-bit program-store benches in both storage modes.
- 1,988 bounded differential traces against the frozen ABI-v4 interpreter.
- All 25 pin-level RTL scenarios, with zero failures, errors or skips.

This is bounded simulation, not formal equivalence. No routed-netlist, signoff,
explicit derated timing or official precheck result exists for this variant yet.
The accepted compact revision remains unchanged.

## Physical result: rejected

[Run 35443893374](https://github.com/fvannel/AstraPIO/actions/runs/35443893374)
at `3d296921ff7011b5353b11f66549c1629fe1b35f` fails post-CTS detailed
placement (`DPL-0036`, six reported entries). It never reaches hold repair or
global routing. Cell area before CTS is 55,335.6 um2, versus 49,424.3 um2 for
the same-density latch trial. After CTS it occupies 57,654.4 um2 (95.916% of
the core), before any hold-repair additions. Fewer clock gates did not offset
the additional payload and feedback-selection logic. Do not promote this
variant or use its failed diagnostic as a qualification.
