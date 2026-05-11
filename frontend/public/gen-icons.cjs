const fs = require('fs');
const zlib = require('zlib');

function crc32(buf) {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++)
      c = (c & 1) ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c;
  }
  let crc = 0xFFFFFFFF;
  for (let i = 0; i < buf.length; i++)
    crc = (crc >>> 8) ^ table[(crc ^ buf[i]) & 0xFF];
  return (crc ^ 0xFFFFFFFF) >>> 0;
}

function writePNG(size, filename) {
  const channels = 4;
  const pixels = new Uint8Array(size * size * channels);

  const cx = size / 2, cy = size / 2;
  const outerR = size * 0.48;
  const innerR = size * 0.38;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const idx = (y * size + x) * channels;
      const dx = x - cx, dy = y - cy;
      const dist = Math.sqrt(dx*dx + dy*dy);

      if (dist <= outerR) {
        if (dist <= innerR) {
          // Dark navy background
          pixels[idx]=6; pixels[idx+1]=13;
          pixels[idx+2]=26; pixels[idx+3]=255;
        } else {
          // Green ring
          pixels[idx]=34; pixels[idx+1]=197;
          pixels[idx+2]=94; pixels[idx+3]=255;
        }
      } else {
        // Transparent outside
        pixels[idx]=6; pixels[idx+1]=13;
        pixels[idx+2]=26; pixels[idx+3]=255;
      }
    }
  }

  // Build PNG
  const chunks = [];

  // IHDR
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8]=8; ihdr[9]=2; // 8-bit RGB...
  // use RGBA: ihdr[9]=6
  ihdr[9]=6;

  function chunk(type, data) {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length);
    const typeB = Buffer.from(type);
    const crcVal = Buffer.alloc(4);
    crcVal.writeUInt32BE(
      crc32(Buffer.concat([typeB, data]))
    );
    return Buffer.concat([len, typeB, data, crcVal]);
  }

  // Build raw image data with filter bytes
  const raw = Buffer.alloc(size * (1 + size * 4));
  for (let y = 0; y < size; y++) {
    raw[y * (1 + size * 4)] = 0; // filter type None
    for (let x = 0; x < size; x++) {
      const src = (y * size + x) * 4;
      const dst = y * (1 + size * 4) + 1 + x * 4;
      raw[dst] = pixels[src];
      raw[dst+1] = pixels[src+1];
      raw[dst+2] = pixels[src+2];
      raw[dst+3] = pixels[src+3];
    }
  }

  const compressed = zlib.deflateSync(raw);

  const sig = Buffer.from([137,80,78,71,13,10,26,10]);
  const ihdrChunk = chunk('IHDR', ihdr);
  const idatChunk = chunk('IDAT', compressed);
  const iendChunk = chunk('IEND', Buffer.alloc(0));

  fs.writeFileSync(
    filename,
    Buffer.concat([sig, ihdrChunk, idatChunk, iendChunk])
  );
  console.log(`Created ${filename}`);
}

writePNG(192, 'icon-192.png');
writePNG(512, 'icon-512.png');
