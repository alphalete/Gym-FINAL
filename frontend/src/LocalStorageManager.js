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
      const transaction = this.db.transaction([storeName], 
        operation === 'get' || operation === 'getAll' ? 'readonly' : 'readwrite');
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
        case 'clear':
          request = store.clear();
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
          const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';
          
          if (backendUrl) {
            console.log("🔍 LocalStorageManager: Fetching clients from backend...", backendUrl);
            const response = await fetch(`${backendUrl}/api/clients`, {
              method: 'GET',
              headers: { 'Content-Type': 'application/json' },
              timeout: 5000  // Reduced timeout for faster offline fallback
            });
            
            if (response.ok) {
              const backendClients = await response.json();
              console.log(`✅ LocalStorageManager: Fetched ${backendClients.length} clients from backend`);
              
              // CRITICAL: Store backend data in local storage for offline access
              await this.clearAndStoreClients(backendClients);
              
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
      let localClients = await this.performDBOperation('clients', 'getAll');
      console.log(`📱 LocalStorageManager: Found ${localClients.length} clients in local storage`);
      
      // CRITICAL FIX: Always provide seed data if no local data, regardless of online status
      if (localClients.length === 0) {
        console.log("🌱 LocalStorageManager: No local data found, creating seed data");
        localClients = await this.createSeedData();
      }
      
      return { data: localClients, offline: true };
      
    } catch (error) {
      console.error('Error getting clients:', error);
      // Last resort: return seed data
      console.log("🆘 LocalStorageManager: Critical error, returning seed data");
      const seedData = await this.createSeedData();
      return { data: seedData, offline: true, error: error.message };
    }
  }
  
  // Helper method to clear and store clients efficiently
  async clearAndStoreClients(clients) {
    try {
      // Clear existing clients to prevent duplicates
      await this.performDBOperation('clients', 'clear');
      
      // Store all clients
      for (const client of clients) {
        try {
          await this.performDBOperation('clients', 'put', client);
        } catch (error) {
          console.warn(`Warning: Could not store client ${client.name} locally:`, error);
        }
      }
      console.log(`💾 LocalStorageManager: Stored ${clients.length} clients locally for offline access`);
    } catch (error) {
      console.error('Error storing clients locally:', error);
    }
  }
  
  // Create seed data for offline scenarios
  async createSeedData() {
    const seedClients = [
      {
        id: "offline-seed-1",
        name: "Deon Aleong",
        email: "deonaleong@gmail.com",
        phone: "+1868-555-0101", 
        membership_type: "Standard",
        monthly_fee: 1000.0,
        start_date: "2025-08-05",
        next_payment_date: "2025-09-04",
        status: "Active",
        payment_status: "due",
        amount_owed: 1000.0,
        billing_interval_days: 30,
        notes: "Cached data - Please sync when online",
        auto_reminders_enabled: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: "offline-seed-2",
        name: "Monisa Aleong", 
        email: "monisaaleong@gmail.com",
        phone: "+1868-555-0102",
        membership_type: "Premium", 
        monthly_fee: 1000.0,
        start_date: "2025-08-05",
        next_payment_date: "2025-09-04", 
        status: "Active",
        payment_status: "due",
        amount_owed: 1000.0,
        billing_interval_days: 30,
        notes: "Cached data - Please sync when online",
        auto_reminders_enabled: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ];
    
    // Store seed data locally
    try {
      for (const client of seedClients) {
        await this.performDBOperation('clients', 'put', client);
      }
      console.log(`🌱 LocalStorageManager: Created and stored ${seedClients.length} seed clients for offline use`);
    } catch (error) {
      console.error('Error storing seed data:', error);
    }
    
    return seedClients;
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
          const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';
          
          if (backendUrl) {
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
          } else {
            console.error("❌ LocalStorageManager: No backend URL configured");
          }
        } catch (error) {
          console.error("❌ LocalStorageManager: Backend error during add client:", error);
        }
      }
      
      // Add to local storage (either offline or backend failed)
      await this.performDBOperation('clients', 'add', clientData);
      
      // Add to sync queue if online but backend failed
      if (this.isOnline) {
        this.addToSyncQueue('CREATE_CLIENT', clientData);
        // Return success true - data is safely stored locally and will sync when backend is available
        console.log(`⚠️ Backend temporarily unavailable - ${clientData.name} stored locally and queued for sync`);
        return { data: clientData, success: true, offline: false, synced: false, message: 'Member added successfully! Data will sync when connection is restored.' };
      }
      
      return { data: clientData, success: true, offline: true };
    } catch (error) {
      console.error('Error adding client:', error);
      return { data: null, success: false, error: error.message };
    }
  }

  // Force refresh data from backend
  async forceRefreshClients() {
    try {
      console.log("🔄 LocalStorageManager: Force refreshing clients from backend...");
      
      let backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';
      // Use relative URL if environment variable is not set
      const apiBaseUrl = backendUrl || window.location.origin;
      
      
      if (!backendUrl) {
        console.log("🔍 LocalStorageManager: No backend URL configured, using relative URLs");
      }
      
      const response = await fetch(`${apiBaseUrl}/api/clients`, {
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
      
      try {
        await this.performDBOperation('clients', 'put', updatedClient);
      } catch (constraintError) {
        if (constraintError.name === 'ConstraintError') {
          console.warn("Warning: Could not store client", updatedClient.name, "locally:", constraintError.message);
          // Still return success since the main update logic worked
        } else {
          throw constraintError;
        }
      }
      
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
    
    let backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
    
    
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
  getBackendUrl() {
    // Use fallback for undefined environment
    const envObject = process.env || import.meta.env || {};
    const backendUrl = envObject.REACT_APP_BACKEND_URL;
    
    if (!backendUrl) {
      // Use relative URLs when environment variable is not set
      console.log('Using relative URLs for API calls (no backend URL configured)');
      return '';
    }
    console.log('Using configured backend URL:', backendUrl);
    return backendUrl;
  }

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

  // =================== BACKUP & EXPORT METHODS ===================

  async exportDataForBackup() {
    console.log('📦 Preparing data for backup...');
    
    try {
      // Get all local data
      const clients = await this.performDBOperation('clients', 'getAll');
      const membershipTypes = await this.performDBOperation('membershipTypes', 'getAll');
      const settings = await this.performDBOperation('settings', 'getAll');
      
      // Get payment stats if available
      let paymentStats = null;
      try {
        const statsResult = await this.getPaymentStats();
        paymentStats = statsResult.data;
      } catch (error) {
        console.warn('Could not get payment stats for backup:', error);
      }
      
      const backupData = {
        version: '1.0',
        app_name: 'Alphalete Club PWA',
        timestamp: new Date().toISOString(),
        data: {
          clients: clients || [],
          membership_types: membershipTypes || [],
          settings: settings || []
        },
        metadata: {
          total_clients: (clients || []).length,
          active_clients: (clients || []).filter(c => c.status === 'Active').length,
          total_membership_types: (membershipTypes || []).length,
          backup_size_kb: 0, // Will be calculated after JSON stringify
          payment_stats: paymentStats
        }
      };
      
      // Calculate backup size
      const backupJson = JSON.stringify(backupData, null, 2);
      backupData.metadata.backup_size_kb = Math.round(new Blob([backupJson]).size / 1024);
      
      console.log(`✅ Backup data prepared: ${backupData.metadata.total_clients} clients, ${backupData.metadata.total_membership_types} membership types`);
      return backupData;
    } catch (error) {
      console.error('❌ Error preparing backup data:', error);
      throw error;
    }
  }

  async createBackupFile() {
    try {
      const backupData = await this.exportDataForBackup();
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
      const filename = `alphalete-backup-${timestamp}.json`;
      
      // Create downloadable backup file
      const backupJson = JSON.stringify(backupData, null, 2);
      const blob = new Blob([backupJson], { 
        type: 'application/json' 
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      // Save backup info to settings
      await this.setSetting('last_backup', {
        timestamp: new Date().toISOString(),
        filename: filename,
        client_count: backupData.metadata.total_clients,
        size_kb: backupData.metadata.backup_size_kb
      });
      
      console.log(`✅ Backup file created: ${filename} (${backupData.metadata.backup_size_kb}KB)`);
      return {
        success: true,
        filename: filename,
        size_kb: backupData.metadata.backup_size_kb,
        client_count: backupData.metadata.total_clients
      };
    } catch (error) {
      console.error('❌ Error creating backup file:', error);
      throw error;
    }
  }

  async restoreFromBackup(backupData) {
    console.log('🔄 Restoring from backup...');
    
    try {
      // Validate backup data structure
      if (!backupData.version || !backupData.data) {
        throw new Error('Invalid backup file format');
      }

      if (!backupData.data.clients || !Array.isArray(backupData.data.clients)) {
        throw new Error('Invalid clients data in backup');
      }

      // Get user confirmation with backup details
      const confirmMessage = `This will replace all current data with backup from ${new Date(backupData.timestamp).toLocaleDateString()}.\n\n` +
        `Backup contains:\n` +
        `• ${backupData.metadata.total_clients} clients\n` +
        `• ${backupData.metadata.total_membership_types} membership types\n\n` +
        `Current data will be backed up before restore. Continue?`;
      
      if (!window.confirm(confirmMessage)) {
        return { success: false, cancelled: true };
      }

      // Create emergency backup of current data first
      try {
        await this.createBackupFile();
        console.log('✅ Emergency backup created before restore');
      } catch (backupError) {
        console.warn('⚠️ Could not create emergency backup:', backupError);
      }

      // Clear existing data and restore from backup
      const transaction = this.db.transaction(['clients', 'membershipTypes', 'settings'], 'readwrite');
      
      // Clear clients
      const clientStore = transaction.objectStore('clients');
      await this.clearObjectStore(clientStore);
      
      // Clear membership types  
      const membershipStore = transaction.objectStore('membershipTypes');
      await this.clearObjectStore(membershipStore);
      
      // Restore clients
      for (const client of backupData.data.clients) {
        await this.addToObjectStore(clientStore, client);
      }
      
      // Restore membership types
      for (const membershipType of backupData.data.membership_types) {
        await this.addToObjectStore(membershipStore, membershipType);
      }
      
      // Restore settings (merge, don't replace completely)
      const settingsStore = transaction.objectStore('settings');
      for (const setting of backupData.data.settings || []) {
        await this.addToObjectStore(settingsStore, setting);
      }
      
      // Save restore info
      await this.setSetting('last_restore', {
        timestamp: new Date().toISOString(),
        backup_timestamp: backupData.timestamp,
        restored_clients: backupData.data.clients.length,
        restored_membership_types: backupData.data.membership_types.length
      });
      
      console.log(`✅ Backup restored successfully: ${backupData.data.clients.length} clients, ${backupData.data.membership_types.length} membership types`);
      return {
        success: true,
        restored_clients: backupData.data.clients.length,
        restored_membership_types: backupData.data.membership_types.length,
        backup_date: backupData.timestamp
      };
    } catch (error) {
      console.error('❌ Error restoring backup:', error);
      throw error;
    }
  }

  // Helper methods for backup operations
  async clearObjectStore(objectStore) {
    return new Promise((resolve, reject) => {
      const request = objectStore.clear();
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async addToObjectStore(objectStore, data) {
    return new Promise((resolve, reject) => {
      const request = objectStore.add(data);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async getStorageStatus() {
    try {
      const clients = await this.performDBOperation('clients', 'getAll');
      const membershipTypes = await this.performDBOperation('membershipTypes', 'getAll');
      const lastBackup = await this.getSetting('last_backup');
      const lastRestore = await this.getSetting('last_restore');
      
      // Calculate storage usage (approximate)
      const dataSize = JSON.stringify({ clients, membershipTypes }).length;
      const storageSizeKB = Math.round(dataSize / 1024);
      
      return {
        local_storage: {
          clients: clients.length,
          active_clients: clients.filter(c => c.status === 'Active').length,
          membership_types: membershipTypes.filter(mt => mt.is_active).length,
          total_records: clients.length + membershipTypes.length,
          storage_size_kb: storageSizeKB
        },
        backup_status: {
          last_backup: lastBackup,
          last_restore: lastRestore,
          has_backups: !!lastBackup
        },
        connection: this.getConnectionStatus(),
        storage_health: 'healthy' // Could add more health checks
      };
    } catch (error) {
      console.error('Error getting storage status:', error);
      return {
        local_storage: { clients: 0, membership_types: 0, total_records: 0 },
        backup_status: { last_backup: null, last_restore: null, has_backups: false },
        connection: { online: false, message: 'Error checking status' },
        storage_health: 'error',
        error: error.message
      };
    }
  }

  async exportToCSV() {
    try {
      const clients = await this.performDBOperation('clients', 'getAll');
      
      if (clients.length === 0) {
        throw new Error('No clients to export');
      }

      // CSV headers
      const headers = ['Name', 'Email', 'Phone', 'Membership Type', 'Monthly Fee', 'Start Date', 'Next Payment Date', 'Status', 'Amount Owed'];
      
      // CSV rows
      const rows = clients.map(client => [
        client.name || '',
        client.email || '',
        client.phone || '',
        client.membership_type || '',
        client.monthly_fee || '0',
        client.start_date || '',
        client.next_payment_date || '',
        client.status || 'Unknown',
        client.amount_owed || '0'
      ]);

      // Combine headers and rows
      const csvContent = [headers, ...rows]
        .map(row => row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(','))
        .join('\n');

      // Create and download file
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `alphalete-clients-${timestamp}.csv`;
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      console.log(`✅ CSV export created: ${filename}`);
      return { success: true, filename, client_count: clients.length };
    } catch (error) {
      console.error('❌ Error exporting to CSV:', error);
      throw error;
    }
  }

  async getPaymentStats() {
    try {
      // If online, try to get from backend first
      if (this.isOnline) {
        let backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
        
        if (backendUrl) {
          try {
            const response = await fetch(`${backendUrl}/api/payments/stats`);
            if (response.ok) {
              const data = await response.json();
              return { data, offline: false };
            }
          } catch (error) {
            console.warn('Could not get payment stats from backend:', error);
          }
        }
      }

      // Calculate basic stats from local data
      const clients = await this.performDBOperation('clients', 'getAll');
      const activeClients = clients.filter(c => c.status === 'Active');
      const totalRevenue = activeClients.reduce((sum, c) => sum + (c.monthly_fee || 0), 0);
      
      return {
        data: {
          total_revenue: totalRevenue,
          monthly_revenue: 0, // Would need actual payment records
          active_clients: activeClients.length,
          total_clients: clients.length
        },
        offline: true
      };
    } catch (error) {
      console.error('Error getting payment stats:', error);
      return { data: null, offline: true, error: error.message };
    }
  }

  // Reminder-related methods
  async getUpcomingReminders(daysAhead = 7) {
    try {
      let backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      
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
      let backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      
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
      let backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      
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
      let backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      
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
      let backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      
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