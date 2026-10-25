def encode_bsr(from_pc, to_target):
    # PC in SuperH is from_pc + 4
    diff = to_target - (from_pc + 4)
    disp = diff // 2
    if not (-2048 <= disp <= 2047):
        raise ValueError(f"BSR out of range: {disp}")
    opcode = 0xB000 | (disp & 0x0FFF)
    return opcode

# Test
print(f"BSR from 0 to 4: 0x{encode_bsr(0, 4):04X}")
print(f"BSR from 0 to 16: 0x{encode_bsr(0, 16):04X}")
