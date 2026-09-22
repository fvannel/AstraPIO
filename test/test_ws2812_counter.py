"""Application replay: a SPI host model owns the counter, never the bit timing.

Uses only public Tiny Tapeout pins. Reports observations, not just stimuli.
Functional RTL/PDK-netlist simulation; no SDF or physical LPC is involved.
"""
import json
import os
from pathlib import Path
import random

import cocotb
from cocotb.triggers import Edge, Timer
from cocotb.utils import get_sim_time
from spi_host import setup


def now_ns():
    return float(get_sim_time(unit="ns"))


async def observe(signal, bit, pulses):
    previous = (int(signal.value) >> bit) & 1
    rise = None
    while True:
        await Edge(signal)
        level = (int(signal.value) >> bit) & 1
        if level != previous:
            if level:
                rise = now_ns()
            elif rise is not None:
                pulses.append((rise, now_ns() - rise))
        previous = level


async def transmit(dut, word, count, period, high0, high1):
    for bit in range(count - 1, -1, -1):
        high = high1 if (word >> bit) & 1 else high0
        dut.uio_in.value = 1
        await Timer(high, unit="ns")
        dut.uio_in.value = 0
        await Timer(period - high, unit="ns")


def decode(pulses):
    result = 0
    for _, high in pulses:
        result = (result << 1) | int(high >= 500)
    return result


async def commit(host, word, control):
    await host.write(0x67, word & 0xFFFF)
    await host.write(0x68, word >> 16)
    await host.write(0x61, control | 0x200)


