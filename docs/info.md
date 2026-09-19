# AstraPIO — single PIO plus autonomous timed I/O (ABI v6)

This revision adds the non-destructive `OUTMSB` instruction to the qualified
single-context PIO while preserving the complete autonomous timed pulse engine,
program memory and FIFO capacities. The previous ABI5 implementation was
accepted as shuttle PR149. Results for that earlier revision do not qualify
this one: every release requires its own full flow and exact-source evidence.
See `docs/micro-studies.md` for the revision-specific qualification ledger.

General-purpose programmable digital IO coprocessor for an LPC546xx host.
This is ABI 0x0600 with capability register 1A equal to 0004. Earlier SRAM,
dual-context and compact submissions describe different implementations.

## How it works

One interpreter uses a programmable 16-word, 10-bit instruction store made from IHP standard-cell latches, with two-byte transmit and receive queues. One instruction slot occurs every four chip clocks. There is no SRAM macro. An autonomous pulse engine can concurrently capture a 1..24-bit prefix, replace it on a regenerated output stream and relay subsequent bits. Timing and routing are programmable; WS2812B V5 is one tested profile, not a hardwired ASIC purpose.

The host uses SPI mode 0, MSB first: command byte (02 write / 03 read), register address byte, then a 16-bit payload. Program words occupy the low ten bits; upper bits must be zero. Stop the interpreter before changing its program. Probe identity 5049, ABI 0600, capability 0004 and context count 1 before using the new instruction. SPI high/low periods and CS setup/hold/gap each require at least six ASIC clocks. MISO is not tri-stated.

`OUTMSB pin` has native encoding 3E0 + pin, for output indices 0..13. It drives
the accumulator's bit 7 onto an owned output without shifting the accumulator.
Unowned pins are not changed; indices 14/15 fault. No new state machine or RAM
is added. Existing ABI5 instruction encodings remain valid. Other experimental
instructions, deeper queues and alternative timed modes are not implemented.

## How to test

Reset, confirm ID/ABI/context count/capacity registers (00/01/02/0F) and the new
capability at 1A, load and read back code, set entry PC and GPIO mask, then run
with mask 1. Use assembler option `--abi 6` for OUTMSB; ABI4 and older binaries
must be reassembled. The pin-level suite checks program integrity, 14 output
indices, FIFO/SPI atomicity, UART timing, faults and reset, plus pulse-stream
capture/replacement/relay while the interpreter runs independently.

The mandatory WS2812 application test sends twelve 120-bit frames: capture the
first 24 bits for host SPI, replace them concurrently with a host-owned 24-bit
counter, then regenerate the remaining 96 bits unchanged. It checks increment
requests, no-request repeats, carry, wrap, IRQ/ACK, output pulse timings, atomic
next-frame updates and concurrent OUTMSB execution. This is a pin-level LPC
behaviour model, not execution of ARM firmware. See `docs/ws2812-release.md`.

See `docs/dense-pio-v5.md` for the unchanged base register map, with the ABI6
addition above. Pulse timing must be configured for the actual attached device.
Physical timing evidence is limited to the stated clock, PVT corners and
nominal extracted RC; broad WS2812 compatibility and board-level timing remain
unqualified.

## External hardware

A host MCU (intended LPC546xx), clock source and wiring for the selected programmable protocol. The exact LPC546xx board transport/DMA and board timing remain to be qualified. No external memory is required for the compact examples.

## Pin use

ui0/1/2: host SCK/MOSI/CS_n; ui3..7: five dedicated PIO inputs.

uo0/1: MISO/IRQ; uo2..7: six dedicated PIO outputs.

uio0..7: eight bidirectional PIO pins. The single interpreter may own any of the 14 outputs; the pulse engine exclusively owns at most one. Masks cannot overlap. All pad output values are forced low and uio directions disabled on reset or deselection; dedicated outputs are not tri-state.

## Qualification status

Submission is conditional on the exact revision passing placement/routing,
Magic/KLayout DRC, LVS, XOR, antenna, official Tiny Tapeout precheck, the complete
routed functional suite including WS2812, and an explicit early 0.95 / late 1.05
three-corner timing audit. No SRAM waiver, DRC filtering or nonblocking signoff
exception is permitted. The revision-specific results and hashes are recorded
in `docs/micro-studies.md` and `design_status.json`. Functional gate simulation
is not SDF-annotated; board voltage levels, real LPC transport/DMA and hardware
timing remain to be validated on the actual development board.
