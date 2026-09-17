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


def program_frames(context: int, words: list[int]) -> list[bytes]:
    """Data frames only. Caller must stop BOTH contexts before uploading."""
    if context not in (0, 1) or not 1 <= len(words) <= 48:
        raise ValueError("context must be 0/1 and program length 1..48")
    frames = [write_frame(0x1F + 16 * context, 0)]  # Invalidate previous program first.
    for index, word in enumerate(words):
        if index < 16:
            frames.append(write_frame(0x40 + 16 * context + index, word))
        else:
            frames.extend((write_frame(0x0A, 64 * context + index), write_frame(0x0B, word)))
    return frames
