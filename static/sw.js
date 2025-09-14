// ===== SERVICE WORKER ДЛЯ PWA =====

const CACHE_NAME = 'geo-astana-v1';
const STATIC_CACHE_NAME = 'geo-astana-static-v1';
const DYNAMIC_CACHE_NAME = 'geo-astana-dynamic-v1';

// Ресурсы для кэширования при установке
const STATIC_ASSETS = [
    '/',
    '/static/css/critical.css',
    '/static/css/main.css',
    '/static/css/animations.css',
    '/static/css/components.css',
    '/static/css/theme-dark.css',
    '/static/css/ui-components.css',
    '/static/css/mobile.css',
    '/static/js/optimized-ui.js',
    '/static/js/advanced-effects.js',
    '/static/manifest.json',
    // Внешние ресурсы (будут кэшироваться при первом запросе)
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap',
    'https://unpkg.com/aos@2.3.1/dist/aos.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
    'https://unpkg.com/aos@2.3.1/dist/aos.js',
    'https://cdn.plot.ly/plotly-2.26.0.min.js'
];

// API эндпоинты для кэширования
const API_CACHE_PATTERNS = [
    /\/api\/stats/,
    /\/api\/charts/,
    /\/api\/heatmap/,
    /\/api\/predictions/
];

// Время жизни кэша (в миллисекундах)
const CACHE_EXPIRY = {
    static: 7 * 24 * 60 * 60 * 1000, // 7 дней
    dynamic: 24 * 60 * 60 * 1000,    // 1 день
    api: 5 * 60 * 1000               // 5 минут
};

// ===== УСТАНОВКА SERVICE WORKER =====
self.addEventListener('install', event => {
    console.log('SW: Установка Service Worker...');
    
    event.waitUntil(
        Promise.all([
            // Кэшируем критические ресурсы
            caches.open(STATIC_CACHE_NAME).then(cache => {
                console.log('SW: Кэширование статических ресурсов...');
                return cache.addAll(STATIC_ASSETS.slice(0, 8)); // Только локальные файлы
            }),
            
            // Предварительно кэшируем внешние ресурсы
            cacheExternalResources()
        ])
    );
    
    // Принудительная активация
    self.skipWaiting();
});

// ===== АКТИВАЦИЯ SERVICE WORKER =====
self.addEventListener('activate', event => {
    console.log('SW: Активация Service Worker...');
    
    event.waitUntil(
        Promise.all([
            // Удаляем старые кэши
            cleanupOldCaches(),
            
            // Берем контроль над всеми клиентами
            self.clients.claim()
        ])
    );
});

// ===== ОБРАБОТКА FETCH ЗАПРОСОВ =====
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Обрабатываем только HTTP(S) запросы
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    event.respondWith(
        handleFetchRequest(request)
    );
});

// ===== ОБРАБОТКА СООБЩЕНИЙ =====
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        clearAllCaches().then(() => {
            event.ports[0].postMessage({ success: true });
        });
    }
});

// ===== ФУНКЦИИ ОБРАБОТКИ =====

async function handleFetchRequest(request) {
    const url = new URL(request.url);
    
    try {
        // 1. API запросы - Cache First с обновлением в фоне
        if (isApiRequest(url)) {
            return handleApiRequest(request);
        }
        
        // 2. Внешние ресурсы - Cache First
        if (isExternalResource(url)) {
            return handleExternalResource(request);
        }
        
        // 3. Статические ресурсы - Cache First
        if (isStaticResource(url)) {
            return handleStaticResource(request);
        }
        
        // 4. HTML страницы - Network First с fallback
        if (isHtmlRequest(request)) {
            return handleHtmlRequest(request);
        }
        
        // 5. Все остальное - Network First
        return handleNetworkFirst(request);
        
    } catch (error) {
        console.error('SW: Ошибка обработки запроса:', error);
        return handleOfflineResponse(request);
    }
}

async function handleApiRequest(request) {
    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    // Проверяем актуальность кэша
    if (cachedResponse && !isCacheExpired(cachedResponse, CACHE_EXPIRY.api)) {
        // Обновляем в фоне
        fetchAndCache(request, cache).catch(console.error);
        return cachedResponse;
    }
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            // Кэшируем только успешные ответы
            const responseClone = response.clone();
            await cache.put(request, responseClone);
        }
        return response;
    } catch (error) {
        // Возвращаем кэш если есть, иначе fallback
        return cachedResponse || createOfflineApiResponse();
    }
}

async function handleExternalResource(request) {
    const cache = await caches.open(STATIC_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            await cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        // Для критических ресурсов возвращаем заглушку
        return createResourceFallback(request);
    }
}

