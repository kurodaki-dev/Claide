// Minimal ZIP writer/reader (deflate through the browser's CompressionStream).
const table = new Uint32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
const crc32 = (data) => {
  let c = 0xffffffff;
  for (let i = 0; i < data.length; i++) c = table[(c ^ data[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
};
const pipe = async (data, stream) => new Uint8Array(await new Response(new Blob([data]).stream().pipeThrough(stream)).arrayBuffer());

export async function makeZip(entries) {
  // entries: [{ name, data: Uint8Array }]
  const enc = new TextEncoder();
  const chunks = [];
  const central = [];
  let offset = 0;
  for (const { name, data } of entries) {
    const nameBytes = enc.encode(name);
    const packed = await pipe(data, new CompressionStream("deflate-raw"));
    const crc = crc32(data);
    const head = new DataView(new ArrayBuffer(30));
    head.setUint32(0, 0x04034b50, true); head.setUint16(4, 20, true); head.setUint16(6, 0x0800, true);
    head.setUint16(8, 8, true); head.setUint32(14, crc, true); head.setUint32(18, packed.length, true);
    head.setUint32(22, data.length, true); head.setUint16(26, nameBytes.length, true);
    chunks.push(new Uint8Array(head.buffer), nameBytes, packed);
    const cd = new DataView(new ArrayBuffer(46));
    cd.setUint32(0, 0x02014b50, true); cd.setUint16(4, 20, true); cd.setUint16(6, 20, true); cd.setUint16(8, 0x0800, true);
    cd.setUint16(10, 8, true); cd.setUint32(16, crc, true); cd.setUint32(20, packed.length, true);
    cd.setUint32(24, data.length, true); cd.setUint16(28, nameBytes.length, true); cd.setUint32(42, offset, true);
    central.push(new Uint8Array(cd.buffer), nameBytes);
    offset += 30 + nameBytes.length + packed.length;
  }
  const size = central.reduce((n, c) => n + c.length, 0);
  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true); end.setUint16(8, entries.length, true); end.setUint16(10, entries.length, true);
  end.setUint32(12, size, true); end.setUint32(16, offset, true);
  return new Blob([...chunks, ...central, new Uint8Array(end.buffer)], { type: "application/zip" });
}

export async function readZip(blob) {
  const buf = new Uint8Array(await blob.arrayBuffer());
  const view = new DataView(buf.buffer);
  let end = buf.length - 22;
  while (end >= 0 && view.getUint32(end, true) !== 0x06054b50) end--;
  if (end < 0) throw new Error("This file is not a zip archive.");
  const count = view.getUint16(end + 10, true);
  let p = view.getUint32(end + 16, true);
  const dec = new TextDecoder();
  const out = [];
  for (let i = 0; i < count; i++) {
    const method = view.getUint16(p + 10, true);
    const csize = view.getUint32(p + 20, true);
    const nlen = view.getUint16(p + 28, true), xlen = view.getUint16(p + 30, true), clen = view.getUint16(p + 32, true);
    const local = view.getUint32(p + 42, true);
    const name = dec.decode(buf.subarray(p + 46, p + 46 + nlen));
    p += 46 + nlen + xlen + clen;
    if (name.endsWith("/")) continue;
    const start = local + 30 + view.getUint16(local + 26, true) + view.getUint16(local + 28, true);
    const raw = buf.subarray(start, start + csize);
    const data = method === 0 ? raw : method === 8 ? await pipe(raw, new DecompressionStream("deflate-raw")) : null;
    if (data) out.push({ name, data });
  }
  return out;
}
