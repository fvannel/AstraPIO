"""AstraPIO compact ABI v3 integration tests, through SPI/GPIO pins only."""
import random
import cocotb
from cocotb.triggers import ClockCycles, FallingEdge, Timer, with_timeout
from spi_host import setup


async def load_shared(host, words):
    await host.write(3, 0)
    await host.write(0x0A, 0)  # Invalidate shared program and both PCs.
    for index, word in enumerate(words):
        await host.write(0x40 + index, word)


@cocotb.test()
async def shared_program_integrity_and_spi_atomicity(dut):
    host = await setup(dut, half=137)
    assert await host.read(0) == 0x5049
    assert await host.read(1) == 0x0300
    assert await host.read(0x0F) == 0x1002  # 16 shared words; 2 bytes/queue.
    assert await host.read(0x40) == 0
    # No holes or address aliasing; a rejected write cannot publish a word.
    await host.write(0x42, 0xAAAA)
    assert await host.read(0x0A) == 0
    assert await host.read(6) == 1
    await host.write(6, 1)
    rng = random.Random(0xC030)
    for pattern in (0x0000, 0xFFFF, 0x5555, 0xAAAA, None):
        words = [rng.randrange(65536) if pattern is None else pattern ^ i for i in range(16)]
        await load_shared(host, words)
        assert await host.read(0x0A) == 16
        assert [await host.read(0x40 + i) for i in range(16)] == words
        await host.write(0x50, 0x1234)
        assert await host.read(0x40) == words[0]
        assert await host.read(6) == 1
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
    assert await host.read(0x0A) == 0
    assert await host.read(0x40) == 0


@cocotb.test()
async def independent_contexts_and_pin_ownership(dut):
    host = await setup(dut)
    await host.write(0x10, 1)
    await host.write(0x20, 0x100)
    await load_shared(host, [0x8108,0x1001,0x3000,0x4000,0xD000,0xE000,
                             0x1002,0x3000,0xD000,0xE000])
    await host.write(0x21, 6)
    await host.write(3, 3)
    assert await host.read(3) == 1
    assert await host.read(7) == 0x100
    assert await host.read(5) == 2
    for address, value in ((0x40,0xE000),(0x10,2),(0x11,1),(0x12,0xFF),(0x0A,0)):
        await host.write(address, value)
        assert await host.read(6) == 1
        await host.write(6,1)
    assert await host.read(0x40) == 0
    host.inputs = 1
    host.drive()
    await ClockCycles(dut.clk, 60)
    assert await host.read(3) == 0
    assert await host.read(7) == 0x101
    assert await host.read(8) == 1
    assert await host.read(5) == 3
    assert await host.read(6) == 0
    assert await host.read(0x40) == 0x8108
    await host.write(5,3)
    assert not int(dut.uo_out.value) & 2


@cocotb.test()
async def streams_overflow_backpressure_and_aborted_read(dut):
    host = await setup(dut, half=139)
    await load_shared(host, [0xF000,0xA05A,0xF100,0x5000])
    for context in (0,1):
        for value in (0x12,0xE7):
            await host.write(0x14 + context*16, value)
        await host.write(0x14 + context*16, 0x99)
        assert await host.read(6) == 1
        assert (await host.read(0x16 + context*16) >> 12) & 3 == 2
        await host.write(6,1)
    await host.write(0x0C,3)
    await host.write(3,3)
    from host_protocol import read_frame
    for context in (0,1):
        a = 0x15 + context*16
        for bits in (16,24,31):
            await host.transfer(read_frame(a), bits=bits)
            assert (await host.read(a+1) >> 14) == 2
        assert await host.read(a) == (0x8000 | (0x12 ^ 0x5A))
        assert await host.read(a) == (0x8000 | (0xE7 ^ 0x5A))
        assert await host.read(a) == 0
    rng = random.Random(302)
    for _ in range(25):
        values = [rng.randrange(256),rng.randrange(256)]
        for context in (0,1): await host.write(0x14+context*16,values[context])
        for context in (0,1): assert await host.read(0x15+context*16) == (0x8000 | (values[context]^0x5A))
    assert await host.read(6) == 0
    assert not int(dut.uo_out.value) & 2


