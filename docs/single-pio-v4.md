# AstraPIO ABI v4 — single PIO plus timed I/O

Development branch `feature/single-pio-timed`. **Not physically qualified or
submitted.** The submitted ABI-v3 compact fallback remains commit `946648ff`,
shuttle PR 142. Its physical results do not qualify this RTL.

## Approved tradeoff

The prior two-context timed extension failed global placement: 114.466%
effective utilization in the better AREA 2 trial. This variant removes the
second interpreter state and its two queues, peer events/receive arbitration,
and the dual-context scheduler. It retains 16 program words, a two-byte TX
queue and two-byte RX queue, all three 24-bit timed payload registers, and
programmable pulse timing/routing. No SRAM, PDK update, waiver or extra tile.

The remaining interpreter can own any subset of all 14 outputs. Its fetch,
execute, idle, idle cadence remains four ASIC clocks per instruction slot
(80 ns at the 50 MHz target), preserving existing context-zero waveforms.
The timed engine works concurrently and exclusively owns at most one output.
One PIO cannot execute two independent programs simultaneously.

## Software migration

Probe ID register 00 = `5049`, ABI 01 = `0400`, context count 02 = `0001`,
capacity 0F = `1002`. The C driver now rejects ABI v3; all context arguments
must be zero. The Python assembler and frame helper retain their legacy ABI-3
default for archival examples: explicitly select `--abi 4` or `abi=4`.

Register addresses use hexadecimal. RUN (03), RESTART (04), IRQ ACK (05),
RX IRQ mask (0C) and host event SET/CLEAR (0D/0E) accept only bit zero.
RUN/RESTART values 2 or 3 are errors, not aliases of context zero. RESTART 1
stops, clears interpreter fault/IRQ/event/state and flushes both queues, but
retains program, output ownership and output levels/directions. Host error is
cleared separately by writing 1 to 06. Reset/deselection releases the pads and
invalidates program length and timed payload-valid flags.

The sole context page is 10..1F; the former 20..2F page reads zero and rejects
writes. 10 is a **14-bit absolute output mask** (bits 15:14 must be zero),
11 entry PC, 12 accumulator, 13 remaining delay, 14 TX, 15 destructive RX,
16 queue status, 17 loop counter, 1F program length. RX bit 15 indicates valid;
only complete valid SPI reads consume a byte. An aborted or empty snapshot
cannot consume a later arrival. Program 40..4F must be uploaded consecutively
while stopped; 0A=0 invalidates it and resets the PC. Read back every word.

Global 06 reports host error in bit 0 and instruction fault in bit 8. 07
reports PIO output levels, 08 directions, 09 synchronized inputs. 0B is program
write busy. Instruction fetch/read/write guards retain the latch-store rules
documented in `compact-v3.md`.

## ISA differences from v3

- `OUT` (`3000`) writes accumulator bits 6:0 to owned output bits 6:0.
- `OUT 1` (`3100`) writes accumulator bits 6:0 to owned output bits 13:7.
- `DIR` controls all eight owned uio direction bits using accumulator bits 7:0.
- `SET p,v` and `OUTBIT p` use **absolute output p = 0..13**.
- `AWAIT` waits for and consumes a host-set event; `CLR_EVENT` clears it.
- Peer-only `SIGNAL` and `RECV` are removed and fault if executed.
- Other byte ALU, branches, input selection, delays, counted loops, PULL/PUSH,
  IRQ and HALT retain their v3 encodings. PC never wraps at word 15.

Output 0..7 means uio0..7; output 8..13 means uo2..7. Input 0..7 means
uio0..7; input 8..12 means ui3..7. Owning a uio pin does not enable output:
use DIR. Dedicated outputs are always physically driven; use external wiring
accordingly. MISO remains push-pull, requiring a dedicated bus or isolation.

## Timed engine

Page 60..6C, transaction protocol, limits and error handling are unchanged
from `timed-pio-v4.md`'s experimental pulse engine. Its name predates ABI v4;
that document's dual-context area/results are historical, not this candidate.
The engine is configurable, not a hardwired WS2812 controller. At the tested
WS2812B-V5 profile it captures the first 24 input bits after qualified idle,
simultaneously transmits the committed 24-bit replacement, then regenerates
the tail with uniform launch latency. The LPC increments/stages the replacement
between frames. It does not need to process each incoming bit.

## Verification scope

21 pin-level RTL scenarios: 10 single-context + 11 timed, including 14 output
indices, FIFO backpressure/aborted reads, program patterns/atomicity, illegal
instructions, reset/deselect, UART cadence, host events and concurrent timed
relay. Timed sweeps retain 24 prefix lengths, 20 input clock phases and atomic
commit/late-host/malformed-frame tests. Two memory/FIFO unit benches, Python
tool/policy tests and sanitized portable C bus-boundary tests supplement them.
These are bounded tests, not exhaustive proof or board/silicon qualification.
Physical placement, routing, DRC, LVS, unchanged official precheck, routed
functional simulation and supplemental derated timing must pass anew.
