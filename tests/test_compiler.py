"""Run using: python -m unittest discover -s tests -v"""
import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from g1m_compiler import (
    CompileError, compile_source, decompile_g1m, inspect_g1m, make_g1m,
    tokenize_line, validate_program_name, main
)


class CompilerTests(unittest.TestCase):
    def test_byte_identical_to_known_working_fixture(self):
        source = (ROOT / 'examples/BLOK112.txt').read_text(encoding='utf-8')
        expected = (ROOT / 'fixtures/BLOK112_known_working.g1m').read_bytes()
        self.assertEqual(make_g1m(source, 'BLOK112'), expected)
        self.assertEqual(len(expected), 1128)

    def test_file_round_trip_metadata(self):
        raw = make_g1m('ClrText\nLocate 1,1,"HI"\nStop\n', 'HELLO')
        data = inspect_g1m(raw)
        self.assertEqual(data['nama_program'], 'HELLO')
        self.assertEqual(data['ukuran_berkas'], len(raw))
        self.assertEqual(data['jumlah_program'], 1)

    def test_unicode_and_ascii_operators(self):
        self.assertEqual(tokenize_line('X→A'), b'X\x0eA')
        self.assertEqual(tokenize_line('X->A'), b'X\x0eA')
        self.assertEqual(tokenize_line('If X>=1'), b'\xf7\x00X\x121')
        self.assertEqual(tokenize_line('If X≤1'), b'\xf7\x00X\x101')
        self.assertEqual(tokenize_line('If X≠1'), b'\xf7\x00X\x111')
        self.assertEqual(tokenize_line('"HELLO"◢'), b'"HELLO"\x0c')
        self.assertEqual(tokenize_line('A*2/B^3'), b'A\xa92\xb9B\xa83')

    def test_comments_ignored_outside_quotes(self):
        self.assertEqual(tokenize_line('Locate 1,1,"A # B" # comment'),
                         b'\xf7\x101,1,"A # B"')
        self.assertEqual(tokenize_line('A+1→A // comment'), b'A\x891\x0eA')
        self.assertEqual(compile_source('  # comment\nA+1→A\n\n'), b'A\x891\x0eA')

    def test_unknown_function_rejected(self):
        with self.assertRaisesRegex(CompileError, 'Print'):
            tokenize_line('Print 23')
        with self.assertRaisesRegex(CompileError, 'sin'):
            tokenize_line('sinh(5)')
        with self.assertRaisesRegex(CompileError, 'belum didukung'):
            tokenize_line('A & B')

    def test_unterminated_string_rejected(self):
        with self.assertRaisesRegex(CompileError, 'penutup'):
            tokenize_line('"oops')

    def test_invalid_name_rejected(self):
        for name in ['VERY_LONG_NAME', '123', 'A B', 'OK!']:
            with self.subTest(name=name):
                with self.assertRaises(CompileError):
                    validate_program_name(name)
        self.assertEqual(validate_program_name('hello'), 'HELLO')

    def test_length_integrity(self):
        raw = bytearray(make_g1m('Stop', 'TEST'))
        raw[-1] ^= 0x01
        with self.assertRaises(CompileError):
            inspect_g1m(bytes(raw))
        raw = bytearray(make_g1m('Stop', 'TEST'))
        raw[19] ^= 0x01
        with self.assertRaises(CompileError):
            inspect_g1m(bytes(raw))

    def test_cli_build_and_inspect(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            src = folder / 'mycasio.txt'
            dest = folder / 'result.g1m'
            src.write_text('ClrText\n"HI"◢\nStop\n', encoding='utf-8')
            self.assertEqual(main(['build', str(src), '-n', 'HI123', '-o', str(dest)]), 0)
            self.assertTrue(dest.exists())
            self.assertEqual(main(['inspect', str(dest)]), 0)

    def test_standalone_example_hello(self):
        source = (ROOT / 'examples/HELLO.txt').read_text(encoding='utf-8')
        self.assertEqual(inspect_g1m(make_g1m(source, 'HELLO'))['nama_program'], 'HELLO')

    def test_decompile_fixture_round_trip(self):
        fixture_bytes = (ROOT / 'fixtures/BLOK112_known_working.g1m').read_bytes()
        name, source = decompile_g1m(fixture_bytes)
        self.assertEqual(name, 'BLOK112')
        # Recompiling decompiled source must produce the exact binary fixture
        recompiled = make_g1m(source, name)
        self.assertEqual(recompiled, fixture_bytes)

    def test_cli_decompile(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            fixture_bytes = (ROOT / 'fixtures/BLOK112_known_working.g1m').read_bytes()
            g1m_file = folder / 'TESTPROG.g1m'
            g1m_file.write_bytes(fixture_bytes)
            txt_file = folder / 'output.txt'
            self.assertEqual(main(['decompile', str(g1m_file), '-o', str(txt_file)]), 0)
            self.assertTrue(txt_file.exists())
            self.assertIn('ClrText', txt_file.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
