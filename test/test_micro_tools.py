"""Independent ISA examples; default and ABI-5 encodings must stay untouched."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from pioasm import assemble

class MicroAssemblerTest(unittest.TestCase):
    def test_new_operations_are_explicit_abi6_only(self):
        self.assertEqual(assemble('SETDIR 7,1\nOUTMSB 13\nJIN 0', abi=6),
                         [0x3CF, 0x3ED, 0x3D0])
        for text in ('SETDIR 0,1', 'OUTMSB 0', 'JIN 0'):
            with self.assertRaises(ValueError): assemble(text, abi=5)
        for text in ('SETDIR 8,1', 'SETDIR 0,2', 'OUTMSB 14', 'JIN 16'):
            with self.assertRaises(ValueError): assemble(text, abi=6)

    def test_legacy_source_has_identical_machine_words(self):
        for name in ('uart_tx.pio', 'spi_tx.pio'):
            path = Path(__file__).resolve().parents[1]/'examples/compact'/name
            self.assertEqual(assemble(path.read_text(), abi=5), assemble(path.read_text(), abi=6))
