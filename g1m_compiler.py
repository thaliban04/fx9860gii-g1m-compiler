#!/usr/bin/env python3
"""Small, dependency-free text-to-G1M compiler for fx-9860GII CASIO BASIC.

Only documented / fixture-verified tokens are accepted.

Changelog:
  v2.0 - Dynamic header/checksum (fix Application Error di FA-124),
          token titik dua '':'' sebagai statement separator (0x3A),
          block-balance linter (If/Then/IfEnd, For/Next, While/WhileEnd, Do/LpWhile),
          validasi Goto/Lbl, normalisasi spasi fungsi, alias simbol khusus.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import struct
import sys

FILE_TYPE_PLAIN = b"USBPower\x31\x00\x10\x00\x10\x00"
PROGRAM_PREFIX = b"\x00" * 10
PROGRAM_TRAILER = b"\xf7\x4d\x00"

KEYWORDS = {
    "ClrText":  b"\xf7\x18",
    "Locate":   b"\xf7\x10",
    "IfEnd":    b"\xf7\x03",
    "If":       b"\xf7\x00",
    "Then":     b"\xf7\x01",
    "Else":     b"\xf7\x02",
    "For":      b"\xf7\x04",
    "To":       b"\xf7\x05",
    "Step":     b"\xf7\x06",
    "Next":     b"\xf7\x07",
    "While":    b"\xf7\x08",
    "WhileEnd": b"\xf7\x09",
    "Do":       b"\xf7\x0a",
    "LpWhile":  b"\xf7\x0b",
    "Goto":     b"\xec",
    "Lbl":      b"\xe2",
    "Stop":     b"\xf7\x0e",
    "Return":   b"\xf7\x0f",
    "Break":    b"\xf7\x0c",
    "Int":      b"\xa6",
    "Disp":     b"\x0c",
}

SINGLE_CHAR_TOKENS = {
    "\u2192": b"\x0e",
    "\u25e2": b"\x0c",
    "\u2264": b"\x10",
    "\u2260": b"\x11",
    "\u2265": b"\x12",
    "+":      b"\x89",
    "-":      b"\x99",
    "\u2212": b"\x99",
    "*":      b"\xa9",
    "\u00d7": b"\xa9",
    "/":      b"\xb9",
    "\u00f7": b"\xb9",
    "^":      b"\xa8",
}

MULTI_CHAR_TOKENS = {
    "->": b"\x0e",
    "<=": b"\x10",
    "!=": b"\x11",
    "<>": b"\x11",
    ">=": b"\x12",
    "==": b"=",
    "_":  b"\x0c",
}

ASCII_EXPRESSION = set('0123456789.,()=<>?')
GOTO_CHARS = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')

BLOCK_PAIRS = [
    ("If",    "IfEnd",    "Then"),
    ("For",   "Next",     None),
    ("While", "WhileEnd", None),
    ("Do",    "LpWhile",  None),
]
BLOCK_OPENERS = {p[0] for p in BLOCK_PAIRS}
BLOCK_CLOSERS = {p[1] for p in BLOCK_PAIRS}


class CompileError(ValueError):
    """Invalid source with location information."""


def _remove_comment(line: str) -> str:
    quoted = False
    pos = 0
    while pos < len(line):
        if line[pos] == '"':
            quoted = not quoted
        if not quoted and (line[pos] == '#' or line[pos:pos+2] == '//'):
            return line[:pos]
        pos += 1
    return line


def _normalize_function_space(line: str) -> str:
    result = []
    quoted = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            quoted = not quoted
        if not quoted and ch == ' ':
            j = i
            while j < len(line) and line[j] == ' ':
                j += 1
            if j < len(line) and line[j] == '(':
                i = j
                continue
        result.append(ch)
        i += 1
    return ''.join(result)


def tokenize_line(line: str, line_number: int = 1) -> bytes:
    line = _remove_comment(line)
    line = _normalize_function_space(line)
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
                    f"Baris {line_number}, kolom {cursor + 1}: string hanya ASCII 32..126."
                )
            result.append(code)
            cursor += 1
            continue
        if ch.isspace():
            cursor += 1
            continue
        if ch == ':':
            result.append(0x3A)
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
                    f"Baris {line_number}, kolom {cursor + 1}: kata '{word}' belum didukung."
                )
            cursor = word_end
            continue
        if ch in SINGLE_CHAR_TOKENS:
            result.extend(SINGLE_CHAR_TOKENS[ch])
            cursor += 1
            continue
        if ch in ASCII_EXPRESSION:
            result.append(ord(ch))
            cursor += 1
            continue
        raise CompileError(
            f"Baris {line_number}, kolom {cursor + 1}: simbol {ch!r} belum didukung."
        )
    if quoted:
        raise CompileError(f'Baris {line_number}: tanda petik penutup tidak ditemukan.')
    return bytes(result)


def _first_keyword(text: str) -> str | None:
    text = text.strip()
    for kw in sorted(KEYWORDS.keys(), key=len, reverse=True):
        if text.lower().startswith(kw.lower()):
            rest = text[len(kw):]
            if not rest or not rest[0].isalpha():
                return kw
    return None


def _statements_in_line(raw_line: str) -> list[str]:
    parts = []
    current = []
    quoted = False
    for ch in raw_line:
        if ch == '"':
            quoted = not quoted
        if not quoted and ch == ':':
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    parts.append(''.join(current).strip())
    return [p for p in parts if p]


def lint_source(source: str) -> list[str]:
    warnings: list[str] = []
    block_stack: list[tuple[str, int]] = []
    goto_targets: set[str] = set()
    lbl_targets: set[str] = set()
    for lineno, raw in enumerate(source.splitlines(), start=1):
        clean = _remove_comment(raw).strip()
        if not clean:
            continue
        statements = _statements_in_line(clean)
        for stmt in statements:
            kw = _first_keyword(stmt)
            rest = stmt[len(kw):].strip() if kw else stmt.strip()
            if kw in BLOCK_OPENERS:
                block_stack.append((kw, lineno))
            elif kw in BLOCK_CLOSERS:
                expected_opener = next((p[0] for p in BLOCK_PAIRS if p[1] == kw), None)
                if block_stack and block_stack[-1][0] == expected_opener:
                    block_stack.pop()
                else:
                    opener_info = block_stack[-1] if block_stack else None
                    if opener_info:
                        warnings.append(
                            f"Baris {lineno}: '{kw}' tidak cocok - pembuka terakhir "
                            f"adalah '{opener_info[0]}' (baris {opener_info[1]})."
                        )
                    else:
                        warnings.append(f"Baris {lineno}: '{kw}' tanpa pembuka yang sesuai.")
            elif kw == "Goto":
                target = rest.strip()
                if target and target[0].upper() in GOTO_CHARS:
                    goto_targets.add(target[0].upper())
                else:
                    warnings.append(f"Baris {lineno}: target Goto '{target}' tidak valid (harus 0-9 atau A-Z).")
            elif kw == "Lbl":
                target = rest.strip()
                if target and target[0].upper() in GOTO_CHARS:
                    lbl_targets.add(target[0].upper())
                else:
                    warnings.append(f"Baris {lineno}: target Lbl '{target}' tidak valid (harus 0-9 atau A-Z).")
    for opener, lineno in block_stack:
        closer = next(p[1] for p in BLOCK_PAIRS if p[0] == opener)
        warnings.append(f"Baris {lineno}: blok '{opener}' tidak ditutup dengan '{closer}'.")
    for t in sorted(goto_targets - lbl_targets):
        warnings.append(f"Peringatan: Goto {t} tidak memiliki pasangan Lbl {t}.")
    return warnings


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


def make_g1m(source: str, name: str, *, warn: bool = True) -> bytes:
    """Build a complete .g1m binary with DYNAMIC header & checksum."""
    name = validate_program_name(name)
    if warn:
        for w in lint_source(source):
            print(f"[LINT] {w}", file=sys.stderr)
    code = compile_source(source)
    contents = bytearray(PROGRAM_PREFIX + code + PROGRAM_TRAILER)
    group = _nulpadded('PROGRAM', 16) + struct.pack('>I', 1)
    item = (_nulpadded('system', 8)
            + _nulpadded(name, 8)
            + b'\x01'
            + struct.pack('>I', len(contents))
            + b'\x00' * 3)
    total_length = 32 + len(group) + len(item) + len(contents)
    if total_length >= 2**32:
        raise CompileError('Berkas melebihi batas maksimum format.')
    header = bytearray(32)
    header[:14]   = bytes(b ^ 0xFF for b in FILE_TYPE_PLAIN)
    header[14]    = (~(total_length + 0x41)) & 0xFF
    header[15]    = 0xFE  # constant stored byte (decodes to 0x01 via ^0xFF)
    header[16:20] = bytes(b ^ 0xFF for b in struct.pack('>I', total_length))
    header[20]    = (~(total_length + 0xB8)) & 0xFF
    header[21:30] = b'\x00' * 9
    header[30:32] = bytes(b ^ 0xFF for b in struct.pack('>H', 1))
    return bytes(header) + group + item + contents


def inspect_g1m(raw: bytes) -> dict:
    if len(raw) < 88:
        raise CompileError('Berkas terlalu kecil untuk sebuah program G1M.')
    head = bytes(b ^ 0xFF for b in raw[:32])
    if head[:14] != FILE_TYPE_PLAIN:
        raise CompileError('Header G1M tidak sesuai dengan format yang didukung.')
    file_length = struct.unpack('>I', head[16:20])[0]
    if file_length != len(raw):
        raise CompileError(f'Ukuran header {file_length} != ukuran asli {len(raw)}.')
    if head[14] != (len(raw) + 0x41) & 0xFF or head[20] != (len(raw) + 0xB8) & 0xFF:
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
    if raw[76:86] != PROGRAM_PREFIX:
        raise CompileError('Preambule konten tidak sesuai.')
    if PROGRAM_TRAILER not in raw[-6:]:
        raise CompileError('Penanda akhir program tidak dikenali.')
    return {
        'nama_program':        name,
        'ukuran_berkas':       len(raw),
        'ukuran_data_program': code_length,
        'jumlah_program':      count,
    }


REVERSE_MULTI_BYTE = {
    b"\xf7\x18": "ClrText",
    b"\xf7\x10": "Locate ",
    b"\xf7\x00": "If ",
    b"\xf7\x01": "Then",
    b"\xf7\x02": "Else",
    b"\xf7\x03": "IfEnd",
    b"\xf7\x04": "For ",
    b"\xf7\x05": " To ",
    b"\xf7\x06": " Step ",
    b"\xf7\x07": "Next",
    b"\xf7\x08": "While ",
    b"\xf7\x09": "WhileEnd",
    b"\xf7\x0a": "Do",
    b"\xf7\x0b": "LpWhile ",
    b"\xf7\x0c": "Break",
    b"\xf7\x0e": "Stop",
    b"\xf7\x0f": "Return",
}

REVERSE_SINGLE_BYTE = {
    0xec: "Goto ",
    0xe2: "Lbl ",
    0xa6: "Int",
    0x0e: "\u2192",
    0x0c: "\u25e2",
    0x10: "\u2264",
    0x11: "\u2260",
    0x12: "\u2265",
    0x89: "+",
    0x99: "-",
    0xa9: "*",
    0xb9: "/",
    0xa8: "^",
    0x3A: ":",
}


def decompile_line(raw: bytes) -> str:
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
        if i + 1 < len(raw):
            pair = bytes(raw[i:i+2])
            if pair in REVERSE_MULTI_BYTE:
                res.append(REVERSE_MULTI_BYTE[pair])
                i += 2
                continue
        if b in REVERSE_SINGLE_BYTE:
            res.append(REVERSE_SINGLE_BYTE[b])
            i += 1
            continue
        if 32 <= b <= 126:
            res.append(chr(b))
        else:
            res.append(f"\\x{b:02x}")
        i += 1
    return "".join(res)


def decompile_g1m(raw: bytes) -> tuple[str, str]:
    if len(raw) < 88:
        raise CompileError('Berkas terlalu kecil untuk format G1M.')
    head = bytes(b ^ 0xFF for b in raw[:32])
    if head[:14] != FILE_TYPE_PLAIN:
        raise CompileError('Header G1M tidak sesuai dengan format yang didukung.')
    name = raw[60:68].rstrip(b'\x00').decode('ascii', errors='replace')
    code_length = struct.unpack('>I', raw[69:73])[0]
    if len(raw) < 76 + code_length:
        raise CompileError('Ukuran data program di header melebihi panjang berkas.')
    contents = raw[76:76+code_length]
    if len(contents) < 13:
        raise CompileError('Data konten program G1M terlalu pendek.')
    code_bytes = contents[10:]
    if code_bytes.endswith(PROGRAM_TRAILER):
        code_bytes = code_bytes[:-len(PROGRAM_TRAILER)]
    elif code_bytes.endswith(b"\x00"):
        code_bytes = code_bytes.rstrip(b"\x00")
    lines = code_bytes.split(b"\x0d")
    return name, "\n".join(decompile_line(l) for l in lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description='Compiler & Decompiler CASIO BASIC (.txt <-> .g1m) fx-9860GII v2.0.'
    )
    sub = parser.add_subparsers(dest='command')

    build = sub.add_parser('build', help='Kompilasi sumber .txt menjadi .g1m')
    build.add_argument('source', type=Path)
    build.add_argument('-n', '--name')
    build.add_argument('-o', '--output', type=Path)
    build.add_argument('--no-lint', action='store_true', help='Lewati pengecekan linter')

    lint_cmd = sub.add_parser('lint', help='Periksa sintaks tanpa kompilasi')
    lint_cmd.add_argument('source', type=Path)

    dc = sub.add_parser('decompile', help='Decompile .g1m ke .txt')
    dc.add_argument('file', type=Path)
    dc.add_argument('-o', '--output', type=Path)

    ch = sub.add_parser('inspect', help='Periksa struktur berkas G1M')
    ch.add_argument('file', type=Path)

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
        if args.command == 'lint':
            src = args.source.read_text(encoding='utf-8-sig')
            issues = lint_source(src)
            if issues:
                for w in issues:
                    print(f'[LINT] {w}')
                return 1
            print('Tidak ada masalah sintaks ditemukan.')
            return 0
        name = validate_program_name(args.name or args.source.stem)
        out  = args.output or args.source.with_name(name + '.g1m')
        src  = args.source.read_text(encoding='utf-8-sig')
        raw  = make_g1m(src, name, warn=not getattr(args, 'no_lint', False))
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
