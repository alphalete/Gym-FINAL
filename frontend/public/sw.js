const CACHE_NAME = 'alphalete-mobile-v5.1.0-dashboard-refresh-fix';
const OFFLINE_DATA_KEY = 'alphalete-offline-data';

console.log('📱 Mobile PWA Service Worker: v5.1.0 DASHBOARD REFRESH FIX - Mobile dashboard now refreshes after client deletion');

// FORCE DELETE ALL CACHES AND RELOAD IMMEDIATELY
self.addEventListener('install', event => {
  console.log('📱 PWA v5.1.0: DASHBOARD REFRESH FIX - Deleting all caches immediately');
  
  event.waitUntil(
    // Delete ALL existing caches first
    caches.keys().then(cacheNames => {
      console.log('📱 PWA v4.0.0: Found caches to delete:', cacheNames);
      return Promise.all(
        cacheNames.map(cacheName => {
          console.log('📱 PWA v5.0.0: REVENUE FIX - deleting cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      console.log('📱 PWA v5.0.0: All old caches deleted, skipping waiting');
      self.skipWaiting();
    })
  );
});

// Take control immediately and reload all pages
self.addEventListener('activate', event => {
  console.log('📱 PWA v5.0.0: ACTIVATE - Taking control and reloading all pages');
  
  event.waitUntil(
    self.clients.claim().then(() => {
      // Force reload all open pages to get new data
      return self.clients.matchAll().then(clients => {
        clients.forEach(client => {
          console.log('📱 PWA v4.0.0: Force reloading client:', client.url);
          client.postMessage({ 
            type: 'FORCE_RELOAD_NEW_DATA',
            message: 'New service worker active - reloading to get fresh data'
          });
        });
      });
    })
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

// Bypass ALL caching for API requests - always go to network
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // For API requests, ALWAYS go to network, never cache
  if (url.pathname.startsWith('/api/')) {
    console.log('📱 PWA v4.0.0: API request - FORCING network call:', url.pathname);
    
    event.respondWith(
      fetch(event.request, { 
        cache: 'no-cache',
        headers: {
          ...event.request.headers,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      }).then(response => {
        console.log('📱 PWA v4.0.0: Fresh API response for:', url.pathname);
        return response;
      }).catch(error => {
        console.error('📱 PWA v4.0.0: API request failed:', url.pathname, error);
        return new Response(JSON.stringify({ error: 'API unavailable' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }
  
  // For app resources, go to network first, fallback to cache
  event.respondWith(
    fetch(event.request, { cache: 'no-cache' })
      .then(response => {
        console.log('📱 PWA v4.0.0: Fresh resource:', url.pathname);
        return response;
      })
      .catch(error => {
        console.log('📱 PWA v4.0.0: Network failed, trying cache:', url.pathname);
        return caches.match(event.request).then(cachedResponse => {
          return cachedResponse || new Response('Offline', { status: 503 });
        });
      })
  );
});

console.log('📱 Mobile PWA Service Worker v4.0.0: COMPLETE FIX ready - Will force reload all pages');