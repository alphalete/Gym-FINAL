import { currentCycleWindow } from "./billing";

class GymStorage {
  constructor() {
    this.dbName = 'GymDB';
    this.version = 3; // Bumped version for plans store
    this.db = null;
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        const ensureStore = (name, options) => { 
          if (!db.objectStoreNames.contains(name)) {
            return db.createObjectStore(name, options);
          }
          return null;
        };

        ensureStore('members', { keyPath: 'id' });
        ensureStore('payments', { keyPath: 'id' });
        ensureStore('statusChecks', { keyPath: 'id' });
        ensureStore('audit', { keyPath: 'id' });
        
        // Create or update plans store with active index
        let plansStore;
        if (!db.objectStoreNames.contains('plans')) {
          plansStore = db.createObjectStore('plans', { keyPath: 'id' });
        } else {
          plansStore = event.target.transaction.objectStore('plans');
        }
        if (plansStore && !plansStore.indexNames.contains('active')) {
          plansStore.createIndex('active', 'active', { unique: false });
        }
      };
    });
  }

  async ensureDB() {
    if (!this.db) {
      await this.init();
    }
    return this.db;
  }

  async saveData(storeName, data) {
    const db = await this.ensureDB();
    const transaction = db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    
    if (Array.isArray(data)) {
      for (const item of data) {
        await store.put(item);
      }
    } else {
      await store.put(data);
    }
    
    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => resolve(data);
      transaction.onerror = () => reject(transaction.error);
    });
  }

  async getData(storeName, key = null) {
    const db = await this.ensureDB();
    const transaction = db.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);
    
    const request = key ? store.get(key) : store.getAll();
    
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // Members
  async saveMembers(members) {
    const result = await this.saveData('members', members);
    await this.saveAudit({ 
      type: 'member_save', 
      count: Array.isArray(members) ? members.length : 1 
    }).catch(() => {}); // non-blocking
    return result;
  }

  async getAllMembers() {
    return this.getData('members');
  }

  async getMember(id) {
    return this.getData('members', id);
  }

  // Payments
  async savePayment(payment, client) {
    // Add cycle information if client is provided
    if (client && client.joinDate) {
      const { start, end } = currentCycleWindow(client.joinDate, new Date(), 30);
      payment = {
        id: crypto?.randomUUID ? crypto.randomUUID() : String(Date.now()),
        clientId: client.id,
        amount: payment.amount,
        paidAt: new Date().toISOString(),
        cycleStart: start ? start.toISOString().slice(0,10) : null,
        cycleEnd: end ? end.toISOString().slice(0,10) : null,
        ...payment // preserve any existing properties
      };
    }
    
    const result = await this.saveData('payments', payment);
    await this.saveAudit({ 
      type: 'payment_save', 
      amount: payment?.amount, 
      clientId: payment?.clientId 
    }).catch(() => {}); // non-blocking
    return result;
  }

  async getAllPayments() {
    return this.getData('payments');
  }

  async getPayment(id) {
    return this.getData('payments', id);
  }

  // Status Checks
  async saveStatusCheck(statusCheck) {
    return this.saveData('statusChecks', statusCheck);
  }

  async getAllStatusChecks() {
    return this.getData('statusChecks');
  }

  // Audit
  async saveAudit(event) {
    return this.saveData('audit', { 
      id: Date.now().toString(), 
      ts: new Date().toISOString(), 
      ...event 
    });
  }

  async getAllAuditEvents() {
    return this.getData('audit');
  }

  // Plans Store Methods
  async listPlans(opts = {}) {
    await this.init();
    const { active } = opts;
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['plans'], 'readonly');
      const store = tx.objectStore('plans');

      if (typeof active === 'boolean' && store.indexNames && store.indexNames.contains('active')) {
        const idx = store.index('active');
        const req = idx.openCursor(IDBKeyRange.only(active));
        const out = [];
        req.onsuccess = (e) => { const c = e.target.result; if (c) { out.push(c.value); c.continue(); } else resolve(out); };
        req.onerror = () => reject(req.error);
        return;
      }

      const out = [];
      const req = store.openCursor();
      req.onsuccess = (e) => { const c = e.target.result; if (c) { out.push(c.value); c.continue(); } else resolve(out); };
      req.onerror = () => reject(req.error);
    });
  }

  async upsertPlan(plan) {
    await this.init();
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['plans'], 'readwrite');
      tx.objectStore('plans').put(plan);
      tx.oncomplete = () => resolve(true);
      tx.onerror = () => reject(tx.error);
    });
  }

  async deletePlan(id) {
    await this.init();
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['plans'], 'readwrite');
      tx.objectStore('plans').delete(id);
      tx.oncomplete = () => resolve(true);
      tx.onerror = () => reject(tx.error);
    });
  }

  async migratePlansFromSettingsIfNeeded() {
    if (this.__plansMigrated) return;
    this.__plansMigrated = true;
    try {
      const legacy = await this.getSetting('membershipPlans', null);
      if (legacy && Array.isArray(legacy) && legacy.length) {
        const existing = await this.listPlans();
        const ids = new Set(existing.map(p => p.id));
        for (const p of legacy) {
          const id = p.id || crypto.randomUUID();
          if (!ids.has(id)) await this.upsertPlan({ ...p, id });
        }
        await this.saveSetting('membershipPlans', []); // clear old blob
        console.log('Plans migrated from settings → plans store');
      }
    } catch (e) {
      console.warn('Plans migration skipped:', e);
    }
  }
}

