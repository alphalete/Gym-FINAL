const CACHE_NAME = 'alphalete-mobile-pwa-v12.0.0';
const OFFLINE_DATA_KEY = 'alphalete-offline-data';

// Mobile-First PWA Service Worker
console.log('📱 MOBILE-FIRST PWA Service Worker: v12.0.0 - Standalone Mobile App Optimization');

// Mobile-First PWA Resources to Cache
const MOBILE_FIRST_RESOURCES = [
  '/',
  '/clients',
  '/add-client',
  '/payments', 
  '/manifest.json',
  '/icon-192x192.png',
  '/icon-512x512.png',
  '/icon-192x192-maskable.png',
  '/icon-512x512-maskable.png'
];

// Enhanced PWA installation event for mobile-first experience
self.addEventListener('install', event => {
  console.log('📱 PWA: Installing Mobile-First Service Worker...');
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('📱 PWA: Caching mobile-first resources...');
      return cache.addAll(MOBILE_FIRST_RESOURCES).catch(error => {
        console.warn('📱 PWA: Some mobile resources failed to cache:', error);
        // Cache critical resources individually
        return Promise.allSettled(
          MOBILE_FIRST_RESOURCES.map(resource => cache.add(resource))
        );
      });
    })
  );
  self.skipWaiting();
});

// Enhanced activation for mobile PWA
self.addEventListener('activate', event => {
  console.log('📱 PWA: Activating Mobile-First Service Worker...');
  event.waitUntil(
    Promise.all([
      // Clean old caches
      caches.keys().then(keys => Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            console.log('📱 PWA: Deleting old cache:', key);
            return caches.delete(key);
          }
        })
      )),
      // Claim all clients for mobile PWA
      self.clients.claim()
    ])
  );
});

// Mobile-Optimized Fetch Strategy
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // Handle navigation requests (mobile app-like behavior)
  if (event.request.mode === 'navigate') {
    event.respondWith(
      caches.match('/').then(response => {
        return response || fetch('/').catch(() => {
          // Offline fallback for navigation
          return new Response(
            `<!DOCTYPE html>
            <html>
            <head>
              <title>Alphalete Club - Offline</title>
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <style>
                body { 
                  font-family: -apple-system, system-ui; 
                  text-align: center; 
                  padding: 2rem; 
                  background: #f8fafc;
                }
                .offline-icon { font-size: 4rem; margin-bottom: 1rem; }
                .offline-title { color: #1e293b; margin-bottom: 0.5rem; }
                .offline-message { color: #64748b; }
              </style>
            </head>
            <body>
              <div class="offline-icon">📱</div>
              <h1 class="offline-title">Alphalete Club</h1>
              <p class="offline-message">You're currently offline. Please check your connection.</p>
            </body>
            </html>`,
            {
              headers: { 'Content-Type': 'text/html' }
            }
          );
        });
      })
    );
    return;
  }
  
  // Handle API requests with mobile-first caching strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      // Network first for API calls (mobile data aware)
      fetch(event.request).then(response => {
        // Cache successful API responses for offline access
        if (response.ok && event.request.method === 'GET') {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      }).catch(() => {
        // Fallback to cache for offline mobile experience
        return caches.match(event.request).then(cachedResponse => {
          if (cachedResponse) {
            return cachedResponse;
          }
          // Return offline response for mobile
          return new Response(
            JSON.stringify({ 
              offline: true, 
              data: [], 
              message: 'Currently offline - using cached data' 
            }),
            { 
              headers: { 'Content-Type': 'application/json' },
              status: 200
            }
          );
        });
      })
    );
    return;
  }
  
  // Handle static resources (cache first for mobile performance)
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request).then(fetchResponse => {
        // Cache static resources for mobile performance
        if (fetchResponse.ok) {
          const responseClone = fetchResponse.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
        }
        return fetchResponse;
      });
    })
  );
});

// ULTIMATE NUCLEAR CACHE BUSTING - Clear ALL browser data
self.addEventListener('install', event => {
  console.log('📱 PWA v6.0.0: ULTIMATE CACHE BUST - Nuclear approach for mobile cache clearing');
  
  event.waitUntil(
    Promise.all([
      // Delete ALL existing caches
      caches.keys().then(cacheNames => {
        console.log('📱 PWA v6.0.0: Found caches to delete:', cacheNames);
        return Promise.all(
          cacheNames.map(cacheName => {
            console.log('📱 PWA v6.0.0: ULTIMATE - Deleting cache:', cacheName);
            return caches.delete(cacheName);
          })
        );
      }),
      // Clear any stored cache variables
      new Promise(resolve => {
        // Force garbage collection of any cache references
        if (self.caches) {
          self.caches.keys().then(keys => {
            keys.forEach(key => self.caches.delete(key));
            resolve();
          });
        } else {
          resolve();
        }
      })
    ]).then(() => {
      console.log('📱 PWA v6.0.0: ULTIMATE - All caches deleted, force taking control');
      self.skipWaiting();
    })
  );
});

