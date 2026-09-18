# AstraPIO compact

General-purpose, dual-context programmable digital IO coprocessor for an LPC546xx host, targeting two Tiny Tapeout IHP26b tiles.

**Active branch: compact ISA/ABI 0x0300. Experimental; fabrication qualification pending.**

- Two contexts with deterministic four-clock scheduling.
- One shared 16 × 16-bit latch program store (32 bytes), using unchanged IHP standard cells; no SRAM macro.
- Two-byte TX and RX queues per context (8 bytes total).
- Same SPI pins and 32-bit framing; new ABI, capacity and firmware APIs.
- Exact shuttle PDK c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c; all checks blocking.

See [architecture, register map, ISA and timing obligations](docs/compact-v3.md), [compact examples](examples/compact/README.md), and [current qualification status](design_status.json).

The historical SRAM implementation and its evidence remain on branch `diagnostic/sram-magic` at `f7f5ca6`. Existing SRAM docs, larger examples and test modules are archival unless explicitly selected by the compact test suite. Their passes do not qualify this design. In particular, the previous WS2812 transmitter/relay does not fit unchanged.

## Development

Install the dependencies in `test/requirements.txt`, Icarus Verilog **13**, and the exact IHP standard-cell Verilog models. Icarus 12 does not correctly drive the delayed signals in these latch models; CI uses the same verified version-13 package as the official Tiny Tapeout gate simulation. Set `PDK_ROOT` to the parent of `ihp-sg13g2` (locally defaults to `work/pdk`). Run `make test`. The tests include host tooling, the C driver, FIFO and latch-store unit benches, and pin-level SPI/GPIO application tests.

The manual GDS workflow runs the official Tiny Tapeout physical flow, precheck and gate simulation. It does not merge, publish a viewer or submit a shuttle revision. A successful functional test or synthesis-area estimate is not physical signoff.
