"""Fast host-side tests; run with python -m unittest discover -s test -p test_tools.py."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from pioasm import assemble
from host_protocol import program_frames, read_frame, read_value, write_frame


class ToolsTest(unittest.TestCase):
    def test_dense_encoding_keeps_program_length_and_byte_constants(self):
        source = 'LDI 255\nDELAY 255\nXOR 255\nOUT 1\nSET 13,1\nOUTBIT 13\nAWAIT\nHALT'
        self.assertEqual(assemble(source, abi=5),
                         [0x0FF, 0x1FF, 0x2FF, 0x30E, 0x37D, 0x38D, 0x309, 0x306])
        self.assertEqual(assemble('NOP\n' * 15 + 'HALT', abi=5), [0x300]*15+[0x306])

    def test_dense_codebook_is_complete_and_collision_free(self):
        forms = []
        for group, op in enumerate(('LDI', 'DELAY', 'XOR')):
            forms.extend((f'{op} {v}', (group << 8) | v) for v in range(256))
        simple = ['NOP','DIR','DEC','SHL','SHR','IRQ','HALT','PULL','PUSH',
                  'AWAIT','CLR_EVENT','IN','IN 1','OUT','OUT 1']
        forms.extend((op, 0x300 | i) for i, op in enumerate(simple))
        for group, op, count in ((1,'JMP',16),(2,'JNZ',16),(3,'JBIT',16),
                                  (8,'OUTBIT',14),(9,'INBIT',13),(10,'LDX',16),(11,'DJNZ',16)):
            forms.extend((f'{op} {v}', 0x300 | group << 4 | v) for v in range(count))
        for level in (0, 1):
            forms.extend((f'WAIT {p},{level}', 0x340 | level << 4 | p) for p in range(13))
            forms.extend((f'SET {p},{level}', 0x360 | level << 4 | p) for p in range(14))
        words = []
        for source, expected in forms:
            with self.subTest(source=source):
                word = assemble(source, abi=5)[0]
                self.assertEqual(word, expected)
                words.append(word)
        self.assertEqual(len(set(words)), 944)
        for source in ('SIGNAL','RECV','SET 14,1','INBIT 13','OUTBIT 14','JMP 16','LDI 256'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                assemble(source, abi=5)

    def test_dense_upload_rejects_wrong_word_width_before_transport(self):
        self.assertEqual(program_frames([0x306], abi=5),
                         [bytes.fromhex(x) for x in ('02030000','02040001','020a0000','02400306')])
        for word in (-1, 0x400, 0xE000):
            with self.subTest(word=word), self.assertRaises(ValueError):
                program_frames([word], abi=5)

    def test_single_context_abi(self):
        self.assertEqual(assemble('OUT 1\nSET 13,1\nOUTBIT 13\nAWAIT', abi=4),
                         [0x3100, 0xF2D1, 0xF3D0, 0xF710])
        for source in ('SET 14,1', 'OUTBIT 14', 'SIGNAL', 'RECV'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                assemble(source, abi=4)
        for abi in (2, 7):
            with self.assertRaises(ValueError): assemble('HALT', abi=abi)
            with self.assertRaises(ValueError): program_frames([0xE000], abi=abi)
        self.assertEqual(program_frames([0xE000], abi=4)[1], bytes.fromhex('02 04 00 01'))

    def test_encoding(self):
        self.assertEqual(assemble("loop: LDI 0x23\nOUT\nWAIT 12,1\nJMP loop\nHALT"),
                         [0x1023, 0x3000, 0x810C, 0x5000, 0xE000])

    def test_all_mnemonics(self):
        self.assertEqual(assemble("NOP\nLDI 0\nIN\nOUT\nDIR\nJMP 0\nJNZ 0\nDEC\n"
                                  "WAIT 0,0\nDELAY 0\nXOR 0\nSHL\nSHR\nIRQ\nHALT"),
                         [op << 12 for op in range(15)])

    def test_reject_bad_programs(self):
        for source in ("", "OUT 1", "LDI -1", "LDI 256", "JMP 16", "JMP missing",
                       "WAIT 13, 0", "WAIT 0, 2", "NOP\n" * 17, "x:NOP\nx:HALT"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                assemble(source)

    def test_extended_instructions(self):
        self.assertEqual(assemble("PULL\nPUSH\nSET 6,1\nOUTBIT 6\nINBIT 12\n"
                                  "LDX 0\nDJNZ 15\nSIGNAL\nAWAIT\nCLR_EVENT\nJBIT 15\nRECV\nIN 1"),
                         [0xF000, 0xF100, 0xF261, 0xF360, 0xF40C, 0xF500, 0xF60F,
                          0xF700, 0xF710, 0xF720, 0xF80F, 0xF900, 0x2100])
        for source in ("SET 7,1", "OUTBIT 7", "INBIT 13", "LDX 16", "DJNZ 16", "JBIT -1"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                assemble(source)

    def test_examples_assemble(self):
        for path in (Path(__file__).resolve().parents[1] / "examples/compact").glob("*.pio"):
            with self.subTest(path=path):
                self.assertLessEqual(len(assemble(path.read_text())), 16)

    def test_frames(self):
        self.assertEqual(read_frame(0x12), bytes.fromhex("03 12 00 00"))
        self.assertEqual(write_frame(0x40, 0x1234), bytes.fromhex("02 40 12 34"))
        self.assertEqual(read_value(bytes.fromhex("00 00 50 49")), 0x5049)
        self.assertEqual(program_frames([0xE000]),
                         [bytes.fromhex("02 03 00 00"), bytes.fromhex("02 04 00 03"),
                          bytes.fromhex("02 0a 00 00"), bytes.fromhex("02 40 e0 00")])
        self.assertEqual(program_frames([0] * 16)[-1], bytes.fromhex("02 4f 00 00"))
        for args in ((256, 0), (0, 65536), (-1, 0)):
            with self.assertRaises(ValueError):
                write_frame(*args)
        with self.assertRaises(ValueError):
            read_value(b"\0")
        with self.assertRaises(ValueError):
            program_frames([0] * 17)


if __name__ == "__main__":
    unittest.main()
