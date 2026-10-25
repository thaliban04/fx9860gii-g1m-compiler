import struct

def create_sample_icon():
    # 30 wide x 17 high = 4 bytes per row * 17 rows = 68 bytes
    icon = bytearray(68)
    for y in range(17):
        for x in range(30):
            # Draw a border and a calculator symbol 'C'
            is_black = False
            if y == 0 or y == 16 or x == 0 or x == 29:
                is_black = True
            elif 4 <= y <= 12 and (x == 8 or ((y == 4 or y == 12) and 8 <= x <= 18)):
                is_black = True
            elif 7 <= y <= 9 and 14 <= x <= 22:
                is_black = True
            
            if is_black:
                byte_idx = y * 4 + (x // 8)
                bit_idx = 7 - (x % 8)
                icon[byte_idx] |= (1 << bit_idx)
    return bytes(icon)

icon = create_sample_icon()
print(f"Icon length: {len(icon)} bytes (expected 68)")
print("Icon hex preview:")
for y in range(17):
    row_bytes = icon[y*4:(y+1)*4]
    bits = "".join(f"{b:08b}" for b in row_bytes)[:30]
    art = bits.replace("0", " ").replace("1", "#")
    print(f"{y:02d}: |{art}| {row_bytes.hex()}")
