#!/usr/bin/env python3
"""Assembler for AstraPIO ABI v3/v4; select --abi 4 for the single-context chip."""

import argparse
from pathlib import Path

SIMPLE = {"NOP": 0x0, "IN": 0x2, "OUT": 0x3, "DIR": 0x4, "DEC": 0x7,
          "SHL": 0xB, "SHR": 0xC, "IRQ": 0xD, "HALT": 0xE}
IMMEDIATE = {"LDI": 0x1, "JMP": 0x5, "JNZ": 0x6, "DELAY": 0x9, "XOR": 0xA}
EXT_SIMPLE = {"PULL": 0xF000, "PUSH": 0xF100, "SIGNAL": 0xF700,
              "AWAIT": 0xF710, "CLR_EVENT": 0xF720, "RECV": 0xF900}


def assemble(source: str, *, abi: int = 3) -> list[int]:
    if abi not in (3, 4):
        raise ValueError("supported ABIs: 3 (two contexts), 4 (single context)")
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
        raise ValueError("the shared program requires 1..16 instructions")

    words = []
    for number, tokens in instructions:
        op, args = tokens[0].upper(), tokens[1:]
        try:
            if op in EXT_SIMPLE and not args:
                if abi == 4 and op in ("SIGNAL", "RECV"):
                    raise ValueError(f"{op} requires two contexts (ABI v3 only)")
                word = EXT_SIMPLE[op]
            elif op in ("OUTBIT", "INBIT", "LDX", "DJNZ", "JBIT") and len(args) == 1:
                value = labels[args[0]] if op in ("DJNZ", "JBIT") and args[0] in labels else int(args[0], 0)
                limit = {"OUTBIT": 13 if abi == 4 else 6, "INBIT": 12, "LDX": 15, "DJNZ": 15, "JBIT": 15}[op]
                if not 0 <= value <= limit:
                    raise ValueError(f"operand must be 0..{limit}")
                base = {"OUTBIT": 0xF300, "INBIT": 0xF400, "LDX": 0xF500,
                        "DJNZ": 0xF600, "JBIT": 0xF800}[op]
                word = base | (value << 4 if op == "OUTBIT" else value)
            elif op == "SET" and len(args) == 2:
                pin, level = (int(arg, 0) for arg in args)
                limit = 13 if abi == 4 else 6
                if not 0 <= pin <= limit or level not in (0, 1):
                    raise ValueError(f"SET expects output 0..{limit} and level 0 or 1")
                word = 0xF200 | (pin << 4) | level
            elif op in SIMPLE and not args:
                word = SIMPLE[op] << 12
            elif op == "IN" and args == ["1"]:
                word = 0x2100
            elif op == "OUT" and args == ["1"] and abi == 4:
                word = 0x3100
            elif op in IMMEDIATE and len(args) == 1:
                value = labels[args[0]] if op in ("JMP", "JNZ") and args[0] in labels else int(args[0], 0)
                limit = 15 if op in ("JMP", "JNZ") else 255
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
    parser.add_argument("--abi", type=int, choices=(3, 4), default=3,
                        help="default 3 retains legacy programs; use 4 for the single-context chip")
    args = parser.parse_args()
    try:
        for word in assemble(args.source.read_text(), abi=args.abi):
            print(f"{word:04x}")
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
