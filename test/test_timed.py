"""Timed extension acceptance through top-level pins and host SPI only."""
import cocotb
import random
from cocotb.triggers import Timer, Edge, ClockCycles
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


async def send_bits(dut, value, count, *, period=1250, high0=320, high1=640, din=0):
    for i in range(count-1, -1, -1):
        high = high1 if value & (1 << i) else high0
        dut.uio_in.value = 1 << din
        await Timer(high, unit="ns")
        dut.uio_in.value = 0
        await Timer(period-high, unit="ns")


async def watch_output(dut, pulses, dout=8):
    signal = dut.uio_out if dout < 8 else dut.uo_out
    bit = dout if dout < 8 else dout-6
    prev = (int(signal.value) >> bit) & 1
    rise = None
    while True:
        await Edge(signal)
        value = (int(signal.value) >> bit) & 1
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


@cocotb.test()
async def atomic_update_and_late_host(dut):
    host = await setup(dut)
    await configure(host)
    await stage(host, 0x00FFFF)
    await host.write(0x61, 7)
    await Timer(310, unit="us")
    pulses = []
    task = cocotb.start_soon(watch_output(dut, pulses))
    tail = int("a55a" * 12, 16)
    stream = cocotb.start_soon(send_bits(dut, (0x112233 << 192) | tail, 216))
    await Timer(10, unit="us")
    await stage(host, 0x010000, control=7)  # A carry across both payload registers.
    assert await host.read(0x6B) & 8
    await host.write(0x67, 0xFFFF)  # Must not corrupt the pending committed value.
    assert await host.read(0x6B) & 0x20
    await host.write(0x61, 0x407)
    await stream
    await Timer(2, unit="us")
    check_pulses(pulses, (0x00FFFF << 192) | tail, 216)
    assert await host.read(0x69) == 0x2233
    assert await host.read(0x6A) == 0x11
    assert await host.read(0x6B) & 0xE0 == 0
    pulses.clear()
    await Timer(310, unit="us")
    # No RX ACK: output must continue, preserving the previous complete RX word.
    await send_bits(dut, (0xABCDEF << 24) | 0x5A55AA, 48)
    await Timer(2, unit="us")
    check_pulses(pulses, (0x010000 << 24) | 0x5A55AA, 48)
    assert await host.read(0x6B) & 0xC8 == 0x40
    assert await host.read(0x69) == 0x2233
    assert await host.read(0x6A) == 0x11
    # Acknowledge and clear errors. The same TX value repeats without a commit.
    await host.write(0x61, 0x507)
    assert await host.read(0x69) == 0
    pulses.clear()
    await Timer(310, unit="us")
    await send_bits(dut, 0xFEDCBA, 24)
    await Timer(2, unit="us")
    check_pulses(pulses, 0x010000, 24)
    assert await host.read(0x69) == 0xDCBA
    assert await host.read(0x6A) == 0xFE
    assert await host.read(0x6B) & 0xE0 == 0
    task.cancel()


@cocotb.test()
async def randomized_legal_waveforms_and_lengths(dut):
    host = await setup(dut, half=137)
    rng = random.Random(0xA57A)
    cases = 0
    for length in range(1, 25):
        await configure(host, length=length)
        replacement = rng.getrandbits(length)
        await stage(host, replacement)
        await host.write(0x61, 0x507)
        await Timer(310_000 + rng.randrange(20), unit="ns")
        periods = [1240, 1250, 1280, 1300]
        period = periods[length % 4]
        # Choose only highs/lows inside the WS2812B V5 specification.
        h0 = rng.randrange(max(220, period-1000), 381)
        h1 = rng.randrange(580, min(1000, period-580)+1)
        prefix = rng.getrandbits(length)
        tail_length = 64
        tail = rng.getrandbits(tail_length)
        pulses = []
        task = cocotb.start_soon(watch_output(dut, pulses))
        input_start = float(get_sim_time(unit="ns"))
        await send_bits(dut, (prefix << tail_length) | tail, length+tail_length,
                        period=period, high0=h0, high1=h1)
        await Timer(2, unit="us")
        check_pulses(pulses, (replacement << tail_length) | tail, length+tail_length)
        assert 680 <= pulses[0][0]-input_start <= 700
        assert await host.read(0x69) | (await host.read(0x6A) << 16) == prefix
        assert await host.read(0x6B) & 0xE0 == 0
        task.cancel()
        cases += length+tail_length
    dut._log.info("Random timing sweep: 24 lengths, %d checked output pulses", cases)


