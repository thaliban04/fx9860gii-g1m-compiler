#!/usr/bin/env python3
"""Small, dependency-free text-to-G1M compiler for fx-9860GII CASIO BASIC.

Only documented / fixture-verified tokens are accepted. This is intentionally
NOT a compiler for Python, C, or the entire CASIO BASIC dialect.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import struct
import sys

# A single PROGRAM object inside a G1M memory archive. The 0x31 identifier,
# zero bytes at encoded header offsets 0x15..0x1D, and 10-byte program prefix
# deliberately match the real BLOK112.g1m accepted by the user's calculator.
# G1M headers are stored inverted (xor 0xff). The file length is total bytes.
FILE_TYPE_PLAIN = b"USBPower\x31\x00\x10\x00\x10\x00"  # 14 bytes
PROGRAM_PREFIX = b"\x00" * 10
PROGRAM_TRAILER = b"\xf7\x4d\x00"

# Verified by comparing the provided CASIO BASIC source against the working
# .g1m fixture. This dictionary can be extended after confirming codes.
KEYWORDS = {
    "ClrText": b"\xf7\x18",
    "Locate": b"\xf7\x10",
    "IfEnd": b"\xf7\x03",
    "If": b"\xf7\x00",
    "Then": b"\xf7\x01",
    "Goto": b"\xec",
    "Lbl": b"\xe2",
    "For": b"\xf7\x04",
    "To": b"\xf7\x05",
    "Next": b"\xf7\x07",
    "Stop": b"\xf7\x0e",
    "Int": b"\xa6",
    # Operator tokens seen in the working program.
}

# Math extensions documented in fx-9860G programming token references.
# Only foundational arithmetic is required to reproduce the verified example.
SINGLE_CHAR_TOKENS = {
    "→": b"\x0e",
    "◢": b"\x0c",
    "≤": b"\x10",
    "≠": b"\x11",
    "≥": b"\x12",
    "+": b"\x89",
    "-": b"\x99",
    "−": b"\x99",
    "*": b"\xa9",
    "×": b"\xa9",
    "/": b"\xb9",
    "÷": b"\xb9",
    "^": b"\xa8",
}
MULTI_CHAR_TOKENS = {
    "->": b"\x0e",
    "<=": b"\x10",
    "!=": b"\x11",
    "<>": b"\x11",
    ">=": b"\x12",
    "==": b"=",
}
# Only the listed punctuation has been verified for code expressions.
ASCII_EXPRESSION = set('0123456789.,()=<>?')


class CompileError(ValueError):
    """Invalid source with location information."""


def _remove_comment(line: str) -> str:
    """Ignore # / // comments outside strings, preserving quoted text."""
    quoted = False
    pos = 0
    while pos < len(line):
        if line[pos] == '"':
            quoted = not quoted
        if not quoted and (line[pos] == '#' or line[pos:pos+2] == '//'):
            return line[:pos]
        pos += 1
    return line


def tokenize_line(line: str, line_number: int = 1) -> bytes:
    line = _remove_comment(line)
    result = bytearray()
    cursor = 0
    quoted = False
    while cursor < len(line):
        ch = line[cursor]
        if ch == '"':
            result.append(ord('"'))
            quoted = not quoted
            cursor += 1
            continue
        if quoted:
            code = ord(ch)
            if not 32 <= code <= 126:
                raise CompileError(
                    f"Baris {line_number}, kolom {cursor + 1}: string hanya ASCII "
                    "32..126. Gunakan teks tanpa aksen / emoji."
                )
            result.append(code)
            cursor += 1
            continue
        if ch.isspace():
            cursor += 1
            continue

        matched = False
        for token, encoded in MULTI_CHAR_TOKENS.items():
            if line.startswith(token, cursor):
                result.extend(encoded)
                cursor += len(token)
                matched = True
                break
        if matched:
            continue

        if ch.isalpha() and ch.isascii():
            word_end = cursor + 1
            while word_end < len(line) and line[word_end].isascii() and line[word_end].isalpha():
                word_end += 1
            word = line[cursor:word_end]
            keyword = next((k for k in KEYWORDS if k.lower() == word.lower()), None)
            if keyword is not None:
                result.extend(KEYWORDS[keyword])
            elif len(word) == 1:
                result.extend(word.upper().encode('ascii'))
            else:
                raise CompileError(
                    f"Baris {line_number}, kolom {cursor + 1}: kata '{word}' "
                    "belum didukung. Pakai perintah Casio BASIC atau tambahkan token baru."
                )
            cursor = word_end
            continue

        if ch in SINGLE_CHAR_TOKENS:
            result.extend(SINGLE_CHAR_TOKENS[ch])
        elif ch in ASCII_EXPRESSION:
            result.append(ord(ch))
        else:
            raise CompileError(
                f"Baris {line_number}, kolom {cursor + 1}: simbol {ch!r} belum didukung."
            )
        cursor += 1
    if quoted:
        raise CompileError(f'Baris {line_number}: tanda petik penutup tidak ditemukan.')
    return bytes(result)


