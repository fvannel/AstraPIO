# SPDX-License-Identifier: Apache-2.0
"""Black-box RTL tests: only Tiny Tapeout pins, no hierarchical state access."""
import random
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, Timer
from cocotb.utils import get_sim_time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from pioasm import assemble
from host_protocol import read_frame, write_frame, read_value


class Host:
    def __init__(self, dut, half_period=100):
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

    async def load(self, context, source):
        words = assemble(source)
        for index, word in enumerate(words):
            await self.write(0x40 + 16 * context + index, word)
        return words


async def setup(dut, half=100):
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


@cocotb.test()
async def spi_framing_and_readback(dut):
    host = await setup(dut, half=137)  # Deliberately asynchronous to clk.
    assert await host.transfer(read_frame(0)) == bytes.fromhex("00 00 50 49")
    assert await host.read(1) == 1
    assert await host.read(0x40) == 0  # Unloaded memory does not expose X values.
    rng = random.Random(0x5049)
    for address in range(0x40, 0x60):
        value = rng.randrange(65536)
        await host.write(address, value)
        assert await host.read(address) == value
    await host.write(0x12, 0x1234)
    for bits in (1, 7, 8, 15, 16, 23, 31):
        await host.transfer(write_frame(0x12, 0xFFFF), bits=bits)
        assert await host.read(0x12) == 0x1234, f"aborted {bits}-bit frame committed"
    await host.transfer(bytes.fromhex("99 12 ff ff"))
    assert await host.read(0x12) == 0x1234
    # Extra clocks are ignored: no implicit second transaction without CS high.
    await host.transfer(write_frame(0x12, 0x4567) + write_frame(0x12, 0xFFFF))
    assert await host.read(0x12) == 0x4567
    assert await host.read(0xFF) == 0


@cocotb.test()
async def two_contexts_wait_and_owned_gpio(dut):
    host = await setup(dut)
    await host.write(0x10, 0x0100)  # ctx0 owns fixed output 0.
    await host.write(0x20, 0x0001)  # ctx1 owns bidirectional 0.
    await host.load(0, "LDI 0x1ff\nOUT\nDIR\nIRQ\nHALT")
    await host.load(1, "WAIT 8,1\nLDI 1\nOUT\nDIR\nIRQ\nHALT")
    await host.write(3, 3)
    assert await host.read(3) == 2  # ctx0 completed while ctx1 remains waiting.
    assert await host.read(7) == 0x100
    assert await host.read(8) == 0  # ctx0 cannot drive ctx1's IO.
    assert await host.read(5) == 1
    host.inputs = 1
    host.drive()
    await ClockCycles(dut.clk, 30)
    assert await host.read(3) == 0
    assert await host.read(7) == 0x101
    assert await host.read(8) == 1
    assert int(dut.uo_out.value) & 6 == 6
    assert int(dut.uio_out.value) == 1
    assert int(dut.uio_oe.value) == 1
    await host.write(5, 3)
    assert await host.read(5) == 0
    assert await host.read(6) == 0
    assert not int(dut.uo_out.value) & 2


@cocotb.test()
async def protections_faults_and_restart(dut):
    host = await setup(dut)
    await host.write(0x10, 1)
    await host.write(0x20, 1)  # Overlap is rejected.
    assert await host.read(0x20) == 0
    assert await host.read(6) == 1
    await host.write(6, 1)
    await host.load(0, "WAIT 0,1\nHALT")
    await host.write(3, 1)
    for address, value in ((0x40, 0xE000), (0x10, 2), (0x11, 5), (0x12, 0x1234)):
        await host.write(address, value)
        assert await host.read(6) == 1
        await host.write(6, 1)
    assert await host.read(0x40) == 0x8100
    assert await host.read(0x10) == 1
    assert await host.read(0x11) == 0
    assert await host.read(0x12) == 0
    await host.write(4, 1)
    assert await host.read(3) == 0
    await host.write(3, 2)  # ctx1 has no loaded instruction: fault and halt.
    assert await host.read(3) == 0
    assert await host.read(6) == 0x0200
    await host.write(3, 2)  # A fault cannot be restarted without RESTART.
    assert await host.read(3) == 0
    await host.write(4, 2)
    assert await host.read(6) == 0
    for bad in (0xF000, 0x810D):
        await host.write(0x50, bad)
        await host.write(3, 2)
        assert await host.read(6) == 0x0200
        await host.write(4, 2)
    await host.write(0xFF, 1)
    assert await host.read(6) == 1


@cocotb.test()
async def arithmetic_branches_inputs_and_direction(dut):
    host = await setup(dut)
    await host.load(0, "LDI 3\nloop: DEC\nJNZ loop\nLDI 0xabc\nXOR 0x123\nSHL\nSHR\nHALT")
    await host.write(3, 1)
    assert await host.read(0x12) == (0xABC ^ 0x123)
    assert await host.read(0x11) == 8
    assert await host.read(3) == 0
    await host.write(4, 1)
    await host.write(0x10, 0x3FFF)
    await host.load(0, "IN\nOUT\nDIR\nHALT")
    host.inputs = 0x15
    host.drive()
    dut.uio_in.value = 0xA5
    await host.write(3, 1)
    assert await host.read(0x12) == 0x15A5
    assert await host.read(7) == 0x15A5
    assert await host.read(8) == 0xA5
    await host.write(4, 1)
    await host.load(0, "LDI 0\nDIR\nHALT")
    await host.write(3, 1)
    assert await host.read(8) == 0
    await host.write(0x10, 0)
    assert await host.read(7) == 0


