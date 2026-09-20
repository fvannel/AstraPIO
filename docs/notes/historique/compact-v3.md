# AstraPIO compact — ISA/ABI 0x0300

Experimental replacement for the SRAM-based ABI 0x0200. The old implementation
is preserved on `diagnostic/sram-magic` at `f7f5ca6`. This revision has **no SRAM
macro**. Its official physical flow and supplemental timing audit now pass;
final release/board review remains necessary, as detailed in the validation ledger.

## Architecture and capacity

- Two architectural contexts share an 8-bit datapath and **16 total 16-bit program
  words**, not 16 words each. Both may run the same code or different regions.
- Each context has a PC, byte accumulator, byte delay, 4-bit loop counter, event,
  fault, IRQ and fixed seven-output ownership mask.
- One TX and one RX queue per context, each **two bytes**. Total payload storage:
  32 program bytes + 8 queue bytes; execution and interface registers are extra.
- Fixed four-clock sequence: fetch context 0, execute 0, fetch 1, execute 1.
  A context receives one slot every four ASIC clocks even when its peer stops.
  At the exploratory 50 MHz target, one slot is 80 ns.
- Blocking WAIT/PULL/PUSH/AWAIT/RECV stalls only the requesting context.
- This is a general programmable IO engine, not a WS2812-specific ASIC and not
  instruction-compatible with Raspberry Pi PIO.

## Program memory implementation and timing obligations

The store uses 256 `sg13g2_dlhq_1` latches and 16 `sg13g2_lgcp_1` integrated
clock-gating cells from the **unchanged c4b8b4e shuttle PDK**, plus capture/control
registers. No user-generated combinational clock gate replaces the characterized
ICG. The ICG is explicitly instantiated despite its automatic-mapping `dont_use`
attribute; its existing functional, timing, physical and LVS views are retained.

An accepted write captures address/data on rising edge N. The selected ICG opens
its row on rising N+1 and closes it on falling N+1. Address and data remain stable
until a later accepted request, no earlier than rising N+3. Busy covers the two
intervening cycles. Requests during busy are rejected by the core with host_error;
the memory unit itself ignores them. Payload is not reset. Program length resets
to zero so stale/uninitialized storage is never executable or host-readable.

This sequencing must be checked **after routing**: ICG gating checks, latch
setup/hold, propagated row clocks, clock pulse widths and unconstrained endpoints.
Functional simulation and synthesis area do not establish those properties.
The old SRAM-specific timing override is no longer selected: the flow uses the
official base SDC. No false-path or relaxed uncertainty is introduced here.

## SPI and pins

The existing pinout and mode-0, MSB-first, 32-clock transactions are retained:
`[command:8][address:8][data:16]`, command 0x02 write / 0x03 read. SCK high/low and
CS setup/hold/gap must each be at least **six ASIC clock periods**. The software
driver must serialize all transactions and wait for physical transfer completion.
MISO is a dedicated output, not tri-stated: use a dedicated host bus or external
isolation. No exact LPC546xx board-level timing is claimed.

Inputs: ui0=SCK, ui1=MOSI, ui2=CS_n; ui3..7 are PIO inputs 8..12;
uio0..7 are PIO inputs 0..7 and programmable outputs 0..7.
uo0=MISO, uo1=IRQ, uo2..7 are outputs 8..13.
Context 0 can own outputs 0..6. Context 1 can own outputs 7..13.
Local SET/OUTBIT pin numbers are 0..6 within that context's bank.

## Register map

All addresses are bytes and data words are 16 bits. Unimplemented reads return 0;
unimplemented writes set sticky host_error. Writes complete only on a full SPI
frame; incomplete frames do not commit. Extra clocks do not form another frame.

