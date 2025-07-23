const CACHE_NAME = 'alphalete-v1.0.1'; // Updated version to force cache refresh
const API_CACHE_NAME = 'alphalete-api-v1.0.0';

// Static assets to cache for offline use
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  // Add other static assets as needed
];

// API endpoints that can work offline
const API_ENDPOINTS = [
  '/api/clients',
  '/api/membership-types',
  '/api/email/test'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker: Install event');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS.map(url => new Request(url, {credentials: 'same-origin'})));
      })
      .catch(err => {
        console.error('Service Worker: Error caching static assets:', err);
      })
  );
  
  // Force activation of new service worker
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activate event');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
            console.log('Service Worker: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Take control of all clients immediately
  self.clients.claim();
});

// Fetch event - handle offline requests
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
  }
  // Handle static assets
  else {
    event.respondWith(handleStaticRequest(request));
  }
});

// Handle API requests with cache-first strategy for offline capability
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  // For email endpoints, always try network first (need internet)
  if (url.pathname.includes('/email/')) {
    try {
      const response = await fetch(request);
      return response;
    } catch (error) {
      // Return offline message for email endpoints
      return new Response(
        JSON.stringify({
          success: false,
          message: 'Email functionality requires internet connection',
          offline: true
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
  }
  
  // For other API endpoints, try cache first, then network
  try {
    // Try network first for fresh data
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful responses
      const cache = await caches.open(API_CACHE_NAME);
      const responseClone = networkResponse.clone();
      await cache.put(request, responseClone);
      
      return networkResponse;
    }
  } catch (error) {
    console.log('Service Worker: Network request failed, trying cache');
  }
  
  // If network fails, try cache
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    // Add offline indicator to cached responses
    const data = await cachedResponse.json();
    const offlineResponse = {
      ...data,
      offline: true,
      cachedAt: cachedResponse.headers.get('date')
    };
    
    return new Response(JSON.stringify(offlineResponse), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  // If no cache available, return offline message
  return new Response(
    JSON.stringify({
      error: 'Offline and no cached data available',
      offline: true,
      message: 'This feature requires an internet connection for first use'
    }),
    {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}

// Handle static requests with cache-first strategy
async function handleStaticRequest(request) {
  // Try cache first for static assets
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // If not in cache, try network
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses for static assets
    if (networkResponse.ok && request.method === 'GET') {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // If offline and no cached version, return offline page
    if (request.mode === 'navigate') {
      const offlineResponse = await caches.match('/');
      if (offlineResponse) {
        return offlineResponse;
      }
    }
    
    throw error;
  }
}

// Background sync for when connection is restored
self.addEventListener('sync', event => {
  console.log('Service Worker: Background sync event:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(syncOfflineData());
  }
});

// Sync offline data when connection is restored
async function syncOfflineData() {
  console.log('Service Worker: Syncing offline data');
  
  try {
    // Here you would sync any offline changes back to the server
    // This is handled by the main application logic
    
    // Notify all clients that sync is complete
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_COMPLETE',
        message: 'Offline data synced successfully'
      });
    });
  } catch (error) {
    console.error('Service Worker: Sync failed:', error);
  }
}

// Push notifications (for future use)
self.addEventListener('push', event => {
  console.log('Service Worker: Push event received');
  
  const options = {
    body: 'You have new notifications from Alphalete Athletics Club',
    icon: '/icon-192.png',
    badge: '/badge-72.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Open App',
        icon: '/icon-192.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/icon-192.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('Alphalete Athletics Club', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  console.log('Service Worker: Notification click received');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      self.clients.openWindow('/')
    );
  }
});

console.log('Service Worker: Registered successfully');