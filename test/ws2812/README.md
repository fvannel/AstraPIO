# WS2812 counter replacement replay

Application test for submitted AstraPIO ABI 5, reference source
`1b1c91183a4a9a5ea3516699845336175ffe6d96`. The hardware is not modified.

The default run executes the eleven existing timed-I/O scenarios and one new
end-to-end application scenario. The latter sends twelve 120-bit frames:
one captured/replaced 24-bit word followed by four relayed 24-bit words.
Two explicitly initialized host counter sequences exercise carry across
`00FFFF -> 010000` and wrap `FFFFFF -> 000000`. Requests occur during incoming
frames and committed values must first appear on the following frame. Frames
without an increment request must repeat the current counter.

The host is a pin-level SPI behaviour model, not an ARM instruction simulator
and not execution of the LPC firmware. It reads and acknowledges the captured
prefix while the tail is still passing. An independent PIO program toggles
another output concurrently. Every DIN/DOUT pulse is observed at public pins:
decoded payloads, pulse count, high/low widths, per-bit latency, IRQ/ACK,
error flags and independent PIO progress are checked.

## Reproduce

From the repository root, create/activate the Python environment as described
in the root README and verify the frozen source and artifacts:

```sh
source .venv/bin/activate
python3 tools/check_final_release.py
make -C test/ws2812 MODE=rtl
python tools/check_results.py work/ws2812-counter-replay/rtl/results.xml
make -C test/ws2812 MODE=gl
python tools/check_results.py work/ws2812-counter-replay/gl/results.xml
```

The expected submitted netlist SHA-256 is
`6d2dbfd333bb89544cf296e9ff408e8870b7151984e7962b098833fd15e3e948`.
PDK models retained in `vendor/ihp-open-pdk/` were copied from Ciel version
`c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`. The default gate-level path
selects `release/tt_um_fabien_pio.v`, the downloaded qualified artifact, not the unrelated
`test/gate_level_netlist.v` file. Do not interpret the reference-commit field
in a report as a provenance check if you override these inputs.

Each mode writes `results.xml` and `counter-report.json` under
`work/ws2812-counter-replay/<mode>/`. JSON contains observed pulses and SPI
results for all twelve frames. The testbench also records `tb.fst` / `tb_gl.fst`
in this directory. Override `RUN_DIR` to preserve results from separate runs.

The historical passing results are retained under
`release/validation/ws2812/{rtl,gl}/`; new executions do not overwrite them.

## Replay result — 2026-09-19

- RTL: **12/12 scenarios PASS**, no failure, error or skip.
- Exact submitted routed netlist: **12/12 scenarios PASS**, no failure, error
  or skip. Netlist hash and source equality were verified before execution.
- The new application scenario checks **12 frames / 1,440 output bits per
  implementation**, with four unchanged tail words in every frame.
- RTL and gate-level observed JSON reports are identical except for `mode`,
  including every recorded input/output edge and SPI read result.
- Observed per-bit latency: **680..699 ns**. Output high widths: **320/640 ns**.
- The host completes prefix reads **58.240..65.074 us** after each input frame
  starts, while the remaining words are still being relayed.
- Counter increments, no-request repeats, carry and wrap all pass. Committing
  during a frame never changes that frame's replacement word.
- Concurrent independent PIO execution, IRQ acknowledgement and error checks
  pass. No RTL, release workflow, timing constraint or submitted revision changed.

First observed frame (24-bit words, hexadecimal):

```text
DIN:   123456  D0448D  8D5FC3  94B2B6  2F4DC0
DOUT:  00FFFE  D0448D  8D5FC3  94B2B6  2F4DC0
SPI RX:123456
```

The tail data is unchanged, but its pulses are regenerated, not an electrical
wire bypass. The first output pulse starts 687 ns after the first input pulse
in this frame, before the 24-bit capture has finished. A host commit of
`00FFFF` completes at 34.120 us and first affects the next frame.

## Limits

Both modes are **functional, without SDF annotation**, at a 50 MHz ASIC clock.
The PDK functional model compilation reports unsupported edge-sensitive
`ifnone` paths in Icarus; these runs do not validate those timing arcs.
No gate-level or RTL pass is a claim of annotated timing, metastability
behaviour, physical LPC transport, board voltage compatibility or silicon
qualification. The existing static-timing/signoff evidence remains separate.
