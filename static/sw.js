/**
 * YITP Service Worker for Performance Optimization
 * Handles caching strategies for better performance
 */

const CACHE_NAME = 'yitp-v1.0.0';
const STATIC_CACHE = 'yitp-static-v1.0.0';
const DYNAMIC_CACHE = 'yitp-dynamic-v1.0.0';

// Assets to cache immediately
const STATIC_ASSETS = [
    '/',
    '/static/assets/css/bootstrap.min.css',
    '/static/assets/css/yitp-optimized.css',
    '/static/assets/css/style.css',
    '/static/assets/js/yitp-performance.js',
    '/static/assets/img/logo/youthImpact.png',
    '/static/assets/img/favicon.png',
    '/static/assets/fonts/inter/Inter-Regular.woff2',
    '/static/assets/fonts/inter/Inter-Bold.woff2',
    '/offline.html'
];

// Cache strategies
const CACHE_STRATEGIES = {
    // Cache first, then network (for static assets)
    CACHE_FIRST: 'cache-first',
    // Network first, then cache (for dynamic content)
    NETWORK_FIRST: 'network-first',
    // Stale while revalidate (for frequently updated content)
    STALE_WHILE_REVALIDATE: 'stale-while-revalidate'
};

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Service Worker: Static assets cached');
                return self.skipWaiting();
            })
            .catch(err => {
                console.error('Service Worker: Failed to cache static assets', err);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker: Activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - handle requests with appropriate caching strategy
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip chrome-extension and other non-http requests
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    // Determine caching strategy based on request type
    if (isStaticAsset(request)) {
        event.respondWith(cacheFirstStrategy(request));
    } else if (isAPIRequest(request)) {
        event.respondWith(networkFirstStrategy(request));
    } else if (isPageRequest(request)) {
        event.respondWith(staleWhileRevalidateStrategy(request));
    } else {
        event.respondWith(networkFirstStrategy(request));
    }
});

// Cache-first strategy (for static assets)
async function cacheFirstStrategy(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.error('Cache-first strategy failed:', error);
        return new Response('Offline', { status: 503 });
    }
}

// Network-first strategy (for dynamic content)
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('Network failed, trying cache:', error);
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            return caches.match('/offline.html');
        }
        
        return new Response('Offline', { status: 503 });
    }
}

// Stale-while-revalidate strategy (for pages)
async function staleWhileRevalidateStrategy(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cachedResponse = await cache.match(request);
    
    const fetchPromise = fetch(request).then(networkResponse => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    }).catch(() => {
        // If network fails and we have cache, return cache
        if (cachedResponse) {
            return cachedResponse;
        }
        // Otherwise return offline page
        return caches.match('/offline.html');
    });
    
    // Return cached version immediately if available, otherwise wait for network
    return cachedResponse || fetchPromise;
}

// Helper functions to determine request types
function isStaticAsset(request) {
    const url = new URL(request.url);
    return url.pathname.includes('/static/') || 
           url.pathname.includes('/media/') ||
           url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|ico)$/);
}

function isAPIRequest(request) {
    const url = new URL(request.url);
    return url.pathname.includes('/api/') || 
           url.pathname.includes('/lms/') ||
           request.headers.get('Accept')?.includes('application/json');
}

function isPageRequest(request) {
    return request.mode === 'navigate' || 
           request.headers.get('Accept')?.includes('text/html');
}

// Background sync for offline actions
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Handle offline form submissions, etc.
    console.log('Service Worker: Background sync triggered');
}

// Push notifications (if needed in future)
self.addEventListener('push', event => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: '/static/assets/img/favicon.png',
            badge: '/static/assets/img/favicon.png',
            data: data.url
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    if (event.notification.data) {
        event.waitUntil(
            clients.openWindow(event.notification.data)
        );
    }
});

// Message handling for cache updates
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CACHE_UPDATE') {
        event.waitUntil(updateCache());
    }
});

async function updateCache() {
    const cache = await caches.open(STATIC_CACHE);
    return cache.addAll(STATIC_ASSETS);
}