@cocotb.test()
async def deterministic_timing_during_host_traffic(dut):
    host = await setup(dut)
    await host.write(0x10, 0x100)
    await host.load(0, "loop: LDI 0x100\nOUT\nDELAY 3\nLDI 0\nOUT\nDELAY 3\nJMP loop")
    await host.load(1, "WAIT 8,1\nHALT")
    edges = []

    async def monitor():
        previous = 0
        for _ in range(6000):
            await FallingEdge(dut.clk)
            current = (int(dut.uo_out.value) >> 2) & 1
            if current != previous:
                edges.append((int(get_sim_time(unit="ns")), current))
                previous = current

    task = cocotb.start_soon(monitor())
    await host.write(3, 3)
    for _ in range(3):
        assert await host.read(0) == 0x5049
        await host.write(5, 3)
    await task
    assert len(edges) > 100
    for (start, high), (end, _) in zip(edges, edges[1:]):
        assert end - start == (240 if high else 280), (start, end, high)
    assert await host.read(3) == 3


@cocotb.test()
async def reset_and_disable_release_pins_and_invalidate_program(dut):
    host = await setup(dut)
    for signal in (dut.rst_n, dut.ena):
        await host.write(0x10, 1)
        await host.load(0, "LDI 1\nOUT\nDIR\nHALT")
        await host.write(3, 1)
        assert int(dut.uio_oe.value) == 1
        signal.value = 0
        await Timer(1, unit="ns")
        assert int(dut.uio_oe.value) == 0
        assert int(dut.uo_out.value) == 0
        assert int(dut.uio_out.value) == 0
        await ClockCycles(dut.clk, 5)
        await Timer(1, unit="ns")
        signal.value = 1
        await ClockCycles(dut.clk, 5)
        await Timer(1, unit="ns")
        assert await host.read(0x10) == 0
        assert await host.read(0x40) == 0
        await host.write(3, 1)
        assert await host.read(6) == 0x100
        await host.write(4, 1)


@cocotb.test()
async def randomized_alu_matches_reference(dut):
    host = await setup(dut, half=113)
    rng = random.Random(0xC0DE)
    for trial in range(16):
        context = trial % 2
        base = 0x10 * (context + 1)
        await host.write(4, 1 << context)
        expected = rng.randrange(65536)
        await host.write(base + 2, expected)
        program = []
        # Expected state computed without the assembler or any RTL state access.
        for _ in range(14):
            operation = rng.choice(("NOP", "LDI", "XOR", "DEC", "SHL", "SHR"))
            if operation in ("LDI", "XOR"):
                value = rng.randrange(4096)
                program.append(f"{operation} {value}")
                expected = value if operation == "LDI" else expected ^ value
            else:
                program.append(operation)
                if operation == "DEC":
                    expected = (expected - 1) & 0xFFFF
                elif operation == "SHL":
                    expected = (expected << 1) & 0xFFFF
                elif operation == "SHR":
                    expected >>= 1
        program.append("HALT")
        await host.load(context, "\n".join(program))
        await host.write(3, 1 << context)
        assert await host.read(3) == 0
        assert await host.read(base + 2) == expected, f"trial {trial}: {program}"
        assert await host.read(base + 1) == 15


@cocotb.test()
async def pc_wrap_stop_resume_and_wait_low(dut):
    host = await setup(dut)
    # Slot 15 wraps to 0; the uninitialized middle slots must not be fetched.
    await host.write(0x4F, 0)  # NOP
    await host.write(0x40, 0xE000)
    await host.write(0x11, 15)
    await host.write(3, 1)
    assert await host.read(3) == 0
    assert await host.read(0x11) == 1
    assert await host.read(6) == 0
    await host.write(4, 1)
    await host.load(0, "WAIT 0,0\nLDI 7\nHALT")
    dut.uio_in.value = 1
    await host.write(3, 1)
    assert await host.read(0x11) == 0
    await host.write(3, 0)
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 30)
    assert await host.read(0x12) == 0  # Stopped context does not advance.
    await host.write(3, 1)
    assert await host.read(0x12) == 7
    assert await host.read(3) == 0


@cocotb.test()
async def reset_during_spi_frame(dut):
    host = await setup(dut, half=109)
    transfer = cocotb.start_soon(host.transfer(write_frame(0x12, 0xFFFF)))
    await Timer(3500, unit="ns")  # After header, before write commit.
    dut.rst_n.value = 0
    await transfer
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    await Timer(1, unit="ns")
    assert await host.read(0) == 0x5049
    assert await host.read(0x12) == 0
    await host.write(0x12, 0xBEEF)
    assert await host.read(0x12) == 0xBEEF