async function handleStaticResource(request) {
    const cache = await caches.open(STATIC_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Если нет в кэше, пытаемся загрузить
    try {
        const response = await fetch(request);
        if (response.ok) {
            await cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        return new Response('Ресурс недоступен офлайн', { status: 404 });
    }
}

async function handleHtmlRequest(request) {
    try {
        // Пытаемся получить свежую версию
        const response = await fetch(request);
        
        // Кэшируем HTML страницы
        if (response.ok) {
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            await cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        // Ищем в кэше
        const cache = await caches.open(DYNAMIC_CACHE_NAME);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Возвращаем офлайн страницу
        return createOfflineHtmlResponse();
    }
}

async function handleNetworkFirst(request) {
    try {
        const response = await fetch(request);
        
        // Кэшируем динамический контент
        if (response.ok && request.method === 'GET') {
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            await cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        const cache = await caches.open(DYNAMIC_CACHE_NAME);
        return await cache.match(request) || new Response('Контент недоступен', { status: 503 });
    }
}

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

function isApiRequest(url) {
    return API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

function isExternalResource(url) {
    return url.origin !== self.location.origin;
}

function isStaticResource(url) {
    const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2'];
    return staticExtensions.some(ext => url.pathname.endsWith(ext));
}

function isHtmlRequest(request) {
    return request.headers.get('Accept')?.includes('text/html');
}

function isCacheExpired(response, maxAge) {
    const dateHeader = response.headers.get('date');
    if (!dateHeader) return true;
    
    const cacheTime = new Date(dateHeader).getTime();
    return Date.now() - cacheTime > maxAge;
}

async function fetchAndCache(request, cache) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            await cache.put(request, response.clone());
        }
    } catch (error) {
        console.warn('SW: Ошибка фонового обновления:', error);
    }
}

async function cacheExternalResources() {
    const cache = await caches.open(STATIC_CACHE_NAME);
    const externalResources = STATIC_ASSETS.slice(8); // Внешние ресурсы
    
    // Кэшируем внешние ресурсы по одному, игнорируя ошибки
    for (const resource of externalResources) {
        try {
            await cache.add(resource);
            console.log(`SW: Кэшировано: ${resource}`);
        } catch (error) {
            console.warn(`SW: Не удалось кэшировать: ${resource}`, error);
        }
    }
}

async function cleanupOldCaches() {
    const cacheNames = await caches.keys();
    const validCaches = [STATIC_CACHE_NAME, DYNAMIC_CACHE_NAME];
    
    return Promise.all(
        cacheNames
            .filter(cacheName => !validCaches.includes(cacheName))
            .map(cacheName => {
                console.log(`SW: Удаление старого кэша: ${cacheName}`);
                return caches.delete(cacheName);
            })
    );
}

async function clearAllCaches() {
    const cacheNames = await caches.keys();
    return Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
    );
}

function createOfflineApiResponse() {
    return new Response(JSON.stringify({
        error: 'Нет подключения к интернету',
        offline: true,
        timestamp: Date.now()
    }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
    });
}

function createResourceFallback(request) {
    const url = new URL(request.url);
    
    // Fallback для CSS
    if (url.pathname.endsWith('.css')) {
        return new Response('/* Ресурс недоступен офлайн */', {
            headers: { 'Content-Type': 'text/css' }
        });
    }
    
    // Fallback для JS
    if (url.pathname.endsWith('.js')) {
        return new Response('// Ресурс недоступен офлайн', {
            headers: { 'Content-Type': 'application/javascript' }
        });
    }
    
    // Общий fallback
    return new Response('Ресурс недоступен', { status: 404 });
}

function createOfflineHtmlResponse() {
    const offlineHtml = `
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Офлайн - Геоаналитика Астаны</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #0f0f23, #1a1a2e);
                    color: white;
                    margin: 0;
                    padding: 2rem;
                    text-align: center;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }
                .icon { font-size: 4rem; margin-bottom: 1rem; }
                h1 { color: #00d4aa; margin-bottom: 1rem; }
                p { opacity: 0.8; margin-bottom: 2rem; line-height: 1.6; }
                button {
                    background: linear-gradient(135deg, #00d4aa, #00a8cc);
                    border: none;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 16px;
                    transition: transform 0.2s;
                }
                button:hover { transform: translateY(-2px); }
            </style>
        </head>
        <body>
            <div class="icon">🌐</div>
            <h1>Нет подключения</h1>
            <p>Приложение работает в офлайн режиме.<br>
            Некоторые функции могут быть недоступны.</p>
            <button onclick="window.location.reload()">
                Повторить попытку
            </button>
            
            <script>
                // Проверяем подключение каждые 10 секунд
                setInterval(() => {
                    if (navigator.onLine) {
                        window.location.reload();
                    }
                }, 10000);
                
                // Слушаем событие восстановления связи
                window.addEventListener('online', () => {
                    window.location.reload();
                });
            </script>
        </body>
        </html>
    `;
    
    return new Response(offlineHtml, {
        headers: { 'Content-Type': 'text/html' }
    });
}

function handleOfflineResponse(request) {
    if (isHtmlRequest(request)) {
        return createOfflineHtmlResponse();
    }
    
    return new Response('Сервис недоступен офлайн', {
        status: 503,
        headers: { 'Content-Type': 'text/plain' }
    });
}

// ===== ФОНОВАЯ СИНХРОНИЗАЦИЯ =====
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    console.log('SW: Фоновая синхронизация...');
    
    // Здесь можно добавить логику синхронизации данных
    // Например, отправка отложенных запросов
    
    try {
        // Обновляем критические данные
        const cache = await caches.open(DYNAMIC_CACHE_NAME);
        
        for (const pattern of API_CACHE_PATTERNS) {
            // Логика обновления API данных
        }
        
        console.log('SW: Фоновая синхронизация завершена');
    } catch (error) {
        console.error('SW: Ошибка фоновой синхронизации:', error);
        throw error;
    }
}

console.log('SW: Service Worker загружен успешно');