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

// Editor completions, read from Claide itself so they always match the module:
// names, signatures and the first line of each docstring.
const completions = py.runPython(`
import inspect, json
import claide
from claide.app import Request
from claide.uitemplate import UITemplate

import re

def _first(doc):
    text = inspect.cleandoc(doc).split("\\n\\n")[0].replace("\\n", " ") if doc else ""
    return text.replace("\\x60\\x60", "")

def _sig(obj):
    try:
        text = str(inspect.signature(obj))
    except (TypeError, ValueError):
        return ""
    text = re.sub(r"""(:|->) ["']+([^"']+)["']+""", r"\\1 \\2", text)   # annotations written as strings
    return re.sub(r"<function .*? at 0x[0-9a-f]+>", "...", text)

def _members(cls):
    out = []
    for name, value in inspect.getmembers(cls):
        if name.startswith("_") or name == "claide_assets":
            continue
        if isinstance(value, property):
            out.append({"label": name, "type": "property", "info": _first(value.__doc__)})
        elif callable(value):
            out.append({"label": name, "type": "method", "detail": _sig(value), "info": _first(value.__doc__)})
    return out

_tags = dict({n: n for n in claide._TAG_NAMES}, **claide._RENAMED)
_globals = []
for name in claide.__all__:
    if name.startswith("_") or name == "ui":
        continue
    obj = getattr(claide, name)
    if name in _tags:
        tag = _tags[name]
        _globals.append({"label": name, "type": "tag", "detail": f"<{tag}>", "info": f"Creates an HTML <{tag}> element."})
    elif inspect.ismodule(obj):
        _globals.append({"label": name, "type": "namespace", "info": _first(obj.__doc__)})
    elif inspect.isclass(obj) and name != "ui":
        _globals.append({"label": name, "type": "class", "detail": _sig(obj), "info": _first(obj.__doc__)})
    elif callable(obj) and name != "ui":
        _globals.append({"label": name, "type": "function", "detail": _sig(obj), "info": _first(obj.__doc__)})
    elif name == "request":
        _globals.append({"label": name, "type": "variable", "info": _first(type(obj).__doc__)})
    elif name == "CATEGORIES":
        _globals.append({"label": name, "type": "constant", "info": "Uiverse categories: " + ", ".join(obj)})
    else:
        _globals.append({"label": name, "type": "variable", "info": ""})
_globals.append({"label": "ui", "type": "function", "detail": "(ref)", "info": "Uiverse.io component: ui(\\"author/name\\") or ui(\\"https://uiverse.io/...\\")."})

_request = _members(Request) + [
    {"label": "method", "type": "property", "info": "HTTP method: \\"GET\\", \\"POST\\"..."},
    {"label": "path", "type": "property", "info": "Path of the URL, e.g. \\"/blog/3\\"."},
    {"label": "params", "type": "property", "info": "Parameters taken from the URL (<int:id>...)."},
    {"label": "g", "type": "property", "info": "Free storage for the duration of the request."},
]
json.dumps({"globals": _globals, "request": _request, "ui": _members(UITemplate)})
`);
writeFileSync(join(dist, "completions.json"), completions);
console.log(`Editor completions: ${JSON.parse(completions).globals.length} names from Claide`);

const snapshot = py.makeMemorySnapshot();
writeFileSync(join(dist, "engine.snapshot"), snapshot);
console.log(`Engine snapshot: ${(snapshot.length / 1e6).toFixed(1)} MB in ${Math.round(performance.now() - started)} ms`);

console.log(`Built dist/ with Claide ${version}, Pyodide ${pyodideVersion}, build ${build}`);
