# Tests

The default integration suite runs `test_compact.py` (11 legacy ABI v3 scenarios)
and `test_timed.py` (10 timed-extension scenarios). Only Tiny Tapeout pins are
used; no internal RTL state is accessed. Timed tests include 24 prefix lengths,
all 20 one-nanosecond input clock phases, strict pulse widths/low times,
concurrent PIO execution and host traffic, atomic commits, frozen RX words,
late host/overrun, generic non-WS2812 timings, and malformed-frame recovery.

`make test` also runs project/release-policy checks, assembler/packet helpers,
depth-two byte FIFO and latch-store unit benches, and both portable C host
drivers with address/undefined-behavior sanitizers. Historical SRAM/older ISA
integration files are retained as evidence but are NOT the current suite.

Install Icarus Verilog and `requirements.txt` in a dedicated Python 3.11–3.13
environment, activate it, then run `make test` from the repository root.
For RTL only, run `make` here, then `python ../tools/check_results.py results.xml`.
See `../docs/verification.md` for required functional and physical checks.

Gate-level mode is `make GATES=yes`, after the matching actual netlist and exact
shuttle PDK models are available. It is functional simulation without SDF; do
not infer timing signoff. The compact submitted fallback and timed experiment
have different netlists. See `../docs/timed-pio-v4.md` for experiment evidence;
do not inherit the fallback's successful physical checks for this extension.
