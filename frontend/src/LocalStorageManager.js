// Local Storage Manager for Offline PWA
class LocalStorageManager {
  constructor() {
    this.dbName = 'AlphaleteDB';
    this.version = 1;
    this.db = null;
    this.isOnline = navigator.onLine;
    this.syncQueue = [];
    
    // Listen for online/offline events
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.processSyncQueue();
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
    
    this.initDB();
  }

  // Initialize IndexedDB
  async initDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create clients store
        if (!db.objectStoreNames.contains('clients')) {
          const clientStore = db.createObjectStore('clients', { keyPath: 'id' });
          clientStore.createIndex('email', 'email', { unique: true });
          clientStore.createIndex('name', 'name', { unique: false });
          clientStore.createIndex('membership_type', 'membership_type', { unique: false });
        }
        
        // Create membership types store
        if (!db.objectStoreNames.contains('membershipTypes')) {
          const membershipStore = db.createObjectStore('membershipTypes', { keyPath: 'id' });
          membershipStore.createIndex('name', 'name', { unique: true });
        }
        
        // Create sync queue store
        if (!db.objectStoreNames.contains('syncQueue')) {
          db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
        }
        
        // Create app settings store
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'key' });
        }
      };
    });
  }

  // Generic method to perform database operations
  async performDBOperation(storeName, operation, data = null) {
    if (!this.db) await this.initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([storeName], operation === 'get' || operation === 'getAll' ? 'readonly' : 'readwrite');
      const store = transaction.objectStore(storeName);
      
      let request;
      
      switch (operation) {
        case 'add':
          request = store.add(data);
          break;
        case 'put':
          request = store.put(data);
          break;
        case 'get':
          request = store.get(data);
          break;
        case 'getAll':
          request = store.getAll();
          break;
        case 'delete':
          request = store.delete(data);
          break;
        default:
          reject(new Error('Invalid operation'));
          return;
      }
      
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // Client management methods
  async getClients() {
    try {
      const clients = await this.performDBOperation('clients', 'getAll');
      return { data: clients, offline: !this.isOnline };
    } catch (error) {
      console.error('Error getting clients from local storage:', error);
      return { data: [], offline: true, error: error.message };
    }
  }

  async addClient(clientData) {
    try {
      // Generate ID if not provided
      if (!clientData.id) {
        clientData.id = this.generateUUID();
      }
      
      // Set default status if not provided
      if (!clientData.status) {
        clientData.status = "Active";
      }
      
      // Add timestamps
      clientData.created_at = new Date().toISOString();
      clientData.updated_at = new Date().toISOString();
      
      // Calculate next payment date (30 days from start date)
      if (clientData.start_date && !clientData.next_payment_date) {
        const startDate = new Date(clientData.start_date);
        const nextPaymentDate = new Date(startDate);
        nextPaymentDate.setDate(startDate.getDate() + 30);
        clientData.next_payment_date = nextPaymentDate.toISOString().split('T')[0];
      }
      
      console.log("🔍 Debug - Adding client with data:", clientData);
      
      await this.performDBOperation('clients', 'add', clientData);
      
      // Add to sync queue if online
      if (this.isOnline) {
        this.addToSyncQueue('CREATE_CLIENT', clientData);
      }
      
      return { data: clientData, success: true, offline: !this.isOnline };
    } catch (error) {
      console.error('Error adding client to local storage:', error);
      throw error;
    }
  }

  async updateClient(clientId, updateData) {
    try {
      const existingClient = await this.performDBOperation('clients', 'get', clientId);
      if (!existingClient) {
        throw new Error('Client not found');
      }
      
      const updatedClient = {
        ...existingClient,
        ...updateData,
        updated_at: new Date().toISOString()
      };
      
      // Recalculate next payment date if start_date changed
      if (updateData.start_date) {
        const startDate = new Date(updateData.start_date);
        const nextPaymentDate = new Date(startDate);
        nextPaymentDate.setDate(startDate.getDate() + 30);
        updatedClient.next_payment_date = nextPaymentDate.toISOString().split('T')[0];
      }
      
      await this.performDBOperation('clients', 'put', updatedClient);
      
      // Add to sync queue if online
      if (this.isOnline) {
        this.addToSyncQueue('UPDATE_CLIENT', updatedClient);
      }
      
      return { data: updatedClient, success: true, offline: !this.isOnline };
    } catch (error) {
      console.error('Error updating client in local storage:', error);
      throw error;
    }
  }

  async deleteClient(clientId) {
    try {
      await this.performDBOperation('clients', 'delete', clientId);
      
      // Add to sync queue if online
      if (this.isOnline) {
        this.addToSyncQueue('DELETE_CLIENT', { id: clientId });
      }
      
      return { success: true, offline: !this.isOnline };
    } catch (error) {
      console.error('Error deleting client from local storage:', error);
      throw error;
    }
  }

  // Membership Types management methods
  async getMembershipTypes() {
    try {
      const types = await this.performDBOperation('membershipTypes', 'getAll');
      
      // If no types exist, seed default ones
      if (types.length === 0) {
        await this.seedDefaultMembershipTypes();
        const seededTypes = await this.performDBOperation('membershipTypes', 'getAll');
        return { data: seededTypes, offline: !this.isOnline };
      }
      
      return { data: types, offline: !this.isOnline };
    } catch (error) {
      console.error('Error getting membership types from local storage:', error);
      return { data: [], offline: true, error: error.message };
    }
  }

  async addMembershipType(typeData) {
    try {
      if (!typeData.id) {
        typeData.id = this.generateUUID();
      }
      
      typeData.created_at = new Date().toISOString();
      typeData.updated_at = new Date().toISOString();
      typeData.is_active = true;
      
      await this.performDBOperation('membershipTypes', 'add', typeData);
      
      // Add to sync queue if online
      if (this.isOnline) {
        this.addToSyncQueue('CREATE_MEMBERSHIP_TYPE', typeData);
      }
      
      return { data: typeData, success: true, offline: !this.isOnline };
    } catch (error) {
      console.error('Error adding membership type to local storage:', error);
      throw error;
    }
  }

  async updateMembershipType(typeId, updateData) {
    try {
      const existingType = await this.performDBOperation('membershipTypes', 'get', typeId);
      if (!existingType) {
        throw new Error('Membership type not found');
      }
      
      const updatedType = {
        ...existingType,
        ...updateData,
        updated_at: new Date().toISOString()
      };
      
      await this.performDBOperation('membershipTypes', 'put', updatedType);
      
      // Add to sync queue if online
      if (this.isOnline) {
        this.addToSyncQueue('UPDATE_MEMBERSHIP_TYPE', updatedType);
      }
      
      return { data: updatedType, success: true, offline: !this.isOnline };
    } catch (error) {
      console.error('Error updating membership type in local storage:', error);
      throw error;
    }
  }

  async deleteMembershipType(typeId) {
    try {
      // Soft delete - mark as inactive
      const existingType = await this.performDBOperation('membershipTypes', 'get', typeId);
      if (!existingType) {
        throw new Error('Membership type not found');
      }
      
      const updatedType = {
        ...existingType,
        is_active: false,
        updated_at: new Date().toISOString()
      };
      
      await this.performDBOperation('membershipTypes', 'put', updatedType);
      
      // Add to sync queue if online
      if (this.isOnline) {
        this.addToSyncQueue('DELETE_MEMBERSHIP_TYPE', { id: typeId });
      }
      
      return { success: true, offline: !this.isOnline };
    } catch (error) {
      console.error('Error deleting membership type from local storage:', error);
      throw error;
    }
  }

  // Seed default membership types
  async seedDefaultMembershipTypes() {
    const defaultTypes = [
      {
        id: this.generateUUID(),
        name: "Standard",
        monthly_fee: 50.00,
        description: "Basic gym access with equipment usage",
        features: ["Equipment Access", "Locker Room", "Basic Support"],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: this.generateUUID(),
        name: "Premium",
        monthly_fee: 75.00,
        description: "Gym access plus group fitness classes",
        features: ["All Standard Features", "Group Classes", "Extended Hours", "Guest Passes"],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: this.generateUUID(),
        name: "Elite",
        monthly_fee: 100.00,
        description: "Premium features plus personal training sessions",
        features: ["All Premium Features", "Personal Training Sessions", "Nutrition Consultation", "Priority Booking"],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: this.generateUUID(),
        name: "VIP",
        monthly_fee: 150.00,
        description: "All-inclusive membership with premium amenities",
        features: ["All Elite Features", "VIP Lounge Access", "Massage Therapy", "Meal Planning", "24/7 Support"],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ];

    for (const type of defaultTypes) {
      await this.performDBOperation('membershipTypes', 'add', type);
    }
  }

  // Sync queue management
  async addToSyncQueue(action, data) {
    const syncItem = {
      action,
      data,
      timestamp: new Date().toISOString(),
      status: 'pending'
    };
    
    await this.performDBOperation('syncQueue', 'add', syncItem);
  }

  async processSyncQueue() {
    if (!this.isOnline) return;
    
    try {
      const queue = await this.performDBOperation('syncQueue', 'getAll');
      const pendingItems = queue.filter(item => item.status === 'pending');
      
      for (const item of pendingItems) {
        try {
          await this.syncItem(item);
          
          // Mark as completed
          item.status = 'completed';
          item.synced_at = new Date().toISOString();
          await this.performDBOperation('syncQueue', 'put', item);
          
        } catch (error) {
          console.error('Error syncing item:', item, error);
          
          // Mark as failed
          item.status = 'failed';
          item.error = error.message;
          await this.performDBOperation('syncQueue', 'put', item);
        }
      }
      
      console.log('Sync queue processed');
    } catch (error) {
      console.error('Error processing sync queue:', error);
    }
  }

  async syncItem(item) {
    // This would sync with your server when online
    // For now, just log the sync action
    console.log('Syncing item:', item.action, item.data);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // In a real implementation, you would make API calls here
    // based on the item.action (CREATE_CLIENT, UPDATE_CLIENT, etc.)
  }

  // Utility methods
  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  // App settings
  async getSetting(key, defaultValue = null) {
    try {
      const setting = await this.performDBOperation('settings', 'get', key);
      return setting ? setting.value : defaultValue;
    } catch (error) {
      return defaultValue;
    }
  }

  async setSetting(key, value) {
    const setting = { key, value, updated_at: new Date().toISOString() };
    await this.performDBOperation('settings', 'put', setting);
  }

  // Get connection status
  getConnectionStatus() {
    const isOnline = navigator.onLine && window.navigator.onLine;
    return {
      online: isOnline,
      message: isOnline ? 'Connected - All features available' : 'Offline - Data stored locally'
    };
  }
}

// Export for use in React components
window.LocalStorageManager = LocalStorageManager;
export default LocalStorageManager;