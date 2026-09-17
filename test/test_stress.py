"""Randomized external queue scoreboard and instruction fault boundaries."""
from collections import deque
import random
import cocotb
from cocotb.triggers import ClockCycles
from test import setup
from host_protocol import read_frame


@cocotb.test()
async def randomized_stream_scoreboard(dut):
    host = await setup(dut, half=129)
    for context in (0, 1):
        await host.load(context, "loop: PULL\nXOR 0xA7\nPUSH\nJMP loop")
    await host.write(3, 3)
    rng = random.Random(0xF1F0)
    expected = [deque(), deque()]
    received = [0, 0]
    for _ in range(420):
        context = rng.randrange(2)
        page = 0x10 + context * 16
        if len(expected[context]) < 15 and (not expected[context] or rng.randrange(2)):
            value = rng.randrange(256)
            await host.write(page + 4, value)
            expected[context].append(value ^ 0xA7)
        else:
            if rng.randrange(3) == 0:
                await host.transfer(read_frame(page + 5), bits=rng.choice([16, 17, 23, 31]))
            value = await host.read(page + 5)
            if value & 0x8000:
                assert expected[context]
                assert value == 0x8000 | expected[context].popleft()
                received[context] += 1
            else:
                assert value == 0
        assert await host.read(6) == 0
    for context in (0, 1):
        while expected[context]:
            assert await host.read(0x15 + 16*context) == 0x8000 | expected[context].popleft()
            received[context] += 1
        assert await host.read(0x16 + 16*context) == 0
        assert received[context] >= 64  # Multiple physical and extended-pointer wraps.
    await host.write(4, 3)
    assert await host.read(3) == 0
    assert await host.read(0x16) == 0
    assert await host.read(0x26) == 0


@cocotb.test()
async def extension_faults_events_and_counter_zero(dut):
    host = await setup(dut)
    for illegal in (0xF201, 0xF270, 0xF370, 0xF40D, 0xF410, 0xF510, 0xFA00):
        # F201 is legal SET pin0=1: exercise masked no-op alongside faults.
        await host.write(4, 1)
        await host.load(0, f"NOP")
        await host.write(0x40, illegal)
        await host.write(0x41, 0xE000)
        await host.write(3, 1)
        assert await host.read(3) == 0
        assert await host.read(6) == (0 if illegal == 0xF201 else 0x100)
    await host.write(4, 1)
    await host.load(0, "LDI 0\nLDX 0\nloop: DEC\nDJNZ loop\nPUSH\nAWAIT\nIRQ\nHALT")
    await host.write(3, 1)
    # The 16-iteration loop finishes AFTER this transaction snapshots an empty
    # RX FIFO. Its later arrival must not be consumed by that empty read.
    assert await host.read(0x15) == 0
    assert await host.read(0x15) == 0x80F0
    assert await host.read(3) == 1
    assert await host.read(0x17) == 0
    await host.write(0x0D, 1)
    await ClockCycles(dut.clk, 30)
    assert await host.read(3) == 0
    assert await host.read(0x0D) == 0
    assert await host.read(5) == 1
    await host.write(5, 1)
    assert not int(dut.uo_out.value) & 2


@cocotb.test()
async def sram_patterns_preserve_stream_partition(dut):
    host = await setup(dut, half=131)
    sentinels = [[(i*37 + c*91) & 255 for i in range(16)] for c in (0, 1)]
    for c in (0, 1):
        for byte in sentinels[c]:
            await host.write(0x14 + 16*c, byte)
    for pattern in (0x0000, 0xFFFF, 0xAAAA, 0x5555):
        for c in (0, 1):
            for address in range(48):
                await host.write(0x0A, 64*c + address)
                await host.write(0x0B, pattern)
                assert await host.read(0x0B) == pattern
    # Reload code without RESTART: clearing the program length must not flush TX.
    for c in (0, 1):
        await host.load(c, "loop: PULL\nPUSH\nJMP loop")
    await host.write(3, 3)
    for c in (0, 1):
        for byte in sentinels[c]:
            assert await host.read(0x15 + 16*c) == 0x8000 | byte
        assert await host.read(0x16 + 16*c) == 0
    assert await host.read(6) == 0
