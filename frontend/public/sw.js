const CACHE_NAME = 'alphalete-mobile-v1.0.0';
const OFFLINE_DATA_KEY = 'alphalete-offline-data';

console.log('📱 Mobile PWA Service Worker: Starting');

// Install event - cache app shell for mobile
self.addEventListener('install', event => {
  console.log('📱 PWA: Installing for mobile use');
  
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll([
        '/',
        '/static/js/bundle.js',
        '/static/css/main.css',
        '/manifest.json'
      ]).catch(err => {
        console.log('📱 PWA: Cache add failed (expected in dev):', err);
      });
    }).then(() => {
      self.skipWaiting();
    })
  );
});

// Activate event
self.addEventListener('activate', event => {
  console.log('📱 PWA: Activating mobile version');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('📱 PWA: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      self.clients.claim();
    })
  );
});

// Store data for offline use
function storeOfflineData(key, data) {
  try {
    const timestamp = new Date().toISOString();
    const offlineData = {
      data: data,
      timestamp: timestamp,
      cached: true
    };
    
    // Store in cache for offline access
    caches.open(CACHE_NAME).then(cache => {
      const response = new Response(JSON.stringify(offlineData), {
        headers: { 'Content-Type': 'application/json' }
      });
      cache.put(key, response);
      console.log(`📱 PWA: Stored offline data for ${key}`);
    });
  } catch (error) {
    console.error('📱 PWA: Failed to store offline data:', error);
  }
}

// Get offline data
async function getOfflineData(key) {
  try {
    const cache = await caches.open(CACHE_NAME);
    const response = await cache.match(key);
    if (response) {
      const data = await response.json();
      console.log(`📱 PWA: Retrieved offline data for ${key}`);
      return data;
    }
  } catch (error) {
    console.error('📱 PWA: Failed to get offline data:', error);
  }
  return null;
}

// Fetch event - mobile-optimized with offline support
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // Handle API requests with offline fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          if (response.ok) {
            console.log('📱 PWA: API success:', url.pathname);
            
            // Store successful API responses for offline use
            const responseClone = response.clone();
            responseClone.json().then(data => {
              storeOfflineData(url.pathname, data);
            });
            
            return response;
          } else {
            throw new Error(`HTTP ${response.status}`);
          }
        })
        .catch(async (error) => {
          console.log('📱 PWA: API failed, trying offline data:', url.pathname);
          
          // Try to get offline data
          const offlineData = await getOfflineData(url.pathname);
          if (offlineData) {
            console.log('📱 PWA: Using offline data for:', url.pathname);
            return new Response(JSON.stringify(offlineData.data), {
              headers: { 
                'Content-Type': 'application/json',
                'X-Offline-Data': 'true'
              }
            });
          }
          
          // Return empty array for client list, 0 for stats
          let fallbackData = [];
          if (url.pathname.includes('stats')) {
            fallbackData = { total_revenue: 0, monthly_revenue: 0, payment_count: 0 };
          }
          
          console.log('📱 PWA: Using fallback data for:', url.pathname);
          return new Response(JSON.stringify(fallbackData), {
            headers: { 
              'Content-Type': 'application/json',
              'X-Fallback-Data': 'true'
            }
          });
        })
    );
    return;
  }
  
  // Handle app shell requests
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          console.log('📱 PWA: Cache hit:', url.pathname);
          return response;
        }
        
        return fetch(event.request)
          .then(response => {
            console.log('📱 PWA: Network success:', url.pathname);
            return response;
          })
          .catch(error => {
            console.log('📱 PWA: Network failed:', url.pathname);
            // Return index.html for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match('/');
            }
            return new Response('Offline', { status: 503 });
          });
      })
  );
});

console.log('📱 Mobile PWA Service Worker: Ready');