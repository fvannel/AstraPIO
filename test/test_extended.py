"""Byte serializer, counted loops, and inter-context rendezvous."""
import cocotb
from cocotb.triggers import ClockCycles, FallingEdge
from test import setup


@cocotb.test()
async def events_receive_and_counted_input(dut):
    host = await setup(dut)
    host.inputs = 1
    host.drive()
    # ctx0: LDI 0; LDX 5; INBIT 8; DJNZ 2; PUSH; SIGNAL; HALT.
    # ctx1: AWAIT; RECV; XOR 0x55; PUSH; IRQ; HALT.
    programs = ((0x1000, 0xF505, 0xF408, 0xF602, 0xF100, 0xF700, 0xE000),
                (0xF710, 0xF900, 0xA055, 0xF100, 0xD000, 0xE000))
    for ctx, words in enumerate(programs):
        for i, word in enumerate(words):
            await host.write(0x40 + 16 * ctx + i, word)
    await host.write(3, 3)
    assert await host.read(3) == 0
    assert await host.read(6) == 0
    assert await host.read(0x12) == 0x1F
    assert await host.read(0x17) == 0
    assert await host.read(0x15) == 0
    assert await host.read(0x25) == 0x804A
    assert await host.read(0x0D) == 0
    assert await host.read(5) == 2


@cocotb.test()
async def msb_serializer_on_owned_pins(dut):
    host = await setup(dut)
    await host.write(0x10, 3)
    # Enable both outputs, then shift MSB-first with a separate clock pin.
    program = (0x1003, 0x4000, 0x10A6, 0xF508,
               0xF300, 0xF211, 0xF210, 0xF604, 0xE000)
    for i, word in enumerate(program):
        await host.write(0x40 + i, word)
    bits = []

    async def capture():
        previous = 0
        for _ in range(900):
            await FallingEdge(dut.clk)
            pins = int(dut.uio_out.value)
            if pins & 2 and not previous & 2:
                bits.append(pins & 1)
            previous = pins

    task = cocotb.start_soon(capture())
    await host.write(3, 1)
    await task
    assert bits == [1, 0, 1, 0, 0, 1, 1, 0]
    assert await host.read(3) == 0
    assert await host.read(6) == 0
    assert await host.read(0x12) == 0
    assert await host.read(0x17) == 0
