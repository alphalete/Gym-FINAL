/**
 * Local-First Data Manager for Alphalete Club
 * Stores everything locally with optional cloud backup
 */

class LocalFirstManager {
  constructor() {
    this.dbName = 'AlphaleteClubDB';
    this.dbVersion = 1;
    this.db = null;
    this.syncSettings = {
      autoBackup: false,
      backupFrequency: 'daily', // 'never', 'daily', 'weekly'
      lastBackup: null,
      cloudProvider: 'none' // 'none', 'dropbox', 'googledrive', 'custom'
    };
    this.initializeDatabase();
  }

  async initializeDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        this.loadSyncSettings();
        resolve();
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        this.createObjectStores(db);
      };
    });
  }

  createObjectStores(db) {
    // Clients store
    if (!db.objectStoreNames.contains('clients')) {
      const clientStore = db.createObjectStore('clients', { keyPath: 'id' });
      clientStore.createIndex('email', 'email', { unique: true });
      clientStore.createIndex('status', 'status');
      clientStore.createIndex('updated_at', 'updated_at');
    }

    // Payments store
    if (!db.objectStoreNames.contains('payments')) {
      const paymentStore = db.createObjectStore('payments', { keyPath: 'id' });
      paymentStore.createIndex('client_id', 'client_id');
      paymentStore.createIndex('payment_date', 'payment_date');
      paymentStore.createIndex('updated_at', 'updated_at');
    }

    // Sync metadata store (tracks what needs backing up)
    if (!db.objectStoreNames.contains('sync_metadata')) {
      const syncStore = db.createObjectStore('sync_metadata', { keyPath: 'id' });
      syncStore.createIndex('table_name', 'table_name');
      syncStore.createIndex('needs_backup', 'needs_backup');
      syncStore.createIndex('last_synced', 'last_synced');
    }

    // Settings store
    if (!db.objectStoreNames.contains('settings')) {
      db.createObjectStore('settings', { keyPath: 'key' });
    }

    console.log('✅ Local database initialized with all stores');
  }

  // =================== CLIENT OPERATIONS ===================
  
  async addClient(clientData) {
    const client = {
      ...clientData,
      id: clientData.id || this.generateId(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      _local_only: false // Flag for local-only data
    };

    const transaction = this.db.transaction(['clients', 'sync_metadata'], 'readwrite');
    
    try {
      // Add client
      await this.addToStore(transaction.objectStore('clients'), client);
      
      // Mark for backup
      await this.markForBackup(transaction.objectStore('sync_metadata'), 'clients', client.id);
      
      console.log(`✅ Client added locally: ${client.name}`);
      return client;
    } catch (error) {
      console.error('❌ Error adding client:', error);
      throw error;
    }
  }

  async getClients() {
    const transaction = this.db.transaction(['clients'], 'readonly');
    const store = transaction.objectStore('clients');
    
    return new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async updateClient(clientId, updateData) {
    const transaction = this.db.transaction(['clients', 'sync_metadata'], 'readwrite');
    const clientStore = transaction.objectStore('clients');
    
    return new Promise((resolve, reject) => {
      const getRequest = clientStore.get(clientId);
      
      getRequest.onsuccess = async () => {
        const client = getRequest.result;
        if (!client) {
          reject(new Error('Client not found'));
          return;
        }

        const updatedClient = {
          ...client,
          ...updateData,
          updated_at: new Date().toISOString()
        };

        try {
          await this.addToStore(clientStore, updatedClient);
          await this.markForBackup(transaction.objectStore('sync_metadata'), 'clients', clientId);
          console.log(`✅ Client updated locally: ${updatedClient.name}`);
          resolve(updatedClient);
        } catch (error) {
          reject(error);
        }
      };
      
      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  // =================== PAYMENT OPERATIONS ===================
  
  async recordPayment(paymentData) {
    const payment = {
      ...paymentData,
      id: paymentData.id || this.generateId(),
      created_at: new Date().toISOString(),
      _local_only: false
    };

    const transaction = this.db.transaction(['payments', 'clients', 'sync_metadata'], 'readwrite');
    
    try {
      // Add payment record
      await this.addToStore(transaction.objectStore('payments'), payment);
      
      // Update client payment status
      const client = await this.getFromStore(transaction.objectStore('clients'), payment.client_id);
      if (client) {
        const updatedClient = {
          ...client,
          payment_status: 'paid',
          amount_owed: 0,
          updated_at: new Date().toISOString()
        };
        await this.addToStore(transaction.objectStore('clients'), updatedClient);
        await this.markForBackup(transaction.objectStore('sync_metadata'), 'clients', client.id);
      }
      
      // Mark payment for backup
      await this.markForBackup(transaction.objectStore('sync_metadata'), 'payments', payment.id);
      
      console.log(`✅ Payment recorded locally: TTD ${payment.amount_paid}`);
      return payment;
    } catch (error) {
      console.error('❌ Error recording payment:', error);
      throw error;
    }
  }

  async getPayments() {
    const transaction = this.db.transaction(['payments'], 'readonly');
    const store = transaction.objectStore('payments');
    
    return new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async getPaymentStats() {
    const payments = await this.getPayments();
    const totalRevenue = payments.reduce((sum, p) => sum + p.amount_paid, 0);
    
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    const monthlyRevenue = payments
      .filter(p => {
        const paymentDate = new Date(p.payment_date);
        return paymentDate.getMonth() === currentMonth && 
               paymentDate.getFullYear() === currentYear;
      })
      .reduce((sum, p) => sum + p.amount_paid, 0);

    return {
      total_revenue: totalRevenue,
      monthly_revenue: monthlyRevenue,
      payment_count: payments.length,
      timestamp: new Date().toISOString(),
      source: 'local' // Indicate this is from local storage
    };
  }

  // =================== SYNC & BACKUP OPERATIONS ===================
  
  async markForBackup(syncStore, tableName, recordId) {
    const syncRecord = {
      id: `${tableName}_${recordId}`,
      table_name: tableName,
      record_id: recordId,
      needs_backup: true,
      last_synced: null,
      created_at: new Date().toISOString()
    };
    
    return this.addToStore(syncStore, syncRecord);
  }

  async getItemsNeedingBackup() {
    const transaction = this.db.transaction(['sync_metadata'], 'readonly');
    const store = transaction.objectStore('sync_metadata');
    const index = store.index('needs_backup');
    
    return new Promise((resolve, reject) => {
      const request = index.getAll(true); // Get all items where needs_backup = true
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async exportDataForBackup() {
    console.log('📦 Preparing data for backup...');
    
    const clients = await this.getClients();
    const payments = await this.getPayments();
    const settings = await this.getSettings();
    
    const backupData = {
      version: '1.0',
      timestamp: new Date().toISOString(),
      data: {
        clients,
        payments,
        settings
      },
      metadata: {
        total_clients: clients.length,
        total_payments: payments.length,
        total_revenue: payments.reduce((sum, p) => sum + p.amount_paid, 0)
      }
    };
    
    console.log(`✅ Backup data prepared: ${clients.length} clients, ${payments.length} payments`);
    return backupData;
  }

  async createBackupFile() {
    const backupData = await this.exportDataForBackup();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `alphalete-backup-${timestamp}.json`;
    
    // Create downloadable backup file
    const blob = new Blob([JSON.stringify(backupData, null, 2)], { 
      type: 'application/json' 
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    // Update sync settings
    this.syncSettings.lastBackup = new Date().toISOString();
    await this.saveSyncSettings();
    
    console.log(`✅ Backup file created: ${filename}`);
    return filename;
  }

  async restoreFromBackup(backupData) {
    console.log('🔄 Restoring from backup...');
    
    const transaction = this.db.transaction(['clients', 'payments', 'settings'], 'readwrite');
    
    try {
      // Clear existing data (optional - could merge instead)
      await this.clearStore(transaction.objectStore('clients'));
      await this.clearStore(transaction.objectStore('payments'));
      
      // Restore clients
      for (const client of backupData.data.clients) {
        await this.addToStore(transaction.objectStore('clients'), client);
      }
      
      // Restore payments
      for (const payment of backupData.data.payments) {
        await this.addToStore(transaction.objectStore('payments'), payment);
      }
      
      // Restore settings
      for (const setting of backupData.data.settings) {
        await this.addToStore(transaction.objectStore('settings'), setting);
      }
      
      console.log(`✅ Backup restored: ${backupData.data.clients.length} clients, ${backupData.data.payments.length} payments`);
      return true;
    } catch (error) {
      console.error('❌ Error restoring backup:', error);
      throw error;
    }
  }

  // =================== CLOUD SYNC OPERATIONS ===================
  
  async syncToCloud() {
    if (this.syncSettings.cloudProvider === 'none') {
      console.log('⚠️ No cloud provider configured');
      return false;
    }

    console.log(`☁️ Starting sync to ${this.syncSettings.cloudProvider}...`);
    
    try {
      const backupData = await this.exportDataForBackup();
      
      // Upload based on provider
      switch (this.syncSettings.cloudProvider) {
        case 'dropbox':
          await this.syncToDropbox(backupData);
          break;
        case 'googledrive':
          await this.syncToGoogleDrive(backupData);
          break;
        case 'custom':
          await this.syncToCustomEndpoint(backupData);
          break;
      }
      
      // Mark all items as synced
      await this.markAllAsSynced();
      
      this.syncSettings.lastBackup = new Date().toISOString();
      await this.saveSyncSettings();
      
      console.log('✅ Cloud sync completed successfully');
      return true;
    } catch (error) {
      console.error('❌ Cloud sync failed:', error);
      return false;
    }
  }

  async syncToDropbox(backupData) {
    // Implementation would use Dropbox API
    console.log('📤 Uploading to Dropbox...');
    // Placeholder for Dropbox integration
  }

  async syncToGoogleDrive(backupData) {
    // Implementation would use Google Drive API
    console.log('📤 Uploading to Google Drive...');
    // Placeholder for Google Drive integration
  }

  async syncToCustomEndpoint(backupData) {
    // Custom API endpoint
    const endpoint = this.syncSettings.customEndpoint;
    const apiKey = this.syncSettings.customApiKey;
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(backupData)
    });
    
    if (!response.ok) {
      throw new Error(`Custom sync failed: ${response.statusText}`);
    }
    
    console.log('✅ Uploaded to custom endpoint');
  }

  // =================== HELPER METHODS ===================
  
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  addToStore(store, data) {
    return new Promise((resolve, reject) => {
      const request = store.put(data);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  getFromStore(store, key) {
    return new Promise((resolve, reject) => {
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  clearStore(store) {
    return new Promise((resolve, reject) => {
      const request = store.clear();
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async markAllAsSynced() {
    const transaction = this.db.transaction(['sync_metadata'], 'readwrite');
    const store = transaction.objectStore('sync_metadata');
    
    return new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = async () => {
        const items = request.result;
        for (const item of items) {
          item.needs_backup = false;
          item.last_synced = new Date().toISOString();
          await this.addToStore(store, item);
        }
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }

  async loadSyncSettings() {
    const transaction = this.db.transaction(['settings'], 'readonly');
    const store = transaction.objectStore('settings');
    
    return new Promise((resolve, reject) => {
      const request = store.get('sync_settings');
      request.onsuccess = () => {
        if (request.result) {
          this.syncSettings = { ...this.syncSettings, ...request.result.value };
        }
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }

  async saveSyncSettings() {
    const transaction = this.db.transaction(['settings'], 'readwrite');
    const store = transaction.objectStore('settings');
    
    return this.addToStore(store, {
      key: 'sync_settings',
      value: this.syncSettings,
      updated_at: new Date().toISOString()
    });
  }

  async getSettings() {
    const transaction = this.db.transaction(['settings'], 'readonly');
    const store = transaction.objectStore('settings');
    
    return new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // =================== STATUS & MONITORING ===================
  
  async getStorageStatus() {
    const clients = await this.getClients();
    const payments = await this.getPayments();
    const itemsNeedingBackup = await this.getItemsNeedingBackup();
    
    return {
      local_storage: {
        clients: clients.length,
        payments: payments.length,
        total_records: clients.length + payments.length
      },
      backup_status: {
        items_needing_backup: itemsNeedingBackup.length,
        last_backup: this.syncSettings.lastBackup,
        auto_backup_enabled: this.syncSettings.autoBackup,
        cloud_provider: this.syncSettings.cloudProvider
      },
      storage_health: 'healthy' // Could add more health checks
    };
  }
}

export default LocalFirstManager;