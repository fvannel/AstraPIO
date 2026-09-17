#!/usr/bin/env python3
"""Assembler for the project's provisional ISA v0, not Raspberry Pi PIO."""

import argparse
from pathlib import Path

SIMPLE = {"NOP": 0x0, "IN": 0x2, "OUT": 0x3, "DIR": 0x4, "DEC": 0x7,
          "SHL": 0xB, "SHR": 0xC, "IRQ": 0xD, "HALT": 0xE}
IMMEDIATE = {"LDI": 0x1, "JMP": 0x5, "JNZ": 0x6, "DELAY": 0x9, "XOR": 0xA}


def assemble(source: str) -> list[int]:
    labels = {}
    instructions = []
    for number, line in enumerate(source.splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" in line:
            label, line = (part.strip() for part in line.split(":", 1))
            if not label.isidentifier() or label in labels:
                raise ValueError(f"line {number}: invalid or duplicate label {label!r}")
            labels[label] = len(instructions)
        if line:
            instructions.append((number, line.replace(",", " ").split()))
    if not 1 <= len(instructions) <= 16:
        raise ValueError("a context requires 1..16 instructions")

    words = []
    for number, tokens in instructions:
        op, args = tokens[0].upper(), tokens[1:]
        try:
            if op in SIMPLE and not args:
                word = SIMPLE[op] << 12
            elif op in IMMEDIATE and len(args) == 1:
                value = labels[args[0]] if op in ("JMP", "JNZ") and args[0] in labels else int(args[0], 0)
                limit = 15 if op in ("JMP", "JNZ") else 4095
                if not 0 <= value <= limit:
                    raise ValueError(f"operand must be 0..{limit}")
                word = (IMMEDIATE[op] << 12) | value
            elif op == "WAIT" and len(args) == 2:
                pin, level = (int(arg, 0) for arg in args)
                if not 0 <= pin <= 12 or level not in (0, 1):
                    raise ValueError("WAIT expects input 0..12 and level 0 or 1")
                word = 0x8000 | (level << 8) | pin
            else:
                raise ValueError(f"unknown instruction or wrong argument count: {' '.join(tokens)}")
        except ValueError as exc:
            raise ValueError(f"line {number}: {exc}") from exc
        words.append(word)
    return words


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    try:
        for word in assemble(args.source.read_text()):
            print(f"{word:04x}")
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