def compile_source(source: str) -> bytes:
    lines = []
    for line_number, raw_line in enumerate(source.splitlines(), start=1):
        encoded = tokenize_line(raw_line, line_number)
        if encoded:
            lines.append(encoded)
    if not lines:
        raise CompileError('File sumber kosong atau hanya berisi komentar.')
    return b'\x0d'.join(lines)


def _nulpadded(name: str, length: int) -> bytes:
    return name.encode('ascii') + b'\x00' * (length - len(name))


def validate_program_name(name: str) -> str:
    name = name.upper()
    if not re.fullmatch(r'[A-Z][A-Z0-9]{0,7}', name):
        raise CompileError('Nama program harus 1-8 karakter A-Z/0-9 dan dimulai huruf.')
    return name


def make_g1m(source: str, name: str) -> bytes:
    name = validate_program_name(name)
    code = compile_source(source)
    contents = bytearray(PROGRAM_PREFIX + code + PROGRAM_TRAILER)
    # Do not pad. The working fixture stores exact program bytes and trailer.
    group = _nulpadded('PROGRAM', 16) + struct.pack('>I', 1)
    item = _nulpadded('system', 8) + _nulpadded(name, 8)
    item += b'\x01' + struct.pack('>I', len(contents)) + b'\x00' * 3
    total_length = 32 + len(group) + len(item) + len(contents)
    if total_length >= 2**32:
        raise CompileError('Berkas melebihi batas maksimum format.')

    header = bytearray(32)
    header[:14] = bytes(b ^ 0xff for b in FILE_TYPE_PLAIN)
    header[14] = ((total_length + 0x41) & 0xff) ^ 0xff
    header[15] = 0xfe
    header[16:20] = bytes(b ^ 0xff for b in struct.pack('>I', total_length))
    header[20] = ((total_length + 0xB8) & 0xff) ^ 0xff
    # Keep the exact successful G1M variant, including encoded reserved fields.
    header[21:30] = b'\x00' * 9
    header[30:32] = bytes(b ^ 0xff for b in struct.pack('>H', 1))
    return bytes(header) + group + item + contents


def inspect_g1m(raw: bytes) -> dict:
    """Validate the exact one-program format emitted by this compiler."""
    if len(raw) < 88:
        raise CompileError('Berkas terlalu kecil untuk sebuah program G1M.')
    head = bytes(b ^ 0xff for b in raw[:32])
    if head[:14] != FILE_TYPE_PLAIN:
        raise CompileError('Header G1M tidak sesuai dengan format yang didukung.')
    file_length = struct.unpack('>I', head[16:20])[0]
    if file_length != len(raw):
        raise CompileError(f'Ukuran header {file_length} tidak sama dengan ukuran asli {len(raw)}.')
    if head[14] != (len(raw) + 0x41) & 0xff or head[20] != (len(raw) + 0xB8) & 0xff:
        raise CompileError('Byte validasi panjang berkas tidak sesuai.')
    count = struct.unpack('>H', head[30:32])[0]
    if count != 1 or raw[32:48].rstrip(b'\x00') != b'PROGRAM':
        raise CompileError('Format arsip ini bukan satu item PROGRAM.')
    if struct.unpack('>I', raw[48:52])[0] != 1:
        raise CompileError('Jumlah item grup tidak tepat.')
    if raw[52:60].rstrip(b'\x00') != b'system':
        raise CompileError('Nama direktori file tidak cocok.')
    name = raw[60:68].rstrip(b'\x00').decode('ascii')
    if raw[68] != 1:
        raise CompileError('Item bukan program biasa.')
    code_length = struct.unpack('>I', raw[69:73])[0]
    if code_length != len(raw) - 76:
        raise CompileError('Ukuran konten program tidak cocok.')
    if not raw[76:86] == PROGRAM_PREFIX:
        raise CompileError('Preambule konten tidak sesuai.')
    if PROGRAM_TRAILER not in raw[-6:]:
        # Some standard exports terminate differently. This inspector is scoped
        # to the self-produced variant, not every G1M found in the wild.
        raise CompileError('Penanda akhir program tidak dikenali.')
    return {'nama_program': name, 'ukuran_berkas': len(raw),
            'ukuran_data_program': code_length, 'jumlah_program': count}


REVERSE_MULTI_BYTE = {
    b"\xf7\x18": "ClrText",
    b"\xf7\x10": "Locate ",
    b"\xf7\x00": "If ",
    b"\xf7\x01": "Then",
    b"\xf7\x03": "IfEnd",
    b"\xf7\x04": "For ",
    b"\xf7\x05": " To ",
    b"\xf7\x07": "Next",
    b"\xf7\x0e": "Stop",
    b"\xf7\x02": "Else",
    b"\xf7\x08": "While ",
    b"\xf7\x09": "WhileEnd",
    b"\xf7\x0a": "Do",
    b"\xf7\x0b": "LpWhile ",
}

