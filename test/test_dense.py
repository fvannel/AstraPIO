"""ABI-v5 native ten-bit program and shared-SPI public-interface regressions."""
import cocotb
from cocotb.triggers import ClockCycles
from spi_host import setup


@cocotb.test()
async def native_ten_bit_program_keeps_all_sixteen_slots(dut):
    host = await setup(dut)
    assert await host.read(1) == 0x0500
    assert await host.read(0x0F) == 0x1002
    # Independent literal encoding, not produced by the assembler under test.
    words = [0x055, 0x308] + [0x300]*13 + [0x306]  # LDI, PUSH, NOPs, HALT
    for index, word in enumerate(words):
        await host.write(0x40+index, word)
    assert await host.read(0x0A) == 16
    assert [await host.read(0x40+i) for i in range(16)] == words
    await host.write(0x40, 0x0455)  # Upper six bits must never silently truncate.
    assert await host.read(0x40) == 0x055
    assert await host.read(6) == 1
    await host.write(6, 1)
    await host.write(3, 1)
    await ClockCycles(dut.clk, 100)
    assert await host.read(3) == 0
    assert await host.read(0x15) == 0x8055
    assert await host.read(6) == 0
