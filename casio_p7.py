"""Casio fx-9860G Protocol 7.00 Implementation.

Reverse-engineered from CASIO FA-124 (CasComn.dll / EnumDev.dll) and Cahute specifications.
Implements the exact packet framing, 0x5C escape padding, two's-complement checksum,
and Command 25 (Transfer file - main memory) flow.
"""
from __future__ import annotations
import struct

TYPE_CMD = 0x01
TYPE_DATA = 0x02
TYPE_CONN = 0x05
TYPE_ACK = 0x06
TYPE_NAK = 0x15
TYPE_TERM = 0x0B

def escape_5c(data: bytes) -> bytes:
    """Encode bytes using Casio Protocol 7.00 0x5C padding.
    
    Bytes < 0x20 are escaped as '\\' (0x5C) followed by (byte + 0x20).
    Byte 0x5C ('\\') is escaped as '\\\\' (0x5C, 0x5C).
    Other bytes are kept as-is.
    """
    out = bytearray()
    for b in data:
        if b < 0x20:
            out.append(0x5C)
            out.append(b + 0x20)
        elif b == 0x5C:
            out.append(0x5C)
            out.append(0x5C)
        else:
            out.append(b)
    return bytes(out)

def unescape_5c(escaped: bytes) -> bytes:
    """Decode Casio Protocol 7.00 0x5C padded bytes."""
    out = bytearray()
    i = 0
    length = len(escaped)
    while i < length:
        b = escaped[i]
        if b == 0x5C:
            i += 1
            if i >= length:
                break
            nxt = escaped[i]
            if nxt == 0x5C:
                out.append(0x5C)
            else:
                out.append(nxt - 0x20)
        else:
            out.append(b)
        i += 1
    return bytes(out)

def compute_checksum(data_for_sum: bytes) -> int:
    """Compute 2's complement checksum (sum bytes, bitwise not + 1)."""
    s = sum(data_for_sum) & 0xFF
    return ((~s + 1) & 0xFF)

def make_packet(pkt_type: int, subtype_str: str, payload: bytes | None = None) -> bytes:
    """Construct a full Protocol 7.00 packet.
    
    Format:
    [Type (1 byte)]
    [Subtype (2 bytes ASCII-HEX)]
    [Extended Flag (1 byte ASCII '0' or '1')]
    If Extended:
      [Data Size (4 bytes ASCII-HEX length of escaped payload)]
      [Escaped Payload (variable)]
    [Checksum (2 bytes ASCII-HEX of ST..Payload)]
    """
    st_bytes = subtype_str.upper().encode('ascii')
    is_extended = payload is not None and len(payload) > 0
    ex_byte = b'1' if is_extended else b'0'

    header = bytearray([pkt_type]) + st_bytes + ex_byte
    bytes_for_cs = bytearray(st_bytes + ex_byte)

    if is_extended:
        escaped_payload = escape_5c(payload)
        ds_bytes = f"{len(escaped_payload):04X}".encode('ascii')
        header += ds_bytes + escaped_payload
        bytes_for_cs += ds_bytes + escaped_payload

    cs = compute_checksum(bytes_for_cs)
    cs_bytes = f"{cs:02X}".encode('ascii')
    return bytes(header + cs_bytes)

def parse_packet(raw: bytes) -> dict:
    """Parse a received Protocol 7.00 packet."""
    if len(raw) < 6:
        raise ValueError("Packet too short")
    pkt_type = raw[0]
    st = raw[1:3].decode('ascii', errors='ignore')
    ex = chr(raw[3])
    
    payload = b''
    if ex == '1':
        ds = int(raw[4:8].decode('ascii', errors='ignore'), 16)
        escaped_payload = raw[8:8+ds]
        payload = unescape_5c(escaped_payload)
        cs_expected = raw[8+ds:10+ds].decode('ascii', errors='ignore')
        bytes_for_cs = raw[1:8+ds]
    else:
        cs_expected = raw[4:6].decode('ascii', errors='ignore')
        bytes_for_cs = raw[1:4]

    calc_cs = f"{compute_checksum(bytes_for_cs):02X}"
    return {
        "type": pkt_type,
        "subtype": st,
        "extended": ex == '1',
        "payload": payload,
        "checksum_ok": calc_cs.upper() == cs_expected.upper()
    }

def make_connection_packet() -> bytes:
    """Packet 0x05 connection handshake: [0x05, '0', '0', '0', CS]."""
    return make_packet(TYPE_CONN, "00", None)

def make_ack_packet(subtype_str: str = "00") -> bytes:
    """Packet 0x06 ACK packet."""
    return make_packet(TYPE_ACK, subtype_str, None)

def make_command_25(prog_name: str, program_body: bytes) -> bytes:
    """Construct Command 25 (Transfer file - main memory) initialization packet.
    
    Payload arguments layout (Casio Protocol 7.00):
    OW (2 bytes ASCII) = '02' (force overwrite)
    DT (2 bytes ASCII) = '01' (Data type 01 = PROGRAM)
    FS (8 bytes ASCII hex) = size of program body
    SD1..SD6 (12 bytes) = lengths of D1..D6 in 2-char hex
    D1 = directory ('system' for Main Memory programs)
    D2 = file name (prog_name, up to 8 chars)
    """
    ow = b"02"
    dt = b"01"
    fs = f"{len(program_body):08X}".encode('ascii')

    d1 = b"system"
    d2 = prog_name.upper().encode('ascii')
    d3 = b""
    d4 = b""
    d5 = b""
    d6 = b""

    args = [d1, d2, d3, d4, d5, d6]
    sd_header = bytearray()
    for arg in args:
        sd_header += f"{len(arg):02X}".encode('ascii')

    payload = ow + dt + fs + bytes(sd_header) + b"".join(args)
    return make_packet(TYPE_CMD, "25", payload)

def make_data_chunks(payload_bytes: bytes, chunk_size: int = 256) -> list[bytes]:
    """Split program payload into Protocol 7.00 Data packets (Type 0x02, Subtype '25').
    
    Data packet layout:
    TN (4 bytes ASCII-HEX) = Total packet count (0001..FFFF)
    CN (4 bytes ASCII-HEX) = Current packet number (0001..FFFF, 1-indexed)
    DD (0..256 bytes) = Raw data payload slice
    """
    num_chunks = (len(payload_bytes) + chunk_size - 1) // chunk_size or 1
    tn_bytes = f"{num_chunks:04X}".encode('ascii')
    packets = []
    for i in range(num_chunks):
        cn_bytes = f"{i + 1:04X}".encode('ascii')
        chunk = payload_bytes[i * chunk_size : (i + 1) * chunk_size]
        d = tn_bytes + cn_bytes + chunk
        pkt = make_packet(TYPE_DATA, "25", d)
        packets.append(pkt)
    return packets

