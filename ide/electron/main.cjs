// Claide IDE desktop app (Windows, Linux): serves dist/ through the claide:// scheme.
const { app, BrowserWindow, Menu, dialog, ipcMain, protocol, shell } = require("electron");
const fs = require("node:fs");
const path = require("node:path");

const DIST = path.join(__dirname, "..", "dist");
const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".json": "application/json", ".wasm": "application/wasm", ".zip": "application/zip",
  ".svg": "image/svg+xml", ".png": "image/png", ".py": "text/plain; charset=utf-8",
};

protocol.registerSchemesAsPrivileged([
  { scheme: "claide", privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true, stream: true } },
]);

function serve(request) {
  const url = new URL(request.url);
  let rel = decodeURIComponent(url.pathname);
  if (rel === "/" || rel === "") rel = "/index.html";
  const file = path.normalize(path.join(DIST, rel));
  if (!file.startsWith(DIST + path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    return new Response("Not found", { status: 404 });
  }
  return new Response(fs.readFileSync(file), {
    headers: { "Content-Type": MIME[path.extname(file)] || "application/octet-stream" },
  });
}

// ---- real folders on disk (the "Open folder" button) ----------------------
const SKIP = new Set(["node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build"]);
const BINARY = /\.(png|jpe?g|gif|webp|ico|woff2?|ttf|otf|mp3|mp4|webm|pdf|zip)$/i;

function inside(root, rel) {
  const full = path.normalize(path.join(root, rel));
  if (!full.startsWith(path.normalize(root) + path.sep)) throw new Error("Path outside the project folder");
  return full;
}

function readFolder(root) {
  const files = {};
  let count = 0;
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.name.startsWith(".") || SKIP.has(entry.name)) continue;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) { walk(full); continue; }
      if (!entry.isFile() || ++count > 2000) continue;
      const rel = path.relative(root, full).split(path.sep).join("/");
      const size = fs.statSync(full).size;
      if (size > 5 * 1024 * 1024) continue;
      files[rel] = BINARY.test(entry.name)
        ? { base64: fs.readFileSync(full).toString("base64") }
        : { text: fs.readFileSync(full, "utf8") };
    }
  };
  walk(root);
  return files;
}

ipcMain.handle("choose-folder", async (event) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  const res = await dialog.showOpenDialog(win, { properties: ["openDirectory", "createDirectory"], title: "Open a Claide project folder" });
  return res.canceled ? null : res.filePaths[0];
});
ipcMain.handle("read-folder", (_e, root) => readFolder(root));
ipcMain.handle("write-file", (_e, root, rel, file) => {
  const full = inside(root, rel);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, file.base64 !== undefined ? Buffer.from(file.base64, "base64") : file.text ?? "");
});
ipcMain.handle("delete-file", (_e, root, rel) => fs.rmSync(inside(root, rel), { force: true }));
ipcMain.handle("rename-file", (_e, root, from, to) => {
  const dest = inside(root, to);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.renameSync(inside(root, from), dest);
});
ipcMain.handle("open-external", (_e, url) => {
  if (/^https?:\/\//i.test(url)) shell.openExternal(url);
});

function createWindow() {
  const win = new BrowserWindow({
    width: 1280, height: 800, minWidth: 360, minHeight: 480,
    title: "Claide IDE",
    backgroundColor: "#141414",
    icon: path.join(__dirname, "..", "resources", "icon.png"),
    autoHideMenuBar: true,
    webPreferences: { preload: path.join(__dirname, "preload.cjs"), contextIsolation: true, sandbox: true },
  });
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (event, url) => {
    if (!url.startsWith("claide://")) { event.preventDefault(); if (/^https?:\/\//i.test(url)) shell.openExternal(url); }
  });
  win.loadURL("claide://app/index.html");
}

Menu.setApplicationMenu(null);
app.whenReady().then(() => {
  protocol.handle("claide", serve);
  createWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
