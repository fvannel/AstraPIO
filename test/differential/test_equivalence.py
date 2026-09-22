"""Cycle-by-cycle differential behavior at the two cores' public bus/pin ports.

The frozen v4 reference is independently decoded RTL, not a second copy of the
new decoder. No internal implementation state is read. This is bounded dynamic
equivalence, not formal proof, and does not qualify physical timing.
"""
import random
import sys
from pathlib import Path
import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools'))
from pioasm import assemble


def canonical_operations():
    result = ['NOP','DIR','DEC','SHL','SHR','IRQ','HALT','PULL','PUSH',
              'AWAIT','CLR_EVENT','IN','IN 1','OUT','OUT 1']
    for op in ('LDI','DELAY','XOR'):
        result += [f'{op} {v}' for v in range(256)]
    for op, count in (('JMP',16),('JNZ',16),('JBIT',16),('OUTBIT',14),
                      ('INBIT',13),('LDX',16),('DJNZ',16)):
        result += [f'{op} {v}' for v in range(count)]
    result += [f'WAIT {p},{v}' for p in range(13) for v in (0,1)]
    result += [f'SET {p},{v}' for p in range(14) for v in (0,1)]
    assert len(result) == 944
    return result


@cocotb.test()
async def all_canonical_operations_and_random_programs_match_v4(dut):
    rng = random.Random(0xA510)
    observable_addresses = [3,5,6,7,8,9,0x0C,0x0D,0x10,0x11,0x12,0x13,0x15,0x16,0x17,0x1F]
    context = ''

    async def cycle():
        dut.clk.value = 0
        await Timer(5, unit='ns')
        dut.clk.value = 1
        await Timer(5, unit='ns')
        for kind in ('claimed','pins','sampled','oe','irq','valid'):
            assert int(getattr(dut,kind+'_v4').value) == int(getattr(dut,kind+'_v5').value), (context,kind)
        if int(dut.address.value) in observable_addresses:
            assert int(dut.read_v4.value) == int(dut.read_v5.value), (context,int(dut.address.value),str(dut.read_v4.value),str(dut.read_v5.value))

    async def write(address, old, new=None):
        dut.address.value = address
        dut.write_v4.value = old
        dut.write_v5.value = old if new is None else new
        dut.write_enable.value = 1
        await cycle()
        dut.write_enable.value = 0
        for _ in range(3):
            await cycle()

    operations = canonical_operations()
    cases = []
    # Both zero and sign-set accumulators exercise conditional branch polarity.
    for acc in (0, 0xA5):
        for op in operations:
            cases.append(('canonical '+op+f' acc={acc}',
                          f'LDI 255\nDIR\nOUT\nOUT 1\nLDI {acc}\n{op}\nHALT'))
    for index in range(100):
        cases.append((f'random {index}', '\n'.join(rng.choices(operations,k=15)+['HALT'])))
    for context, source in cases:
        dut.clk.value = 0
        dut.rst_n.value = 0
        dut.write_enable.value = 0
        dut.read_commit.value = 0
        dut.address.value = 0
        dut.write_v4.value = 0
        dut.write_v5.value = 0
        dut.pins_in.value = rng.randrange(8192)
        dut.reserved_pins.value = 0
        for _ in range(3): await cycle()
        dut.rst_n.value = 1
        await write(0x10, 0x3FFF)
        await write(0x17, rng.randrange(16))
        await write(0x14, rng.randrange(256))
        await write(0x14, rng.randrange(256))
        await write(0x0D, rng.randrange(2))
        old, new = assemble(source,abi=4), assemble(source,abi=5)
        assert len(old) == len(new)
        for index, (v4,v5) in enumerate(zip(old,new)):
            await write(0x40+index,v4,v5)
        await write(3,1)
        # Longest DELAY (255 four-clock slots) must finish, not only its prefix.
        for index in range(1100):
            dut.address.value = observable_addresses[index % len(observable_addresses)]
            if index % 29 == 0: dut.pins_in.value = rng.randrange(8192)
            await cycle()
        await write(3,0)
        for address in observable_addresses:
            dut.address.value = address
            await cycle()
    dut._log.info('Matched 944 operations x 2 initial accumulator states and 100 random programs cycle by cycle.')