@cocotb.test()
async def pin_ownership_and_safe_disable(dut):
    host = await setup(dut)
    await configure(host, dout=0)
    await host.write(0x10, 1)  # Core owns uio0, even while stopped.
    await host.write(0x61, 3)
    assert await host.read(0x61) == 0
    assert await host.read(0x6B) & 0x20
    await host.write(0x10, 0)
    await host.write(0x61, 0x403)
    assert int(dut.uio_oe.value) == 1
    await host.write(0x10, 1)
    assert await host.read(0x10) == 0
    assert await host.read(6) & 1
    await host.write(0x62, 0x81)  # Active pin reassignment is rejected.
    assert await host.read(0x62) == 0
    assert await host.read(0x6B) & 0x20
    dut.ena.value = 0
    await Timer(1, unit="ns")
    assert int(dut.uio_oe.value) == 0 and int(dut.uo_out.value) == 0
    dut.ena.value = 1
    await host.write(0x61, 0x400)
    assert int(dut.uio_oe.value) == 0
    await host.write(0x10, 1)
    assert await host.read(0x10) == 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_oe.value) == 0 and int(dut.uo_out.value) == 0


@cocotb.test()
async def simultaneous_single_program_and_timed_relay(dut):
    from test_single import load_program
    host = await setup(dut)
    await load_program(host, [0x371, 0x379, 0x361, 0x369, 0x310])
    await host.write(0x10, 0x202)
    await configure(host)
    await stage(host, 0xAA55FF)
    await host.write(0x61, 7)
    await host.write(3, 1)
    await Timer(310, unit="us")
    pulses, core_edges = [], [0, 0]
    async def count_edges(signal, bit, index):
        prev = (int(signal.value) >> bit) & 1
        while True:
            await Edge(signal)
            value = (int(signal.value) >> bit) & 1
            if value != prev: core_edges[index] += 1
            prev = value
    tasks = [cocotb.start_soon(watch_output(dut, pulses)),
             cocotb.start_soon(count_edges(dut.uio_out, 1, 0)),
             cocotb.start_soon(count_edges(dut.uo_out, 3, 1))]
    await send_bits(dut, 0x123456AABBCC, 48)
    await Timer(2, unit="us")
    check_pulses(pulses, 0xAA55FFAABBCC, 48)
    assert all(n > 100 for n in core_edges), core_edges
    assert await host.read(3) == 1
    assert await host.read(6) == 0
    assert await host.read(0x6B) & 0xE0 == 0
    for task in tasks: task.cancel()


@cocotb.test()
async def generic_timing_and_routing_profile(dut):
    host = await setup(dut)
    await configure(host, length=7, din=3, dout=5, idle=2000,
                    sample=5, launch=8, high0=3, high1=6)
    for address, invalid in [(0x62, 0xFD), (0x63, 0), (0x64, 0x0405),
                             (0x65, 0x0600), (0x66, 25), (0x68, 0x100),
                             (0x61, 0x8000), (0x60, 1)]:
        before = await host.read(address)
        await host.write(address, invalid)
        assert await host.read(address) == before
        assert await host.read(0x6B) & 0x20
        await host.write(0x61, 0x400)
    await stage(host, 0x51)
    await host.write(0x61, 7)
    assert int(dut.uio_oe.value) == 1 << 5
    await Timer(50, unit="us")
    pulses = []
    task = cocotb.start_soon(watch_output(dut, pulses, dout=5))
    await send_bits(dut, (0x36 << 9) | 0x12F, 16, period=400,
                    high0=60, high1=140, din=3)
    await Timer(1, unit="us")
    task.cancel()
    expected = (0x51 << 9) | 0x12F
    assert len(pulses) == 16
    for i, (rise, high) in enumerate(pulses):
        assert high == (120 if expected & (1 << (15-i)) else 60)
        if i: assert rise-pulses[i-1][0] == 400
    assert await host.read(0x69) == 0x36
    assert await host.read(0x6A) == 0
    assert await host.read(0x6B) & 0xE0 == 0


