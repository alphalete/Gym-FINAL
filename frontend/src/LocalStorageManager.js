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
      console.log("🔍 LocalStorageManager: Initializing IndexedDB...");
      const request = indexedDB.open(this.dbName, this.version);
      
      request.onerror = () => {
        console.error("🔍 LocalStorageManager: IndexedDB open error:", request.error);
        reject(request.error);
      };
      
      request.onsuccess = () => {
        this.db = request.result;
        console.log("🔍 LocalStorageManager: IndexedDB opened successfully");
        resolve(this.db);
      };
      
      request.onupgradeneeded = (event) => {
        console.log("🔍 LocalStorageManager: IndexedDB upgrade needed");
        const db = event.target.result;
        
        // Create clients store
        if (!db.objectStoreNames.contains('clients')) {
          const clientStore = db.createObjectStore('clients', { keyPath: 'id' });
          clientStore.createIndex('email', 'email', { unique: true });
          clientStore.createIndex('name', 'name', { unique: false });
          clientStore.createIndex('membership_type', 'membership_type', { unique: false });
          console.log("🔍 LocalStorageManager: Created clients store");
        }
        
        // Create membership types store
        if (!db.objectStoreNames.contains('membershipTypes')) {
          const membershipStore = db.createObjectStore('membershipTypes', { keyPath: 'id' });
          membershipStore.createIndex('name', 'name', { unique: true });
          console.log("🔍 LocalStorageManager: Created membershipTypes store");
        }
        
        // Create sync queue store
        if (!db.objectStoreNames.contains('syncQueue')) {
          db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
          console.log("🔍 LocalStorageManager: Created syncQueue store");
        }
        
        // Create app settings store
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'key' });
          console.log("🔍 LocalStorageManager: Created settings store");
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
      // First try to fetch from backend if online
      if (this.isOnline) {
        try {
          const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
          if (backendUrl) {
            console.log("🔍 LocalStorageManager: Fetching clients from backend...", backendUrl);
            const response = await fetch(`${backendUrl}/api/clients`, {
              method: 'GET',
              headers: { 'Content-Type': 'application/json' },
              timeout: 10000
            });
            
            if (response.ok) {
              const backendClients = await response.json();
              console.log(`✅ LocalStorageManager: Fetched ${backendClients.length} clients from backend`);
              
              // Store backend data in local storage for offline access
              for (const client of backendClients) {
                try {
                  await this.performDBOperation('clients', 'put', client);
                } catch (error) {
                  console.warn(`Warning: Could not store client ${client.name} locally:`, error);
                }
              }
              
              return { data: backendClients, offline: false };
            } else {
              console.warn("⚠️ LocalStorageManager: Backend fetch failed, status:", response.status, "falling back to local storage");
            }
          } else {
            console.warn("⚠️ LocalStorageManager: No backend URL configured, using local storage only");
          }
        } catch (error) {
          console.warn("⚠️ LocalStorageManager: Backend error, falling back to local storage:", error);
        }
      } else {
        console.log("📱 LocalStorageManager: Offline mode, using local storage");
      }
      
      // Fallback to local storage (offline mode or backend unavailable)
      console.log("📱 LocalStorageManager: Using local storage for clients");
      const localClients = await this.performDBOperation('clients', 'getAll');
      console.log(`📱 LocalStorageManager: Found ${localClients.length} clients in local storage`);
      return { data: localClients, offline: true };
      
    } catch (error) {
      console.error('Error getting clients:', error);
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
      
      // Calculate billing period dates (30 days from start date)
      if (clientData.start_date && !clientData.next_payment_date) {
        const startDate = new Date(clientData.start_date);
        const nextPaymentDate = new Date(startDate);
        nextPaymentDate.setDate(startDate.getDate() + 30);
        
        // Set initial billing period
        clientData.next_payment_date = nextPaymentDate.toISOString().split('T')[0];
        clientData.current_period_start = startDate.toISOString().split('T')[0];
        clientData.current_period_end = nextPaymentDate.toISOString().split('T')[0];
      }
      
      console.log("🔍 Debug - Adding client with data:", clientData);
      
      // Try to add to backend first if online
      if (this.isOnline) {
        try {
          const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
          if (backendUrl) {
            console.log("🔍 LocalStorageManager: Adding client to backend first...");
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
              return { data: backendClient, success: true, offline: false };
            } else {
              console.warn("⚠️ LocalStorageManager: Backend add failed, storing locally for sync later");
            }
          }
        } catch (error) {
          console.warn("⚠️ LocalStorageManager: Backend error, storing locally for sync later:", error);
        }
      }
      
      // Add to local storage (either offline or backend failed)
      await this.performDBOperation('clients', 'add', clientData);
      
      // Add to sync queue if online but backend failed
      if (this.isOnline) {
        this.addToSyncQueue('CREATE_CLIENT', clientData);
      }
      
      return { data: clientData, success: true, offline: !this.isOnline };
    } catch (error) {
      console.error('Error adding client:', error);
      throw error;
    }
  }

  // Force refresh data from backend
  async forceRefreshClients() {
    try {
      console.log("🔄 LocalStorageManager: Force refreshing clients from backend...");
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      if (!backendUrl) {
        console.warn("⚠️ No backend URL configured for force refresh");
        return await this.getClients();
      }
      
      const response = await fetch(`${backendUrl}/api/clients`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-cache' // Force bypass cache
      });
      
      if (response.ok) {
        const backendClients = await response.json();
        console.log(`✅ Force refresh: Fetched ${backendClients.length} clients from backend`);
        
        // Clear local storage and repopulate with fresh backend data
        const transaction = this.db.transaction(['clients'], 'readwrite');
        const store = transaction.objectStore('clients');
        await store.clear();
        
        // Add all fresh data
        for (const client of backendClients) {
          await store.put(client);
        }
        
        console.log("✅ Local storage refreshed with backend data");
        return { data: backendClients, offline: false, refreshed: true };
      } else {
        console.warn("⚠️ Force refresh failed, using existing local data");
        return await this.getClients();
      }
    } catch (error) {
      console.error("❌ Force refresh error:", error);
      return await this.getClients();
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
    console.log('🔄 Syncing item with backend:', item.action, item.data);
    
    const backendUrl = process.env.REACT_APP_BACKEND_URL;
    
    if (!backendUrl) {
      throw new Error('Backend URL not configured. Please set REACT_APP_BACKEND_URL environment variable.');
    }
    
    try {
      switch (item.action) {
        case 'CREATE_CLIENT':
          console.log('🔄 Creating client in backend:', item.data.name);
          const createResponse = await fetch(`${backendUrl}/api/clients`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: item.data.name,
              email: item.data.email,
              phone: item.data.phone || null,
              membership_type: item.data.membership_type,
              monthly_fee: item.data.monthly_fee,
              start_date: item.data.start_date
            })
          });
          
          if (!createResponse.ok) {
            const errorText = await createResponse.text();
            throw new Error(`Failed to create client: ${createResponse.status} - ${errorText}`);
          }
          
          const createdClient = await createResponse.json();
          console.log('✅ Client created in backend:', createdClient.name);
          break;
          
        case 'UPDATE_CLIENT':
          console.log('🔄 Updating client in backend:', item.data.name);
          const updateResponse = await fetch(`${backendUrl}/api/clients/${item.data.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: item.data.name,
              email: item.data.email,
              phone: item.data.phone,
              membership_type: item.data.membership_type,
              monthly_fee: item.data.monthly_fee,
              start_date: item.data.start_date,
              status: item.data.status
            })
          });
          
          if (!updateResponse.ok) {
            const errorText = await updateResponse.text();
            throw new Error(`Failed to update client: ${updateResponse.status} - ${errorText}`);
          }
          
          const updatedClient = await updateResponse.json();
          console.log('✅ Client updated in backend:', updatedClient.name);
          break;
          
        case 'DELETE_CLIENT':
          console.log('🔄 Deleting client from backend:', item.data.id);
          const deleteResponse = await fetch(`${backendUrl}/api/clients/${item.data.id}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
          });
          
          if (!deleteResponse.ok) {
            const errorText = await deleteResponse.text();
            throw new Error(`Failed to delete client: ${deleteResponse.status} - ${errorText}`);
          }
          
          console.log('✅ Client deleted from backend');
          break;
          
        case 'CREATE_MEMBERSHIP_TYPE':
          console.log('🔄 Creating membership type in backend:', item.data.name);
          const createTypeResponse = await fetch(`${backendUrl}/api/membership-types`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: item.data.name,
              monthly_fee: item.data.monthly_fee,
              description: item.data.description,
              features: item.data.features,
              is_active: item.data.is_active
            })
          });
          
          if (!createTypeResponse.ok) {
            const errorText = await createTypeResponse.text();
            throw new Error(`Failed to create membership type: ${createTypeResponse.status} - ${errorText}`);
          }
          
          console.log('✅ Membership type created in backend');
          break;
          
        default:
          console.log('⚠️ Unknown sync action:', item.action);
      }
      
      console.log('✅ Sync completed for:', item.action);
      
    } catch (error) {
      console.error('❌ Sync failed for:', item.action, error);
      throw error;
    }
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

  // Force sync all existing data to backend
  async forceSyncAllData() {
    console.log('🔄 Force syncing all local data to backend...');
    
    try {
      // Get all clients from local storage
      const clients = await this.performDBOperation('clients', 'getAll');
      console.log(`🔄 Found ${clients.length} clients to sync`);
      
      // Add all clients to sync queue
      for (const client of clients) {
        await this.addToSyncQueue('CREATE_CLIENT', client);
      }
      
      // Get all membership types from local storage
      const membershipTypes = await this.performDBOperation('membershipTypes', 'getAll');
      console.log(`🔄 Found ${membershipTypes.length} membership types to sync`);
      
      // Add all membership types to sync queue
      for (const type of membershipTypes) {
        await this.addToSyncQueue('CREATE_MEMBERSHIP_TYPE', type);
      }
      
      // Process the sync queue
      await this.processSyncQueue();
      
      console.log('✅ Force sync completed');
      return true;
      
    } catch (error) {
      console.error('❌ Force sync failed:', error);
      throw error;
    }
  }

  // Get connection status
  getConnectionStatus() {
    const isOnline = navigator.onLine && window.navigator.onLine;
    return {
      online: isOnline,
      message: isOnline ? 'Connected - All features available' : 'Offline - Data stored locally'
    };
  }

  // Reminder-related methods
  async getUpcomingReminders(daysAhead = 7) {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      if (!backendUrl || !this.isOnline) {
        throw new Error('Backend URL not configured or offline');
      }
      
      const response = await fetch(`${backendUrl}/api/reminders/upcoming?days_ahead=${daysAhead}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      return { data: data.upcoming_reminders, offline: false };
    } catch (error) {
      console.error('Error getting upcoming reminders:', error);
      return { data: [], offline: true, error: error.message };
    }
  }

  async getReminderHistory(clientId = null, limit = 100) {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      if (!backendUrl || !this.isOnline) {
        throw new Error('Backend URL not configured or offline');
      }
      
      const url = clientId 
        ? `${backendUrl}/api/reminders/history?client_id=${clientId}&limit=${limit}`
        : `${backendUrl}/api/reminders/history?limit=${limit}`;
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      return { data: data.reminder_history, offline: false };
    } catch (error) {
      console.error('Error getting reminder history:', error);
      return { data: [], offline: true, error: error.message };
    }
  }

  async getReminderStats() {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      if (!backendUrl || !this.isOnline) {
        throw new Error('Backend URL not configured or offline');
      }
      
      const response = await fetch(`${backendUrl}/api/reminders/stats`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      return { data, offline: false };
    } catch (error) {
      console.error('Error getting reminder stats:', error);
      return { data: null, offline: true, error: error.message };
    }
  }

  async updateClientReminderSettings(clientId, enabled) {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      if (!backendUrl || !this.isOnline) {
        throw new Error('Backend URL not configured or offline');
      }
      
      const response = await fetch(`${backendUrl}/api/clients/${clientId}/reminders`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Update local storage as well
      try {
        const localClient = await this.performDBOperation('clients', 'get', clientId);
        if (localClient) {
          localClient.auto_reminders_enabled = enabled;
          await this.performDBOperation('clients', 'put', localClient);
        }
      } catch (localError) {
        console.warn('Could not update local client reminder settings:', localError);
      }
      
      return { data, success: true, offline: false };
    } catch (error) {
      console.error('Error updating client reminder settings:', error);
      return { data: null, success: false, offline: true, error: error.message };
    }
  }

  async triggerTestReminderRun() {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      if (!backendUrl || !this.isOnline) {
        throw new Error('Backend URL not configured or offline');
      }
      
      const response = await fetch(`${backendUrl}/api/reminders/test-run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      return { data, success: true, offline: false };
    } catch (error) {
      console.error('Error triggering test reminder run:', error);
      return { data: null, success: false, offline: true, error: error.message };
    }
  }
}

// Export for use in React components
window.LocalStorageManager = LocalStorageManager;
export default LocalStorageManager;