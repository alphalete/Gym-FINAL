const CACHE_NAME = 'alphalete-v4.3.0-loading-fix'; // Updated version for loading fix
const API_CACHE_NAME = 'alphalete-api-v4.3.0';

// Minimal service worker to avoid interfering with app loading
console.log('Service Worker: Starting minimal version to avoid loading issues');

// Install event - skip static asset caching for now
self.addEventListener('install', event => {
  console.log('Service Worker: Install event - skipping heavy caching');
  // Force activation immediately
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

// Fetch event - minimal handling, prefer network for now
self.addEventListener('fetch', event => {
  const { request } = event;
  
  // For now, just let all requests go to network to avoid caching issues
  event.respondWith(
    fetch(request).catch(err => {
      console.log('Service Worker: Network request failed:', err);
      // Only use cache as absolute fallback
      return caches.match(request);
    })
  );
});
  
  // For email endpoints, always try network first (need internet)
  if (url.pathname.includes('/email/')) {
    try {
      console.log('Service Worker: Handling email request:', url.pathname);
      
      // Clone the request to avoid consumption issues
      const networkRequest = request.clone();
      
      // Add timeout for mobile networks
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
      
      const response = await fetch(networkRequest, {
        signal: controller.signal,
        credentials: 'include',
        mode: 'cors'
      });
      
      clearTimeout(timeoutId);
      
      console.log('Service Worker: Email request successful:', response.status);
      return response;
    } catch (error) {
      console.error('Service Worker: Email request failed:', error);
      
      // Return more detailed offline message for email endpoints
      return new Response(
        JSON.stringify({
          success: false,
          message: `Email functionality requires internet connection. Error: ${error.message}`,
          offline: true,
          error_type: error.name
        }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
  }
  
  // For other API endpoints (clients, membership-types), try cache first
  try {
    // Try network first for better data freshness
    const response = await fetch(request);
    
    // Cache successful responses
    if (response.ok && (url.pathname.includes('/clients') || url.pathname.includes('/membership-types'))) {
      const cache = await caches.open(API_CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.log('Service Worker: Network failed, trying cache for:', url.pathname);
    
    // Try cache as fallback
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return error response if no cache available
    return new Response(
      JSON.stringify({
        success: false,
        message: 'No internet connection and no cached data available',
        offline: true
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
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