@cocotb.test()
async def malformed_frame_requires_new_idle(dut):
    host = await setup(dut)
    await configure(host)
    await host.write(0x61, 3)  # Pure relay, no TX payload required.
    await Timer(310, unit="us")
    await send_bits(dut, 0, 4, period=400, high0=200)
    assert await host.read(0x6B) & 0x80
    assert await host.read(0x6B) & 7 == 0  # No complete prefix, no active frame.
    await host.write(0x61, 0x403)
    pulses = []
    task = cocotb.start_soon(watch_output(dut, pulses))
    await send_bits(dut, 0xFFFFFF, 24)  # A fast retry without reset is ignored.
    assert not pulses
    await Timer(310, unit="us")
    await send_bits(dut, 0xAF0001, 24)
    await Timer(2, unit="us")
    check_pulses(pulses, 0xAF0001, 24)
    assert await host.read(0x69) == 1
    assert await host.read(0x6A) == 0xAF
    assert await host.read(0x6B) & 0xE0 == 0
    task.cancel()


@cocotb.test()
async def every_clock_phase_at_input_timing_limits(dut):
    host = await setup(dut)
    await configure(host)
    await stage(host, 0xAA55AA)
    await host.write(0x61, 7)
    for phase in range(20):
        await host.write(0x61, 0x507)
        await ClockCycles(dut.clk, 1)
        await Timer(310_000+phase, unit="ns")
        pulses = []
        task = cocotb.start_soon(watch_output(dut, pulses))
        input_start = float(get_sim_time(unit="ns"))
        # Zero at its longest and one at its shortest legal V5 high.
        await send_bits(dut, 0xFFFF000000FFFFFFAA5555AA, 96,
                        period=1250, high0=380, high1=580)
        await Timer(2, unit="us")
        check_pulses(pulses, 0xAA55AA0000FFFFFFAA5555AA, 96)
        assert 680 <= pulses[0][0]-input_start <= 700
        assert await host.read(0x69) == 0xFF00
        assert await host.read(0x6A) == 0xFF
        assert await host.read(0x6B) & 0xE0 == 0
        task.cancel()


@cocotb.test()
async def partial_frame_and_midframe_ack_cannot_publish_torn_word(dut):
    host = await setup(dut)
    await configure(host)
    await stage(host, 0x123456)
    await host.write(0x61, 7)
    await Timer(310, unit="us")
    await send_bits(dut, 0xA5, 8)
    assert await host.read(0x6B) & 4 == 0
    await Timer(310, unit="us")
    await send_bits(dut, 0x112233, 24)
    assert await host.read(0x69) == 0x2233
    assert await host.read(0x6A) == 0x11
    await Timer(310, unit="us")
    stream = cocotb.start_soon(send_bits(dut, 0xABCDEF, 24))
    await Timer(6, unit="us")
    await host.write(0x61, 0x107)  # The second frame was already declared dropped.
    await stream
    assert await host.read(0x6B) & 0x44 == 0x40
    assert await host.read(0x69) == 0  # No suffix masquerading as a complete word.
    await host.write(0x61, 0x407)
    await Timer(310, unit="us")
    await send_bits(dut, 0xABCDEF, 24)
    assert await host.read(0x69) == 0xCDEF
    assert await host.read(0x6A) == 0xAB
    assert await host.read(0x6B) & 0xE0 == 0
