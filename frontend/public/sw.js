const CACHE_NAME = 'alphalete-mobile-pwa-v17.0.0';
const STATIC_CACHE = 'alphalete-static-v17.0.0';
const API_CACHE = 'alphalete-api-v17.0.0';

// Mobile-First PWA Service Worker - API Debug Mode
console.log('📱 SERVICE WORKER DEBUG v17.0.0 - Temporarily disabling API interference for troubleshooting');

// Core mobile-first resources for immediate caching
const CORE_MOBILE_RESOURCES = [
  '/',
  '/manifest.json',
  '/icon-72x72.png',
  '/icon-96x96.png',
  '/icon-128x128.png',
  '/icon-144x144.png',
  '/icon-152x152.png',
  '/icon-192x192.png',
  '/icon-384x384.png',
  '/icon-512x512.png',
  '/icon-192x192-maskable.png',
  '/icon-512x512-maskable.png',
  '/favicon.ico'
];

// App shell resources for mobile app-like experience
const APP_SHELL_RESOURCES = [
  '/clients',
  '/payments',
  '/settings'
];

// Mobile-optimized installation
self.addEventListener('install', event => {
  console.log('📱 PWA v13.0.0: Installing mobile-first service worker...');
  
  event.waitUntil(
    Promise.all([
      // Cache core resources first (critical for mobile startup)
      caches.open(STATIC_CACHE).then(cache => {
        console.log('📱 PWA: Caching core mobile resources...');
        return cache.addAll(CORE_MOBILE_RESOURCES).catch(error => {
          console.warn('📱 PWA: Some core resources failed to cache, continuing...', error);
          // Cache individual resources that succeed
          return Promise.allSettled(
            CORE_MOBILE_RESOURCES.map(resource => cache.add(resource))
          );
        });
      }),
      
      // Cache app shell for instant navigation
      caches.open(CACHE_NAME).then(cache => {
        console.log('📱 PWA: Pre-caching app shell...');
        return Promise.allSettled(
          APP_SHELL_RESOURCES.map(resource => {
            return fetch(resource).then(response => {
              if (response.ok) {
                return cache.put(resource, response);
              }
            }).catch(() => {
              console.log('📱 PWA: App shell resource unavailable:', resource);
            });
          })
        );
      })
    ])
  );
  
  self.skipWaiting();
});

// Mobile-optimized activation
self.addEventListener('activate', event => {
  console.log('📱 PWA v13.0.0: Activating mobile-first service worker...');
  
  event.waitUntil(
    Promise.all([
      // Clean old caches (keep only current versions)
      caches.keys().then(cacheNames => {
        const validCaches = [CACHE_NAME, STATIC_CACHE, API_CACHE];
        return Promise.all(
          cacheNames.map(cacheName => {
            if (!validCaches.includes(cacheName)) {
              console.log('📱 PWA: Removing old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Take control for immediate mobile app behavior
      self.clients.claim()
    ])
  );
});

// Mobile-First Fetch Strategy - Optimized for Performance & Offline
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  const { pathname, origin } = url;
  
  // Only handle same-origin requests
  if (origin !== self.location.origin) {
    return;
  }
  
  // Navigation requests - Mobile app-like behavior
  if (event.request.mode === 'navigate') {
    event.respondWith(
      // Try network first for fresh content
      fetch(event.request).then(response => {
        // Cache the page for offline access
        if (response.ok) {
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, response.clone());
          });
        }
        return response;
      }).catch(() => {
        // Fallback to cached version
        return caches.match(event.request).then(cachedResponse => {
          if (cachedResponse) {
            return cachedResponse;
          }
          
          // Final fallback - offline page
          return caches.match('/').then(indexPage => {
            return indexPage || new Response(
              `<!DOCTYPE html>
              <html>
              <head>
                <title>Alphalete Club - Offline</title>
                <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
                <meta name="theme-color" content="#6366f1">
                <style>
                  body { 
                    font-family: -apple-system, BlinkMacSystemFont, system-ui; 
                    margin: 0; padding: 2rem; text-align: center; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; min-height: 100vh;
                    display: flex; flex-direction: column; justify-content: center;
                  }
                  .offline-icon { font-size: 4rem; margin-bottom: 1rem; }
                  .offline-title { font-size: 2rem; margin-bottom: 1rem; font-weight: 600; }
                  .offline-message { font-size: 1.1rem; opacity: 0.9; line-height: 1.5; }
                  .retry-btn { 
                    margin-top: 2rem; padding: 1rem 2rem; 
                    background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3);
                    border-radius: 50px; color: white; font-size: 1rem;
                    cursor: pointer; backdrop-filter: blur(10px);
                  }
                </style>
              </head>
              <body>
                <div class="offline-icon">📱</div>
                <h1 class="offline-title">Alphalete Club</h1>
                <p class="offline-message">You're currently offline.<br>Please check your connection and try again.</p>
                <button class="retry-btn" onclick="window.location.reload()">Retry Connection</button>
              </body>
              </html>`,
              { 
                headers: { 
                  'Content-Type': 'text/html',
                  'Cache-Control': 'no-cache'
                } 
              }
            );
          });
        });
      })
    );
    return;
  }
  
  // API requests - Network First with Minimal Caching (TEMPORARY DEBUG MODE)
  if (pathname.startsWith('/api/')) {
    console.log('🚨 SW DEBUG: API request detected:', pathname);
    
    // TEMPORARY: Let API requests pass through without interference
    event.respondWith(
      fetch(event.request).then(response => {
        console.log('✅ SW DEBUG: API request successful:', response.status, pathname);
        return response;
      }).catch(error => {
        console.error('❌ SW DEBUG: API request failed:', error, pathname);
        
        // Return a proper error response instead of masking the real error
        return new Response(
          JSON.stringify({ 
            offline: false,
            error: 'API request failed',
            message: `Failed to fetch ${pathname}: ${error.message}`,
            timestamp: Date.now(),
            debug: true
          }),
          { 
            status: 503,
            headers: { 
              'Content-Type': 'application/json',
              'X-Debug-SW': 'true'
            }
          }
        );
      })
    );
    return;
  }
  
  // Static resources - Cache First for Performance
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        // Serve from cache, update in background
        fetch(event.request).then(fetchResponse => {
          if (fetchResponse.ok) {
            caches.open(STATIC_CACHE).then(cache => {
              cache.put(event.request, fetchResponse);
            });
          }
        }).catch(() => {
          // Network failed, cached version is fine
        });
        
        return cachedResponse;
      }
      
      // Not in cache, fetch and cache
      return fetch(event.request).then(fetchResponse => {
        if (fetchResponse.ok) {
          caches.open(STATIC_CACHE).then(cache => {
            cache.put(event.request, fetchResponse.clone());
          });
        }
        return fetchResponse;
      }).catch(() => {
        // Network failed and no cache
        return new Response('Resource unavailable offline', { status: 503 });
      });
    })
  );
});

