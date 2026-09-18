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


def program_frames(words: list[int]) -> list[bytes]:
    """ABI v3: stop/reset both contexts, invalidate shared code, upload once.

    Callers must probe ABI 0x0300 first and read back words/errors afterwards.
    Each transfer must honor the documented six-clock CS gap.
    """
    if not 1 <= len(words) <= 16:
        raise ValueError("shared program length must be 1..16")
    return [write_frame(3, 0), write_frame(4, 3), write_frame(0x0A, 0)] + [
        write_frame(0x40 + index, word) for index, word in enumerate(words)]
