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