@cocotb.test()
async def peer_events_recv_and_counted_loop(dut):
    host = await setup(dut)
    host.inputs = 1
    host.drive()
    await load_shared(host, [0x1000,0xF505,0xF408,0xF602,0xF100,0xF700,0xE000,
                             0xF710,0xF900,0xA055,0xF100,0xD000,0xE000])
    await host.write(0x21,7)
    await host.write(3,3)
    assert await host.read(3) == 0
    assert await host.read(0x12) == 31
    assert await host.read(0x17) == 0
    assert await host.read(0x15) == 0
    assert await host.read(0x25) == 0x804A
    assert await host.read(0x0D) == 0
    assert await host.read(5) == 2
    assert await host.read(6) == 0


@cocotb.test()
async def instruction_bounds_fault_and_restart(dut):
    host = await setup(dut)
    for words in ([0]*16, [0x5010], [0xF610], [0xF810], [0x810D], [0xF40D], [0xF271], [0xFF00]):
        await host.write(4,3)
        await load_shared(host, words)
        await host.write(3,1)
        assert await host.read(3) == 0
        assert await host.read(6) == 0x100
        if len(words) == 16: assert await host.read(0x11) == 16
        await host.write(3,1)
        assert await host.read(3) == 0
    await host.write(4,3)
    await load_shared(host, [0xE000])
    await host.write(0x11,16)
    assert await host.read(6) == 1
    await host.write(6,1)
    await host.write(3,3)
    assert await host.read(6) == 0


@cocotb.test()
async def spi_loopback_two_programs_in_shared_store(dut):
    host = await setup(dut, half=131)
    from pioasm import assemble
    program = assemble('''LDI 3
DIR
txbyte: PULL
LDX 8
txbit: OUTBIT 0
SET 1,1
SET 1,0
DJNZ txbit
JMP txbyte
rxbyte: LDX 8
rxbit: WAIT 1,1
INBIT 0
WAIT 1,0
DJNZ rxbit
PUSH
JMP rxbyte''')
    assert len(program) == 16
    await load_shared(host, program)
    await host.write(0x10,3)
    await host.write(0x21,9)
    async def board_wires():
        while True:
            await FallingEdge(dut.clk)
            dut.uio_in.value = int(dut.uio_out.value) & 3
    task = cocotb.start_soon(board_wires())
    await host.write(3,3)
    for value in (0,255,0x55,0xAA,0x80,1,0xA6,0x39):
        await host.write(0x14,value)
        assert await host.read(0x25) == 0x8000 | value
    assert await host.read(6) == 0
    task.cancel()


@cocotb.test()
async def uart_waveform_and_streaming_refill(dut):
    host = await setup(dut)
    from pathlib import Path
    from pioasm import assemble
    words = assemble((Path(__file__).resolve().parents[1]/'examples/compact/uart_tx.pio').read_text())
    await load_shared(host, words)
    await host.write(0x10,1)
    payload = [0xA6,0x00,0xFF]
    for byte in payload[:2]: await host.write(0x14,byte)
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
    await host.write(3,1)
    await host.write(0x14,payload[2])
    assert await with_timeout(task,400,'us') == payload
    assert await host.read(6) == 0


