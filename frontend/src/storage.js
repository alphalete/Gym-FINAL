import { currentCycleWindow } from "./billing";

class GymStorage {
  constructor() {
    this.dbName = 'GymDB';
    this.version = 2;
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
            db.createObjectStore(name, options);
          }
        };

        ensureStore('members', { keyPath: 'id' });
        ensureStore('payments', { keyPath: 'id' });
        ensureStore('statusChecks', { keyPath: 'id' });
        ensureStore('audit', { keyPath: 'id' });
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
  async savePayment(payment) {
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
}

const gymStorage = new GymStorage();
export default gymStorage;