"""Streaming through pins, including destructive SPI reads and backpressure."""
import cocotb
from cocotb.triggers import ClockCycles
from test import setup
from host_protocol import read_frame


@cocotb.test()
async def fifo_stream_and_atomic_reads(dut):
    host = await setup(dut, half=127)
    # PULL; XOR 0x5a; PUSH; JMP 0, independently on both contexts.
    for ctx in range(2):
        for index, word in enumerate((0xF000, 0xA05A, 0xF100, 0x5000)):
            await host.write(0x40 + ctx * 16 + index, word)
        for word in range(16):
            await host.write(0x14 + ctx * 16, word)
        assert await host.read(0x16 + ctx * 16) & 31 == 16
        await host.write(0x14 + ctx * 16, 0xFF)  # Reject overflow, no overwrite.
        assert await host.read(6) & 1
        await host.write(6, 1)
    await host.write(3, 3)
    for ctx in range(2):
        base = 0x10 + ctx * 16
        for _ in range(4):
            if await host.read(base + 6) == 0x1000:
                break
        assert await host.read(base + 6) == 0x1000
        for bits in (16, 17, 23, 31):
            await host.transfer(read_frame(base + 5), bits=bits)
            assert await host.read(base + 6) == 0x1000
        # One complete transaction, even with 32 extra clocks, consumes once.
        result = await host.transfer(read_frame(base + 5) + bytes(4))
        assert int.from_bytes(result[2:4], "big") == 0x805A
        assert await host.read(base + 6) == 0x0F00
        for word in range(1, 16):
            assert await host.read(base + 5) == 0x8000 | (word ^ 0x5A)
        assert await host.read(base + 5) == 0
        assert await host.read(base + 6) == 0
    # Backpressure: fill RX then TX, PIO may hold one word in accumulator.
    for word in range(33):
        await host.write(0x14, word)
    assert await host.read(0x16) == 0x1010
    for word in range(33):
        assert await host.read(0x15) == 0x8000 | (word ^ 0x5A)
    assert await host.read(0x16) == 0
    assert await host.read(6) == 0
    assert await host.read(3) == 3
    # Restart flushes this context only, even when the program is stalled.
    await host.write(0x24, 0x77)
    await host.write(0x14, 0x88)
    await host.write(4, 1)
    assert await host.read(0x16) == 0
    assert await host.read(0x25) == 0x802D
    await ClockCycles(dut.clk, 10)
