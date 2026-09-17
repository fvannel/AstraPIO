"""FIFO contract tested only at module ports against a deque scoreboard."""
from collections import deque
import random

import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def fifo_order_capacity_simultaneous_and_flush(dut):
    queue = deque()
    rng = random.Random(0xF1F0)
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.flush.value = 0
    dut.push.value = 0
    dut.pop.value = 0
    dut.data_in.value = 0

    async def cycle(push=0, pop=0, value=0, flush=0):
        dut.clk.value = 0
        dut.push.value = push
        dut.pop.value = pop
        dut.data_in.value = value
        dut.flush.value = flush
        await Timer(5, unit="ns")
        reset = not int(dut.rst_n.value) or flush
        can_pop = bool(queue) and pop
        can_push = push and (len(queue) < 4 or can_pop)
        if not reset:
            assert int(dut.empty.value) == (len(queue) == 0)
            assert int(dut.full.value) == (len(queue) == 4)
            assert int(dut.level.value) == len(queue)
            assert int(dut.data_out.value) == (queue[0] if queue else 0)
            assert int(dut.push_ready.value) == (len(queue) < 4 or can_pop)
        if reset:
            queue.clear()
        else:
            if can_pop:
                queue.popleft()
            if can_push:
                queue.append(value)
        dut.clk.value = 1
        await Timer(5, unit="ns")
        assert int(dut.level.value) == len(queue)
        assert int(dut.data_out.value) == (queue[0] if queue else 0)

    await cycle()
    dut.rst_n.value = 1
    await cycle(pop=1)  # Empty pop: no wraparound.
    for value in range(4):
        await cycle(push=1, value=0x1000 + value)
    await cycle(push=1, value=0xDEAD)  # Full push is rejected.
    await cycle(push=1, pop=1, value=0xBEEF)  # Full replacement keeps capacity/order.
    for _ in range(4):
        await cycle(pop=1)
    await cycle(push=1, pop=1, value=0x1234)  # No empty fall-through; value is queued.
    await cycle(flush=1, push=1, pop=1, value=0xFFFF)
    for _ in range(2000):
        await cycle(rng.randrange(2), rng.randrange(2), rng.randrange(65536), rng.randrange(80) == 0)
