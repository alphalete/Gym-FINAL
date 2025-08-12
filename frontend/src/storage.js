// storage.js — robust shim (IndexedDB with localStorage fallback)
class GymStorage {
  constructor() {
    this.db = null;
    this.idbOk = null;
  }

  async init() {
    if (this.idbOk !== null) return this.idbOk;
    if (!('indexedDB' in window)) {
      this.idbOk = false;
      return false;
    }
    return new Promise((resolve) => {
      try {
        const request = indexedDB.open('gym-db', 2);
        request.onupgradeneeded = (e) => {
          const db = e.target.result;
          if (!db.objectStoreNames.contains('members')) {
            const s = db.createObjectStore('members', { keyPath: 'id' });
            s.createIndex('id', 'id', { unique: true });
          }
          if (!db.objectStoreNames.contains('payments')) {
            const s = db.createObjectStore('payments', { keyPath: 'id' });
            s.createIndex('id', 'id', { unique: true });
            s.createIndex('memberId', 'memberId', { unique: false });
          }
          if (!db.objectStoreNames.contains('settings')) {
            const s = db.createObjectStore('settings', { keyPath: 'name' });
            s.createIndex('name', 'name', { unique: true });
          }
          if (!db.objectStoreNames.contains('plans')) {
            const s = db.createObjectStore('plans', { keyPath: 'id' });
            s.createIndex('id', 'id', { unique: true });
          }
        };
        request.onsuccess = () => { this.db = request.result; this.idbOk = true; resolve(true); };
        request.onerror = () => { console.error('[storage] IDB open failed', request.error); this.idbOk = false; resolve(false); };
      } catch (e) {
        console.error('[storage] IDB init error', e);
        this.idbOk = false; resolve(false);
      }
    });
  }

  // ---------- helpers (IDB or localStorage fallback) ----------
  async saveData(storeName, value) {
    const ok = await this.init();
    if (ok) {
      return new Promise((resolve, reject) => {
        try {
          const tx = this.db.transaction([storeName], 'readwrite');
          const store = tx.objectStore(storeName);
          const req = store.put(value);
          req.onsuccess = () => { try { window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail: storeName })); } catch {} ; resolve(true); };
          req.onerror = () => reject(req.error);
        } catch (e) { reject(e); }
      });
    }
    // fallback to localStorage
    const key = `__${storeName}__`;
    const arr = JSON.parse(localStorage.getItem(key) || '[]');
    const id = String(value.id || crypto.randomUUID?.() || Date.now());
    const idx = arr.findIndex(x => String(x.id) === id);
    const rec = { ...value, id };
    if (idx >= 0) arr[idx] = rec; else arr.push(rec);
    localStorage.setItem(key, JSON.stringify(arr));
    try { window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail: storeName })); } catch {}
    return true;
  }

  async getAll(storeName) {
    const ok = await this.init();
    if (ok) {
      return new Promise((resolve) => {
        try {
          const tx = this.db.transaction([storeName], 'readonly');
          const store = tx.objectStore(storeName);
          const out = [];
          const req = store.openCursor();
          req.onsuccess = (e) => { const c = e.target.result; if (c) { out.push(c.value); c.continue(); } else resolve(out); };
          req.onerror = () => resolve([]);
        } catch (_e) { resolve([]); }
      });
    }
    // fallback
    const key = `__${storeName}__`;
    return JSON.parse(localStorage.getItem(key) || '[]');
  }

  // convenience
  async getAllMembers() { return this.getAll('members'); }
  async getAllPayments() { return this.getAll('payments'); }

  // Generic getAll method
  async getAll(storeName) {
    const ok = await this.init();
    if (ok) {
      return new Promise((resolve) => {
        try {
          const tx = this.db.transaction([storeName], 'readonly');
          const store = tx.objectStore(storeName);
          const out = [];
          const req = store.openCursor();
          req.onsuccess = (e) => { const c = e.target.result; if (c) { out.push(c.value); c.continue(); } else resolve(out); };
          req.onerror = () => resolve([]);
        } catch (_e) { resolve([]); }
      });
    }
    // fallback
    const key = `__${storeName}__`;
    return JSON.parse(localStorage.getItem(key) || '[]');
  }

  async getSetting(name, fallback = {}) {
    const ok = await this.init();
    if (ok) {
      return new Promise((resolve) => {
        try {
          const tx = this.db.transaction(['settings'], 'readonly');
          const store = tx.objectStore('settings');
          const req = store.get(name);
          req.onsuccess = () => {
            const rec = req.result;
            resolve(rec && Object.prototype.hasOwnProperty.call(rec, 'value') ? rec.value : (rec ?? fallback));
          };
          req.onerror = () => resolve(fallback);
        } catch (_e) { resolve(fallback); }
      });
    }
    // fallback
    const key = `__settings__${name}`;
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  }

  async saveSetting(name, value) {
    const ok = await this.init();
    if (ok) {
      return new Promise((resolve, reject) => {
        try {
          const tx = this.db.transaction(['settings'], 'readwrite');
          const store = tx.objectStore('settings');
          const req = store.put({ name, value });
          req.onsuccess = () => { try { window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail: 'settings' })); } catch {}; resolve(true); };
          req.onerror = () => reject(req.error);
        } catch (e) { reject(e); }
      });
    }
    // fallback
    const key = `__settings__${name}`;
    localStorage.setItem(key, JSON.stringify(value));
    try { window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail: 'settings' })); } catch {}
    return true;
  }

  // convenience batch
  async saveMembers(members) {
    const list = Array.isArray(members) ? members : [members];
    await Promise.all(list.map(m => this.saveData('members', m)));
  }
}

const gymStorage = new GymStorage();

// Named exports for convenience
export async function getAll(storeName){ return gymStorage.getAll(storeName); }
export async function getSetting(name, fallback){ return gymStorage.getSetting(name, fallback); }
export async function saveSetting(name, value){ return gymStorage.saveSetting(name, value); }

export async function getPlanById(id){
  try {
    const all = await gymStorage.getAll?.('plans');
    return (all || []).find(p => String(p.id) === String(id)) || null;
  } catch { return null; }
}

export async function upsertMemberWithPlanSnapshot(member, plan){
  // plan snapshot stored on member so prices/cycle survive plan edits
  const snap = plan ? {
    planId: plan.id,
    planName: plan.name,
    cycleDays: Number(plan.cycleDays || 30),
    fee: Number(plan.price || 0),
  } : {};
  const rec = { ...member, ...snap };
  await gymStorage.saveMembers(rec);
  try { window.dispatchEvent(new CustomEvent('DATA_CHANGED', { detail:'members' })); } catch {}
  return rec;
}

export default gymStorage;