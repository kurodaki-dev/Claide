// Builds the IDE into dist/: bundles the UI, copies Pyodide and the Claide sources.
import { build as esbuild } from "esbuild";
import { createHash } from "node:crypto";
import { cpSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const dist = join(here, "dist");
rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });

await esbuild({
  entryPoints: [join(here, "src/main.js")],
  outfile: join(dist, "app.js"),
  bundle: true, format: "esm", minify: true, target: "es2020", legalComments: "none",
});
await esbuild({
  entryPoints: [join(here, "src/worker.js")],
  outfile: join(dist, "worker.js"),
  bundle: true, format: "esm", minify: true, target: "es2020",
  external: ["./pyodide/pyodide.mjs"],
});

for (const file of ["index.html", "style.css", "icon.svg"]) {
  cpSync(join(here, "src", file), join(dist, file));
}

const pyodideSrc = join(here, "node_modules/pyodide");
mkdirSync(join(dist, "pyodide"));
for (const file of ["pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]) {
  cpSync(join(pyodideSrc, file), join(dist, "pyodide", file));
}

// Claide sources + the IDE bridge in a single file, with a build id that changes
// whenever any of them (or Pyodide) changes: it invalidates the saved engine snapshot.
const claideSrc = join(here, "..", "claide");
const files = {};
for (const file of readdirSync(claideSrc).filter((f) => f.endsWith(".py")).sort()) {
  files[file] = readFileSync(join(claideSrc, file), "utf8");
}
const bridge = readFileSync(join(here, "src/bridge.py"), "utf8");
const pyodideVersion = JSON.parse(readFileSync(join(pyodideSrc, "package.json"), "utf8")).version;
const version = /__version__ = "([^"]+)"/.exec(files["__init__.py"])[1];
const build = createHash("sha256").update(JSON.stringify([pyodideVersion, files, bridge])).digest("hex").slice(0, 16);
mkdirSync(join(dist, "claide"));
writeFileSync(join(dist, "claide", "bundle.json"), JSON.stringify({ version, build, pyodide: pyodideVersion, files, bridge }));

// Engine snapshot: Python already started with Claide imported. Restoring it is
// several times faster than starting Python, so the app starts quickly, even on
// its very first launch. Made with Node from the same Pyodide files.
const { loadPyodide } = await import(pathToFileURL(join(pyodideSrc, "pyodide.mjs")).href);
const started = performance.now();
const py = await loadPyodide({ indexURL: pyodideSrc + "/", _makeSnapshot: true, stdout: () => {}, stderr: () => {} });
py.FS.mkdirTree("/lib/claide");
for (const [name, code] of Object.entries(files)) py.FS.writeFile(`/lib/claide/${name}`, code);
py.FS.writeFile("/lib/claide_ide_bridge.py", bridge);
py.runPython("import sys; sys.path.insert(0, '/lib')");
py.pyimport("claide_ide_bridge");
const snapshot = py.makeMemorySnapshot();
writeFileSync(join(dist, "engine.snapshot"), snapshot);
console.log(`Engine snapshot: ${(snapshot.length / 1e6).toFixed(1)} MB in ${Math.round(performance.now() - started)} ms`);

console.log(`Built dist/ with Claide ${version}, Pyodide ${pyodideVersion}, build ${build}`);
