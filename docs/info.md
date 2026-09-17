## How it works

**Functional RTL prototype — not a validated ASIC and not ready for submission.**

This is a general-purpose programmable I/O coprocessor intended for an LPC55xxx
host over a dedicated SPI link. A shared execution engine runs two independent
program contexts using fixed alternating execution slots.
WS2812 interception is one planned software example, not a hardwired protocol.
Neither RP2040 instruction compatibility nor two-tile fit is currently claimed.

The prototype implements mode-0 SPI register access, 16 x 16-bit instructions
per context, 16-bit accumulators, masked GPIO operations, branches, shifts,
wait-for-level, delay, interrupts, halt and faults. Program writes require both
contexts to be stopped. SPI timing currently requires SCK <= clk/10 and CS setup,
hold and inter-frame high times >= 5 clk periods. These are RTL protocol limits,
not characterized silicon specifications. See isa-v0.md for the full contract.

There are no host streaming FIFOs, inter-context data queues, absolute deadlines
or LPC driver yet. Memory uses inferred logic rather than a SRAM macro. No
application protocol, two-tile physical fit or 50 MHz operation has been proven.
Reset/disable releases bidirectional pins; halt/fault/stop retain their state.

## How to test

Run `make test` with Icarus Verilog and the pinned cocotb dependencies installed.
The pin-level tests cover host transfers, abort/reset, both contexts, ownership,
instruction behavior, faults and deterministic slot timing during SPI traffic.
These establish prototype behavior, not silicon readiness. Further streaming,
application, CDC, IHP physical-flow and gate-level validation is required.

## External hardware

Planned: an LPC55xxx board, a stable external ASIC clock, and appropriate voltage
translation for the selected application. The dedicated SPI MISO output is on
an output-only pin and must not share a bus with another active MISO driver.
Do not connect 5 V sources without checking the board's electrical limits.
