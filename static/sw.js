// Service Worker for KortekStream
// Handles caching and offline functionality for better SEO performance

const CACHE_NAME = 'kortekstream-v1.0';
const urlsToCache = [
    '/',
    '/static/css/output.css',
    '/static/css/critical.css', 
    '/static/js/performance-optimizations.js',
    '/static/images/logo.png',
    '/static/images/favicon-16x16.png',
    '/static/images/favicon-32x32.png',
    '/manifest.json',
    '/offline.html'
];

// Install event - cache resources
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Return cached version or fetch from network
                return response || fetch(event.request);
            }
        )
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Background sync for offline actions
self.addEventListener('sync', function(event) {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

function doBackgroundSync() {
    // Handle background sync tasks
    return new Promise((resolve) => {
        // Your background sync logic here
        resolve();
    });
}