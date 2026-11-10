// Gives the IDE access to real project folders on disk (desktop only).
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("claideDesktop", {
  chooseFolder: () => ipcRenderer.invoke("choose-folder"),
  readFolder: (root) => ipcRenderer.invoke("read-folder", root),
  writeFile: (root, rel, file) => ipcRenderer.invoke("write-file", root, rel, file),
  deleteFile: (root, rel) => ipcRenderer.invoke("delete-file", root, rel),
  renameFile: (root, from, to) => ipcRenderer.invoke("rename-file", root, from, to),
  openExternal: (url) => ipcRenderer.invoke("open-external", url),
});
