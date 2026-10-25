import struct

def assemble_gui_payload():
    # We will build the payload with precise byte offsets
    # Layout:
    # 0x00: Main code
    #   sts.l pr, @-r15        (4F 22)
    #   mov.l r14, @-r15       (2F E6)
    #
    #   bsr   stub_allclr      (Bxxx)
    #   nop                    (00 09)
    #
    #   bsr   stub_putdisp     (Bxxx)
    #   nop                    (00 09)
    #
    #   add   #-4, r15         (7F FC)   ; int key on stack
    #   mov   r15, r4          (64 F3)   ; r4 = &key
    #   bsr   stub_getkey      (Bxxx)
    #   nop                    (00 09)
    #   add   #4, r15          (7F 04)
    #
    #   mov   #1, r0           (E0 01)   ; normal return
    #   mov.l @r15+, r14       (6E F6)
    #   lds.l @r15+, pr        (4F 26)
    #   rts                    (00 0B)
    #   nop                    (00 09)
    
    code = bytearray()
    
    # 0x00:
    code.extend(b"\x4f\x22") # 0x00: sts.l pr, @-r15
    code.extend(b"\x2f\xe6") # 0x02: mov.l r14, @-r15
    
    # Calls will be patched:
    pos_call_allclr = len(code)
    code.extend(b"\x00\x00") # 0x04: bsr stub_allclr
    code.extend(b"\x00\x09") # 0x06: nop
    
    pos_call_putdisp = len(code)
    code.extend(b"\x00\x00") # 0x08: bsr stub_putdisp
    code.extend(b"\x00\x09") # 0x0A: nop
    
    code.extend(b"\x7f\xfc") # 0x0C: add #-4, r15
    code.extend(b"\x64\xf3") # 0x0E: mov r15, r4
    
    pos_call_getkey = len(code)
    code.extend(b"\x00\x00") # 0x10: bsr stub_getkey
    code.extend(b"\x00\x09") # 0x12: nop
    
    code.extend(b"\x7f\x04") # 0x14: add #4, r15
    code.extend(b"\xe0\x01") # 0x16: mov #1, r0
    code.extend(b"\x6e\xf6") # 0x18: mov.l @r15+, r14
    code.extend(b"\x4f\x26") # 0x1A: lds.l @r15+, pr
    code.extend(b"\x00\x0b") # 0x1C: rts
    code.extend(b"\x00\x09") # 0x1E: nop
    
    # Align to 4 bytes for stubs:
    while len(code) % 4 != 0:
        code.extend(b"\x00")
        
    def add_stub(syscall_id):
        target_pos = len(code)
        # Each stub is exactly 16 bytes:
        # D201: mov.l @(4, PC), r2 -> loads target_pos + 8
        # D002: mov.l @(8, PC), r0 -> loads target_pos + 12
        # 422B: jmp @r2
        # 0009: nop
        # 80010070
        # syscall_id
        stub = struct.pack(">IIII", 0xD201D002, 0x422B0009, 0x80010070, syscall_id)
        code.extend(stub)
        return target_pos

    target_allclr = add_stub(0x0272)
    target_putdisp = add_stub(0x025F)
    target_getkey = add_stub(0x090F)
    
    def patch_bsr(call_pos, target_pos):
        diff = target_pos - (call_pos + 4)
        disp = diff // 2
        opcode = 0xB000 | (disp & 0x0FFF)
        struct.pack_into(">H", code, call_pos, opcode)

    patch_bsr(pos_call_allclr, target_allclr)
    patch_bsr(pos_call_putdisp, target_putdisp)
    patch_bsr(pos_call_getkey, target_getkey)
    
    return bytes(code), target_allclr, target_putdisp, target_getkey

payload, t1, t2, t3 = assemble_gui_payload()
print(f"Payload assembled cleanly: {len(payload)} bytes")
print(f"Stubs at: allclr={t1:02X}, putdisp={t2:02X}, getkey={t3:02X}")
for i in range(0, len(payload), 16):
    chunk = payload[i:i+16]
    hex_str = " ".join(f"{b:02x}" for b in chunk)
    print(f"{i:04x}: {hex_str}")
