// Claide IDE: projects, editor, live preview and console.
import { createEditor } from "./editor.js";
import { icon, logo } from "./icons.js";
import { deleteProject, getProject, listProjects, newId, saveProject } from "./store.js";
import { makeZip, readZip } from "./zip.js";

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const desktop = window.claideDesktop || null; // Electron bridge (real folders on disk)
const app = $("#app");

/* ------------------------------------------------------------------ theme */
const THEMES = ["system", "light", "dark"];
let themePref = localStorage.getItem("claide-ide-theme") || "system";
const media = matchMedia("(prefers-color-scheme: dark)");
function applyTheme() {
  const dark = themePref === "dark" || (themePref === "system" && media.matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
}
media.addEventListener("change", applyTheme);
applyTheme();
function themeButton() {
  const name = { system: "auto", light: "sun", dark: "moon" }[themePref];
  return `<button class="btn ghost icon" data-act="theme" title="Theme: ${themePref}" aria-label="Theme: ${themePref}">${icon(name)}</button>`;
}
function cycleTheme() {
  themePref = THEMES[(THEMES.indexOf(themePref) + 1) % THEMES.length];
  try { localStorage.setItem("claide-ide-theme", themePref); } catch {}
  applyTheme();
  document.querySelectorAll('[data-act="theme"]').forEach((b) => (b.outerHTML = themeButton()));
}

/* ----------------------------------------------------------------- engine */
const engine = { ready: false, version: "", error: null, listeners: new Set() };
const worker = window.claideEngine || new Worker("worker.js", { type: "module" });
let seq = 0;
const pending = new Map();
worker.onmessage = (e) => {
  const msg = e.data;
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); return; }
  if (msg.type === "ready") { engine.ready = true; engine.version = msg.version; engine.listeners.forEach((f) => f()); }
  else if (msg.type === "fatal") { engine.error = msg.error; engine.listeners.forEach((f) => f()); }
  else if (msg.type === "log") log(msg.stream === "err" ? "err" : "out", msg.text);
};
const call = (type, data = {}) => new Promise((resolve) => {
  const id = ++seq;
  pending.set(id, resolve);
  worker.postMessage({ id, type, ...data });
});

/* ------------------------------------------------------------------ utils */
function toast(text) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = text;
  document.body.append(el);
  setTimeout(() => el.remove(), 2200);
}

function dialog({ title, text = "", value = null, ok = "OK", danger = false }) {
  return new Promise((resolve) => {
    const back = document.createElement("div");
    back.className = "modal-back";
    back.innerHTML = `<form class="modal" role="dialog" aria-modal="true">
      <h2>${esc(title)}</h2>${text ? `<p>${esc(text)}</p>` : ""}
      ${value !== null ? `<input type="text" value="${esc(value)}" spellcheck="false" autocomplete="off">` : ""}
      <div class="row"><button type="button" class="btn" data-no>Cancel</button>
      <button class="btn primary">${esc(danger ? ok : ok)}</button></div></form>`;
    document.body.append(back);
    const input = $("input", back);
    const done = (v) => { back.remove(); resolve(v); };
    $("[data-no]", back).onclick = () => done(null);
    back.addEventListener("mousedown", (e) => { if (e.target === back) done(null); });
    back.addEventListener("keydown", (e) => { if (e.key === "Escape") done(null); });
    $("form", back).onsubmit = (e) => { e.preventDefault(); done(input ? input.value.trim() : true); };
    (input || $(".primary", back)).focus();
    if (input) input.select();
  });
}

const timeAgo = (ms) => {
  const s = Math.round((Date.now() - ms) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 86400) return `${Math.round(s / 3600)} h ago`;
  return new Date(ms).toLocaleDateString();
};

const isBinaryName = (name) => /\.(png|jpe?g|gif|webp|ico|woff2?|ttf|otf|mp3|mp4|webm|pdf|zip)$/i.test(name);
const bytesToB64 = (bytes) => {
  let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
};
const b64ToBytes = (b64) => Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
function download(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
function pickFile(accept, multiple = false) {
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = accept;
    input.multiple = multiple;
    input.onchange = () => resolve([...input.files]);
    input.click();
  });
}

