"""Experimental capabilities observed only through the ASIC SPI/GPIO boundary."""
import os
import random
import cocotb
from cocotb.triggers import ClockCycles, Timer, FallingEdge, with_timeout
from cocotb.utils import get_sim_time
from spi_host import setup
from test_single import load_program
from micro_variant import simulation_features

FEATURES = simulation_features()


if FEATURES & 128:
    @cocotb.test()
    async def spi_fifo_burst_consumes_only_complete_valid_words(dut):
        host = await setup(dut)
        for partial in range(16):
            await host.write(4, 1)
            await load_program(host, [0x0A6,0x308,0x039,0x308,0x306])
            await host.write(3, 1)
            # Header + first full word + any incomplete prefix of second word.
            raw = await host.transfer(bytes.fromhex('0b1500000000'), bits=32+partial)
            if partial == 0: assert int.from_bytes(raw, 'big') & 0xFFFF == 0x80A6
            assert await host.read(0x15) == 0x8039
            assert await host.read(0x15) == 0
        await host.write(4, 1)
        await load_program(host, [0x0FF,0x308,0x000,0x308,0x306])
        await host.write(3, 1)
        raw = await host.transfer(bytes.fromhex('0b15000000000000'))
        assert raw[2:] == bytes.fromhex('80ff80000000')
        # Empty snapshots never consume an arrival or fabricate a valid byte.
        assert await host.transfer(bytes.fromhex('0b150000')) == bytes(4)
        assert await host.read(6) == 0


if FEATURES & 64:
    @cocotb.test()
    async def triggered_sampler_captures_fixed_period_data_and_preserves_unread_word(dut):
        host = await setup(dut)
        from test_timed import configure
        rng = random.Random(0xCA24)
        for length in (1, 8, 16, 24):
            await configure(host, length=length, din=0, dout=1, idle=5,
                            sample=12, launch=50)
            await host.write(0x6D, 2)
            await host.write(0x61, 0x501)  # Clear old RX/errors; capture only.
            expected = rng.randrange(1 << length)
            async def frame(value):
                for index in range(length-1, -1, -1):
                    bit = (value >> index) & 1
                    dut.uio_in.value = bit | (2 if index == length-1 else 0)
                    await Timer(400, unit='ns')
                    dut.uio_in.value = bit
                    await Timer(600, unit='ns')
                dut.uio_in.value = 0
            await frame(expected)
            assert await host.read(0x6B) & 4
            actual = await host.read(0x69) | (await host.read(0x6A) << 16)
            assert actual == expected, (length,hex(actual),hex(expected))
            await frame(expected ^ ((1 << length)-1))
            assert await host.read(0x6B) & 0x40  # Explicit overrun, no overwrite.
            assert await host.read(0x69) | (await host.read(0x6A) << 16) == expected
            assert int(dut.uio_oe.value) == 0
        await host.write(0x61, 0)
        await host.write(0x61, 3)  # Capture mode must not drive a trigger pin.
        assert await host.read(0x61) == 0
        assert await host.read(0x6B) & 0x20


if FEATURES & 32:
    @cocotb.test()
    async def event_divider_counts_edges_not_elapsed_time(dut):
        host = await setup(dut)
        from test_timed import configure
        rng = random.Random(0xE001)
        for period, width in ((3,1), (17,3), (525,2)):
            await configure(host, idle=period, high0=width, high1=1)
            await host.write(0x6D, 1)
            await host.write(0x61, 3)
            for index in range(1, 2*period+width+2):
                dut.uio_in.value = 1
                await Timer(100, unit='ns')
                phase = index % period
                expected = index >= period and phase < width
                assert bool(int(dut.uo_out.value) & 4) == expected, (period,index)
                dut.uio_in.value = 0
                await Timer(rng.randrange(100,301), unit='ns')
                assert bool(int(dut.uo_out.value) & 4) == expected
            assert await host.read(0x6B) & 0xE0 == 0
            await host.write(0x6D, 0)
            assert await host.read(0x6B) & 0x20  # No live mode changes.
            await host.write(0x61, 0x400)
            assert not int(dut.uo_out.value) & 4
        await configure(host, idle=2, high0=2)
        await host.write(0x6D, 1)
        await host.write(0x61, 3)
        assert await host.read(0x61) == 0
        assert await host.read(0x6B) & 0x20  # Width must be below period.


