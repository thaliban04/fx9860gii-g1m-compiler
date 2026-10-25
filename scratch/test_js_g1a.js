// Test JS G1A builder
const fs = require('fs');

function makeG1A_JS(internalName, title, version, iconBytes, lines, fkeys) {
  const G1A_FILE_TYPE_PLAIN = [0x55, 0x53, 0x42, 0x50, 0x6f, 0x77, 0x65, 0x72, 0xf3, 0x00, 0x10, 0x00, 0x10, 0x00];
  
  // 1. Native SuperH payload
  const code = [
    0x2f, 0xe6, 0x4f, 0x22, 0x6e, 0xf3,
    0xd2, 0x0a, 0xd0, 0x0b, 0x42, 0x0b, 0x00, 0x09,
    0xd2, 0x07, 0xd0, 0x09, 0x42, 0x0b, 0x00, 0x09,
    0x7f, 0xfc, 0x64, 0xf3, 0xd2, 0x03, 0xd0, 0x06, 0x42, 0x0b, 0x00, 0x09, 0x7f, 0x04,
    0xe0, 0x01, 0x6f, 0xe3, 0x4f, 0x26, 0x6e, 0xf6, 0x00, 0x0b, 0x00, 0x09
  ];
  while (code.length % 4 !== 0) code.push(0);
  
  // Literal pool (0x80010070, 0x0272, 0x025F, 0x090F)
  const pushUint32 = (arr, val) => {
    arr.push((val >>> 24) & 0xff, (val >>> 16) & 0xff, (val >>> 8) & 0xff, val & 0xff);
  };
  pushUint32(code, 0x80010070);
  pushUint32(code, 0x0272);
  pushUint32(code, 0x025F);
  pushUint32(code, 0x090F);

  // Metadata
  const magic = Buffer.from("CASIO_GUI_V1\0", "ascii");
  for (let b of magic) code.push(b);
  const titleBuf = Buffer.from(title.substring(0, 16), "ascii");
  code.push(0, titleBuf.length);
  for (let b of titleBuf) code.push(b);
  code.push(0, lines.length);
  for (let l of lines) {
    const lBuf = Buffer.from(l.substring(0, 24), "ascii");
    code.push(0, lBuf.length);
    for (let b of lBuf) code.push(b);
  }
  while (code.length % 16 !== 0) code.push(0);

  const payload = Buffer.from(code);

  // 2. Add-in Header (480 B)
  const addin = Buffer.alloc(480, 0);
  const nameBuf = Buffer.from(("@" + internalName).substring(0, 8), "ascii");
  nameBuf.copy(addin, 0);

  const verBuf = Buffer.from(version.substring(0, 10), "ascii");
  verBuf.copy(addin, 0x10);

  const now = new Date();
  const dateStr = now.getFullYear() + "." +
    String(now.getMonth() + 1).padStart(2, '0') +
    String(now.getDate()).padStart(2, '0') + "." +
    String(now.getHours()).padStart(2, '0') +
    String(now.getMinutes()).padStart(2, '0');
  Buffer.from(dateStr, "ascii").copy(addin, 0x1C);

  if (iconBytes && iconBytes.length === 68) {
    Buffer.from(iconBytes).copy(addin, 0x2C);
  }

  const titleField = Buffer.from(title.substring(0, 8), "ascii");
  titleField.copy(addin, 0x1B4);

  addin.writeUInt32BE(payload.length, 0x1D0);

  // 3. Container Header (32 B)
  const totalSize = 32 + 480 + payload.length;
  const cont = Buffer.alloc(32, 0);
  for (let i = 0; i < 14; i++) cont[i] = G1A_FILE_TYPE_PLAIN[i];
  cont[0x0E] = (totalSize + 0x41) & 0xFF;
  cont[0x0F] = 0x01;
  cont.writeUInt32BE(totalSize, 0x10);
  cont[0x14] = (totalSize + 0xB8) & 0xFF;

  // Invert container header
  for (let i = 0; i < 32; i++) {
    cont[i] = cont[i] ^ 0xFF;
  }

  return Buffer.concat([cont, addin, payload]);
}

const g1a = makeG1A_JS("TOMLIN", "Tomlin P", "01.00.0000", new Uint8Array(68), ["Hello", "World"], {});
fs.writeFileSync("output/TEST_JS.g1a", g1a);
console.log("TEST_JS.g1a created, size:", g1a.length);
