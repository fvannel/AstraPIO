# AstraPIO ABI v5 — native ten-bit instruction experiment

Branch `codex/dense-pio10`. Not physically qualified or submitted. The merged
compact fallback `946648ff` / shuttle PR 142 remains unchanged.

The user approved reducing storage representation and sharing SPI shift storage,
not reducing capabilities. Keep one general PIO, sixteen instruction slots,
two-byte queues in each direction and three 24-bit timed payload banks.

## External interface

Probe ABI register 01 = `0500`; capacity 0F stays `1002` (16 words, depth 2).
The SPI transaction remains command8/address8/data16, mode 0, MSB first, with
six ASIC clocks minimum for every SCK high/low and CS setup/hold/gap. Program
40..4F accepts ten-bit values only; nonzero upper six bits are rejected without
changing memory or length. Reads zero-extend to 16 bits. Invalid ten-bit opcodes
can be read back but fault when executed. All other register semantics are
unchanged from `single-pio-v4.md`; no old binary compatibility is claimed.

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

## Validation sequence

First, the ABI-5 pin-level tracer failed against v4, then passed after native
ten-bit storage/decode. All 23 pin-level integration scenarios pass locally
before SPI sharing. Assembler checks enumerate all 944 encodings. C driver
checks reject old ABIs and oversized words; sanitizer checks pass.

Physical baseline is diagnostic run 35436643505: v4 passed CTS but failed
post-hold legalization after adding 390 buffers. The planned comparison keeps
the exact PDK, two-tile boundary, clocks, margins, corners and checkers fixed:
first measure encoding alone, then shared SPI. Neither a smaller cell count nor
functional tests qualify a release. Full routing/checks and a new explicit
derated timing audit remain mandatory before any new submission.

The repository has no separate agent glossary/ADR configuration; existing
`compact-v3.md`, `single-pio-v4.md` and their validation ledgers remain the
domain references. No issue-tracker setup, label or external issue is created.