// Take control immediately and force ALL pages to reload with fresh data
self.addEventListener('activate', event => {
  console.log('📱 PWA v6.0.0: ULTIMATE ACTIVATE - Taking control and force reloading with fresh data');
  
  event.waitUntil(
    Promise.all([
      // Take control of all clients
      self.clients.claim(),
      // Clear ALL possible caches
      caches.keys().then(keys => Promise.all(keys.map(key => caches.delete(key)))),
      // Force all clients to reload with hard refresh
      self.clients.matchAll().then(clients => {
        clients.forEach(client => {
          console.log('📱 PWA v6.0.0: ULTIMATE - Force hard reload client:', client.url);
          client.postMessage({ 
            type: 'ULTIMATE_FORCE_RELOAD',
            message: 'Ultimate cache clear - hard reloading with location.replace',
            action: 'HARD_RELOAD_NOW'
          });
        });
      })
    ])
  );
});

// Handle messages from app
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'CLEAR_ALL_DATA') {
    console.log('📱 PWA v4.0.0: Received clear all data request');
    // Clear all caches
    caches.keys().then(cacheNames => {
      return Promise.all(cacheNames.map(name => caches.delete(name)));
    });
  }
});

// ULTIMATE NUCLEAR API CACHE BYPASS - Never cache API responses, force fresh data
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // For API requests, ULTIMATE NUCLEAR APPROACH - bypass ALL caching mechanisms
  if (url.pathname.startsWith('/api/')) {
    console.log('📱 PWA v6.0.0: ULTIMATE API bypass for:', url.pathname);
    
    // Create completely fresh request with ULTIMATE cache-busting
    const ultimateRequest = new Request(
      event.request.url + (event.request.url.includes('?') ? '&' : '?') + 
      `_nuclear=${Date.now()}&_mobile_ultimate=${Math.random().toString(36)}&_force_fresh=true&_bypass_all_cache=1`, 
      {
        method: event.request.method,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0, private',
          'Pragma': 'no-cache',
          'Expires': '0',
          'If-None-Match': '*',
          'If-Modified-Since': 'Thu, 01 Jan 1970 00:00:00 GMT',
          'X-Requested-With': 'XMLHttpRequest',
          'X-Mobile-Ultimate-Cache-Bust': Date.now().toString(),
          'X-Force-Fresh': 'true',
          'User-Agent': 'AlphaleteMobile-UltimateCacheBust/6.0.0'
        },
        body: event.request.body,
        mode: 'cors',
        credentials: 'same-origin',
        cache: 'no-store',
        redirect: 'follow'
      }
    );
    
    event.respondWith(
      fetch(ultimateRequest, { cache: 'no-store' })
        .then(response => {
          console.log('📱 PWA v6.0.0: ULTIMATE - Fresh API response for:', url.pathname);
          
          // Clone and add ULTIMATE no-cache headers
          const responseHeaders = new Headers(response.headers);
          responseHeaders.set('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0, private');
          responseHeaders.set('Pragma', 'no-cache');
          responseHeaders.set('Expires', '0');
          responseHeaders.set('X-Ultimate-Cache-Bust', Date.now().toString());
          
          return new Response(response.body, {
            status: response.status,
            statusText: response.statusText,
            headers: responseHeaders
          });
        })
        .catch(error => {
          console.error('📱 PWA v6.0.0: ULTIMATE API request failed:', url.pathname, error);
          return new Response(JSON.stringify({ 
            error: 'API unavailable',
            ultimate_cache_bust: true,
            timestamp: Date.now()
          }), {
            status: 503,
            headers: { 
              'Content-Type': 'application/json',
              'Cache-Control': 'no-cache, no-store'
            }
          });
        })
    );
    return;
  }
  
  // For app resources, ULTIMATE bypass - never use cache
  event.respondWith(
    fetch(event.request, { 
      cache: 'no-store',
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    })
      .then(response => {
        console.log('📱 PWA v6.0.0: ULTIMATE - Fresh resource:', url.pathname);
        return response;
      })
      .catch(error => {
        console.log('📱 PWA v6.0.0: ULTIMATE - Network failed for:', url.pathname);
        return new Response('Ultimate Cache Bypass - Offline', { status: 503 });
      })
  );
});

console.log('📱 Mobile PWA Service Worker v6.0.0: ULTIMATE NUCLEAR CACHE BUST - Final mobile cache solution ready');