const gymStorage = new GymStorage();

// Dedicated Plans Store Functions with Active Index
export async function getDB() {
  await gymStorage.ensureDB();
  return gymStorage.db;
}

export async function listPlans(opts = {}) {
  const { active } = opts;
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(['plans'], 'readonly');
    const store = tx.objectStore('plans');
    if (typeof active === 'boolean' && store.indexNames.contains('active')) {
      const idx = store.index('active');
      const req = idx.openCursor(IDBKeyRange.only(active));
      const out = [];
      req.onsuccess = e => { 
        const c = e.target.result; 
        if (c) { 
          out.push(c.value); 
          c.continue(); 
        } else { 
          resolve(out); 
        } 
      };
      req.onerror = () => reject(req.error);
      return;
    }
    const out = [];
    const req = store.openCursor();
    req.onsuccess = e => { 
      const c = e.target.result; 
      if (c) { 
        out.push(c.value); 
        c.continue(); 
      } else { 
        resolve(out); 
      } 
    };
    req.onerror = () => reject(req.error);
  });
}

export async function upsertPlan(plan) {
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(['plans'], 'readwrite');
    const store = tx.objectStore('plans');
    const req = store.put(plan);
    req.onsuccess = () => resolve(plan);
    req.onerror = () => reject(req.error);
  });
}

export async function deletePlan(id) {
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(['plans'], 'readwrite');
    const store = tx.objectStore('plans');
    const req = store.delete(id);
    req.onsuccess = () => resolve(true);
    req.onerror = () => reject(req.error);
  });
}

// Settings Helper Functions
export async function getSetting(key, defaultValue = null) {
  return gymStorage.getSetting(key, defaultValue);
}

export async function saveSetting(key, value) {
  return gymStorage.saveSetting(key, value);
}

// Migration Function
export async function migratePlansFromSettingsIfNeeded() {
  if (migratePlansFromSettingsIfNeeded.done) return;
  migratePlansFromSettingsIfNeeded.done = true;
  try {
    const legacy = await getSetting('membershipPlans', null);
    if (legacy && Array.isArray(legacy) && legacy.length) {
      const existing = await listPlans();
      const ids = new Set(existing.map(p => p.id));
      for (const p of legacy) {
        const id = p.id || crypto.randomUUID();
        if (!ids.has(id)) {
          await upsertPlan({ 
            ...p, 
            id,
            active: p.active !== undefined ? p.active : true // Default to active
          });
        }
      }
      await saveSetting('membershipPlans', []);
      console.log('Plans migrated from settings → plans store');
    }
  } catch (e) {
    console.warn('Plans migration skipped:', e);
  }
}

// Generic helper to get all data from a store
export async function getAllData(storeName) {
  await gymStorage.init?.();
  return new Promise((resolve, reject) => {
    try {
      const tx = gymStorage.db.transaction([storeName], 'readonly');
      const store = tx.objectStore(storeName);
      const out = [];
      const req = store.openCursor();
      req.onsuccess = (e) => { 
        const c = e.target.result; 
        if (c) { 
          out.push(c.value); 
          c.continue(); 
        } else { 
          resolve(out); 
        } 
      };
      req.onerror = () => reject(req.error);
    } catch (e) { 
      resolve([]); 
    }
  });
}

// Generic getter with simplified name
export async function getAll(storeName) {
  if (typeof gymStorage?.init === 'function') await gymStorage.init();
  return new Promise((resolve) => {
    try {
      const tx = gymStorage.db.transaction([storeName], 'readonly');
      const store = tx.objectStore(storeName);
      const out = [];
      const req = store.openCursor();
      req.onsuccess = (e) => { const c = e.target.result; if (c) { out.push(c.value); c.continue(); } else resolve(out); };
      req.onerror = () => resolve([]);
    } catch (_e) { resolve([]); }
  });
}

// Signal data changes to refresh dashboard
export function signalDataChanged(what='') {
  try {
    localStorage.setItem('dataChangedAt', String(Date.now()));
    window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail: what }));
  } catch {}
}

export default gymStorage;