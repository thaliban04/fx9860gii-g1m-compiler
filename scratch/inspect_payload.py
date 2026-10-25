import sys
sys.path.insert(0, ".")
import g1a_builder

payload = g1a_builder.build_native_gui_payload()
print(f"Total payload size: {len(payload)} bytes")
print("Hex dump of payload (first 128 bytes):")
for i in range(0, min(len(payload), 128), 16):
    chunk = payload[i:i+16]
    hex_str = " ".join(f"{b:02x}" for b in chunk)
    ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
    print(f"{i:04x}: {hex_str:<48} |{ascii_str}|")