// Handle app messages for cache management - Enhanced for user issues
self.addEventListener('message', event => {
  const { type, payload } = event.data || {};
  
  switch (type) {
    case 'CLEAR_ALL_CACHES':
      console.log('📱 PWA: EMERGENCY CACHE CLEAR - Resolving user discrepancy issues...');
      Promise.all([
        caches.delete(CACHE_NAME),
        caches.delete(STATIC_CACHE),
        caches.delete(API_CACHE),
        // Clear any legacy cache versions
        caches.delete('alphalete-mobile-pwa-v16.0.0'),
        caches.delete('alphalete-static-v16.0.0'),
        caches.delete('alphalete-api-v16.0.0'),
        caches.delete('alphalete-mobile-pwa-v15.0.0'),
        caches.delete('alphalete-static-v15.0.0'),
        caches.delete('alphalete-api-v15.0.0'),
        caches.delete('alphalete-mobile-pwa-v14.0.0'),
        caches.delete('alphalete-static-v14.0.0'),
        caches.delete('alphalete-api-v14.0.0'),
        caches.delete('alphalete-mobile-pwa-v13.0.0'),
        caches.delete('alphalete-static-v13.0.0'),
        caches.delete('alphalete-api-v13.0.0'),
      ]).then(() => {
        console.log('📱 PWA: All caches cleared successfully');
        event.ports[0]?.postMessage({ success: true, message: 'All caches cleared - fresh data guaranteed' });
      });
      break;
      
    case 'CLEAR_API_CACHE':
      console.log('📱 PWA: Clearing API cache...');
      caches.delete(API_CACHE).then(() => {
        event.ports[0]?.postMessage({ success: true, message: 'API cache cleared' });
      });
      break;
      
    case 'FORCE_REFRESH':
      console.log('📱 PWA: Force refreshing all caches...');
      Promise.all([
        caches.delete(CACHE_NAME),
        caches.delete(API_CACHE)
      ]).then(() => {
        event.ports[0]?.postMessage({ success: true, message: 'All caches refreshed' });
      });
      break;
      
    case 'GET_CACHE_INFO':
      Promise.all([
        caches.has(CACHE_NAME),
        caches.has(STATIC_CACHE),
        caches.has(API_CACHE)
      ]).then(([appCache, staticCache, apiCache]) => {
        event.ports[0]?.postMessage({
          success: true,
          caches: { appCache, staticCache, apiCache },
          version: '16.0.0'
        });
      });
      break;
  }
});

// Background sync for mobile data optimization (future enhancement)
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    console.log('📱 PWA: Background sync triggered');
    // Implementation for background data sync when connection is restored
  }
});

console.log('📱 CRITICAL SERVICE WORKER FIX v16.0.0: Aggressive cache clearing to resolve user discrepancy issues');