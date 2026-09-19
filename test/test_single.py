"""Single-context ABI v4 acceptance, using only SPI/GPIO pins."""
import cocotb
import random
from cocotb.triggers import ClockCycles, FallingEdge, Timer, with_timeout
from spi_host import setup


async def load_program(host, words):
    await host.write(3, 0)
    await host.write(0x0A, 0)
    for index, word in enumerate(words):
        await host.write(0x40 + index, word)


@cocotb.test()
async def single_context_identity_capacity_and_no_alias(dut):
    host = await setup(dut)
    assert await host.read(0) == 0x5049
    assert await host.read(1) == 0x0400
    assert await host.read(2) == 1
    assert await host.read(0x0F) == 0x1002
    words = [0x1000+i for i in range(15)] + [0xE000]
    await load_program(host, words)
    assert await host.read(0x0A) == 16
    assert [await host.read(0x40+i) for i in range(16)] == words
    await host.write(0x12, 0x55)
    await host.write(0x22, 0xAA)  # Removed context must not alias context zero.
    assert await host.read(0x12) == 0x55
    assert await host.read(0x22) == 0
    assert await host.read(6) == 1
    await host.write(6, 1)
    await host.write(3, 2)
    assert await host.read(3) == 0 and await host.read(6) == 1


@cocotb.test()
async def program_integrity_and_spi_atomicity(dut):
    host = await setup(dut, half=137)
    assert await host.read(0x40) == 0
    await host.write(0x42, 0xAAAA)
    assert await host.read(0x0A) == 0 and await host.read(6) == 1
    await host.write(6, 1)
    rng = random.Random(0xC040)
    for pattern in (0, 0xFFFF, 0x5555, 0xAAAA, None):
        words = [rng.randrange(65536) if pattern is None else pattern ^ i for i in range(16)]
        await load_program(host, words)
        assert await host.read(0x0A) == 16
        assert [await host.read(0x40+i) for i in range(16)] == words
        await host.write(0x50, 0x1234)
        assert await host.read(0x40) == words[0] and await host.read(6) == 1
        await host.write(6, 1)
    from host_protocol import write_frame
    for bits in (1, 7, 8, 15, 16, 23, 31):
        await host.transfer(write_frame(0x40, 0xBEEF), bits=bits)
        assert await host.read(0x40) == words[0]
    await host.transfer(bytes.fromhex('9940beef'))
    assert await host.read(0x40) == words[0]
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    assert await host.read(0x0A) == 0 and await host.read(0x40) == 0


@cocotb.test()
async def all_output_pins_and_running_write_protection(dut):
    host = await setup(dut)
    await host.write(0x10, 0x3FFF)
    await load_program(host, [0x8108,0x10FF,0x4000,0x3000,0x3100,0xD000,0xE000])
    await host.write(3, 1)
    for address, value in ((0x40,0xE000),(0x10,2),(0x11,1),(0x12,0xFF),(0x0A,0)):
        await host.write(address, value)
        assert await host.read(6) == 1
        await host.write(6, 1)
    assert await host.read(0x40) == 0
    host.inputs = 1
    host.drive()
    await ClockCycles(dut.clk, 60)
    assert await host.read(3) == 0
    assert await host.read(7) == 0x3FFF and await host.read(8) == 0xFF
    assert int(dut.uio_out.value) == 0xFF and int(dut.uo_out.value) & 0xFC == 0xFC
    assert await host.read(5) == 1 and await host.read(6) == 0
    await host.write(5, 1)
    assert not int(dut.uo_out.value) & 2
    for pin in range(14):
        await host.write(4, 1)
        await host.write(0x10, 1 << pin)
        await load_program(host, [0xF201 | (pin << 4),0xE000])
        await host.write(3, 1)
        assert await host.read(7) == 1 << pin
        await host.write(4, 1)
        await load_program(host, [0x1000,0xF300 | (pin << 4),0xE000])
        await host.write(3, 1)
        assert await host.read(7) == 0 and await host.read(6) == 0


