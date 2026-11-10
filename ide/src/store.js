// Projects saved in the browser storage (IndexedDB). Works offline on every platform.
const DB = "claide-ide";
let dbPromise = null;

function db() {
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB, 1);
      req.onupgradeneeded = () => req.result.createObjectStore("projects", { keyPath: "id" });
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }
  return dbPromise;
}

async function tx(mode, fn) {
  const d = await db();
  return new Promise((resolve, reject) => {
    const t = d.transaction("projects", mode);
    const result = fn(t.objectStore("projects"));
    t.oncomplete = () => resolve(result && "result" in result ? result.result : undefined);
    t.onerror = () => reject(t.error);
  });
}

export const listProjects = async () =>
  ((await tx("readonly", (s) => s.getAll())) || []).sort((a, b) => b.updated - a.updated);
export const getProject = (id) => tx("readonly", (s) => s.get(id));
export const saveProject = (project) => tx("readwrite", (s) => s.put({ ...project, updated: Date.now() }));
export const deleteProject = (id) => tx("readwrite", (s) => s.delete(id));
export const newId = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
