# Tests

`test.py` contains nine black-box cocotb tests of the current PIO prototype.
Only Tiny Tapeout pins are used; no internal RTL state is accessed.
`test_tools.py` contains four unittest cases for assembly and host packet helpers.

Install Icarus Verilog and `requirements.txt` in a dedicated Python 3.11–3.13
environment, activate it, then run `make test` from the repository root.
For RTL only, run `make` here, then `python ../tools/check_results.py results.xml`.
See `../docs/verification.md` for required functional and physical checks.

The inherited gate-level mode is `make GATES=yes`, after the actual netlist and
PDK models are available. It has not been run on this prototype.
