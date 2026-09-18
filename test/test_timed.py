"""Timed extension acceptance through top-level pins and host SPI only."""
import cocotb
from cocotb.triggers import Timer, Edge
from cocotb.utils import get_sim_time
from spi_host import setup


async def configure(host, *, length=24, din=0, dout=8, idle=15000,
                    sample=25, launch=32, high0=16, high1=32):
    await host.write(0x61, 0)
    await host.write(0x62, din | (dout << 4))
    await host.write(0x63, idle)
    await host.write(0x64, sample | (launch << 8))
    await host.write(0x65, high0 | (high1 << 8))
    await host.write(0x66, length)


async def send_bits(dut, value, count, *, period=1250, high0=320, high1=640):
    for i in range(count-1, -1, -1):
        high = high1 if value & (1 << i) else high0
        dut.uio_in.value = 1
        await Timer(high, unit="ns")
        dut.uio_in.value = 0
        await Timer(period-high, unit="ns")


async def watch_output(dut, pulses):
    prev = (int(dut.uo_out.value) >> 2) & 1
    rise = None
    while True:
        await Edge(dut.uo_out)
        value = (int(dut.uo_out.value) >> 2) & 1
        if value != prev:
            now = float(get_sim_time(unit="ns"))
            if value: rise = now
            elif rise is not None: pulses.append((rise, now-rise))
            prev = value


def check_pulses(pulses, expected, count):
    assert len(pulses) == count, (len(pulses), count)
    decoded = 0
    for i, (rise, high) in enumerate(pulses):
        bit = (expected >> (count-1-i)) & 1
        assert high == (640 if bit else 320), (i, high, bit)
        decoded = (decoded << 1) | int(high >= 480)
        if i+1 < count:
            low = pulses[i+1][0] - rise - high
            assert 580 <= low <= 1000, (i, low)
    assert decoded == expected


async def stage(host, value, control=0):
    await host.write(0x67, value & 0xFFFF)
    await host.write(0x68, value >> 16)
    await host.write(0x61, control | 0x200)


@cocotb.test()
async def idle_qualified_prefix_capture(dut):
    host = await setup(dut)
    assert await host.read(0x60) == 0x5449
    assert await host.read(0x6C) == 0x0118
    await configure(host)
    await host.write(0x61, 1)  # RX only; the engine must not drive DOUT.
    await send_bits(dut, 0xFFFFFF, 24)  # No qualified reset: ignore this.
    assert await host.read(0x6B) & 4 == 0
    await Timer(310, unit="us")
    await send_bits(dut, 0x123456, 24)
    await send_bits(dut, 0xABCDEF, 24)  # The tail must not overwrite the prefix.
    assert await host.read(0x6B) & 4
    assert await host.read(0x69) == 0x3456
    assert await host.read(0x6A) == 0x12
    assert int(dut.uo_out.value) & 4 == 0


@cocotb.test()
async def prefix_replacement_and_unbroken_tail(dut):
    host = await setup(dut)
    await configure(host)
    await stage(host, 0x012345)
    await host.write(0x61, 7)
    await Timer(310, unit="us")
    pulses = []
    task = cocotb.start_soon(watch_output(dut, pulses))
    original = 0x123456
    tail = 0x00FF558001FE
    await send_bits(dut, (original << 48) | tail, 72)
    await Timer(2, unit="us")
    task.cancel()
    check_pulses(pulses, (0x012345 << 48) | tail, 72)
    assert await host.read(0x69) == 0x3456
    assert await host.read(0x6A) == 0x12
    assert await host.read(0x6B) & 0xE0 == 0


@cocotb.test()
async def uninitialized_payload_cannot_be_committed(dut):
    host = await setup(dut)
    await host.write(0x61, 0x200)
    status = await host.read(0x6B)
    assert status & 0x20 and status & 8 == 0
    assert await host.read(0x67) == 0
    assert await host.read(0x68) == 0
    await host.write(0x67, 0x1234)
    await host.write(0x61, 0x600)
    assert await host.read(0x6B) & 0x20
    await host.write(0x68, 0x56)
    await host.write(0x61, 0x600)
    assert await host.read(0x6B) & 0x38 == 8
    assert await host.read(0x6A) == 0
    assert int(dut.uo_out.value) & 4 == 0
    assert await host.read(0x69) == 0