/* ------------------------------------------------------------------- home */
async function showHome() {
  current = null;
  document.title = "Claide IDE";
  const projects = await listProjects();
  app.innerHTML = `
    <header class="topbar">
      <button class="brand" data-act="home" aria-label="Claide IDE">${logo}<span>Claide IDE</span></button>
      <div class="spacer"></div>${themeButton()}
    </header>
    <main class="home"><div class="home-inner">
      <h1>Projects</h1>
      <p class="sub">Write a website in Python, see it immediately. Everything runs on this device.</p>
      <div class="home-actions">
        <button class="btn primary" data-act="new">${icon("plus")} New project</button>
        <button class="btn" data-act="empty">${icon("file")} Empty project</button>
        ${desktop ? `<button class="btn" data-act="folder">${icon("open")} Open folder</button>` : ""}
        <button class="btn" data-act="import">${icon("upload")} Import .zip</button>
      </div>
      <p class="section-title">Recent</p>
      ${projects.length ? `<div class="project-list">${projects.map((p) => `
        <div class="project-row" data-open="${p.id}" tabindex="0">
          ${icon(p.kind === "folder" ? "folder" : "code")}
          <div class="grow"><div class="title">${esc(p.name)}</div>
          <div class="meta">${p.kind === "folder" ? esc(p.folder) : `${Object.keys(p.files || {}).length} files`} · ${timeAgo(p.updated)}</div></div>
          <div class="row-actions">
            ${p.kind === "folder" ? "" : `<button class="btn ghost icon" data-rename="${p.id}" title="Rename" aria-label="Rename">${icon("edit")}</button>`}
            <button class="btn ghost icon" data-delete="${p.id}" title="${p.kind === "folder" ? "Remove from list" : "Delete"}" aria-label="Delete">${icon("trash")}</button>
          </div>
        </div>`).join("")}</div>`
      : `<div class="empty">No project yet. Create one to start.</div>`}
      <div class="engine"><span class="dot ${engine.ready ? "on" : ""}"></span><span data-engine>${engineText()}</span></div>
    </div></main>`;
}

function engineText() {
  if (engine.error) return `Python engine failed to start: ${esc(engine.error)}`;
  return engine.ready ? `Python engine ready · Claide ${esc(engine.version)}` : "Starting the Python engine…";
}
engine.listeners.add(() => {
  const el = $("[data-engine]");
  if (el) { el.innerHTML = engineText(); el.previousElementSibling.classList.toggle("on", engine.ready); }
  if (current && engine.ready) run();
});

async function createProject(empty) {
  const name = await dialog({ title: empty ? "Empty project" : "New project", text: "Project name", value: "my-site", ok: "Create" });
  if (!name) return;
  let files;
  if (empty) {
    files = { "app.py": { text: 'from claide import *\n\n\n@route("/")\ndef home():\n    return h1("Hello!")\n\n\nrun()\n' } };
  } else {
    if (!engine.ready) await new Promise((r) => engine.listeners.add(r));
    const res = await call("template");
    files = Object.fromEntries(Object.entries(res.files).map(([k, v]) => [k, { text: v.replace(/my site/g, name) }]));
  }
  const project = { id: newId(), name, kind: "local", files, openFile: "app.py", previewPath: "/" };
  await saveProject(project);
  openProject(project.id);
}

