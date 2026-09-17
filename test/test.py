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
from host_protocol import read_frame, write_frame, read_value, program_frames


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

    async def load(self, context, source):
        words = assemble(source)
        for frame in program_frames(context, words):
            await self.transfer(frame)
        return words


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


@cocotb.test()
async def spi_framing_and_readback(dut):
    host = await setup(dut, half=137)  # Deliberately asynchronous to clk.
    assert await host.transfer(read_frame(0)) == bytes.fromhex("00 00 50 49")
    assert await host.read(1) == 0x0200
    assert await host.read(0x40) == 0  # Unloaded memory does not expose X values.
    rng = random.Random(0x5049)
    for address in range(0x40, 0x60):
        value = rng.randrange(65536)
        await host.write(address, value)
        assert await host.read(address) == value
    await host.write(0x12, 0x1234)
    for bits in (1, 7, 8, 15, 16, 23, 31):
        await host.transfer(write_frame(0x12, 0xFFFF), bits=bits)
        assert await host.read(0x12) == 0x34, f"aborted {bits}-bit frame committed"
    await host.transfer(bytes.fromhex("99 12 ff ff"))
    assert await host.read(0x12) == 0x34
    # Extra clocks are ignored: no implicit second transaction without CS high.
    await host.transfer(write_frame(0x12, 0x4567) + write_frame(0x12, 0xFFFF))
    assert await host.read(0x12) == 0x67
    assert await host.read(0xFF) == 0


@cocotb.test()
async def two_contexts_wait_and_owned_gpio(dut):
    host = await setup(dut)
    await host.write(0x10, 0x0001)  # ctx0 owns bidirectional 0.
    await host.write(0x20, 0x0100)  # ctx1 owns fixed output 0 (local output 1).
    await host.load(0, "WAIT 8,1\nLDI 1\nOUT\nDIR\nIRQ\nHALT")
    await host.load(1, "LDI 2\nOUT\nDIR\nIRQ\nHALT")
    await host.write(3, 3)
    assert await host.read(3) == 1  # ctx1 completed while ctx0 remains waiting.
    assert await host.read(7) == 0x100
    assert await host.read(8) == 0  # ctx0 cannot drive ctx1's IO.
    assert await host.read(5) == 2
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
    # The single SRAM port is reserved for execution while running.
    assert await host.read(0x40) == 0
    assert await host.read(0x10) == 1
    assert await host.read(0x11) == 0
    assert await host.read(0x12) == 0
    await host.write(4, 1)
    assert await host.read(3) == 0
    assert await host.read(0x40) == 0x8100  # Forbidden live write did not alter code.
    await host.write(3, 2)  # ctx1 has no loaded instruction: fault and halt.
    assert await host.read(3) == 0
    assert await host.read(6) == 0x0200
    await host.write(3, 2)  # A fault cannot be restarted without RESTART.
    assert await host.read(3) == 0
    await host.write(4, 2)
    assert await host.read(6) == 0
    for bad in (0xFF00, 0x810D):
        await host.write(0x50, bad)
        await host.write(3, 2)
        assert await host.read(6) == 0x0200
        await host.write(4, 2)
    await host.write(0xFF, 1)
    assert await host.read(6) == 1


@cocotb.test()
async def arithmetic_branches_inputs_and_direction(dut):
    host = await setup(dut)
    await host.load(0, "LDI 3\nloop: DEC\nJNZ loop\nLDI 0x3c\nXOR 0x23\nSHL\nSHR\nHALT")
    await host.write(3, 1)
    assert await host.read(0x12) == (0x3C ^ 0x23)
    assert await host.read(0x11) == 8
    assert await host.read(3) == 0
    await host.write(4, 1)
    await host.write(0x10, 0x007F)
    await host.load(0, "IN\nOUT\nDIR\nHALT")
    host.inputs = 0x15
    host.drive()
    dut.uio_in.value = 0xA5
    await host.write(3, 1)
    assert await host.read(0x12) == 0xA5
    assert await host.read(7) == 0x25
    assert await host.read(8) == 0x25
    await host.write(4, 1)
    await host.load(0, "LDI 0\nDIR\nHALT")
    await host.write(3, 1)
    assert await host.read(8) == 0
    await host.write(0x10, 0)
    assert await host.read(7) == 0


