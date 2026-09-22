# SPDX-License-Identifier: Apache-2.0
"""Pin-only SPI transport shared by the compact integration scenarios."""
import sys
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from host_protocol import read_frame, write_frame, read_value


class Host:
    def __init__(self, dut, half_period=120):
        self.dut = dut
        self.half = half_period
        self.inputs = 0

    def drive(self, cs=1, sck=0, mosi=0):
        self.dut.ui_in.value = (self.inputs << 3) | (cs << 2) | (mosi << 1) | sck

    async def transfer(self, frame, bits=None):
        bits = len(frame) * 8 if bits is None else bits
        self.drive(cs=0)
        await Timer(self.half, unit="ns")
        result = 0
        value = int.from_bytes(frame, "big")
        for index in range(bits):
            bit = (value >> (len(frame) * 8 - index - 1)) & 1
            self.drive(cs=0, mosi=bit)
            await Timer(self.half, unit="ns")
            self.drive(cs=0, sck=1, mosi=bit)
            await Timer(1, unit="ns")
            result = (result << 1) | (int(self.dut.uo_out.value) & 1)
            await Timer(self.half - 1, unit="ns")
            self.drive(cs=0, mosi=bit)
        await Timer(self.half, unit="ns")
        self.drive()
        await Timer(self.half, unit="ns")
        return result.to_bytes((bits + 7) // 8, "big")

    async def read(self, address):
        return read_value(await self.transfer(read_frame(address)))

    async def write(self, address, value):
        await self.transfer(write_frame(address, value))


async def setup(dut, half=120):
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.ui_in.value = 4
    dut.uio_in.value = 0
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    await ClockCycles(dut.clk, 5)
    await Timer(1, unit="ns")
    assert int(dut.uio_oe.value) == 0
    assert int(dut.uo_out.value) == 0
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    await Timer(1, unit="ns")
    return Host(dut, half)
