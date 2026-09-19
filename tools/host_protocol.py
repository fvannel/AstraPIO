"""Pure framing helpers. Transport/DMA for a specific LPC remains to implement."""

READ = 0x03
WRITE = 0x02


def read_frame(address: int) -> bytes:
    if not 0 <= address <= 0xFF:
        raise ValueError("address must fit in 8 bits")
    return bytes((READ, address, 0, 0))


def write_frame(address: int, value: int) -> bytes:
    if not 0 <= address <= 0xFF or not 0 <= value <= 0xFFFF:
        raise ValueError("address/data must fit in 8/16 bits")
    return bytes((WRITE, address, value >> 8, value & 0xFF))


def read_value(response: bytes) -> int:
    if len(response) != 4:
        raise ValueError("exactly four response bytes required")
    return int.from_bytes(response[2:], "big")


def program_frames(words: list[int], *, abi: int = 3) -> list[bytes]:
    """Stop/reset the selected ABI's context(s), invalidate code, upload once.

    Callers must probe ABI (abi << 8) first and read back words/errors afterwards.
    Each transfer must honor the documented six-clock CS gap.
    """
    if abi not in (3, 4, 5, 6):
        raise ValueError("supported ABIs: 3, 4, 5, 6")
    if not 1 <= len(words) <= 16:
        raise ValueError("shared program length must be 1..16")
    if abi >= 5 and any(not 0 <= word <= 0x3FF for word in words):
        raise ValueError("ABI v5/v6 program words must fit in ten bits")
    return [write_frame(3, 0), write_frame(4, 1 if abi >= 4 else 3), write_frame(0x0A, 0)] + [
        write_frame(0x40 + index, word) for index, word in enumerate(words)]