@cocotb.test()
async def deterministic_timing_during_host_traffic(dut):
    host = await setup(dut)
    await host.write(0x20, 0x100)
    await host.load(1, "loop: LDI 2\nOUT\nDELAY 3\nLDI 0\nOUT\nDELAY 3\nJMP loop")
    await host.load(0, "WAIT 8,1\nHALT")
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
        assert end - start == (720 if high else 840), (start, end, high)
    assert await host.read(3) == 3


@cocotb.test()
async def reset_and_disable_release_pins_and_invalidate_program(dut):
    host = await setup(dut)
    for signal in (dut.rst_n, dut.ena):
        await host.write(0x10, 1)
        await host.load(0, "LDI 1\nOUT\nDIR\nHALT")
        await host.write(3, 1)
        assert await host.read(3) == 0  # Wait for the four-cycle PIO to finish.
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
    host = await setup(dut, half=133)
    rng = random.Random(0xC0DE)
    for trial in range(16):
        context = trial % 2
        base = 0x10 * (context + 1)
        await host.write(4, 1 << context)
        expected = rng.randrange(256)
        await host.write(base + 2, expected)
        program = []
        # Expected state computed without the assembler or any RTL state access.
        for _ in range(14):
            operation = rng.choice(("NOP", "LDI", "XOR", "DEC", "SHL", "SHR"))
            if operation in ("LDI", "XOR"):
                value = rng.randrange(256)
                program.append(f"{operation} {value}")
                expected = value if operation == "LDI" else expected ^ value
            else:
                program.append(operation)
                if operation == "DEC":
                    expected = (expected - 1) & 0xFF
                elif operation == "SHL":
                    expected = (expected << 1) & 0xFF
                elif operation == "SHR":
                    expected >>= 1
        program.append("HALT")
        await host.load(context, "\n".join(program))
        await host.write(3, 1 << context)
        assert await host.read(3) == 0
        assert await host.read(base + 2) == expected, f"trial {trial}: {program}"
        assert await host.read(base + 1) == 15


@cocotb.test()
async def program_bound_stop_resume_and_wait_low(dut):
    host = await setup(dut)
    # Last initialized instruction may HALT, but execution beyond it faults.
    for index in range(48):
        await host.write(0x0A, index)
        await host.write(0x0B, 0xE000 if index == 47 else 0)
    await host.write(0x11, 47)
    await host.write(3, 1)
    assert await host.read(3) == 0
    assert await host.read(0x11) == 48
    assert await host.read(6) == 0
    await host.write(3, 1)
    assert await host.read(6) == 0x100
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
    host = await setup(dut, half=129)
    transfer = cocotb.start_soon(host.transfer(write_frame(0x12, 0xFFFF)))
    await Timer(4500, unit="ns")  # After header, before write commit.
    dut.rst_n.value = 0
    await transfer
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    await Timer(1, unit="ns")
    assert await host.read(0) == 0x5049
    assert await host.read(0x12) == 0
    await host.write(0x12, 0xBEEF)
    assert await host.read(0x12) == 0xEF


@cocotb.test()
async def full_program_memory_window(dut):
    host = await setup(dut)
    # 96 instruction words / 192 bytes; the other 64 bytes belong to queues.
    rng = random.Random(0x512)
    expected = {a: rng.randrange(65536) for a in (*range(48), *range(64, 112))}
    for address, word in expected.items():
        await host.write(0x0A, address)
        await host.write(0x0B, word)
    for address, word in expected.items():
        await host.write(0x0A, address)
        assert await host.read(0x0B) == word, f"SRAM address {address}"
    assert await host.read(0x1F) == 48
    assert await host.read(0x2F) == 48
    for address in (48, 63, 112, 127, 128, 255):
        await host.write(0x0A, address)
        await host.write(0x0B, 0xFFFF)
        assert await host.read(6) == 1
        assert await host.read(0x0B) == 0
        await host.write(6, 1)
