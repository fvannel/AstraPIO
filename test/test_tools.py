"""Fast host-side tests; run with python -m unittest discover -s test -p test_tools.py."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from pioasm import assemble
from host_protocol import program_frames, read_frame, read_value, write_frame


class ToolsTest(unittest.TestCase):
    def test_encoding(self):
        self.assertEqual(assemble("loop: LDI 0x123\nOUT\nWAIT 12,1\nJMP loop\nHALT"),
                         [0x1123, 0x3000, 0x810C, 0x5000, 0xE000])

    def test_all_mnemonics(self):
        self.assertEqual(assemble("NOP\nLDI 0\nIN\nOUT\nDIR\nJMP 0\nJNZ 0\nDEC\n"
                                  "WAIT 0,0\nDELAY 0\nXOR 0\nSHL\nSHR\nIRQ\nHALT"),
                         [op << 12 for op in range(15)])

    def test_reject_bad_programs(self):
        for source in ("", "OUT 1", "LDI -1", "LDI 4096", "JMP 16", "JMP missing",
                       "WAIT 13, 0", "WAIT 0, 2", "NOP\n" * 17, "x:NOP\nx:HALT"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                assemble(source)

    def test_frames(self):
        self.assertEqual(read_frame(0x12), bytes.fromhex("03 12 00 00"))
        self.assertEqual(write_frame(0x40, 0x1234), bytes.fromhex("02 40 12 34"))
        self.assertEqual(read_value(bytes.fromhex("00 00 50 49")), 0x5049)
        self.assertEqual(program_frames(1, [0xE000]), [bytes.fromhex("02 50 e0 00")])
        for args in ((256, 0), (0, 65536), (-1, 0)):
            with self.assertRaises(ValueError):
                write_frame(*args)
        with self.assertRaises(ValueError):
            read_value(b"\0")
        with self.assertRaises(ValueError):
            program_frames(2, [0])


if __name__ == "__main__":
    unittest.main()
