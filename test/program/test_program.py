"""Clock-gated latch storage through its public port, with provider cell models."""
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge, Timer

@cocotb.test()
async def accepted_write_isolated_from_busy_bus_changes(dut):
    dut.rst_n.value=0
    dut.write_enable.value=0
    dut.write_address.value=0
    dut.write_data.value=0
    dut.read_address.value=0
    cocotb.start_soon(Clock(dut.clk,20,unit='ns').start())
    await ClockCycles(dut.clk,3)
    dut.rst_n.value=1
    expected={}
    rng=random.Random(0x16A7)
    width=len(dut.write_data)
    mask=(1 << width)-1
    for index in range(200):
        address=index if index<16 else rng.randrange(16)
        value=rng.randrange(1 << width)
        await FallingEdge(dut.clk)
        await Timer(1,unit='ns')
        assert int(dut.busy.value)==0
        dut.write_address.value=address
        dut.write_data.value=value
        dut.write_enable.value=1
        await RisingEdge(dut.clk)
        await Timer(1,unit='ns')
        assert int(dut.busy.value)==1
        # Inputs can change while busy, but no second request may be accepted.
        dut.write_address.value=(address+1)%16
        dut.write_data.value=value^mask
        await RisingEdge(dut.clk)
        await Timer(1,unit='ns')
        assert int(dut.busy.value)==1
        dut.write_enable.value=0
        await RisingEdge(dut.clk)
        await Timer(1,unit='ns')
        assert int(dut.busy.value)==0
        expected[address]=value
        for a,v in expected.items():
            dut.read_address.value=a
            await Timer(1,unit='ns')
            assert int(dut.read_data.value)==v,(index,a,v)