@cocotb.test()
async def reset_disable_and_queue_flush_isolation(dut):
    host = await setup(dut)
    await load_shared(host,[0x1001,0x4000,0x3000,0x5003])
    await host.write(0x10,1)
    await host.write(0x24,0xAB)
    await host.write(0x14,0xCD)
    await host.write(3,1)
    assert int(dut.uio_oe.value) == 1
    await host.write(4,1)
    assert (await host.read(0x16)>>12)&3 == 0
    assert (await host.read(0x26)>>12)&3 == 1
    assert int(dut.uio_oe.value) == 1  # RESTART retains pad state.
    dut.ena.value = 0
    await Timer(1,unit='ns')
    assert int(dut.uio_oe.value) == 0
    assert int(dut.uo_out.value) == 0
    await ClockCycles(dut.clk,5)
    dut.ena.value = 1
    await ClockCycles(dut.clk,5)
    assert await host.read(0x0A) == 0
    assert await host.read(3) == 0
    assert (await host.read(0x26)>>12)&3 == 0


@cocotb.test()
async def host_snapshot_excludes_peer_through_commit(dut):
    host = await setup(dut)
    for offset in (0, 20, 40, 60):
        host.inputs = 0
        host.drive()
        dut.rst_n.value = 0
        await ClockCycles(dut.clk,5)
        dut.rst_n.value = 1
        await ClockCycles(dut.clk,5)
        await Timer(offset + 1,unit='ns')
        # Context 0 sends two bytes; context 1 requests the first only after the
        # host snapshot has already locked it. The peer must get only byte two.
        await load_shared(host, [0x10A5,0xF100,0x8108,0x105A,0xF100,0xE000,
                                 0x8109,0xF900,0xF100,0xE000])
        await host.write(0x21,6)
        await host.write(3,3)
        async def release_peer():
            await Timer(5000,unit='ns')
            host.inputs = 2  # transfer() drives the changed input on its next bit.
        task = cocotb.start_soon(release_peer())
        assert await host.read(0x15) == 0x80A5
        await task
        assert await host.read(0x25) == 0, 'peer duplicated the host snapshot'
        host.inputs = 3
        host.drive()
        assert await host.read(0x25) == 0x805A
        assert await host.read(0x15) == 0
        assert await host.read(6) == 0


@cocotb.test()
async def empty_snapshot_does_not_pop_late_byte(dut):
    host = await setup(dut,half=137)
    await load_shared(host,[0x8108,0x10C7,0xF100,0xE000])
    await host.write(3,1)
    async def release_producer():
        await Timer(5500,unit='ns')
        host.inputs = 1
    task = cocotb.start_soon(release_producer())
    assert await host.read(0x15) == 0
    await task
    assert await host.read(0x15) == 0x80C7
    assert await host.read(0x15) == 0
    assert await host.read(6) == 0


@cocotb.test()
async def byte_alu_branches_and_both_input_banks(dut):
    host = await setup(dut)
    rng = random.Random(0xA103)
    for value, mask in [(0,0),(255,0),(0x80,0x55)] + [(rng.randrange(256),rng.randrange(256)) for _ in range(7)]:
        await host.write(4,3)
        await load_shared(host,[0x1000|value,0xA000|mask,0xB000,0xC000,0x7000,0xF100,0xE000])
        await host.write(3,3)
        expected = (((value ^ mask) & 0x7F) - 1) & 255
        for address in (0x15,0x25): assert await host.read(address) == 0x8000 | expected
        assert await host.read(6) == 0
    await host.write(4,3)
    # A zero loop count means sixteen iterations. JBIT taken and JNZ not taken.
    await load_shared(host,[0x1000,0xF500,0x7000,0xF602,0xF100,0x1080,0xF809,
                            0x10AA,0xE000,0x1000,0x600D,0x1055,0xF100,0xE000])
    await host.write(3,3)
    for address in (0x15,0x25):
        assert await host.read(address) == 0x80F0
        assert await host.read(address) == 0x8055
    await host.write(4,3)
    host.inputs = 0x1B
    host.drive()
    dut.uio_in.value = 0xA5
    await load_shared(host,[0x2000,0xF100,0x2100,0xF100,0xE000])
    await host.write(3,3)
    for address in (0x15,0x25):
        assert await host.read(address) == 0x80A5
        assert await host.read(address) == 0x801B
    assert await host.read(6) == 0
