# Tests

`test.py` tests the inert scaffold only. It is not a PIO functional test.
Replace/extend it when implementing the host port and programmable engine.

Install Icarus Verilog and `requirements.txt` in a dedicated Python environment,
then run `make` here. No local HDL simulator was available at initialization.
See `../docs/verification.md` for required functional and physical checks.

The inherited gate-level mode is `make GATES=yes`, after the actual netlist and
PDK models are available. It has not been run on this scaffold.