| Address | Meaning |
|---|---|
| 00 | Read identity 0x5049 |
| 01 | Read ABI 0x0300; reject incompatible firmware |
| 02 / 03 | Read running bits; write 03 to set running mask, faults remain inhibited |
| 04 | Write-one RESTART per context: stop, clear fault/IRQ/event/state and flush its queues; retain program and GPIO |
| 05 | IRQ pending bits; write-one clear |
| 06 | Host error bit 0; context faults bits 8/9. Write bit 0 to clear host error; RESTART clears faults |
| 07 / 08 / 09 | Read output levels / directions / synchronized inputs |
| 0A | Read shared initialized length; write zero while both stopped and memory idle to invalidate program and reset both PCs |
| 0B | Read memory busy bit 0 |
| 0C | RX-available IRQ mask |
| 0D / 0E | Read events; write-one set / clear |
| 0F | Read capacity 0x1002: 16 shared words, 2 bytes per queue |
| 10 / 20 | Context output ownership mask; only while both stopped; reject pins outside fixed bank |
| 11 / 21 | Context PC; writable 0..15 only while that context is stopped |
| 12 / 22 | Context accumulator; writable while stopped |
| 13 / 23 | Read remaining delay slots |
| 14 / 24 | Write TX byte; a full queue rejects the byte and sets host_error |
| 15 / 25 | Read RX snapshot, valid in bit 15 and byte in bits 7..0; pop only after complete read of a valid snapshot |
| 16 / 26 | Queue status: RX level bits 15:14, TX level 13:12, RXfull/RXempty/TXfull/TXempty bits 3:0 |
| 17 / 27 | Context loop counter; writable low four bits while stopped |
| 1F / 2F | Read shared initialized length; unlike ABI v2, not writable |
| 40..4F | Shared program words, readable/writable only while both stopped and memory idle |

Program writes may overwrite initialized words or append the next word, never
leave a hole. Start/execute checks the initialized length; falling off word 15
faults rather than wrapping. A RUN command during a memory write is rejected.
RESTART resets PC to zero; set a different entry again before RUN when needed.

## ISA

The v2 byte-oriented opcodes are retained with **branch destinations restricted
to 0..15**. The supplied assembler enforces program size and operand ranges.

| Encoding | Operation |
|---|---|
| 0xxx / 1xii | NOP / LDI byte |
| 2000 / 2100 | IN low eight inputs / high five inputs |
| 3000 / 4000 | OUT / DIR using the accumulator, limited by ownership |
| 500a / 600a | JMP / JNZ accumulator to shared address a |
| 7000 | DEC accumulator modulo 256 |
| 800p / 810p | WAIT input p low/high; p=0..12 |
| 90dd | DELAY: consume this slot then dd further slots |
| A0ii / B000 / C000 | XOR byte / SHL / SHR, zero filling |
| D000 / E000 | IRQ / HALT |
| F000 / F100 | Blocking PULL own TX / PUSH own RX |
| F2pL / F3p0 | SET local pin p to level L / OUTBIT accumulator MSB to p, then shift left |
| F40p / F50n | INBIT p into accumulator LSB after shift / LDX loop counter |
| F60a | DJNZ counter to a; initial zero means 16 iterations |
| F700 / F710 / F720 | SIGNAL peer / AWAIT-and-consume own event / clear own event |
| F80a / F900 | JBIT on accumulator MSB / blocking RECV peer RX |

Undefined extended opcodes, invalid WAIT/INBIT/SET pins and out-of-range branch
encodings fault and halt that context. Unused bits of basic non-branch opcodes
are ignored as in v2; software emits canonical encodings.

Host reads lock the selected RX head until the SPI transaction ends. Peer RECV
cannot consume that head while a read snapshot is in flight. A full queue may
accept a simultaneous push/pop. Events generated by execution take precedence
over a same-cycle host clear; RUN and selected RESTART suppress that execution
slot. Input synchronizers provide latency, not guaranteed capture of short pulses.

## Migration and examples

Use `tools/pioasm.py`, `tools/host_protocol.py` and `firmware/pio_host.*` from this
branch together. `pio_load(device, words, count)` now loads the shared store once
and resets both contexts. `pio_set_entry` selects each start address. ABI v2
firmware must not be reused silently. LPC transport/DMA remains board-specific.

Validated application examples live in `examples/compact/`: two-context byte
transform, SPI transmitter and UART transmitter. The old 27-word WS2812 code and
larger relay **do not fit unchanged**. Their old validation is not applicable.
The eleven pin-level scenarios include a full 16-word SPI TX/RX loopback,
an external UART decoder and phased RX arbitration checks. See the
[validation ledger](compact-validation.md) for evidence and outstanding checks.

## Release policy

Local and GitHub diagnostics may run on `feature/compact-pio`. No automatic merge,
Pages deployment or shuttle revision is part of this work. All DRC/LVS/timing
errors remain blocking. Prior SRAM results are historical, not inherited passes.
