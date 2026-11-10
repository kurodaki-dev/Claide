// Python engine of the IDE: Pyodide + Claide, running off the main thread.
import { loadPyodide } from "./pyodide/pyodide.mjs";

let py = null;
let bridge = null;
let known = new Set();
const ready = start();

function post(msg) { self.postMessage(msg); }

// ---- startup ---------------------------------------------------------------
// Starting Python and importing Claide is what takes time. The build saves the
// interpreter memory right after that point (engine.snapshot); restoring it is
// several times faster. If it can't be used, Python starts the normal way.
function writeClaide(bundle) {
  py.FS.mkdirTree("/lib/claide");
  for (const [name, code] of Object.entries(bundle.files)) py.FS.writeFile(`/lib/claide/${name}`, code);
  py.FS.writeFile("/lib/claide_ide_bridge.py", bundle.bridge);
}

async function start() {
  const t0 = performance.now();
  const options = {
    indexURL: new URL("./pyodide/", import.meta.url).href,
    stdout: (text) => post({ type: "log", stream: "out", text }),
    stderr: (text) => post({ type: "log", stream: "err", text }),
  };
  const bundle = await (await fetch(new URL("./claide/bundle.json", import.meta.url))).json();
  let restored = false;
  try {
    const res = await fetch(new URL("./engine.snapshot", import.meta.url));
    if (!res.ok) throw new Error("no snapshot");
    const snapshot = new Uint8Array(await res.arrayBuffer());
    py = await loadPyodide({ ...options, _loadSnapshot: snapshot });
    writeClaide(bundle); // still needed for modules imported later
    bridge = py.pyimport("claide_ide_bridge");
    py.runPython("import random; random.seed()"); // the snapshot froze the random state
    restored = true;
  } catch {
    py = await loadPyodide(options);
    writeClaide(bundle);
    py.runPython("import sys; sys.path.insert(0, '/lib')");
    bridge = py.pyimport("claide_ide_bridge");
  }
  post({ type: "ready", version: bundle.version, restored, ms: Math.round(performance.now() - t0) });
}

function rmTree(path) {
  const FS = py.FS;
  if (!FS.analyzePath(path).exists) return;
  for (const name of FS.readdir(path)) {
    if (name === "." || name === "..") continue;
    const full = `${path}/${name}`;
    if (FS.isDir(FS.stat(full).mode)) { rmTree(full); FS.rmdir(full); } else { FS.unlink(full); }
  }
}

function writeProject(files) {
  const FS = py.FS;
  rmTree("/project");
  FS.mkdirTree("/project");
  known = new Set(Object.keys(files));
  for (const [path, file] of Object.entries(files)) {
    const full = `/project/${path}`;
    FS.mkdirTree(full.slice(0, full.lastIndexOf("/")));
    if (file.base64 !== undefined) {
      const bin = Uint8Array.from(atob(file.base64), (c) => c.charCodeAt(0));
      FS.writeFile(full, bin);
    } else {
      FS.writeFile(full, file.text ?? "");
    }
  }
}

function newFiles() {
  const found = toJs(bridge.project_files(py.toPy([...known])));
  for (const name of Object.keys(found)) known.add(name);
  return found;
}

function toJs(proxy) {
  return proxy.toJs({ dict_converter: Object.fromEntries });
}

const handlers = {
  async load({ files, entry }) {
    writeProject(files);
    const result = toJs(bridge.safe(bridge.load, entry || "app.py"));
    return { ...result, created: newFiles() };
  },
  async request({ method, path, fields, body, contentType }) {
    const result = toJs(bridge.safe(bridge.request, method, path,
      fields ? py.toPy(fields) : undefined, body ?? undefined, contentType ?? undefined));
    return { ...result, created: newFiles() };
  },
  async template() {
    return { ok: true, files: toJs(bridge.new_project_files()) };
  },
};

self.onmessage = async (event) => {
  const { id, type, ...data } = event.data;
  try {
    await ready;
    const result = await handlers[type](data);
    post({ id, ...result });
  } catch (err) {
    post({ id, ok: false, error: String(err && err.message || err) });
  }
};

ready.catch((err) => post({ type: "fatal", error: String(err && err.message || err) }));
