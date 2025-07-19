// IndexedDB Storage Service for Gym Management App
// This saves all data directly on your phone

class GymStorageService {
  constructor() {
    this.dbName = 'AlphaleteGymDB';
    this.version = 1;
    this.db = null;
  }

  // Initialize the database
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
        
        // Create object stores (tables)
        if (!db.objectStoreNames.contains('members')) {
          const membersStore = db.createObjectStore('members', { keyPath: 'id' });
          membersStore.createIndex('name', 'name', { unique: false });
          membersStore.createIndex('email', 'email', { unique: false });
          membersStore.createIndex('status', 'status', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('payments')) {
          db.createObjectStore('payments', { keyPath: 'id' });
        }
        
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'key' });
        }
        
        if (!db.objectStoreNames.contains('status_checks')) {
          db.createObjectStore('status_checks', { keyPath: 'id' });
        }
      };
    });
  }

  // Generic method to save data
  async saveData(storeName, data) {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.put(data);
      
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // Generic method to get all data from a store
  async getAllData(storeName) {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.getAll();
      
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  }

  // Generic method to delete data
  async deleteData(storeName, id) {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.delete(id);
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  // Specific methods for gym members
  async saveMembers(members) {
    if (!Array.isArray(members)) members = [members];
    
    const promises = members.map(member => this.saveData('members', member));
    return Promise.all(promises);
  }

  async getAllMembers() {
    try {
      return await this.getAllData('members');
    } catch (error) {
      console.error('Error loading members:', error);
      return [];
    }
  }

  async deleteMember(id) {
    return this.deleteData('members', id);
  }

  // Specific methods for payments
  async savePayment(payment) {
    return this.saveData('payments', payment);
  }

  async getAllPayments() {
    try {
      return await this.getAllData('payments');
    } catch (error) {
      console.error('Error loading payments:', error);
      return [];
    }
  }

  // Specific methods for status checks
  async saveStatusCheck(statusCheck) {
    return this.saveData('status_checks', statusCheck);
  }

  async getAllStatusChecks() {
    try {
      return await this.getAllData('status_checks');
    } catch (error) {
      console.error('Error loading status checks:', error);
      return [];
    }
  }

  // Settings management
  async saveSetting(key, value) {
    return this.saveData('settings', { key, value });
  }

  async getSetting(key, defaultValue = null) {
    try {
      if (!this.db) await this.init();
      
      return new Promise((resolve, reject) => {
        const transaction = this.db.transaction(['settings'], 'readonly');
        const store = transaction.objectStore('settings');
        const request = store.get(key);
        
        request.onsuccess = () => {
          const result = request.result;
          resolve(result ? result.value : defaultValue);
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Error loading setting:', error);
      return defaultValue;
    }
  }

  // Backup functionality
  async exportData() {
    const data = {
      members: await this.getAllMembers(),
      payments: await this.getAllPayments(),
      statusChecks: await this.getAllStatusChecks(),
      timestamp: new Date().toISOString()
    };
    
    return JSON.stringify(data, null, 2);
  }

  // Import functionality
  async importData(jsonData) {
    try {
      const data = JSON.parse(jsonData);
      
      if (data.members) {
        for (const member of data.members) {
          await this.saveData('members', member);
        }
      }
      
      if (data.payments) {
        for (const payment of data.payments) {
          await this.saveData('payments', payment);
        }
      }
      
      if (data.statusChecks) {
        for (const statusCheck of data.statusChecks) {
          await this.saveData('status_checks', statusCheck);
        }
      }
      
      return true;
    } catch (error) {
      console.error('Error importing data:', error);
      return false;
    }
  }

  // Clear all data (for testing or reset)
  async clearAllData() {
    const stores = ['members', 'payments', 'status_checks', 'settings'];
    
    for (const storeName of stores) {
      if (!this.db) await this.init();
      
      await new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.clear();
        
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
    }
  }

  // Get storage usage statistics
  async getStorageStats() {
    const members = await this.getAllMembers();
    const payments = await this.getAllPayments();
    const statusChecks = await this.getAllStatusChecks();
    
    return {
      members: members.length,
      payments: payments.length,
      statusChecks: statusChecks.length,
      totalRecords: members.length + payments.length + statusChecks.length
    };
  }
}

// Create and export a single instance
const gymStorage = new GymStorageService();

export default gymStorage;