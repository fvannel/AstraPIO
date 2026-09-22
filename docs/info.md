# AstraPIO — single PIO plus timed I/O (ABI v5)

**Release status:** final source `1b1c91183a4a9a5ea3516699845336175ffe6d96`,
project 5799, TTIHP26b, 1×2 tiles. Submitted as
[PR149](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/149), merged
2026-09-19 at 15:14:01 UTC. It passes the official physical flow and the
explicit three-corner derated audit. The local cleanup does not change the
submitted circuit or create a new submission. See [the validation summary](validation-finale.md).

General-purpose programmable digital IO coprocessor, **submitted and accepted; hardware qualification remains pending**. This is ABI 0x0500; earlier single/dual-context and SRAM submissions describe different implementations.

## How it works

One interpreter uses a programmable 16-word, 10-bit instruction store made from IHP standard-cell latches, with two-byte transmit and receive queues. One instruction slot occurs every four chip clocks. There is no SRAM macro. An autonomous pulse engine can concurrently capture a 1..24-bit prefix, replace it on a regenerated output stream and relay subsequent bits. Timing and routing are programmable; WS2812B V5 is one tested profile, not a hardwired ASIC purpose.

The host uses SPI mode 0, MSB first: command byte (02 write / 03 read), register address byte, then a 16-bit payload. Program words occupy the low ten bits; upper bits must be zero. Stop the interpreter before changing its program. Probe identity 5049, ABI 0500 and context count 1 before using the driver. SPI high/low periods and CS setup/hold/gap each require at least six ASIC clocks. MISO is not tri-stated.

## How to test

Reset, confirm ID/ABI/context count/capacity registers (00/01/02/0F), load and read back code, set entry PC and GPIO mask, then run with mask 1. Use assembler option `--abi 5`; old binaries are incompatible. The pin-level suite checks program integrity, 14 output indices, FIFO/SPI atomicity, UART timing, faults and reset, plus pulse-stream capture/replacement/relay while the interpreter runs independently.

See `docs/dense-pio-v5.md` for the register map, ISA migration and verification scope. Pulse timing must be configured for the actual attached device. Physical timing evidence is limited to the stated clock, PVT corners and nominal extracted RC; broad WS2812 compatibility and board-level timing remain unqualified.

## External hardware

A host MCU (intended LPC546xx), clock source and wiring for the selected programmable protocol. The exact LPC546xx board transport/DMA and board timing remain to be qualified. No external memory is required for the compact examples.

## Pin use

ui0/1/2: host SCK/MOSI/CS_n; ui3..7: five dedicated PIO inputs.

uo0/1: MISO/IRQ; uo2..7: six dedicated PIO outputs.

uio0..7: eight bidirectional PIO pins. The single interpreter may own any of the 14 outputs; the pulse engine exclusively owns at most one. Masks cannot overlap. All pad output values are forced low and uio directions disabled on reset or deselection; dedicated outputs are not tri-state.

## Qualification status

Exact candidate `1b1c91183a4a9a5ea3516699845336175ffe6d96` passes placement/routing, Magic/KLayout DRC, LVS, XOR, antenna, all ten official prechecks and all 25 routed-netlist functional tests. Audit 35448283122 passes setup/hold, recovery/removal, clock-gating, pulse-width, electrical and unconstrained-path checks at all three cell corners with explicit early 0.95 / late 1.05 derating. No SDF simulation was performed. No SRAM waiver, DRC filtering or nonblocking signoff exception is permitted. These results qualify only the named frozen candidate, not arbitrary later changes.

Older compact and SRAM candidates are historical only; their results are in
[the archived notes](notes/README.md). The retained ABI 5 circuit is the one
accepted through PR149. Board and silicon validation remain separate.
