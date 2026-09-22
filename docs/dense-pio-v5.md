# AstraPIO ABI v5 — final ten-bit instruction architecture

Final submitted source `1b1c91183a4a9a5ea3516699845336175ffe6d96`,
project 5799 / TTIHP26b / 1×2 tiles. PR149 merged on 2026-09-19.
The official physical flow and supplemental derated audit pass.

One general PIO, sixteen ten-bit instruction slots, two-byte queues in each
direction and three 24-bit timed payload banks are retained. Storage uses
standard-cell latches, not SRAM macros. SPI read/write shifting shares storage.

## External interface

Probe ABI register 01 = `0500`; capacity 0F stays `1002` (16 words, depth 2).
The SPI transaction remains command8/address8/data16, mode 0, MSB first, with
six ASIC clocks minimum for every SCK high/low and CS setup/hold/gap. Program
40..4F accepts ten-bit values only; nonzero upper six bits are rejected without
changing memory or length. Reads zero-extend to 16 bits. Invalid ten-bit opcodes
can be read back but fault when executed. All other register semantics are
unchanged from the [single-PIO register description](notes/historique/single-pio-v4.md#software-migration),
except the ABI value and ten-bit instruction format specified here. Its old
release status, binary opcodes and physical results are historical, not current.
No old binary compatibility is claimed.

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

## Timed engine and validation

The timed register page 60..6C retains the interface documented in
[the pulse-engine notes](notes/historique/timed-pio-v4.md). The portable API is
in `firmware/pio_timed.h` / `firmware/pio_timed.c`; the exact ABI-5 application
scenario is [the WS2812 counter replay](../test/ws2812/README.md).
The interpreter and timed engine run concurrently with exclusive output ownership.

The [final validation summary](validation-finale.md) distinguishes 25 pin-level
scenarios, 1,988 differential traces, official signoff and the supplemental
three-corner timing audit. Retained artifacts are in `release/`, with a
SHA-256 manifest binding them to the submitted source. Simulations have no SDF;
physical LPC/board/silicon operation remains unqualified.

The complete chronological study, including failed densities and the flip-flop
alternative, is retained in
[the pre-cleanup engineering notes](notes/historique/dense-pio-v5-before-cleanup.md).
Do not treat historical submission instructions there as the present status.
OUTMSB/ABI 6 was not approved and is not implemented in the final source.
