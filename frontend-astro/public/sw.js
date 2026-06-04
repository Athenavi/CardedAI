// P10-2: PWA Service Worker - 离线支持和缓存策略
const CACHE_NAME = 'fastblog-v1';
const OFFLINE_PAGE = '/offline.html';

// 需要预缓存的资源
const PRECACHE_URLS = [
    '/',
    '/config.js',
];

// API 缓存策略： stale-while-revalidate
const API_CACHE_STRATEGY = 'stale-while-revalidate';

// 安装事件：预缓存关键资源
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Pre-caching critical resources');
            return cache.addAll(PRECACHE_URLS);
        })
    );
    self.skipWaiting();
});

// 激活事件：清理旧缓存
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        })
    );
    self.clients.claim();
});

// Fetch 事件：拦截网络请求
self.addEventListener('fetch', (event) => {
    const {request} = event;
    const url = new URL(request.url);

    // 1. API 请求：Network First, fallback to cache
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }

    // 2. 静态资源：Cache First, fallback to network
    if (
        request.destination === 'style' ||
        request.destination === 'script' ||
        request.destination === 'image' ||
        request.destination === 'font'
    ) {
        event.respondWith(cacheFirstStrategy(request));
        return;
    }

    // 3. 页面导航：Stale-while-revalidate
    if (request.mode === 'navigate') {
        event.respondWith(staleWhileRevalidateStrategy(request));
        return;
    }

    // 4. 默认策略：Network First
    event.respondWith(networkFirstStrategy(request));
});

// Network First 策略（API 请求）
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);

        // 如果响应成功，克隆并缓存
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        // 网络失败，尝试从缓存获取
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            console.log('[SW] Serving from cache (network failed):', request.url);
            return cachedResponse;
        }

        // 如果是导航请求，返回离线页面
        if (request.mode === 'navigate') {
            return caches.match(OFFLINE_PAGE);
        }

        throw error;
    }
}

// Cache First 策略（静态资源）
async function cacheFirstStrategy(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        // 后台更新缓存
        fetch(request).then((networkResponse) => {
            if (networkResponse.ok) {
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(request, networkResponse);
                });
            }
        }).catch(() => {
            // 忽略错误
        });

        return cachedResponse;
    }

    // 缓存未命中，从网络获取
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.error('[SW] Fetch failed:', error);
        throw error;
    }
}

// Stale-while-revalidate 策略（页面导航）
async function staleWhileRevalidateStrategy(request) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);

    // 立即返回缓存（如果有）
    const fetchPromise = fetch(request).then((networkResponse) => {
        // 后台更新缓存
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    }).catch(() => {
        // 如果网络失败且没有缓存，返回离线页面
        if (!cachedResponse) {
            return caches.match(OFFLINE_PAGE);
        }
    });

    return cachedResponse || fetchPromise;
}

// 后台同步：草稿自动保存
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-drafts') {
        event.waitUntil(syncDrafts());
    }
});

async function syncDrafts() {
    console.log('[SW] Syncing drafts...');
  const DB_NAME = 'fastblog-drafts';
  const STORE_NAME = 'pending-drafts';

  try {
    const drafts = await new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, {keyPath: 'id'});
        }
      };

      request.onsuccess = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          resolve([]);
          return;
        }
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const getAllReq = store.getAll();

        getAllReq.onsuccess = () => resolve(getAllReq.result || []);
        getAllReq.onerror = () => resolve([]);
      };

      request.onerror = () => resolve([]);
    });

    for (const draft of drafts) {
      try {
        const response = await fetch('/api/v1/articles', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(draft),
        });

        if (response.ok) {
          // 同步成功后从 IndexedDB 中删除该草稿
          await removeFromIndexedDB(DB_NAME, STORE_NAME, draft.id);
          console.log('[SW] Draft synced:', draft.id);
        } else {
          console.warn('[SW] Draft sync failed with status:', response.status, draft.id);
        }
      } catch (error) {
        console.error('[SW] Failed to sync draft:', draft.id, error);
      }
        }
  } catch (error) {
    console.error('[SW] IndexedDB access error:', error);
    }
}

/**
 * 从 IndexedDB 中删除已同步的草稿
 */
function removeFromIndexedDB(dbName, storeName, key) {
  return new Promise((resolve) => {
    const request = indexedDB.open(dbName, 1);
    request.onsuccess = (event) => {
      const db = event.target.result;
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      store.delete(key);
      tx.oncomplete = () => resolve(true);
      tx.onerror = () => resolve(false);
    };
    request.onerror = () => resolve(false);
  });
}

// 推送通知支持
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'FastBlog 通知';
    const options = {
        body: data.body || '您有新的消息',
        icon: '/icon-192.png',
        badge: '/badge-72.png',
        data: data.url || '/',
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// 通知点击事件
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    event.waitUntil(
        clients.openWindow(event.notification.data)
    );
});