@cocotb.test()
async def lpc_counter_on_demand_replaces_prefix_and_relays_tail(dut):
    host = await setup(dut)
    assert await host.read(0x00) == 0x5049
    assert await host.read(0x01) == 0x0500
    assert await host.read(0x60) == 0x5449

    # Independent general PIO program keeps toggling uio1 during all traffic.
    # LDI 2; DIR; SET 1,1; SET 1,0; JMP 2 (native ABI-5 words).
    await host.write(0x10, 2)
    for address, word in enumerate((0x002, 0x301, 0x371, 0x361, 0x312)):
        await host.write(0x40 + address, word)
    await host.write(0x03, 1)

    incoming, outgoing, pio_pulses = [], [], []
    monitors = [cocotb.start_soon(observe(dut.uio_in, 0, incoming)),
                cocotb.start_soon(observe(dut.uo_out, 2, outgoing)),
                cocotb.start_soon(observe(dut.uio_out, 1, pio_pulses))]
    rng = random.Random(0xA57A0500)
    frames = []
    # Two explicitly initialized counter sequences; no increment on False.
    requests = (True, False, True, True, False, False)
    for seed in (0x00FFFE, 0xFFFFFE):
        await host.write(0x61, 0)
        for address, value in ((0x62, 0x80), (0x63, 15000),
                               (0x64, 0x2019), (0x65, 0x2010), (0x66, 24)):
            await host.write(address, value)
        counter = seed
        await commit(host, counter, 0)
        await host.write(0x61, 7)

        for request in requests:
            index = len(frames)
            host.half = (120, 133, 137)[index % 3]
            await Timer(310_000, unit="ns")
            assert await host.read(0x6B) & 1  # Qualified low/reset interval.
            phase = (index * 7 + 3) % 20
            offset = (phase - int(now_ns()) % 20) % 20
            if offset:
                await Timer(offset, unit="ns")
            assert int(now_ns()) % 20 == phase

            prefix = (0x123456, 0xABCDEF, 0x000000, 0xFFFFFF,
                      0xA55A80, 0x010203)[index % 6]
            tail = rng.getrandbits(96)  # Four more RGB words, unchanged.
            word = (prefix << 96) | tail
            expected = (counter << 96) | tail
            period = (1240, 1250, 1280, 1300)[index % 4]
            high0, high1 = ((320, 640), (380, 580))[index % 2]
            in_before, out_before = len(incoming), len(outgoing)
            pio_before = len(pio_pulses)
            start = now_ns()
            stream = cocotb.start_soon(transmit(dut, word, 120, period, high0, high1))

            # The modelled LPC receives a request during the first RGB word.
            # The update must affect the NEXT frame, never tear this prefix.
            await Timer(10_000, unit="ns")
            next_counter = (counter + 1) & 0xFFFFFF if request else counter
            committed_at = None
            if request:
                await commit(host, next_counter, 7)
                committed_at = now_ns() - start
            else:
                await Timer(24_000, unit="ns")
            status = await host.read(0x6B)
            assert status & 4, (index, "RX word missing", status)
            assert (status & 8 != 0) == request, (index, "pending commit", status)
            assert status & 0xE0 == 0, (index, "engine error", status)
            assert int(dut.uo_out.value) & 2, (index, "RX IRQ not asserted")
            received = await host.read(0x69) | (await host.read(0x6A) << 16)
            received_at = now_ns() - start
            assert received == prefix, (index, "SPI capture", received, prefix)
            assert received_at < 120 * period, "Host read must overlap the tail"
            await host.write(0x61, 0x107)  # Explicit ACK; relay remains enabled.
            assert await host.read(0x6B) & 4 == 0
            assert int(dut.uo_out.value) & 2 == 0

            await stream
            await Timer(2_000, unit="ns")
            observed_in = incoming[in_before:]
            observed_out = outgoing[out_before:]
            assert len(observed_in) == len(observed_out) == 120
            assert decode(observed_in) == word
            assert decode(observed_out) == expected, (index, "output differs")
            latencies = []
            for bit, ((din_rise, _), (dout_rise, high)) in enumerate(zip(observed_in, observed_out)):
                expected_bit = (expected >> (119 - bit)) & 1
                assert high == (640 if expected_bit else 320), (index, bit, high)
                latencies.append(dout_rise - din_rise)
                assert 680 <= latencies[-1] <= 700, (index, bit, latencies[-1])
                if bit:
                    low = dout_rise - observed_out[bit - 1][0] - observed_out[bit - 1][1]
                    assert 580 <= low <= 1000, (index, bit, "low", low)
            assert observed_out[0][0] < observed_in[23][0], "Output must stream during capture"
            assert len(pio_pulses) - pio_before > 100
            assert await host.read(0x03) == 1
            assert await host.read(0x06) == 0
            final_status = await host.read(0x6B)
            assert final_status & 0xE0 == 0
            # Host reads and silence after the frame must create no extra bit.
            assert len(outgoing) == out_before + 120

            frames.append({
                "frame": index + 1, "counter_seed_hex": f"{seed:06X}",
                "din_prefix_hex": f"{prefix:06X}",
                "spi_rx_hex": f"{received:06X}",
                "dout_prefix_hex": f"{decode(observed_out[:24]):06X}",
                "tail_in_hex": f"{tail:024X}",
                "tail_out_hex": f"{decode(observed_out[24:]):024X}",
                "increment_requested": request, "next_counter_hex": f"{next_counter:06X}",
                "spi_half_ns": host.half, "input_phase_ns": phase,
                "period_ns": period, "input_high_zero_ns": high0, "input_high_one_ns": high1,
                "latency_min_ns": min(latencies), "latency_max_ns": max(latencies),
                "commit_completed_ns": committed_at, "spi_rx_completed_ns": received_at,
                "pio_pulses_during_frame": len(pio_pulses) - pio_before,
                "din_pulses_ns": [(rise - start, high) for rise, high in observed_in],
                "dout_pulses_ns": [(rise - start, high) for rise, high in observed_out],
                "status": "PASS",
            })
            dut._log.info("Frame %02d DIN=%06X SPI_RX=%06X DOUT=%06X tail=OK increment=%s next=%06X",
                          index + 1, prefix, received, counter, request, next_counter)
            counter = next_counter

    for monitor in monitors:
        monitor.cancel()
    report = {"status": "PASS", "mode": os.environ.get("ASTRA_WS_MODE", "unspecified"),
              "source_commit": "1b1c91183a4a9a5ea3516699845336175ffe6d96",
              "asic_clock_hz": 50_000_000, "frame_count": len(frames),
              "checked_output_bits": 120 * len(frames), "sdf_annotated": False,
              "host": "SPI pin-level LPC behaviour model; not firmware execution",
              "frames": frames}
    if os.environ.get("ASTRA_WS_REPORT"):
        path = Path(os.environ["ASTRA_WS_REPORT"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n")
    dut._log.info("WS2812 counter replay PASS: %d frames, %d output bits checked",
                  len(frames), report["checked_output_bits"])