async function importZip() {
  const [file] = await pickFile(".zip,application/zip");
  if (!file) return;
  try {
    const entries = await readZip(file);
    const names = entries.map((e) => e.name);
    const root = names.length && names.every((n) => n.includes("/")) && new Set(names.map((n) => n.split("/")[0])).size === 1
      ? names[0].split("/")[0] + "/" : "";
    const dec = new TextDecoder();
    const files = {};
    for (const { name, data } of entries) {
      const path = name.slice(root.length);
      if (!path || /(^|\/)(__pycache__|\.git)\//.test(path)) continue;
      files[path] = isBinaryName(path) ? { base64: bytesToB64(data) } : { text: dec.decode(data) };
    }
    const project = { id: newId(), name: (root.replace("/", "") || file.name.replace(/\.zip$/i, "")), kind: "local",
      files, openFile: files["app.py"] ? "app.py" : Object.keys(files)[0], previewPath: "/" };
    await saveProject(project);
    openProject(project.id);
  } catch (err) {
    toast(err.message);
  }
}

async function openFolder() {
  const folder = await desktop.chooseFolder();
  if (!folder) return;
  const existing = (await listProjects()).find((p) => p.kind === "folder" && p.folder === folder);
  const project = existing || { id: newId(), kind: "folder", folder, name: folder.split(/[\\/]/).pop(), openFile: "app.py", previewPath: "/" };
  await saveProject({ ...project, files: {} });
  openProject(project.id);
}

/* -------------------------------------------------------------- workspace */
let current = null; // { project, editor, ... }

async function openProject(id) {
  const project = await getProject(id);
  if (!project) return showHome();
  if (project.kind === "folder") {
    try {
      project.files = await desktop.readFolder(project.folder);
    } catch (err) {
      toast(`Cannot open ${project.folder}: ${err.message || err}`);
      return showHome();
    }
  }
  if (!project.files[project.openFile]) project.openFile = project.files["app.py"] ? "app.py" : Object.keys(project.files)[0];
  current = { project, routes: [], history: [], closed: new Set(), view: "code", logs: [] };
  document.title = `${project.name} · Claide IDE`;
  app.innerHTML = `
    <header class="topbar">
      <button class="brand" data-act="home" title="All projects" aria-label="All projects">${logo}<span class="hide-mobile">Claide</span></button>
      <span class="project-name">${esc(project.name)}</span>
      <div class="spacer"></div>
      <button class="btn ghost hide-mobile" data-act="export" title="Download the project as a .zip">${icon("download")} Export</button>
      ${themeButton()}
      <button class="btn primary" data-act="run" title="Run (Ctrl+Enter)">${icon("play")} Run<span class="kbd hide-mobile">⌃↵</span></button>
    </header>
    <div class="workspace" data-view="code">
      <section class="pane pane-files" aria-label="Files">
        <div class="pane-head"><span class="label">Files</span><div class="spacer"></div>
          <button class="btn ghost icon" data-act="upload" title="Add a file from this device" aria-label="Add a file">${icon("upload")}</button>
          <button class="btn ghost icon" data-act="newfile" title="New file" aria-label="New file">${icon("plus")}</button>
        </div>
        <div class="files" data-tree></div>
      </section>
      <section class="pane pane-code" aria-label="Editor">
        <div class="pane-head"><span class="filename mono" data-filename></span><span class="saved" data-saved></span></div>
        <div class="editor-wrap" data-editor></div>
      </section>
      <section class="pane pane-preview" aria-label="Preview">
        <div class="preview-bar">
          <button class="btn ghost icon" data-act="back" title="Back" aria-label="Back">${icon("chevron").replace('class="i"', 'class="i" style="transform:rotate(90deg)"')}</button>
          <button class="btn ghost icon" data-act="reload" title="Reload" aria-label="Reload">${icon("reload")}</button>
          <input class="address mono" data-address spellcheck="false" autocomplete="off" aria-label="Address" value="${esc(project.previewPath || "/")}">
          <select class="routes-select" data-routes aria-label="Pages"></select>
        </div>
        <div class="preview-frame">
          <iframe data-frame title="Preview" sandbox="allow-scripts allow-forms allow-modals allow-popups"></iframe>
          <div class="preview-overlay" data-overlay>${engine.ready ? "Running…" : "Starting the Python engine…"}</div>
        </div>
        <div class="console" data-console>
          <div class="pane-head"><span class="label">Console</span><span class="status-pill" data-status></span><div class="spacer"></div>
            <button class="btn ghost icon" data-act="clear" title="Clear" aria-label="Clear the console">${icon("clear")}</button>
            <button class="btn ghost icon" data-act="toggle-console" title="Hide or show" aria-label="Hide or show the console">${icon("chevron")}</button>
          </div>
          <div class="console-body mono" data-logs></div>
        </div>
      </section>
    </div>
    <nav class="tabs" aria-label="Views">
      <button data-tab="files" aria-selected="false">${icon("folder")}Files</button>
      <button data-tab="code" aria-selected="true">${icon("code")}Code</button>
      <button data-tab="preview" aria-selected="false">${icon("eye")}Preview</button>
    </nav>`;
  if (matchMedia("(max-width: 860px)").matches) $("[data-console]").classList.add("collapsed");
  current.editor = createEditor($("[data-editor]"), { onChange: onEdit, onRun: () => run() });
  renderTree();
  openFile(project.openFile);
  if (engine.ready) run();
}

function setView(view) {
  if (!current) return;
  current.view = view;
  $(".workspace").dataset.view = view;
  document.querySelectorAll("[data-tab]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === view)));
}

function renderTree() {
  const { files, openFile } = current.project;
  const paths = Object.keys(files).sort((a, b) => {
    const da = a.includes("/"), db = b.includes("/");
    if (a === "app.py") return -1;
    if (b === "app.py") return 1;
    if (da !== db) return da ? 1 : -1;
    return a.localeCompare(b);
  });
  const folders = new Map();
  const top = [];
  for (const p of paths) {
    const i = p.lastIndexOf("/");
    if (i < 0) top.push(p);
    else {
      const dir = p.slice(0, i);
      if (!folders.has(dir)) folders.set(dir, []);
      folders.get(dir).push(p);
    }
  }
  const fileRow = (p, depth) => `
    <div class="tree-file ${p === openFile ? "active" : ""}" data-file="${esc(p)}" style="padding-left:${10 + depth * 14}px" tabindex="0">
      ${icon("file")}<span class="name">${esc(p.split("/").pop())}</span>
      <span class="file-actions">
        <button class="btn ghost icon" data-rename-file="${esc(p)}" title="Rename" aria-label="Rename">${icon("edit")}</button>
        <button class="btn ghost icon" data-delete-file="${esc(p)}" title="Delete" aria-label="Delete">${icon("trash")}</button>
      </span>
    </div>`;
  let html = top.map((p) => fileRow(p, 0)).join("");
  for (const [dir, list] of [...folders].sort((a, b) => a[0].localeCompare(b[0]))) {
    const closed = current.closed.has(dir);
    const depth = dir.split("/").length - 1;
    html += `<div class="tree-folder ${closed ? "closed" : ""}" data-folder="${esc(dir)}" style="padding-left:${10 + depth * 14}px">
      ${icon("chevron").replace('class="i"', 'class="i chev"')}${icon("folder")}<span>${esc(dir.split("/").pop())}</span></div>`;
    if (!closed) html += list.map((p) => fileRow(p, depth + 1)).join("");
  }
  $("[data-tree]").innerHTML = html || `<div class="tree-folder">No files</div>`;
}

function openFile(path) {
  const file = current.project.files[path];
  if (!file) return;
  current.project.openFile = path;
  $("[data-filename]").textContent = path;
  const wrap = $("[data-editor]");
  wrap.querySelector(".binary-note")?.remove();
  if (file.base64 !== undefined) {
    current.editor.open(path, "");
    current.editor.view.dom.style.display = "none";
    wrap.insertAdjacentHTML("beforeend", `<div class="binary-note">${esc(path)} is a binary file (${Math.round(file.base64.length * 0.75 / 1024)} KB). It is served at /${esc(path)}.</div>`);
  } else {
    current.editor.view.dom.style.display = "";
    current.editor.open(path, file.text);
  }
  renderTree();
  persist();
}

let saveTimer = null;
let runTimer = null;
function onEdit(text) {
  const { project } = current;
  project.files[project.openFile] = { text };
  $("[data-saved]").textContent = "Editing…";
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => persist(project.openFile), 400);
  clearTimeout(runTimer);
  runTimer = setTimeout(() => run(), 900);
}

async function persist(changedPath) {
  if (!current) return;
  const { project } = current;
  try {
    if (project.kind === "folder") {
      if (changedPath && project.files[changedPath]) await desktop.writeFile(project.folder, changedPath, project.files[changedPath]);
      await saveProject({ ...project, files: {} });
    } else {
      await saveProject(project);
    }
    const el = $("[data-saved]");
    if (el && changedPath) el.textContent = "Saved";
  } catch (err) {
    toast(`Could not save: ${err.message || err}`);
  }
}

/* ----------------------------------------------------------- run/preview */
function log(kind, text) {
  if (!current) return;
  const el = $("[data-logs]");
  if (!el) return;
  const line = document.createElement("div");
  line.className = `log ${kind}`;
  line.textContent = text;
  el.append(line);
  if (kind === "error") $("[data-console]")?.classList.remove("collapsed");
  while (el.childElementCount > 500) el.firstChild.remove();
  el.scrollTop = el.scrollHeight;
}

function status(text) {
  const el = $("[data-status]");
  if (el) el.textContent = text;
}

async function syncCreated(created) {
  const names = Object.keys(created || {});
  if (!names.length) return;
  for (const name of names) {
    current.project.files[name] = { text: created[name] };
    if (current.project.kind === "folder") await desktop.writeFile(current.project.folder, name, { text: created[name] });
    log("info", `Saved ${name}`);
  }
  renderTree();
  persist();
}

let running = false;
let rerun = false;
async function run() {
  if (!current || !engine.ready) return;
  if (running) { rerun = true; return; }
  running = true;
  clearTimeout(runTimer);
  status("Running…");
  const started = performance.now();
  const res = await call("load", { files: current.project.files });
  if (!current) { running = false; return; }
  await syncCreated(res.created);
  if (!res.ok) {
    showError(res.error);
    status("Error");
  } else {
    current.routes = res.routes;
    renderRoutes();
    await navigate($("[data-address]").value || "/", { method: "GET", record: false });
    status(`Ready · ${Math.round(performance.now() - started)} ms`);
  }
  running = false;
  if (rerun) { rerun = false; run(); }
}

function renderRoutes() {
  const select = $("[data-routes]");
  const pages = current.routes.filter((r) => r.methods.includes("GET") && !r.path.includes("<"));
  select.innerHTML = `<option value="">Pages</option>` + pages.map((r) => `<option value="${esc(r.path)}">${esc(r.path)}</option>`).join("");
}

function showError(text) {
  log("error", text);
  const frame = $("[data-frame]");
  frame.srcdoc = `<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:20px;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;background:#fff;color:#141414}
    h1{font:600 15px system-ui,sans-serif;margin:0 0 12px}pre{white-space:pre-wrap;margin:0}</style>
    <h1>Your site could not start</h1><pre>${esc(text)}</pre>`;
  $("[data-overlay]").hidden = true;
}

const PREVIEW_SCRIPT = `<script>(function(){
  var send=function(m){m.__claide=true;parent.postMessage(m,"*")};
  var external=function(h){return /^[a-z][a-z0-9+.-]*:/i.test(h)||h.indexOf("//")===0};
  document.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest("a[href]");if(!a)return;
    var h=a.getAttribute("href");if(!h||h[0]==="#"||h.indexOf("javascript:")===0)return;e.preventDefault();
    send(external(h)?{type:"external",href:h}:{type:"navigate",href:h})},true);
  document.addEventListener("submit",function(e){var f=e.target;e.preventDefault();var fd=new FormData(f,e.submitter||undefined);var fields=[];
    fd.forEach(function(v,k){if(typeof v==="string")fields.push([k,v])});
    send({type:"submit",method:(f.getAttribute("method")||"GET").toUpperCase(),action:f.getAttribute("action")||"",fields:fields})},true);
  var seq=0,waits={},realFetch=window.fetch;
  window.addEventListener("message",function(e){var d=e.data;if(d&&d.__claideFetch&&waits[d.id]){waits[d.id](d);delete waits[d.id]}});
  window.fetch=function(input,init){init=init||{};var url=typeof input==="string"?input:input.url;if(external(url))return realFetch(input,init);
    var headers=init.headers||{};var ct=headers["Content-Type"]||headers["content-type"];
    return new Promise(function(resolve){var id=++seq;waits[id]=function(d){var empty=d.status===204||d.status===304;
      resolve(new Response(empty?null:d.body,{status:d.status,headers:{"Content-Type":d.contentType||"text/plain"}}))};
      send({type:"fetch",id:id,url:url,method:(init.method||"GET").toUpperCase(),body:typeof init.body==="string"?init.body:undefined,contentType:ct})})};
})();<\/script>`;

function resolvePath(href) {
  const base = new URL($("[data-address]").value || "/", "http://preview.local");
  const url = new URL(href, base);
  return url.pathname + url.search;
}

async function navigate(path, { method = "GET", fields, record = true } = {}) {
  if (!current) return;
  let target = path || "/";
  let req = { method, path: target, fields };
  let res;
  for (let hop = 0; hop < 6; hop++) {
    res = await call("request", req);
    if (!current) return;
    await syncCreated(res.created);
    if (!res.ok || !res.location || res.status < 300 || res.status >= 400) break;
    target = resolvePath(res.location);
    req = { method: "GET", path: target };
  }
  if (record) current.history.push($("[data-address]").value);
  $("[data-address]").value = target;
  current.project.previewPath = target;
  if (!res.ok) return showError(res.error);
  const frame = $("[data-frame]");
  if (res.contentType.includes("text/html")) {
    const body = res.body.includes("</body>") ? res.body.replace(/<\/body>(?![\s\S]*<\/body>)/, PREVIEW_SCRIPT + "</body>") : res.body + PREVIEW_SCRIPT;
    frame.srcdoc = body;
  } else {
    let text = res.body;
    if (res.contentType.includes("json")) { try { text = JSON.stringify(JSON.parse(text), null, 2); } catch {} }
    frame.srcdoc = `<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:16px;background:#fff;color:#141414;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace}pre{margin:0;white-space:pre-wrap}</style><pre>${esc(text)}</pre>`;
  }
  $("[data-overlay]").hidden = true;
  if (res.status >= 400) log("info", `${method} ${target} → ${res.status}`);
}

window.addEventListener("message", async (e) => {
  const d = e.data;
  if (!current || !d || !d.__claide || e.source !== $("[data-frame]")?.contentWindow) return;
  if (d.type === "navigate") navigate(resolvePath(d.href));
  else if (d.type === "external") openExternal(d.href);
  else if (d.type === "submit") {
    const action = resolvePath(d.action || $("[data-address]").value);
    if (d.method === "GET") {
      const url = new URL(action, "http://preview.local");
      d.fields.forEach(([k, v]) => url.searchParams.append(k, v));
      navigate(url.pathname + url.search);
    } else navigate(action, { method: d.method, fields: d.fields });
  } else if (d.type === "fetch") {
    const res = await call("request", { method: d.method, path: resolvePath(d.url), body: d.body, contentType: d.contentType });
    if (!res.ok) log("error", res.error);
    e.source.postMessage({ __claideFetch: true, id: d.id, status: res.ok ? res.status : 500, body: res.ok ? res.body : res.error,
      contentType: res.ok ? res.contentType : "text/plain" }, "*");
  }
});

function openExternal(href) {
  if (desktop) desktop.openExternal(href);
  else window.open(href, "_blank", "noopener");
}

/* ------------------------------------------------------------ file ops */
async function newFile() {
  const name = await dialog({ title: "New file", text: "Path, e.g. routes/blog.py or static/style.css", value: "routes/page.py", ok: "Create" });
  if (!name) return;
  const path = name.replace(/^\/+/, "");
  if (current.project.files[path]) return toast("This file already exists.");
  const starter = path.startsWith("routes/") && path.endsWith(".py")
    ? `from claide import *\n\n\n@route("/${path.slice(7, -3).replace(/(^|\/)index$/, "")}")\ndef ${path.slice(7, -3).replace(/\W+/g, "_")}():\n    return h1("${path.slice(7, -3).split("/").pop()}")\n`
    : "";
  current.project.files[path] = { text: starter };
  if (current.project.kind === "folder") await desktop.writeFile(current.project.folder, path, { text: starter });
  openFile(path);
  setView("code");
  run();
}

async function uploadFiles() {
  const files = await pickFile("*/*", true);
  for (const f of files) {
    const folder = /\.(png|jpe?g|gif|webp|svg|ico|css|js|woff2?|ttf)$/i.test(f.name) ? "static/" : "";
    const path = folder + f.name;
    const data = new Uint8Array(await f.arrayBuffer());
    const entry = isBinaryName(f.name) ? { base64: bytesToB64(data) } : { text: new TextDecoder().decode(data) };
    current.project.files[path] = entry;
    if (current.project.kind === "folder") await desktop.writeFile(current.project.folder, path, entry);
  }
  if (files.length) { renderTree(); persist(); run(); toast(`${files.length} file(s) added`); }
}

async function renameFile(path) {
  const name = await dialog({ title: "Rename", value: path, ok: "Rename" });
  if (!name || name === path) return;
  const files = current.project.files;
  if (files[name]) return toast("A file with this name already exists.");
  files[name] = files[path];
  delete files[path];
  if (current.project.kind === "folder") await desktop.renameFile(current.project.folder, path, name);
  if (current.project.openFile === path) current.project.openFile = name;
  openFile(current.project.openFile);
  run();
}

async function removeFile(path) {
  if (!(await dialog({ title: `Delete ${path}?`, text: "This cannot be undone.", ok: "Delete", danger: true }))) return;
  delete current.project.files[path];
  if (current.project.kind === "folder") await desktop.deleteFile(current.project.folder, path);
  if (current.project.openFile === path) current.project.openFile = Object.keys(current.project.files)[0];
  if (current.project.openFile) openFile(current.project.openFile); else { renderTree(); persist(); }
  run();
}

async function exportZip() {
  const enc = new TextEncoder();
  const { project } = current;
  const entries = Object.entries(project.files).map(([name, f]) => ({
    name: `${project.name}/${name}`, data: f.base64 !== undefined ? b64ToBytes(f.base64) : enc.encode(f.text),
  }));
  download(await makeZip(entries), `${project.name}.zip`);
}

/* --------------------------------------------------------------- events */
document.addEventListener("click", async (e) => {
  const t = e.target.closest("button, [data-open], [data-file], [data-folder]");
  if (!t) return;
  const act = t.dataset.act;
  if (act === "theme") return cycleTheme();
  if (act === "home") { if (current) await persist(); return showHome(); }
  if (act === "new") return createProject(false);
  if (act === "empty") return createProject(true);
  if (act === "import") return importZip();
  if (act === "folder") return openFolder();
  if (act === "run") {
    await persist(current?.project.openFile);
    if (matchMedia("(max-width: 860px)").matches) setView("preview");
    return run();
  }
  if (act === "export") return exportZip();
  if (act === "newfile") return newFile();
  if (act === "upload") return uploadFiles();
  if (act === "reload") return navigate($("[data-address]").value, { record: false });
  if (act === "back") { const prev = current?.history.pop(); if (prev) navigate(prev, { record: false }); return; }
  if (act === "clear") { $("[data-logs]").innerHTML = ""; return; }
  if (act === "toggle-console") { $("[data-console]").classList.toggle("collapsed"); return; }
  if (t.dataset.tab) return setView(t.dataset.tab);
  if (t.dataset.renameFile) { e.stopPropagation(); return renameFile(t.dataset.renameFile); }
  if (t.dataset.deleteFile) { e.stopPropagation(); return removeFile(t.dataset.deleteFile); }
  if (t.dataset.rename) {
    e.stopPropagation();
    const p = await getProject(t.dataset.rename);
    const name = await dialog({ title: "Rename project", value: p.name, ok: "Rename" });
    if (name) { await saveProject({ ...p, name }); showHome(); }
    return;
  }
  if (t.dataset.delete) {
    e.stopPropagation();
    const p = await getProject(t.dataset.delete);
    const ok = await dialog({
      title: p.kind === "folder" ? `Remove ${p.name} from the list?` : `Delete ${p.name}?`,
      text: p.kind === "folder" ? "The folder on your disk is not touched." : "Its files will be deleted from this device.",
      ok: p.kind === "folder" ? "Remove" : "Delete", danger: true,
    });
    if (ok) { await deleteProject(p.id); showHome(); }
    return;
  }
  if (t.dataset.open) return openProject(t.dataset.open);
  if (t.dataset.file) { openFile(t.dataset.file); if (matchMedia("(max-width: 860px)").matches) setView("code"); return; }
  if (t.dataset.folder) {
    const dir = t.dataset.folder;
    current.closed.has(dir) ? current.closed.delete(dir) : current.closed.add(dir);
    return renderTree();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.matches?.("[data-open], [data-file]")) e.target.click();
  if (e.key === "Enter" && e.target.matches?.("[data-address]")) { e.preventDefault(); navigate(resolvePath(e.target.value)); }
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && current) { e.preventDefault(); run(); }
});
document.addEventListener("change", (e) => {
  if (e.target.matches("[data-routes]") && e.target.value) {
    navigate(e.target.value);
    e.target.value = "";
    if (matchMedia("(max-width: 860px)").matches) setView("preview");
  }
});
window.addEventListener("beforeunload", () => { if (current) persist(); });

showHome();
