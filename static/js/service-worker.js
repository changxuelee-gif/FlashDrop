// Service Worker for FlashDrop
const CACHE_NAME = 'flashdrop-cache-v1';
const urlsToCache = [
  '/',
  '/static/index.html',
  '/static/favicon.svg',
  '/static/og-image.svg',
  '/static/manifest.json',
  '/static/js/vue.global.js',
  '/static/js/tailwindcss-3.4.17.js',
  '/static/css/all.min.css'
];

// Install event - cache the necessary resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event - serve cached resources if available
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return from cache if found
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

// Handle background sync (optional)
self.addEventListener('sync', (event) => {
  if (event.tag === 'flashdrop-sync') {
    event.waitUntil(performBackgroundSync());
  }
});

// Background sync implementation
async function performBackgroundSync() {
  // Add background sync logic here if needed
  console.log('Background sync performed');
}