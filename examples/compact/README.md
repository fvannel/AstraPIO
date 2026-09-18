# Compact ABI v3 examples

These programs use the new 16-word shared store and four-clock context slots.
Files one directory above are historical SRAM/ABI v2 examples, **not** validated
for this revision. In particular, the former WS2812 transmitter and relay do not
fit the shared 16-word budget. No unchanged WS2812 compatibility is claimed.

Load the shared program once, configure each stopped context's entry PC at
0x11/0x21, configure ownership, then run. TX and RX queues hold only two bytes
each; software must respect credits. A halted/blocked context does not accelerate
its peer: timing remains one instruction slot per four ASIC clocks.
