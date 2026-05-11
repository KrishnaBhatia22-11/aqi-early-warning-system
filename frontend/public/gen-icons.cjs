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
  const outerR  = size * 0.47;  // outer edge of green ring
  const ringW   = size * 0.07;  // ring width
  const innerR  = outerR - ringW;
  const dotR    = size * 0.08;  // center green dot

  // Green ring color
  const G = [34, 197, 94, 255];
  // Dark navy
  const N = [6, 13, 26, 255];
  // Slightly lighter navy for inner area
  const N2 = [10, 20, 40, 255];
  // Transparent
  const T = [0, 0, 0, 0];

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const idx = (y * size + x) * channels;
      const dx = x - cx, dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);

      let col;
      if (dist > outerR) {
        col = T;                    // transparent outside
      } else if (dist > innerR) {
        col = G;                    // green ring
      } else if (dist <= dotR) {
        col = G;                    // green center dot
      } else {
        col = N;                    // dark navy fill
      }

      pixels[idx]   = col[0];
      pixels[idx+1] = col[1];
      pixels[idx+2] = col[2];
      pixels[idx+3] = col[3];
    }
  }

  function chunk(type, data) {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length);
    const typeB = Buffer.from(type);
    const crcVal = Buffer.alloc(4);
    crcVal.writeUInt32BE(crc32(Buffer.concat([typeB, data])));
    return Buffer.concat([len, typeB, data, crcVal]);
  }

  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8; ihdr[9] = 6; // RGBA

  const raw = Buffer.alloc(size * (1 + size * 4));
  for (let y = 0; y < size; y++) {
    raw[y * (1 + size * 4)] = 0;
    for (let x = 0; x < size; x++) {
      const src = (y * size + x) * 4;
      const dst = y * (1 + size * 4) + 1 + x * 4;
      raw[dst]   = pixels[src];
      raw[dst+1] = pixels[src+1];
      raw[dst+2] = pixels[src+2];
      raw[dst+3] = pixels[src+3];
    }
  }

  const compressed = zlib.deflateSync(raw);
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

  fs.writeFileSync(
    filename,
    Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', compressed), chunk('IEND', Buffer.alloc(0))])
  );
  console.log(`Created ${filename} (${size}x${size})`);
}

writePNG(192, 'icon-192.png');
writePNG(512, 'icon-512.png');
