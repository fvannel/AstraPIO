# Timed PIO experiment — not a submitted revision

The validated compact candidate `946648ff` / shuttle PR 142 remains the fallback.
This experiment adds one shared, configurable pulse-I/O engine beside the two
unchanged compact contexts. No WS2812-specific constants are built into its
protocol: input/output selection, idle qualification, prefix length, sample
delay, output delay and both pulse widths are registers. Existing PIO programs
and ABI 0x0300 remain supported; the extension has its own identity/version.

## Acceptance scope

At a 50 MHz ASIC clock the initial application profile is WS2812B V5:
idle >=300 us; bit periods 1240..1300 ns; legal input highs/lows within the
manufacturer's V5 table; output high 320/640 ns. Both paths use the same delayed
output scheduling, including the first relayed bit. No instantaneous mux splice.
The LPC's 24-bit counter is prepared before a frame; an explicit commit becomes
active at the next frame. The completed RX prefix is frozen until acknowledged.
If the LPC is late, keep the old RX result, flag overrun, and continue the relay.

The 24-bit maximum is an area-conscious prototype choice, not a WS2812 decoder:
all prefix lengths 1..24 are programmable, as are pulse timing and idle duration.
Only one output is owned by this shared engine. A core context may not claim it
at the same time. Configuration changes require the engine disabled; staged
payload updates are allowed while a frame runs, with commit locking the staging
register until the next frame consumes it. Output is zero when disabled/reset.

## Proposed host map, page 0x60

| Address | Function |
|---|---|
| 60 | Identity 0x5449 |
| 61 | Control: enable bit0, output enable bit1, replace prefix bit2; write pulses ACK RX bit8, COMMIT bit9, clear errors bit10 |
| 62 | Pins: DIN selector bits3:0 (0..12), DOUT bits7:4 (0..13) |
| 63 | Continuous-low qualification, ASIC cycles, 1..65535 |
| 64 | Sample delay bits5:0; output delay bits13:8; 1 <= sample < output <=63 |
| 65 | Zero high cycles bits5:0; one high cycles bits13:8; nonzero |
| 66 | Prefix length, 1..24 |
| 67/68 | Staging payload low16/high8; writes rejected while a commit is pending |
| 69/6A | Completed RX prefix low16/high8, zero if invalid; MSB first on wire |
| 6B | Status: armed, frame, RX valid, commit pending, active TX valid, config/host error, RX overrun, timing error |
| 6C | Extension version/capacity 0x0118 |

Bits outside these encodings are rejected. Disabling aborts the current frame
and releases output ownership; a new qualified idle is required on re-enable.
The received word is right-aligned. Only its configured low N bits are sent.
Read/ack is not an implicit destructive read; a completed word is stable across
two SPI reads until ACK. The engine must not stall serial timing for host access.

## Validation gates

Implement/test vertical slices via SPI and GPIO only: RX prefix and idle,
independent injected TX and tail relay, atomic updates/late host, reset and
configuration conflicts, randomized timings and length. Run all old compact
regressions too. Then measure synthesis and routing in 1x2 on the exact shuttle
PDK. Preserve all DRC/LVS/timing/precheck guards and run explicit derating audit.
No new platform revision unless every required gate passes. No automatic main
merge is needed for a commit-specific submission.

Existing domain references: `compact-v3.md`, `compact-validation.md`; no repository
agent configuration or issue workflow exists. The autonomous experiment uses
these existing docs and this local ledger, without creating issues or labels.
