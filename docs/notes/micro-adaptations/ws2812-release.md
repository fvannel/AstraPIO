# WS2812 application: mandatory release contract

The candidate must preserve the user's application, not just generate a valid
WS2812 waveform. The LPC owns a 24-bit counter; the autonomous timed engine owns
bit timing. The general PIO must remain independently usable at the same time.

## Required behaviour

1. A sufficiently long low input qualifies a new frame (300 us in this test).
2. Capture the first 24 DIN bits and expose them to the host over SPI, with IRQ.
3. Concurrently emit the host's previously committed counter on DOUT.
4. Regenerate all subsequent input bits unchanged, without a host transaction
   per bit or per LED. This is a delayed regenerated relay, not an electrical
   zero-delay bypass and not consumption/removal of the first word.
5. Accept an increment request or retain the counter when no request occurs.
   A counter committed during a frame must take effect only on the next frame.
6. IRQ acknowledgement and host reads must not interrupt the relayed tail.
7. Concurrent OUTMSB activity on a different owned pin must remain operational.

## Reproducible evidence

`test/test_ws2812_counter.py` uses only public ASIC pins and the SPI register
interface. It sends twelve 120-bit frames (five RGB words each), with two
counter sequences starting at `00FFFE` and `FFFFFE`. The request pattern checks
hold, carry and 24-bit wrap. Six input prefixes include all-zero and all-one
values; four trailing words are independently seeded random data per frame.
Input phases, legal pulse widths and SPI periods vary. Every DOUT bit is
decoded from observed edges, not copied from stimulus expectations.

Local RTL result: all 29 suite scenarios pass; the dedicated application checks
1,440 output bits, first-word capture, every trailing bit, IRQ/ACK, atomic
next-frame commits and concurrent PIO progress. Observed input-to-output rise
latency is 680–697 ns under these phases. Output highs are 320 ns / 640 ns.
The separate timed-engine suite covers malformed frames, missing data,
ownership, resets and every input phase at the configured timing limits.

Run `make test`, then `python3 tools/check_ws2812_release.py --mode rtl`.
The official GDS workflow runs the same suite with `GATES=yes`, then invokes
the checker with `--mode gl`. Both CI artifact sets preserve the JSON evidence.

The checker rejects absent, incomplete or stale evidence. It binds the report
to the checked-out source commit and RTL SHA256 values. For routed simulation
it also checks the submission commit, frozen PDK and the SHA256 of the exact
simulated/submission netlist. Unit tests exercise acceptance and rejection of
malformed evidence; these are not substitutes for the pin-level simulation.

## Release decision

Functional RTL success alone does not authorize submission. The final source
must also pass the official full physical flow (Magic/KLayout DRC, LVS, XOR,
antenna, timing), all official prechecks, all 29 routed functional scenarios,
the WS2812 evidence checker and the separate three-cell-corner timing audit
with early 0.95 / late 1.05 derating. No check may be bypassed. The existing
qualified ABI5 revision `1b1c911` / shuttle PR149 is the fallback.

The selected qualitative gain is OUTMSB: it preserves the accumulator while
outputting its high bit, enabling the demonstrated 14-instruction mode-0
full-duplex SPI byte program without reducing memory or the timed engine.
Other prototype features have not been approved. If this minimal addition
cannot meet unchanged physical constraints, retain the qualified fallback.

After all gates pass, submit the exact qualified commit to project 5799 and
verify the resulting revision, pull request and central precheck. Do not submit
a later documentation-only HEAD or claim success merely because an upload
started. The user explicitly authorized this conditional submission.

## Limits

The host is a pin-level LPC behaviour model, not execution of ARM firmware.
Gate simulation has no SDF annotation. Timing signoff covers the specified
50 MHz clock, IO constraints, three cell corners and nominal extracted RC;
it is not a board-level qualification or proof for every WS2812 variant.
Actual LPC546xx SPI/DMA integration, clock quality, voltage translation and
real LED timing must still be checked on hardware. The host must service the
capture mailbox before a subsequent completed prefix if every frame matters.
