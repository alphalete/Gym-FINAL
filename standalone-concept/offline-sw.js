// Enhanced Service Worker for fully offline PWA
const CACHE_NAME = 'alphalete-standalone-v1';
const DB_NAME = 'AlphaleteOfflineDB';
const DB_VERSION = 1;

// Cache all app resources
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icon-192x192.png',
  '/icon-512x512.png'
];

class OfflineDatabase {
  constructor() {
    this.db = null;
  }

  async initialize() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create object stores (tables)
        if (!db.objectStoreNames.contains('clients')) {
          const clientStore = db.createObjectStore('clients', { keyPath: 'id' });
          clientStore.createIndex('email', 'email', { unique: true });
          clientStore.createIndex('status', 'status');
        }
        
        if (!db.objectStoreNames.contains('payments')) {
          const paymentStore = db.createObjectStore('payments', { keyPath: 'id' });
          paymentStore.createIndex('client_id', 'client_id');
          paymentStore.createIndex('payment_date', 'payment_date');
        }
        
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'key' });
        }
      };
    });
  }

  async addClient(client) {
    const transaction = this.db.transaction(['clients'], 'readwrite');
    const store = transaction.objectStore('clients');
    return store.add({
      ...client,
      id: client.id || this.generateId(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
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

  async addPayment(payment) {
    const transaction = this.db.transaction(['payments'], 'readwrite');
    const store = transaction.objectStore('payments');
    return store.add({
      ...payment,
      id: payment.id || this.generateId(),
      created_at: new Date().toISOString()
    });
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
      timestamp: new Date().toISOString()
    };
  }

  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
}

// Service Worker lifecycle
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('✅ Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', (event) => {
  // Handle API requests with offline database
  if (event.request.url.includes('/api/')) {
    event.respondWith(handleAPIRequest(event.request));
    return;
  }
  
  // Handle static resources with cache
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response; // Return cached version
        }
        return fetch(event.request); // Fallback to network
      })
  );
});

// Handle API requests offline
async function handleAPIRequest(request) {
  const url = new URL(request.url);
  const pathname = url.pathname;
  
  // Initialize offline database
  const offlineDB = new OfflineDatabase();
  await offlineDB.initialize();
  
  try {
    // Route API requests to offline handlers
    if (pathname.includes('/api/clients')) {
      return handleClientsAPI(request, offlineDB);
    } else if (pathname.includes('/api/payments')) {
      return handlePaymentsAPI(request, offlineDB);
    }
    
    // Fallback to network if available
    return await fetch(request);
  } catch (error) {
    console.error('Offline API error:', error);
    return new Response(
      JSON.stringify({ error: 'Offline mode - limited functionality' }),
      { 
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

async function handleClientsAPI(request, offlineDB) {
  if (request.method === 'GET') {
    const clients = await offlineDB.getClients();
    return new Response(JSON.stringify(clients), {
      headers: { 'Content-Type': 'application/json' }
    });
  } else if (request.method === 'POST') {
    const clientData = await request.json();
    await offlineDB.addClient(clientData);
    return new Response(JSON.stringify(clientData), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function handlePaymentsAPI(request, offlineDB) {
  const url = new URL(request.url);
  
  if (url.pathname.includes('/stats')) {
    const stats = await offlineDB.getPaymentStats();
    return new Response(JSON.stringify(stats), {
      headers: { 'Content-Type': 'application/json' }
    });
  } else if (request.method === 'POST' && url.pathname.includes('/record')) {
    const paymentData = await request.json();
    await offlineDB.addPayment(paymentData);
    return new Response(JSON.stringify({
      ...paymentData,
      invoice_sent: false, // Can't send emails offline
      message: 'Payment recorded offline - invoice will send when online'
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
}