@cocotb.test()
async def streams_overflow_backpressure_and_aborted_read(dut):
    host = await setup(dut, half=139)
    await load_program(host, [0xF000,0xA05A,0xF100,0x5000])
    for value in (0x12,0xE7): await host.write(0x14, value)
    await host.write(0x14, 0x99)
    assert await host.read(6) == 1 and (await host.read(0x16) >> 12) & 3 == 2
    await host.write(6, 1)
    await host.write(0x0C, 1)
    await host.write(3, 1)
    assert int(dut.uo_out.value) & 2
    from host_protocol import read_frame
    for bits in (16,24,31):
        await host.transfer(read_frame(0x15), bits=bits)
        assert await host.read(0x16) >> 14 == 2
    # TX continues into a stalled PUSH while RX is full; nothing may be lost.
    for value in (0xAB,0xCD): await host.write(0x14, value)
    for value in (0x12,0xE7,0xAB,0xCD):
        assert await host.read(0x15) == 0x8000 | (value ^ 0x5A)
    assert await host.read(0x15) == 0
    rng = random.Random(402)
    for _ in range(50):
        value = rng.randrange(256)
        await host.write(0x14, value)
        assert await host.read(0x15) == 0x8000 | (value ^ 0x5A)
    assert await host.read(6) == 0 and not int(dut.uo_out.value) & 2


@cocotb.test()
async def host_events_and_counted_input_loop(dut):
    host = await setup(dut)
    host.inputs = 1
    host.drive()
    await load_program(host, [0xF710,0x1000,0xF505,0xF408,0xF603,0xF100,0xD000,0xE000])
    await host.write(3, 1)
    assert await host.read(3) == 1 and await host.read(0x11) == 0
    assert await host.read(0x15) == 0
    await host.write(0x0D, 1)
    assert await host.read(3) == 0 and await host.read(0x15) == 0x801F
    assert await host.read(0x0D) == 0 and await host.read(0x17) == 0
    assert await host.read(5) == 1 and await host.read(6) == 0
    await host.write(0x0D, 1)
    await host.write(0x0E, 1)
    assert await host.read(0x0D) == 0
    await host.write(4, 1)
    await load_program(host, [0xF720,0xE000])
    await host.write(0x0D, 1)
    await host.write(3, 1)
    assert await host.read(0x0D) == 0


@cocotb.test()
async def bounds_removed_instructions_and_restart(dut):
    host = await setup(dut)
    for words in ([0]*16,[0x5010],[0xF610],[0xF810],[0x810D],[0xF40D],
                  [0xF2E1],[0xF3F0],[0xF700],[0xF900],[0xFF00]):
        await host.write(4, 1)
        await load_program(host, words)
        await host.write(3, 1)
        assert await host.read(3) == 0 and await host.read(6) == 0x100
        if len(words) == 16: assert await host.read(0x11) == 16
        await host.write(3, 1)
        assert await host.read(3) == 0
    await host.write(4, 1)
    await load_program(host, [0xE000])
    for address, value in ((0x11,16),(0x10,0x4000),(3,3),(4,3),(0x0C,2)):
        await host.write(address, value)
        assert await host.read(6) == 1
        await host.write(6, 1)
    await host.write(3, 1)
    assert await host.read(6) == 0


@cocotb.test()
async def uart_waveform_preserves_instruction_cadence(dut):
    host = await setup(dut)
    from pathlib import Path
    from pioasm import assemble
    words = assemble((Path(__file__).resolve().parents[1]/'examples/compact/uart_tx.pio').read_text())
    await load_program(host, words)
    await host.write(0x10, 1)
    payload = [0xA6,0,0xFF]
    for byte in payload[:2]: await host.write(0x14, byte)
    async def receiver():
        while not int(dut.uio_out.value)&1: await FallingEdge(dut.clk)
        decoded = []
        for _ in payload:
            while int(dut.uio_out.value)&1: await FallingEdge(dut.clk)
            await Timer(4320, unit='ns')
            assert int(dut.uio_out.value)&1 == 0
            value = 0
            for bit in range(8):
                await Timer(8640, unit='ns')
                value |= (int(dut.uio_out.value)&1) << bit
            await Timer(8640, unit='ns')
            assert int(dut.uio_out.value)&1 == 1
            decoded.append(value)
        return decoded
    task = cocotb.start_soon(receiver())
    await host.write(3, 1)
    await host.write(0x14, payload[2])
    assert await with_timeout(task,400,'us') == payload
    assert await host.read(6) == 0


