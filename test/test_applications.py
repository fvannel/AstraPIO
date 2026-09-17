"""Protocol-level examples, measured at pins rather than internal CPU state."""
import random
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles, FallingEdge, Timer, with_timeout
from cocotb.utils import get_sim_time
from test import setup

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@cocotb.test()
async def application_spi_two_context_loopback(dut):
    host = await setup(dut)
    await host.write(0x10, 3)
    await host.load(0, (EXAMPLES / "spi_tx.pio").read_text())
    await host.load(1, (EXAMPLES / "spi_rx.pio").read_text())
    payload = bytes((i*73 + 0xA6) & 255 for i in range(16))
    for byte in payload:
        await host.write(0x14, byte)

    async def board_wires():
        while True:
            await FallingEdge(dut.clk)
            dut.uio_in.value = int(dut.uio_out.value) & 3

    wires = cocotb.start_soon(board_wires())
    await host.write(3, 3)
    await ClockCycles(dut.clk, 4000)
    for byte in payload:
        assert await host.read(0x25) == 0x8000 | byte
    assert await host.read(0x26) == 0
    assert await host.read(6) == 0
    wires.cancel()


@cocotb.test()
async def application_spi_stream(dut):
    host = await setup(dut, half=133)
    await host.write(0x10, 3)
    await host.load(0, (EXAMPLES / "spi_tx.pio").read_text())
    payload = bytes([0, 255, 0xA6, 0x39, 0x80, 1])
    for byte in payload:
        await host.write(0x14, byte)
    samples = []

    async def capture():
        prev = 0
        for _ in range(2200):
            await FallingEdge(dut.clk)
            pins = int(dut.uio_out.value)
            if pins & 2 and not prev & 2:
                samples.append(pins & 1)
            prev = pins

    task = cocotb.start_soon(capture())
    await host.write(3, 1)
    await task
    expected = [(b >> bit) & 1 for b in payload for bit in range(7, -1, -1)]
    assert samples == expected
    assert await host.read(6) == 0
    assert await host.read(0x16) == 0


@cocotb.test()
async def application_uart_8n1(dut):
    host = await setup(dut)
    await host.write(0x10, 1)
    await host.load(0, (EXAMPLES / "uart_tx.pio").read_text())
    payload = [0xA6, 0x00, 0xFF]
    for byte in payload:
        await host.write(0x14, byte)
    decoded = []

    async def receiver():
        while not int(dut.uio_out.value) & 1:
            await FallingEdge(dut.clk)
        for _ in payload:
            while int(dut.uio_out.value) & 1:
                await FallingEdge(dut.clk)
            await Timer(4320, unit="ns")
            assert int(dut.uio_out.value) & 1 == 0
            value = 0
            for bit in range(8):
                await Timer(8640, unit="ns")
                value |= (int(dut.uio_out.value) & 1) << bit
            await Timer(8640, unit="ns")
            assert int(dut.uio_out.value) & 1 == 1
            decoded.append(value)

    task = cocotb.start_soon(receiver())
    await host.write(3, 1)
    await with_timeout(task, 400, "us")
    assert decoded == payload
    assert await host.read(6) == 0


@cocotb.test()
async def application_ws2812_transmit_waveform(dut):
    host = await setup(dut)
    await host.write(0x20, 0x100)
    await host.load(1, (EXAMPLES / "ws2812_tx.pio").read_text())
    payload = bytes([0xA6, 0x00, 0xFF, 0x55, 0x81, 0x7E])
    for byte in payload:
        await host.write(0x24, byte)
    rises, widths = [], []

    async def capture():
        previous = 0
        for _ in range(20000):
            await FallingEdge(dut.clk)
            level = (int(dut.uo_out.value) >> 2) & 1
            now = round(get_sim_time(unit="ps"))
            if level and not previous:
                rises.append(now)
            if previous and not level:
                widths.append(now - rises[-1])
            previous = level

    task = cocotb.start_soon(capture())
    await host.write(3, 2)
    await task
    bits = [(b >> bit) & 1 for b in payload for bit in range(7, -1, -1)]
    assert widths == [720000 if bit else 360000 for bit in bits]
    assert set(b-a for a,b in zip(rises, rises[1:])) <= {1200000, 1320000}
    assert len(rises) == len(bits)
    assert get_sim_time(unit="ps") - rises[-1] > 300000000
    assert not int(dut.uo_out.value) & 4
    assert await host.read(6) == 0


@cocotb.test()
async def ws2812_capture_and_programmable_transform(dut):
    host = await setup(dut, half=137)
    # Fully unrolled sampler avoids counter/bookkeeping latency between bytes.
    # Assumes aligned complete bytes, no malformed pulses or partial-frame reset.
    capture = "byte:\n" + "WAIT 8,1\nDELAY 2\nINBIT 8\nWAIT 8,0\n" * 8
    capture += "PUSH\nJMP byte"
    await host.load(0, capture)
    await host.load(1, "loop: RECV\nXOR 0x5A\nPUSH\nJMP loop")
    await host.write(0x0C, 2)
    await host.write(3, 3)
    rng = random.Random(0x2812)
    payload = bytes(rng.randrange(256) for _ in range(12))
    await Timer(13, unit="ns")
    for byte in payload:
        for bit in range(7, -1, -1):
            high = 700 if (byte >> bit) & 1 else 350
            host.inputs = 1
            host.drive()
            await Timer(high, unit="ns")
            host.inputs = 0
            host.drive()
            await Timer(1250-high, unit="ns")
    await ClockCycles(dut.clk, 50)
    assert int(dut.uo_out.value) & 2
    assert await host.read(0x26) == len(payload) << 8
    for byte in payload:
        assert await host.read(0x25) == 0x8000 | (byte ^ 0x5A)
    assert await host.read(0x25) == 0
    assert not int(dut.uo_out.value) & 2
    assert await host.read(6) == 0


@cocotb.test()
async def ws2812_relay_modified_in_software(dut):
    host = await setup(dut)
    capture = "byte:\n" + "WAIT 8,1\nDELAY 2\nINBIT 8\nWAIT 8,0\n" * 8
    capture += "PUSH\nJMP byte"
    transmit = (EXAMPLES / "ws2812_tx.pio").read_text().replace("    PULL", "    RECV\n    XOR 0x5A")
    await host.load(0, capture)
    await host.load(1, transmit)
    await host.write(0x20, 0x100)
    await host.write(3, 3)
    rng = random.Random(0xC1AC017)
    payload = bytes(rng.randrange(256) for _ in range(48))
    widths = []

    async def monitor():
        previous, start = 0, 0
        for _ in range(26000):
            await FallingEdge(dut.clk)
            level = (int(dut.uo_out.value) >> 2) & 1
            now = round(get_sim_time(unit="ps"))
            if level and not previous:
                start = now
            if previous and not level:
                widths.append(now-start)
            previous = level

    task = cocotb.start_soon(monitor())
    await Timer(17, unit="ns")
    for byte in payload:
        for bit in range(7, -1, -1):
            high = 700 if (byte >> bit) & 1 else 350
            host.inputs = 1
            host.drive()
            await Timer(high, unit="ns")
            host.inputs = 0
            host.drive()
            await Timer(1250-high, unit="ns")
    await task
    expected = [720000 if ((b ^ 0x5A) >> bit) & 1 else 360000
                for b in payload for bit in range(7, -1, -1)]
    assert widths == expected
    assert await host.read(6) == 0
    assert await host.read(0x16) == 0