@cocotb.test()
async def exact_experimental_identity_and_disabled_feature_guards(dut):
    host = await setup(dut)
    assert await host.read(1) == (0x0600 if FEATURES else 0x0500)
    assert await host.read(0x1A) == FEATURES
    for bit, address, value in ((2,0x18,0),(8,0x19,0)):
        if not FEATURES & bit:
            await host.write(address, value)
            assert await host.read(6) == 1
            await host.write(6, 1)


if FEATURES & 8:
    @cocotb.test()
    async def hardware_wrap_saves_jump_and_never_bypasses_fifo_stall(dut):
        host = await setup(dut)
        for bottom in (0, 14):
            await host.write(4, 1)
            await host.write(0x10, 1 << 8)
            await load_program(host, [0x300]*bottom + [0x378, 0x368])
            await host.write(0x19, 0x10 | bottom)
            await host.write(3, 1)
            await ClockCycles(dut.clk, 80)  # Allow the 14-word prologue to finish.
            edges, prior = [], int(dut.uo_out.value) & 4
            for _ in range(100):
                await FallingEdge(dut.clk)
                level = int(dut.uo_out.value) & 4
                if level != prior: edges.append(float(get_sim_time(unit='ns')))
                prior = level
            assert len(edges) >= 20
            assert all(b-a == 80 for a,b in zip(edges, edges[1:]))
            await host.write(0x19, 0)
            assert await host.read(6) == 1  # Running configuration cannot change.
            await host.write(6, 1)
        await host.write(4, 1)
        await load_program(host, [0x307, 0x308])
        assert await host.read(0x19) == 0  # Program invalidation disarms wrap.
        for invalid in (0x12, 0x30, 0x100):
            await host.write(0x19, invalid)
            assert await host.read(6) == 1
            await host.write(6, 1)
        await host.write(0x19, 0x10)
        await host.write(3, 1)
        assert await host.read(0x11) == 0
        for value in (0x17, 0xA6):
            await host.write(0x14, value)
            assert await host.read(0x15) == 0x8000 | value
        assert await host.read(6) == 0


if FEATURES & 16:
    @cocotb.test()
    async def four_byte_receive_queue_absorbs_a_burst_without_overwrite(dut):
        host = await setup(dut)
        await load_program(host, [0x011,0x308,0x022,0x308,0x033,0x308,
                                  0x044,0x308,0x055,0x308,0x306])
        await host.write(3, 1)
        assert await host.read(0x1B) == 0x0402
        assert await host.read(0x1C) == 0x0400
        assert await host.read(0x11) == 9  # Fifth PUSH stalls, no overwrite.
        from host_protocol import read_frame
        for bits in (16, 24, 31):
            await host.transfer(read_frame(0x15), bits=bits)
            assert await host.read(0x1C) == 0x0400
        for value in (0x11,0x22,0x33,0x44,0x55):
            assert await host.read(0x15) == 0x8000 | value
        assert await host.read(0x1C) == 0
        assert await host.read(6) == 0
        await host.write(4, 1)
        assert await host.read(0x15) == 0


if FEATURES & 1:
    @cocotb.test()
    async def per_pin_direction_preserves_payload_and_ownership(dut):
        host = await setup(dut)
        for pin in range(8):
            await host.write(4, 1)
            await host.write(0x10, 1 << pin)
            # Drive low, release, drive again, without destroying A=0xA5.
            await load_program(host, [0x0A5, 0x3C0 | pin*2 | 1, 0x306])
            await host.write(3, 1)
            assert int(dut.uio_oe.value) == 1 << pin
            assert await host.read(0x12) == 0xA5
            assert await host.read(6) == 0
            await load_program(host, [0x3C0 | pin*2, 0x306])
            await host.write(0x11, 0)
            await host.write(3, 1)
            assert int(dut.uio_oe.value) == 0
            assert await host.read(0x12) == 0xA5
        await host.write(4, 1)
        await host.write(0x10, 0)
        await load_program(host, [0x3C1, 0x306])
        await host.write(3, 1)
        assert int(dut.uio_oe.value) == 0


