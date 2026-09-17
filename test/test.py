# SPDX-License-Identifier: Apache-2.0
"""Scaffold test ONLY. Passing this test does not validate a PIO implementation."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer


@cocotb.test()
async def test_scaffold_keeps_outputs_inactive(dut):
    dut.ena.value = 0
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())

    for enabled, reset_n in [(0, 0), (1, 0), (1, 1), (0, 1)]:
        dut.ena.value = enabled
        dut.rst_n.value = reset_n
        for pattern in (0x00, 0xFF, 0x55, 0xAA, 0x01, 0x80):
            dut.ui_in.value = pattern
            dut.uio_in.value = pattern ^ 0xFF
            await ClockCycles(dut.clk, 2)
            await Timer(1, unit="ns")
            assert int(dut.uo_out.value) == 0
            assert int(dut.uio_out.value) == 0
            assert int(dut.uio_oe.value) == 0
