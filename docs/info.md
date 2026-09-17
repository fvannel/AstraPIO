## How it works

**Development scaffold — not a functional ASIC and not ready for submission.**

The intended design is a general-purpose programmable I/O coprocessor connected
to an LPC55xxx host over a dedicated SPI link. A shared execution engine is
intended to run two independent program contexts with deterministic scheduling.
WS2812 interception is one planned software example, not a hardwired protocol.
Neither RP2040 instruction compatibility nor two-tile fit is currently claimed.

The current RTL only exposes the Tiny Tapeout interface and drives zero on its
outputs, with all bidirectional output enables deasserted. No SPI, instruction
memory, scheduler or application program is implemented.

## How to test

Run the scaffold consistency checker and the cocotb wrapper test described in
the README. Neither establishes functional PIO operation or silicon readiness.
An implemented design must additionally pass independent protocol tests,
contention/overflow/timing tests, the IHP physical flow and gate-level simulation.

## External hardware

Planned: an LPC55xxx board, a stable external ASIC clock, and appropriate voltage
translation for the selected application. The dedicated SPI MISO output is on
an output-only pin and must not share a bus with another active MISO driver.
Do not connect 5 V sources without checking the board's electrical limits.
