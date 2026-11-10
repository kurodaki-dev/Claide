// Builds the IDE into dist/: bundles the UI, copies Pyodide and the Claide sources.
import { build } from "esbuild";
import { cpSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const dist = join(here, "dist");
rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });

await build({
  entryPoints: [join(here, "src/main.js")],
  outfile: join(dist, "app.js"),
  bundle: true, format: "esm", minify: true, target: "es2020", legalComments: "none",
});
await build({
  entryPoints: [join(here, "src/worker.js")],
  outfile: join(dist, "worker.js"),
  bundle: true, format: "esm", minify: true, target: "es2020",
  external: ["./pyodide/pyodide.mjs"],
});

for (const file of ["index.html", "style.css", "bridge.py", "icon.svg"]) {
  cpSync(join(here, "src", file), join(dist, file));
}

const pyodideSrc = join(here, "node_modules/pyodide");
mkdirSync(join(dist, "pyodide"));
for (const file of ["pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]) {
  cpSync(join(pyodideSrc, file), join(dist, "pyodide", file));
}

const claideSrc = join(here, "..", "claide");
const claideFiles = readdirSync(claideSrc).filter((f) => f.endsWith(".py"));
mkdirSync(join(dist, "claide"));
for (const file of claideFiles) cpSync(join(claideSrc, file), join(dist, "claide", file));
const version = /__version__ = "([^"]+)"/.exec(readFileSync(join(claideSrc, "__init__.py"), "utf8"))[1];
writeFileSync(join(dist, "claide", "manifest.json"), JSON.stringify({ version, files: claideFiles }));

console.log(`Built dist/ with Claide ${version} (${claideFiles.length} modules)`);
