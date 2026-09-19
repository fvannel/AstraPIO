"""Experimental capabilities observed only through the ASIC SPI/GPIO boundary."""
import os
import random
import cocotb
from cocotb.triggers import ClockCycles, Timer, FallingEdge, with_timeout
from cocotb.utils import get_sim_time
from spi_host import setup
from test_single import load_program
from micro_variant import VARIANTS

FEATURES = VARIANTS[os.environ.get("ASTRA_VARIANT", "baseline")]


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