@cocotb.test()
async def spi_transmitter_preserves_all_bits_and_cycle_widths(dut):
    from pioasm import assemble
    from cocotb.utils import get_sim_time
    host = await setup(dut)
    words = assemble('''LDI 3
DIR
byte: PULL
LDX 8
bit: OUTBIT 0
SET 1,1
SET 1,0
DJNZ bit
JMP byte''', abi=4)
    await load_program(host, words)
    await host.write(0x10, 3)
    payload = [0,255,0x55,0xAA,0x80,1,0xA6,0x39]
    async def receiver():
        decoded, value, count = [], 0, 0
        prev, rise = 0, None
        while len(decoded) < len(payload):
            await FallingEdge(dut.clk)
            level = int(dut.uio_out.value)
            sck = (level >> 1) & 1
            if sck and not prev:
                assert int(dut.uio_oe.value) == 3
                rise = float(get_sim_time(unit='ns'))
                value = (value << 1) | (level & 1)
                count += 1
            elif prev and not sck:
                assert float(get_sim_time(unit='ns')) - rise == 80
                if count == 8:
                    decoded.append(value)
                    value, count = 0, 0
            prev = sck
        return decoded
    task = cocotb.start_soon(receiver())
    await host.write(3, 1)
    for value in payload: await host.write(0x14, value)
    assert await with_timeout(task,200,'us') == payload
    assert await host.read(6) == 0


@cocotb.test()
async def reset_disable_and_queue_flush(dut):
    host = await setup(dut)
    await load_program(host, [0x1001,0x4000,0x3000,0x5003])
    await host.write(0x10, 1)
    await host.write(0x14, 0xCD)
    await host.write(3, 1)
    assert int(dut.uio_oe.value) == 1
    await host.write(4, 1)
    assert (await host.read(0x16)>>12)&3 == 0
    assert int(dut.uio_oe.value) == 1  # RESTART retains pad state.
    dut.ena.value = 0
    await Timer(1,unit='ns')
    assert int(dut.uio_oe.value) == 0 and int(dut.uo_out.value) == 0
    await ClockCycles(dut.clk,5)
    dut.ena.value = 1
    await ClockCycles(dut.clk,5)
    assert await host.read(0x0A) == 0 and await host.read(3) == 0
    assert (await host.read(0x16)>>12)&3 == 0


@cocotb.test()
async def empty_snapshot_does_not_pop_late_byte(dut):
    host = await setup(dut,half=137)
    await load_program(host,[0x8108,0x10C7,0xF100,0xE000])
    await host.write(3,1)
    async def release_producer():
        await Timer(5500,unit='ns')
        host.inputs = 1
    task = cocotb.start_soon(release_producer())
    assert await host.read(0x15) == 0
    await task
    assert await host.read(0x15) == 0x80C7
    assert await host.read(0x15) == 0 and await host.read(6) == 0


@cocotb.test()
async def byte_alu_branches_and_both_input_banks(dut):
    host = await setup(dut)
    rng = random.Random(0xA104)
    for value, mask in [(0,0),(255,0),(0x80,0x55)] + [(rng.randrange(256),rng.randrange(256)) for _ in range(7)]:
        await host.write(4,1)
        await load_program(host,[0x1000|value,0xA000|mask,0xB000,0xC000,0x7000,0xF100,0xE000])
        await host.write(3,1)
        assert await host.read(0x15) == 0x8000 | ((((value ^ mask) & 0x7F) - 1) & 255)
        assert await host.read(6) == 0
    await host.write(4,1)
    await load_program(host,[0x1000,0xF500,0x7000,0xF602,0xF100,0x1080,0xF809,
                            0x10AA,0xE000,0x1000,0x600D,0x1055,0xF100,0xE000])
    await host.write(3,1)
    assert await host.read(0x15) == 0x80F0 and await host.read(0x15) == 0x8055
    await host.write(4,1)
    host.inputs = 0x1B
    host.drive()
    dut.uio_in.value = 0xA5
    await load_program(host,[0x2000,0xF100,0x2100,0xF100,0xE000])
    await host.write(3,1)
    assert await host.read(0x15) == 0x80A5 and await host.read(0x15) == 0x801B
    assert await host.read(6) == 0