REVERSE_SINGLE_BYTE = {
    0xec: "Goto ",
    0xe2: "Lbl ",
    0xa6: "Int",
    0x0e: "→",
    0x0c: "◢",
    0x10: "≤",
    0x11: "≠",
    0x12: "≥",
    0x89: "+",
    0x99: "-",
    0xa9: "*",
    0xb9: "/",
    0xa8: "^",
}


def decompile_line(raw: bytes) -> str:
    """Konversi satu baris token byte kalkulator menjadi teks Casio BASIC."""
    res = []
    i = 0
    in_quotes = False
    while i < len(raw):
        b = raw[i]
        if b == ord('"'):
            in_quotes = not in_quotes
            res.append('"')
            i += 1
            continue

        if in_quotes:
            res.append(chr(b))
            i += 1
            continue

        # Periksa token 2 byte
        if i + 1 < len(raw):
            pair = bytes(raw[i:i+2])
            if pair in REVERSE_MULTI_BYTE:
                res.append(REVERSE_MULTI_BYTE[pair])
                i += 2
                continue

        # Periksa token 1 byte
        if b in REVERSE_SINGLE_BYTE:
            res.append(REVERSE_SINGLE_BYTE[b])
            i += 1
            continue

        # Karakter ASCII biasa
        if 32 <= b <= 126:
            res.append(chr(b))
        else:
            res.append(f"\\x{b:02x}")
        i += 1

    return "".join(res)


def decompile_g1m(raw: bytes) -> tuple[str, str]:
    """Ekstrak nama program dan teks sumber Casio BASIC dari berkas biner G1M."""
    if len(raw) < 88:
        raise CompileError('Berkas terlalu kecil untuk format G1M.')

    head = bytes(b ^ 0xff for b in raw[:32])
    if head[:14] != FILE_TYPE_PLAIN:
        raise CompileError('Header G1M tidak sesuai dengan format yang didukung.')

    name = raw[60:68].rstrip(b'\x00').decode('ascii', errors='replace')
    code_length = struct.unpack('>I', raw[69:73])[0]

    if len(raw) < 76 + code_length:
        raise CompileError('Ukuran data program di header melebihi panjang berkas.')

    contents = raw[76:76+code_length]
    if len(contents) < 13:
        raise CompileError('Data konten program G1M terlalu pendek.')

    # Hapus 10-byte prefix dan trailer akhir
    code_bytes = contents[10:]
    if code_bytes.endswith(PROGRAM_TRAILER):
        code_bytes = code_bytes[:-len(PROGRAM_TRAILER)]
    elif code_bytes.endswith(b"\x00"):
        code_bytes = code_bytes.rstrip(b"\x00")

    lines = code_bytes.split(b"\x0d")
    decompiled_lines = [decompile_line(l) for l in lines]
    return name, "\n".join(decompiled_lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description='Compiler & Decompiler CASIO BASIC (.txt <-> .g1m) fx-9860GII.'
    )
    sub = parser.add_subparsers(dest='command')
    build = sub.add_parser('build', help='Kompilasi sumber .txt menjadi .g1m')
    build.add_argument('source', type=Path, help='File CASIO BASIC UTF-8')
    build.add_argument('-n', '--name', help='Nama program di kalkulator, maksimal 8 karakter')
    build.add_argument('-o', '--output', type=Path, help='Jalur keluaran .g1m')

    decompile = sub.add_parser('decompile', help='Dekomplikasi berkas .g1m kembali menjadi .txt')
    decompile.add_argument('file', type=Path, help='Berkas .g1m yang akan diekstrak')
    decompile.add_argument('-o', '--output', type=Path, help='Jalur keluaran berkas .txt (opsional)')

    check = sub.add_parser('inspect', help='Periksa struktur berkas G1M buatan compiler ini')
    check.add_argument('file', type=Path)
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        if args.command == 'inspect':
            meta = inspect_g1m(args.file.read_bytes())
            for key, value in meta.items():
                print(f'{key}: {value}')
            print('Struktur: OK')
            return 0
        if args.command == 'decompile':
            raw = args.file.read_bytes()
            name, source = decompile_g1m(raw)
            out = args.output or args.file.with_name(name + '.txt')
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(source, encoding='utf-8')
            print(f'Berhasil didekompilasi: {out} (Nama program: {name}, {len(source.splitlines())} baris)')
            return 0

        name = validate_program_name(args.name or args.source.stem)
        out = args.output or args.source.with_name(name + '.g1m')
        raw = make_g1m(args.source.read_text(encoding='utf-8-sig'), name)
        # Self-check before writing.
        inspect_g1m(raw)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
        print(f'Berhasil: {out} ({len(raw)} byte, nama program: {name})')
        return 0
    except (OSError, UnicodeError, CompileError) as exc:
        print(f'GAGAL: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

