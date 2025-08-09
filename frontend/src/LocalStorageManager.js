class LocalStorageManager {
  constructor() {
    this.dbName = 'alphalete-mobile-app';
    this.version = 7;
    this.isOnline = navigator.onLine;
    this.syncQueue = [];
    
    // Listen for online/offline events
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.syncOfflineData();
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  // Consistent backend URL helper - matches App.js getBackendUrl()
  getBackendUrl() {
    const envUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
    if (envUrl && envUrl.trim() !== '') {
      return envUrl;
    }
    return window.location.origin;
  }

  async initDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);
      
      request.onerror = () => {
        console.error('Failed to open IndexedDB');
        reject(request.error);
      };
      
      request.onsuccess = (event) => {
        const db = event.target.result;
        resolve(db);
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create clients store
        if (!db.objectStoreNames.contains('clients')) {
          const clientsStore = db.createObjectStore('clients', { keyPath: 'id' });
          clientsStore.createIndex('email', 'email', { unique: true });
        }
        
        // Create sync queue store
        if (!db.objectStoreNames.contains('syncQueue')) {
          db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
        }
        
        // Create settings store
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'id' });
        }
      };
    });
  }

  async performDBOperation(storeName, operation, data = null) {
    try {
      const db = await this.initDB();
      const transaction = db.transaction([storeName], operation === 'getAll' || operation === 'get' ? 'readonly' : 'readwrite');
      const store = transaction.objectStore(storeName);
      
      let request;
      switch (operation) {
        case 'getAll':
          request = store.getAll();
          break;
        case 'get':
          request = store.get(data);
          break;
        case 'put':
          request = store.put(data);
          break;
        case 'delete':
          request = store.delete(data);
          break;
        case 'clear':
          request = store.clear();
          break;
        default:
          throw new Error(`Unknown operation: ${operation}`);
      }
      
      return new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Database operation failed:', error);
      throw error;
    }
  }

  // Client management methods
  async getClients() {
    try {
      // First try to fetch from backend if online
      if (this.isOnline) {
        try {
          const backendUrl = this.getBackendUrl();
          console.log("🔍 LocalStorageManager: Fetching clients from backend...", backendUrl);
          
          const response = await fetch(`${backendUrl}/api/clients`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            timeout: 5000
          });
          
          if (response.ok) {
            const clients = await response.json();
            console.log("✅ LocalStorageManager: Fetched", clients.length, "clients from backend");
            
            // Update local storage with fresh data
            await this.performDBOperation('clients', 'clear');
            for (const client of clients) {
              await this.performDBOperation('clients', 'put', client);
            }
            
            return clients;
          } else {
            console.warn("⚠️ Backend fetch failed, falling back to local storage");
          }
        } catch (error) {
          console.warn("⚠️ Backend error, falling back to local storage:", error.message);
        }
      }
      
      // Fallback to local storage
      console.log("📱 LocalStorageManager: Using local storage data");
      const localClients = await this.performDBOperation('clients', 'getAll');
      return localClients || [];
      
    } catch (error) {
      console.error("❌ LocalStorageManager: Error getting clients:", error);
      return [];
    }
  }

  async addClient(clientData) {
    try {
      console.log("🔍 LocalStorageManager: Adding client:", clientData.name);
      
      // Generate ID if not provided
      if (!clientData.id) {
        clientData.id = this.generateUUID();
      }
      
      // Set timestamps
      const now = new Date().toISOString();
      clientData.created_at = clientData.created_at || now;
      clientData.updated_at = now;
      
      // Try backend first if online
      if (this.isOnline) {
        try {
          const backendUrl = this.getBackendUrl();
          console.log("🔍 LocalStorageManager: Adding client to backend...", backendUrl);
          
          const response = await fetch(`${backendUrl}/api/clients`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clientData)
          });
          
          if (response.ok) {
            const backendClient = await response.json();
            console.log("✅ LocalStorageManager: Client added to backend successfully");
            
            // Store the backend response (with any server-generated fields)
            await this.performDBOperation('clients', 'put', backendClient);
            return { data: backendClient, success: true, offline: false, synced: true };
          } else {
            const errorText = await response.text();
            console.error("❌ LocalStorageManager: Backend add failed:", response.status, errorText);
            
            // Check if this is a business logic error (400-499) vs server error (500+)
            if (response.status >= 400 && response.status < 500) {
              // Business logic error (duplicate email, validation, etc.) - don't store locally
              let errorMessage = "Unable to add member";
              try {
                const errorData = JSON.parse(errorText);
                if (errorData.detail) {
                  errorMessage = errorData.detail;
                }
              } catch (e) {
                // If we can't parse the error, use the raw text
                errorMessage = errorText || errorMessage;
              }
              return { data: null, success: false, error: errorMessage };
            }
            // Server error (500+) - continue to local storage fallback below
          }
        } catch (error) {
          console.error("❌ LocalStorageManager: Network error:", error);
        }
      }
      
      // Add to local storage (either offline or backend failed)
      await this.performDBOperation('clients', 'put', clientData);
      console.log("✅ LocalStorageManager: Client stored locally");
      
      // Add to sync queue if online but backend failed
      if (this.isOnline) {
        this.addToSyncQueue('CREATE_CLIENT', clientData);
        // Return success true - data is safely stored locally and will sync when backend is available
        console.log(`⚠️ Backend temporarily unavailable - ${clientData.name} stored locally and queued for sync`);
        return { data: clientData, success: true, offline: false, synced: false, message: 'Member added successfully! Data will sync when connection is restored.' };
      }
      
      // Offline mode
      this.addToSyncQueue('CREATE_CLIENT', clientData);
      return { data: clientData, success: true, offline: true, synced: false };
      
    } catch (error) {
      console.error("❌ LocalStorageManager: Error adding client:", error);
      return { data: null, success: false, error: error.message };
    }
  }

  async updateClient(clientId, updateData) {
    try {
      // Try backend first if online
      if (this.isOnline) {
        try {
          const backendUrl = this.getBackendUrl();
          const response = await fetch(`${backendUrl}/api/clients/${clientId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
          });
          
          if (response.ok) {
            const updatedClient = await response.json();
            await this.performDBOperation('clients', 'put', updatedClient);
            return { data: updatedClient, success: true, offline: false };
          }
        } catch (error) {
          console.error("Backend update failed:", error);
        }
      }
      
      // Fallback to local storage
      const existingClient = await this.performDBOperation('clients', 'get', clientId);
      if (existingClient) {
        const updatedClient = { ...existingClient, ...updateData, updated_at: new Date().toISOString() };
        await this.performDBOperation('clients', 'put', updatedClient);
        this.addToSyncQueue('UPDATE_CLIENT', updatedClient);
        return { data: updatedClient, success: true, offline: !this.isOnline };
      }
      
      return { data: null, success: false, error: 'Client not found' };
    } catch (error) {
      console.error("Error updating client:", error);
      return { data: null, success: false, error: error.message };
    }
  }

  async deleteClient(clientId) {
    try {
      // Try backend first if online
      if (this.isOnline) {
        try {
          const backendUrl = this.getBackendUrl();
          const response = await fetch(`${backendUrl}/api/clients/${clientId}`, {
            method: 'DELETE'
          });
          
          if (response.ok) {
            await this.performDBOperation('clients', 'delete', clientId);
            return { success: true, offline: false };
          }
        } catch (error) {
          console.error("Backend delete failed:", error);
        }
      }
      
      // Fallback to local storage
      await this.performDBOperation('clients', 'delete', clientId);
      this.addToSyncQueue('DELETE_CLIENT', { id: clientId });
      return { success: true, offline: !this.isOnline };
    } catch (error) {
      console.error("Error deleting client:", error);
      return { success: false, error: error.message };
    }
  }

  // Sync queue management
  addToSyncQueue(operation, data) {
    const syncItem = {
      operation,
      data,
      timestamp: new Date().toISOString(),
      retries: 0
    };
    
    this.syncQueue.push(syncItem);
    this.performDBOperation('syncQueue', 'put', syncItem);
  }

  async syncOfflineData() {
    if (!this.isOnline) return;
    
    try {
      const syncItems = await this.performDBOperation('syncQueue', 'getAll');
      const backendUrl = this.getBackendUrl();
      
      for (const item of syncItems) {
        try {
          let success = false;
          
          switch (item.operation) {
            case 'CREATE_CLIENT':
              const createResponse = await fetch(`${backendUrl}/api/clients`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(item.data)
              });
              success = createResponse.ok;
              break;
              
            case 'UPDATE_CLIENT':
              const updateResponse = await fetch(`${backendUrl}/api/clients/${item.data.id}`, {
                method: 'PUT',  
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(item.data)
              });
              success = updateResponse.ok;
              break;
              
            case 'DELETE_CLIENT':
              const deleteResponse = await fetch(`${backendUrl}/api/clients/${item.data.id}`, {
                method: 'DELETE'
              });
              success = deleteResponse.ok;
              break;
          }
          
          if (success) {
            await this.performDBOperation('syncQueue', 'delete', item.id);
            console.log(`✅ Synced ${item.operation} for ${item.data.name || item.data.id}`);
          }
        } catch (error) {
          console.error(`Failed to sync ${item.operation}:`, error);
          item.retries = (item.retries || 0) + 1;
          
          // Remove items that have failed too many times
          if (item.retries > 3) {
            await this.performDBOperation('syncQueue', 'delete', item.id);
          }
        }
      }
    } catch (error) {
      console.error("Sync failed:", error);
    }
  }

  // Utility functions
  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  async clearAllData() {
    try {
      await this.performDBOperation('clients', 'clear');
      await this.performDBOperation('syncQueue', 'clear');
      this.syncQueue = [];
      console.log("✅ All local data cleared");
      return { success: true };
    } catch (error) {
      console.error("Error clearing data:", error);
      return { success: false, error: error.message };
    }
  }

  // Email functionality
  async sendPaymentReminder(clientData) {
    try {
      const backendUrl = this.getBackendUrl();
      const response = await fetch(`${backendUrl}/api/email/payment-reminder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(clientData)
      });
      
      if (response.ok) {
        return { success: true };
      } else {
        const errorText = await response.text();
        return { success: false, error: errorText };
      }
    } catch (error) {
      console.error("Error sending payment reminder:", error);
      return { success: false, error: error.message };
    }
  }

  // Payment functionality  
  async recordPayment(paymentData) {
    try {
      const backendUrl = this.getBackendUrl();
      const response = await fetch(`${backendUrl}/api/payments/record`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(paymentData)
      });
      
      if (response.ok) {
        const result = await response.json();
        return { success: true, data: result };
      } else {
        const errorText = await response.text();
        return { success: false, error: errorText };
      }
    } catch (error) {
      console.error("Error recording payment:", error);
      return { success: false, error: error.message };
    }
  }

  // Settings functionality
  async getSetting(key, defaultValue = null) {
    try {
      const settings = await this.performDBOperation('settings', 'get', key);
      return settings ? settings.value : defaultValue;
    } catch (error) {
      console.error("Error getting setting:", error);
      return defaultValue;
    }
  }

  async setSetting(key, value) {
    try {
      await this.performDBOperation('settings', 'put', { id: key, value });
      return { success: true };
    } catch (error) {
      console.error("Error setting value:", error);
      return { success: false, error: error.message };
    }
  }
}

export default LocalStorageManager;