if FEATURES & 4:
    @cocotb.test()
    async def full_duplex_spi_uses_one_byte_register_at_uniform_cadence(dut):
        host = await setup(dut)
        tx = [0, 255, 0x55, 0xAA, 0x80, 1, 0xA6, 0x39]
        rx = [0x91, 0, 0xFE, 0x13, 0xA5, 0x5A, 1, 0x80]
        await host.write(0x10, 11)  # MOSI=0 SCK=1 MISO=2 CS_n=3.
        # 14 instructions including safe CS-before-direction initialization.
        await load_program(host, [0x00B,0x373,0x301,0x307,0x3A8,0x363,
                                  0x3E0,0x371,0x392,0x361,0x3B6,0x373,0x308,0x313])
        async def slave():
            seen, bit, value, prior, last_rise = [], 0, 0, 8, None
            while len(seen) < len(tx):
                await FallingEdge(dut.clk)
                pins = int(dut.uio_out.value)
                if prior & 8 and not pins & 8:
                    bit, value, last_rise = 0, 0, None
                    dut.uio_in.value = ((rx[len(seen)] >> 7) & 1) << 2
                if not pins & 8 and not prior & 2 and pins & 2:
                    now = float(get_sim_time(unit='ns'))
                    if last_rise is not None: assert now-last_rise == 400
                    last_rise = now
                    value = (value << 1) | (pins & 1)
                if not pins & 8 and prior & 2 and not pins & 2:
                    bit += 1
                    if bit < 8: dut.uio_in.value = ((rx[len(seen)] >> (7-bit)) & 1) << 2
                    else:
                        seen.append(value)
                        dut.uio_in.value = 0
                prior = pins
            return seen
        task = cocotb.start_soon(slave())
        await host.write(0x14, tx[0])
        await host.write(3, 1)
        for index, value in enumerate(tx):
            if index: await host.write(0x14, value)
            await Timer(5000, unit='ns')
            assert await host.read(0x15) == 0x8000 | rx[index]
        assert await with_timeout(task, 200, 'us') == tx
        assert await host.read(6) == 0


if FEATURES & 4:
    @cocotb.test()
    async def outmsb_all_pins_preserve_data_and_respect_ownership(dut):
        host = await setup(dut)
        for pin in range(14):
            for owned in (False, True):
                for value in (0x7F, 0x80):
                    await host.write(4, 1)
                    await host.write(0x10, (1 << pin) if owned else 0)
                    await load_program(host, [0x0FF, 0x301, value, 0x3E0 | pin, 0x306])
                    await host.write(3, 1)
                    assert await host.read(0x12) == value
                    expected = (1 << pin) if owned and value & 0x80 else 0
                    assert await host.read(7) == expected
                    assert int(dut.uio_out.value) == expected & 255
                    assert int(dut.uo_out.value) >> 2 == expected >> 8
                    assert await host.read(6) == 0


if FEATURES & 2:
    @cocotb.test()
    async def input_branch_preserves_accumulator_and_has_bounded_recovery(dut):
        host = await setup(dut)
        for pin in range(13):
            for level in (0, 1):
                await host.write(4, 1)
                host.inputs = (level << (pin-8)) if pin >= 8 else 0
                host.drive()
                dut.uio_in.value = (level << pin) if pin < 8 else 0
                await load_program(host, [0x0A5, 0x3D4, 0x011, 0x306, 0x306])
                await host.write(0x18, pin)
                await host.write(3, 1)
                assert await host.read(0x12) == (0xA5 if level else 0x11)
                assert await host.read(6) == 0
        await host.write(4, 1)
        for invalid in (13, 14, 15, 0x100):
            await host.write(0x18, invalid)
            assert await host.read(6) == 1
            await host.write(6, 1)
        host.inputs = 0
        host.drive()
        dut.uio_in.value = 0
        await load_program(host, [0x3A4, 0x3D4, 0x3B1, 0x305, 0x306])
        await host.write(0x18, 0)
        await host.write(3, 1)
        assert await host.read(5) == 1  # Four polls terminate and report timeout.
        assert await host.read(3) == 0
        dut.ena.value = 0
        await Timer(1, unit="ns")
        assert int(dut.uio_oe.value) == 0
