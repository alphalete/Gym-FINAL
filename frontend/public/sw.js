const CACHE_NAME = 'alphalete-mobile-v5.2.0-mobile-cache-bypass';
const OFFLINE_DATA_KEY = 'alphalete-offline-data';

console.log('📱 Mobile PWA Service Worker: v5.2.0 MOBILE CACHE BYPASS - Aggressive mobile browser cache bypass implemented');

// FORCE DELETE ALL CACHES AND RELOAD IMMEDIATELY
self.addEventListener('install', event => {
  console.log('📱 PWA v5.2.0: MOBILE CACHE BYPASS - Deleting all caches immediately');
  
  event.waitUntil(
    // Delete ALL existing caches first
    caches.keys().then(cacheNames => {
      console.log('📱 PWA v4.0.0: Found caches to delete:', cacheNames);
      return Promise.all(
        cacheNames.map(cacheName => {
          console.log('📱 PWA v5.1.0: DASHBOARD REFRESH FIX - deleting cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      console.log('📱 PWA v5.1.0: All old caches deleted, skipping waiting');
      self.skipWaiting();
    })
  );
});

// Take control immediately and reload all pages
self.addEventListener('activate', event => {
  console.log('📱 PWA v5.1.0: ACTIVATE - Taking control and reloading all pages');
  
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

// Bypass ALL caching for API requests - always go to network with mobile cache bypass
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // For API requests, ALWAYS go to network, never cache - Mobile aggressive approach
  if (url.pathname.startsWith('/api/')) {
    console.log('📱 PWA v5.1.0: API request - MOBILE AGGRESSIVE cache bypass:', url.pathname);
    
    // Create a new request with mobile-aggressive cache-busting
    const newRequest = new Request(event.request.url + (event.request.url.includes('?') ? '&' : '?') + '_mobile_cb=' + Date.now(), {
      method: event.request.method,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'If-None-Match': '*'
      },
      body: event.request.body,
      mode: 'cors',
      credentials: 'same-origin',
      cache: 'no-cache',
      redirect: 'follow'
    });
    
    event.respondWith(
      fetch(newRequest).then(response => {
        console.log('📱 PWA v5.1.0: Fresh mobile API response for:', url.pathname);
        // Clone response and add no-cache headers
        const responseHeaders = new Headers(response.headers);
        responseHeaders.set('Cache-Control', 'no-cache, no-store, must-revalidate');
        responseHeaders.set('Pragma', 'no-cache');
        responseHeaders.set('Expires', '0');
        
        return new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders
        });
      }).catch(error => {
        console.error('📱 PWA v5.1.0: Mobile API request failed:', url.pathname, error);
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