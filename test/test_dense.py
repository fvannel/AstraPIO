"""ABI-v5 native ten-bit program and shared-SPI public-interface regressions."""
import cocotb
import random
from cocotb.triggers import ClockCycles, Timer
from cocotb.utils import get_sim_time
from spi_host import setup
from host_protocol import write_frame, read_frame, read_value
from test_single import ABI, FEATURES


@cocotb.test()
async def native_ten_bit_program_keeps_all_sixteen_slots(dut):
    host = await setup(dut)
    assert await host.read(1) == ABI
    assert await host.read(0x0F) == 0x1002
    # Independent literal encoding, not produced by the assembler under test.
    words = [0x055, 0x308] + [0x300]*13 + [0x306]  # LDI, PUSH, NOPs, HALT
    for index, word in enumerate(words):
        await host.write(0x40+index, word)
    assert await host.read(0x0A) == 16
    assert [await host.read(0x40+i) for i in range(16)] == words
    for bit in range(10,16):  # Upper six bits must never silently truncate.
        await host.write(0x40, 0x055 | (1 << bit))
        assert await host.read(0x40) == 0x055
        assert await host.read(0x0A) == 16
        assert await host.read(6) == 1
        await host.write(6, 1)
    await host.write(3, 1)
    await ClockCycles(dut.clk, 100)
    assert await host.read(3) == 0
    assert await host.read(0x15) == 0x8055
    assert await host.read(6) == 0


@cocotb.test()
async def every_remaining_reserved_ten_bit_encoding_faults(dut):
    host = await setup(dut)
    invalid = [0x30F] + list(range(0x3C0,0x400))
    invalid += [base+pin for base in (0x340,0x350,0x390) for pin in (13,14,15)]
    invalid += [base+pin for base in (0x360,0x370,0x380) for pin in (14,15)]
    assert len(set(invalid)) == 80
    new_legal = set()
    if FEATURES & 1: new_legal.update(range(0x3C0,0x3D0))
    if FEATURES & 2: new_legal.update(range(0x3D0,0x3E0))
    if FEATURES & 4: new_legal.update(range(0x3E0,0x3EE))
    invalid = [word for word in invalid if word not in new_legal]
    for word in invalid:
        await host.write(4,1)
        await host.write(0x0A,0)
        await host.write(0x40,word)
        assert await host.read(0x40) == word
        await host.write(3,1)
        assert await host.read(6) == 0x100, hex(word)
        assert await host.read(3) == 0


@cocotb.test()
async def spi_read_write_turnaround_ignores_read_payload_and_aborted_frames(dut):
    host = await setup(dut)
    rng = random.Random(0x5105)
    # At the minimum supported SCK/CS timing, exercise every clock phase and
    # both shift-register roles. Arbitrary MOSI read payload must be ignored.
    for phase in range(20):
        offset = (phase - int(get_sim_time(unit='ns')) % 20) % 20
        if offset:
            await Timer(offset, unit='ns')
        assert int(get_sim_time(unit='ns')) % 20 == phase
        for value in (0, 0xFFFF, 0x5555, 0xAAAA, rng.randrange(65536)):
            await host.write(0x67, value)
            dummy = rng.randrange(65536)
            reply = await host.transfer(bytes((3,0x67,dummy>>8,dummy&255)))
            assert read_value(reply) == value, (phase,value)
            assert await host.read(0) == 0x5049
    await host.write(0x67, 0x5AC3)
    for bits in range(32):
        await host.transfer(write_frame(0x67, 0xC35A), bits=bits)
        assert await host.read(0x67) == 0x5AC3, ('write abort',bits)
        await host.transfer(read_frame(0x67), bits=bits)
        assert await host.read(1) == ABI, ('read abort',bits)
    # Unknown commands must not alias writes or leave part of a read active.
    for command in (0,1,4,0x82,0x83,0xFE,0xFF):
        await host.transfer(bytes((command,0x67,0xC3,0x5A)))
        assert await host.read(0x67) == 0x5AC3
    # Every partial destructive read must leave both FIFO bytes intact.
    for i, word in enumerate((0x0C7,0x308,0x05A,0x308,0x306)):
        await host.write(0x40+i,word)
    await host.write(3,1)
    for bits in range(32):
        await host.transfer(read_frame(0x15),bits=bits)
        assert await host.read(0x16) >> 14 == 2
    assert await host.read(0x15) == 0x80C7
    assert await host.read(0x15) == 0x805A
    assert await host.read(0x15) == 0
    assert await host.read(6) == 0
