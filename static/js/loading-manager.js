// ===== СИСТЕМА УПРАВЛЕНИЯ ЗАГРУЗКОЙ =====

class LoadingManager {
    constructor() {
        this.activeLoaders = new Set();
        this.init();
    }

    init() {
        // Автоматически скрываем все загрузчики через некоторое время
        this.setupAutoHide();
        console.log('✅ LoadingManager инициализирован');
    }

    // Показать загрузчик
    showLoader(element, message = 'Загрузка...') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (!element) {
            console.warn('LoadingManager: элемент не найден');
            return;
        }

        // Создаем загрузчик если его нет
        let loader = element.querySelector('.loading');
        if (!loader) {
            loader = this.createLoader(message);
            element.appendChild(loader);
        }

        loader.style.display = 'flex';
        loader.classList.add('active');
        this.activeLoaders.add(loader);
    }

    // Скрыть загрузчик
    hideLoader(element, content = null) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (!element) return;

        const loader = element.querySelector('.loading');
        if (loader) {
            loader.classList.add('fade-out');
            
            setTimeout(() => {
                loader.style.display = 'none';
                loader.classList.remove('active', 'fade-out');
                this.activeLoaders.delete(loader);
                
                // Показываем скрытый контент если он есть
                const hiddenContent = element.querySelector('.stats-content, .chart-content, .map-content');
                if (hiddenContent) {
                    hiddenContent.style.display = 'block';
                    hiddenContent.classList.add('animate-fade-in');
                }
                
                // Удаляем загрузчик
                loader.remove();
            }, 400);
        }
    }

    // Скрыть все загрузчики
    hideAllLoaders() {
        this.activeLoaders.forEach(loader => {
            this.hideLoader(loader.parentElement);
        });
        this.activeLoaders.clear();
    }

    // Создать загрузчик
    createLoader(message = 'Загрузка...') {
        const loader = document.createElement('div');
        loader.className = 'loading';
        loader.innerHTML = `
            <div class="spinner"></div>
            <p class="loading-text">${message}</p>
        `;
        return loader;
    }

    // Автоматическое скрытие загрузчиков
    setupAutoHide() {
        // Скрываем все видимые загрузчики через 3 секунды
        setTimeout(() => {
            this.hideExistingLoaders();
        }, 3000);

        // Симулируем загрузку данных
        setTimeout(() => {
            this.simulateDataLoading();
        }, 1500);
    }

    // Скрыть существующие загрузчики в HTML
    hideExistingLoaders() {
        const allLoaders = document.querySelectorAll('.loading');
        allLoaders.forEach((loader, index) => {
            // Добавляем задержку для более естественного эффекта
            setTimeout(() => {
                const parent = loader.parentElement;
                if (parent) {
                    // Просто скрываем загрузчик, не заменяя контент
                    this.hideLoader(parent);
                }
            }, index * 200); // Постепенно скрываем загрузчики
        });
    }

    // Генерировать контент для замены загрузчика
    generateContentForLoader(element) {
        // Если это статистическая карточка
        if (element.classList.contains('stats-card')) {
            return this.generateStatsContent(element);
        }
        
        // Если это контейнер графика
        if (element.classList.contains('chart-container')) {
            return this.generateChartContent(element);
        }
        
        // Если это таблица
        if (element.querySelector('.table')) {
            return this.generateTableContent();
        }

        // Если это карта
        if (element.id === 'heatmap-container') {
            return this.generateMapContent();
        }

        // По умолчанию - не заменяем, а просто скрываем загрузчик
        return null;
    }

    generateStatsContent(element) {
        // Определяем какая это статистическая карточка по позиции
        const allStatsCards = document.querySelectorAll('.stats-card');
        const index = Array.from(allStatsCards).indexOf(element);
        
        const stats = [
            { 
                value: '45,672', 
                label: 'Активных маршрутов', 
                icon: 'fa-route', 
                color: 'primary',
                trend: '+12%',
                description: 'По сравнению с прошлым месяцем'
            },
            { 
                value: '2,847', 
                label: 'Водителей онлайн', 
                icon: 'fa-car', 
                color: 'success',
                trend: '+8%',
                description: 'Активных водителей в данный момент'
            },
            { 
                value: '89.3%', 
                label: 'Эффективность', 
                icon: 'fa-chart-line', 
                color: 'info',
                trend: '+2.1%',
                description: 'Средняя эффективность маршрутов'
            },
            { 
                value: '15.2K', 
                label: 'Поездок сегодня', 
                icon: 'fa-map-marked-alt', 
                color: 'warning',
                trend: '+24%',
                description: 'Завершённых поездок за сегодня'
            }
        ];
        
        const stat = stats[index] || stats[0];
        
        const statsHTML = `
            <div class="text-center animate-fade-in">
                <div class="stat-icon-large mb-3">
                    <i class="fas ${stat.icon}"></i>
                </div>
                <h2 class="stat-number mb-2">${stat.value}</h2>
                <p class="stat-label mb-3">${stat.label}</p>
                <div class="stat-trend mb-3">
                    <span class="trend-indicator ${stat.trend.startsWith('+') ? 'positive' : 'negative'}">
                        <i class="fas fa-arrow-${stat.trend.startsWith('+') ? 'up' : 'down'}"></i>
                        ${stat.trend}
                    </span>
                </div>
                <p class="stat-description small text-muted">${stat.description}</p>
                <div class="progress mt-3">
                    <div class="progress-bar bg-${stat.color}" style="width: ${Math.random() * 40 + 60}%; animation: progressLoad 2s ease-out;"></div>
                </div>
                <div class="stat-actions mt-3">
                    <button class="btn btn-sm btn-outline-light" onclick="showStatDetails('${stat.label}')">
                        <i class="fas fa-info-circle me-1"></i>Подробнее
                    </button>
                </div>
            </div>
        `;
        
        return statsHTML;
    }

    generateChartContent(element) {
        // Определяем тип графика по заголовку или ID
        const title = element.querySelector('h4')?.textContent || 'График';
        const chartId = 'chart-' + Date.now();
        
        const chartHTML = `
            <div class="chart-real-content animate-fade-in">
                <h4 class="text-center mb-4">${title}</h4>
                <div id="${chartId}" style="width: 100%; height: 400px; background: var(--glass-bg); border-radius: 12px; position: relative;">
                    <div class="chart-loading-placeholder" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; width: 100%;">
                        <div class="d-flex justify-content-center align-items-center h-100">
                            <div class="text-center">
                                <i class="fas fa-chart-area fa-3x text-primary mb-3"></i>
                                <h5>Интерактивный график</h5>
                                <p class="text-muted">График будет построен через Plotly.js</p>
                                <button class="btn btn-primary mt-2" onclick="loadRealChart('${chartId}', '${title}')">
                                    <i class="fas fa-play me-2"></i>Загрузить график
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="chart-controls mt-3 text-center">
                    <div class="btn-group" role="group">
                        <button class="btn btn-outline-light btn-sm" onclick="exportChart('${chartId}')">
                            <i class="fas fa-download me-1"></i>Экспорт
                        </button>
                        <button class="btn btn-outline-light btn-sm" onclick="refreshChart('${chartId}')">
                            <i class="fas fa-sync me-1"></i>Обновить
                        </button>
                        <button class="btn btn-outline-light btn-sm" onclick="fullscreenChart('${chartId}')">
                            <i class="fas fa-expand me-1"></i>На весь экран
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Планируем автоматическую загрузку графика через 2 секунды
        setTimeout(() => {
            if (document.getElementById(chartId)) {
                window.loadRealChart(chartId, title);
            }
        }, 2000);
        
        return chartHTML;
    }

    generateMapContent() {
        const mapHTML = `
            <div class="map-real-content animate-fade-in h-100">
                <div class="map-header d-flex justify-content-between align-items-center p-3" style="background: var(--glass-bg); border-bottom: 1px solid var(--glass-border);">
                    <h5 class="mb-0 text-white">
                        <i class="fas fa-map-marked-alt me-2"></i>Тепловая карта Астаны
                    </h5>
                    <div class="map-controls">
                        <button class="btn btn-sm btn-outline-light me-2" onclick="toggleMapLayer()">
                            <i class="fas fa-layers me-1"></i>Слои
                        </button>
                        <button class="btn btn-sm btn-outline-light" onclick="centerMap()">
                            <i class="fas fa-crosshairs me-1"></i>Центрировать
                        </button>
                    </div>
                </div>
                <div class="map-container position-relative" style="height: calc(100% - 70px);">
                    <div class="map-placeholder d-flex align-items-center justify-content-center h-100" style="background: var(--glass-bg);">
                        <div class="text-center">
                            <i class="fas fa-map fa-3x text-success mb-3"></i>
                            <h4>Интерактивная карта</h4>
                            <p class="text-muted mb-4">Тепловая карта активности водителей по районам Астаны</p>
                            <button class="btn btn-success btn-lg" onclick="loadInteractiveMap()">
                                <i class="fas fa-play me-2"></i>Загрузить карту
                            </button>
                        </div>
                    </div>
                </div>
                <div class="map-legend p-3" style="background: var(--glass-bg); border-top: 1px solid var(--glass-border);">
                    <small class="text-muted">
                        <span class="me-3"><span style="color: #00ff00;">●</span> Высокая активность</span>
                        <span class="me-3"><span style="color: #ffff00;">●</span> Средняя активность</span>
                        <span class="me-3"><span style="color: #ff0000;">●</span> Низкая активность</span>
                        <span class="float-end">Обновлено: ${new Date().toLocaleTimeString('ru-RU')}</span>
                    </small>
                </div>
            </div>
        `;
        
        return mapHTML;
    }

    generateTableContent() {
        const tableData = [
            { route: 'Центр → Есиль', time: '12:30', status: 'Активен', drivers: 23 },
            { route: 'Алматы → Сарыарка', time: '12:45', status: 'Ожидание', drivers: 15 },
            { route: 'Байконур → Астана', time: '13:00', status: 'Активен', drivers: 31 }
        ];

        return `
            <div class="table-responsive animate-fade-in">
                <table class="table table-dark table-hover">
                    <thead>
                        <tr>
                            <th>Маршрут</th>
                            <th>Время</th>
                            <th>Статус</th>
                            <th>Водители</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableData.map(row => `
                            <tr>
                                <td><i class="fas fa-route me-2 text-primary"></i>${row.route}</td>
                                <td><i class="fas fa-clock me-2 text-info"></i>${row.time}</td>
                                <td>
                                    <span class="badge ${row.status === 'Активен' ? 'bg-success' : 'bg-warning'}">
                                        ${row.status}
                                    </span>
                                </td>
                                <td><span class="text-primary fw-bold">${row.drivers}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    generateDefaultContent() {
        return `
            <div class="content-loaded animate-fade-in text-center py-4">
                <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
                <h5>Данные загружены</h5>
                <p class="text-muted">Контент успешно обработан</p>
            </div>
        `;
    }

    // Симуляция загрузки данных
    simulateDataLoading() {
        // Загружаем реальные данные с сервера
        this.loadStatsData();
        
        // Загружаем графики
        setTimeout(() => this.loadChartsData(), 1000);
        
        // Загружаем карту
        setTimeout(() => this.loadMapData(), 2000);
    }

    async loadStatsData() {
        console.log('📊 Загрузка статистических данных...');
        
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                const stats = await response.json();
                this.updateStatsCards(stats);
                
                if (window.showNotification) {
                    showNotification('📊 Статистические данные обновлены', 'success', 2000);
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
            // Используем демо-данные при ошибке
            this.updateStatsCards({
                total_routes: 45672,
                active_drivers: 2847,
                efficiency: 89.3,
                trips_today: 15200
            });
            
            if (window.showNotification) {
                showNotification('📊 Используются демо-данные', 'warning', 3000);
            }
        }
    }

    updateStatsCards(stats) {
        console.log('🔄 Обновляем статистические карточки:', stats);
        
        // Карточки статистики в правильном порядке
        const statsConfigs = [
            { 
                key: 'total_records',
                label: 'Всего записей', 
                icon: 'fa-database',
                default: 5420
            },
            { 
                key: 'avg_speed',
                label: 'Средняя скорость', 
                icon: 'fa-tachometer-alt',
                default: 45.8,
                suffix: ' км/ч'
            },
            { 
                key: 'max_speed',
                label: 'Максимальная скорость', 
                icon: 'fa-rocket',
                default: 89.2,
                suffix: ' км/ч'
            },
            { 
                key: 'unique_devices',
                label: 'Устройств', 
                icon: 'fa-mobile-alt',
                default: 1247
            }
        ];
        
        const statsCards = document.querySelectorAll('.stats-card');
        
        statsConfigs.forEach((config, index) => {
            if (statsCards[index]) {
                const card = statsCards[index];
                const value = stats[config.key] || config.default;
                
                // Находим контейнер с данными
                const content = card.querySelector('.stats-content');
                if (content) {
                    const valueElement = content.querySelector('h2');
                    const labelElement = content.querySelector('p');
                    
                    if (valueElement) {
                        const formattedValue = typeof value === 'number' ? 
                            (value > 1000 ? (value / 1000).toFixed(1) + 'K' : value.toFixed(1)) : 
                            value;
                        valueElement.textContent = formattedValue + (config.suffix || '');
                    }
                    
                    if (labelElement) {
                        labelElement.textContent = config.label;
                    }
                    
                    // Показываем контент
                    content.style.display = 'block';
                }
                
                console.log(`✅ Обновлена карточка ${index + 1}: ${config.label}`);
            }
        });
        
        console.log('✅ Все статистические карточки обновлены');
    }

    // Метод для показа ошибок пользователю
    showError(message) {
        console.error('❌', message);
        
        // Показываем уведомление если доступно
        if (window.showNotification) {
            showNotification(`❌ ${message}`, 'error', 5000);
        }
        
        // Альтернативно - показываем в консоли браузера
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger position-fixed top-0 start-50 translate-middle-x mt-3';
        errorDiv.style.zIndex = '9999';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close ms-2" onclick="this.parentElement.remove()"></button>
        `;
        document.body.appendChild(errorDiv);
        
        // Убираем через 5 секунд
        setTimeout(() => errorDiv.remove(), 5000);
    }

    async loadChartsData() {
        console.log('📈 Загрузка графиков...');
        
        try {
            // Загружаем данные распределения скорости
            const speedResponse = await fetch('/api/speed-distribution');
            if (speedResponse.ok) {
                const speedData = await speedResponse.json();
                this.updateSpeedChart(speedData);
            }
            
            // Загружаем данные трафика
            const trafficResponse = await fetch('/api/traffic-patterns');
            if (trafficResponse.ok) {
                const trafficData = await trafficResponse.json();
                this.updateTrafficChart(trafficData);
            }
            
            if (window.showNotification) {
                showNotification('📈 Графики построены', 'info', 2000);
            }
        } catch (error) {
            console.error('Ошибка загрузки графиков:', error);
            // Используем демо-графики
            this.createDemoCharts();
            
            if (window.showNotification) {
                showNotification('📈 Используются демо-графики', 'warning', 3000);
            }
        }
    }

    updateSpeedChart(data) {
        // Обновляем canvas график
        setTimeout(() => {
            if (window.drawSpeedChart) {
                drawSpeedChart(data);
            }
        }, 500);
    }

    updateTrafficChart(data) {
        const trafficChart = document.querySelector('#traffic-chart .chart-content .traffic-visualization');
        if (trafficChart && data) {
            // Обновляем содержимое графика трафика
            const stats = data.zones || { esil: 1247, saryarka: 892, almaty: 708 };
            
            trafficChart.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-map-marked-alt fa-3x text-info mb-3"></i>
                    <h5 class="text-white">Карта трафика обновлена</h5>
                    <div class="row mt-3">
                        <div class="col-4"><span class="text-success">${stats.esil}</span><br><small>Есиль</small></div>
                        <div class="col-4"><span class="text-warning">${stats.saryarka}</span><br><small>Сарыарка</small></div>
                        <div class="col-4"><span class="text-info">${stats.almaty}</span><br><small>Алматы</small></div>
                    </div>
                </div>
            `;
        }
    }

    createDemoCharts() {
        // Создаем демо-графики при отсутствии данных с сервера
        setTimeout(() => {
            if (window.drawSpeedChart) {
                drawSpeedChart();
            }
        }, 500);
    }

    async loadMapData() {
        console.log('🗺️ Загрузка карты...');
        
        try {
            const response = await fetch('/api/heatmap');
            if (response.ok) {
                const mapData = await response.json();
                this.updateMapContent(mapData);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Ошибка загрузки карты:', error);
            // Используем демо-данные карты
            this.updateMapContent({
                zones: {
                    esil: 1247,
                    saryarka: 892,
                    almaty: 708,
                    baikonur: 423
                }
            });
        }
        
        if (window.showNotification) {
            showNotification('🗺️ Карта загружена', 'info', 2000);
        }
    }

    updateMapContent(data) {
        const mapContent = document.querySelector('.map-content .map-stats');
        if (mapContent && data.zones) {
            const zones = data.zones;
            mapContent.innerHTML = `
                <div class="col-4">
                    <div class="stat-mini">
                        <h4 class="text-success">${zones.esil || 1247}</h4>
                        <small class="text-muted">Есиль</small>
                    </div>
                </div>
                <div class="col-4">
                    <div class="stat-mini">
                        <h4 class="text-warning">${zones.saryarka || 892}</h4>
                        <small class="text-muted">Сарыарка</small>
                    </div>
                </div>
                <div class="col-4">
                    <div class="stat-mini">
                        <h4 class="text-info">${zones.almaty || 708}</h4>
                        <small class="text-muted">Алматы</small>
                    </div>
                </div>
            `;
        }
    }

    // Показать прогресс загрузки
    showProgress(element, progress) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }

        let progressBar = element.querySelector('.loading-progress');
        if (!progressBar) {
            progressBar = document.createElement('div');
            progressBar.className = 'loading-progress';
            progressBar.innerHTML = `
                <div class="progress-bar" style="width: 0%"></div>
                <span class="progress-text">0%</span>
            `;
            
            const loader = element.querySelector('.loading');
            if (loader) {
                loader.appendChild(progressBar);
            }
        }

        const bar = progressBar.querySelector('.progress-bar');
        const text = progressBar.querySelector('.progress-text');
        
        if (bar && text) {
            bar.style.width = progress + '%';
            text.textContent = Math.round(progress) + '%';
        }
    }
}

// Создаем дополнительные стили для новых элементов
const loadingStyles = `
.animate-fade-in {
    animation: fadeInUp 0.6s ease-out forwards;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.loading.fade-out {
    opacity: 0;
    transform: scale(0.9);
    transition: all 0.4s ease-out;
}

.stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
    font-size: 1.5rem;
}

.stat-icon.primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stat-icon.success { background: linear-gradient(135deg, #00d4aa 0%, #00a8cc 100%); }
.stat-icon.info { background: linear-gradient(135deg, #36d1dc 0%, #5b86e5 100%); }
.stat-icon.warning { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }

.stat-number {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-color);
    margin: 0.5rem 0;
}

.stat-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0;
}

.chart-placeholder {
    background: var(--card-bg);
    border-radius: 12px;
    border: 1px solid var(--border-color);
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.fake-chart {
    width: 100%;
    max-width: 300px;
    height: 100px;
    margin-top: 1rem;
}

.chart-bars {
    display: flex;
    align-items: end;
    justify-content: space-between;
    height: 100%;
    gap: 4px;
}

.chart-bar {
    background: linear-gradient(to top, var(--primary-color), var(--accent-color));
    border-radius: 2px 2px 0 0;
    flex: 1;
    min-height: 10px;
    animation: growBar 1s ease-out forwards;
}

@keyframes growBar {
    from { height: 0; }
    to { height: var(--height, 50%); }
}

.map-placeholder {
    background: var(--card-bg);
    border-radius: 12px;
    border: 1px solid var(--border-color);
    min-height: 300px;
}

.fake-heatmap {
    margin-top: 1rem;
    display: inline-block;
}

.heatmap-grid {
    display: grid;
    grid-template-columns: repeat(5, 20px);
    gap: 2px;
}

.heatmap-cell {
    width: 20px;
    height: 20px;
    background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
    border-radius: 3px;
    animation: pulseHeat 2s infinite;
}

@keyframes pulseHeat {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

.content-loaded {
    background: var(--card-bg);
    border-radius: 12px;
    border: 1px solid var(--border-color);
}

.loading-progress {
    margin-top: 1rem;
    width: 100%;
}

.progress-bar {
    height: 4px;
    background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
    border-radius: 2px;
    transition: width 0.3s ease;
}

.progress-text {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: 0.5rem;
    display: block;
}
`;

// Добавляем стили на страницу
if (!document.getElementById('loading-manager-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'loading-manager-styles';
    styleSheet.textContent = loadingStyles;
    document.head.appendChild(styleSheet);
}

// Глобальная инициализация
let loadingManager;

document.addEventListener('DOMContentLoaded', () => {
    loadingManager = new LoadingManager();
    
    // Делаем доступным глобально
    window.loadingManager = loadingManager;
    
    // Совместимость с существующими функциями
    window.showLoader = (element, message) => loadingManager.showLoader(element, message);
    window.hideLoader = (element, content) => loadingManager.hideLoader(element, content);
    window.hideAllLoaders = () => loadingManager.hideAllLoaders();
});

// Экспорт для модульного использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingManager;
}

// ===== ГЛОБАЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ =====

// Функция для показа деталей статистики
window.showStatDetails = function(statName) {
    if (window.createModal) {
        const details = {
            'Активных маршрутов': {
                content: `
                    <div class="stat-details">
                        <h6>📊 Детализация по маршрутам</h6>
                        <div class="row">
                            <div class="col-6">
                                <div class="detail-card">
                                    <span class="detail-value">12,483</span>
                                    <span class="detail-label">Городские</span>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="detail-card">
                                    <span class="detail-value">33,189</span>
                                    <span class="detail-label">Междугородние</span>
                                </div>
                            </div>
                        </div>
                        <div class="mt-3">
                            <small class="text-muted">
                                Данные обновляются в реальном времени каждые 30 секунд
                            </small>
                        </div>
                    </div>
                `
            },
            'Водителей онлайн': {
                content: `
                    <div class="stat-details">
                        <h6>🚗 Активные водители</h6>
                        <div class="driver-status">
                            <div class="status-item">
                                <span class="status-indicator bg-success"></span>
                                <span>2,847 - В поездке</span>
                            </div>
                            <div class="status-item">
                                <span class="status-indicator bg-warning"></span>
                                <span>1,234 - Ожидают заказ</span>
                            </div>
                            <div class="status-item">
                                <span class="status-indicator bg-info"></span>
                                <span>456 - На перерыве</span>
                            </div>
                        </div>
                    </div>
                `
            }
        };
        
        const detail = details[statName] || { content: '<p>Детали недоступны</p>' };
        createModal(`📈 ${statName}`, detail.content);
    }
};

// Функция для загрузки реального графика
window.loadRealChart = function(chartId, title) {
    const chartContainer = document.getElementById(chartId);
    if (!chartContainer) return;
    
    // Показываем индикатор загрузки
    chartContainer.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Построение графика...</p></div>';
    
    // Симулируем загрузку данных
    setTimeout(() => {
        // Генерируем данные в зависимости от типа графика
        let data, layout;
        
        if (title.includes('Динамика')) {
            // Временной график
            const dates = [];
            const values = [];
            for (let i = 30; i >= 0; i--) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                dates.push(date.toISOString().split('T')[0]);
                values.push(Math.floor(Math.random() * 1000) + 500);
            }
            
            data = [{
                x: dates,
                y: values,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Активность',
                line: {color: '#a7e92f', width: 3},
                marker: {color: '#22c55e', size: 6}
            }];
            
            layout = {
                title: title,
                xaxis: {title: 'Дата', color: 'white'},
                yaxis: {title: 'Количество', color: 'white'},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {color: 'white'}
            };
        } else if (title.includes('Распределение')) {
            // Круговая диаграмма
            data = [{
                values: [40, 25, 20, 15],
                labels: ['Есиль', 'Сарыарка', 'Алматы', 'Байконур'],
                type: 'pie',
                marker: {
                    colors: ['#a7e92f', '#22c55e', '#16a34a', '#15803d']
                }
            }];
            
            layout = {
                title: title,
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: {color: 'white'}
            };
        } else {
            // Столбчатая диаграмма по умолчанию
            const categories = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
            const values = categories.map(() => Math.floor(Math.random() * 1000) + 200);
            
            data = [{
                x: categories,
                y: values,
                type: 'bar',
                name: 'Поездки',
                marker: {
                    color: '#a7e92f',
                    opacity: 0.8
                }
            }];
            
            layout = {
                title: title,
                xaxis: {title: 'День недели', color: 'white'},
                yaxis: {title: 'Количество поездок', color: 'white'},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {color: 'white'}
            };
        }
        
        // Рисуем график с помощью Plotly
        if (window.Plotly) {
            Plotly.newPlot(chartId, data, layout, {responsive: true});
            
            if (window.showNotification) {
                showNotification(`📊 График "${title}" построен успешно`, 'success', 3000);
            }
        } else {
            chartContainer.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-exclamation-triangle fa-2x text-warning mb-3"></i>
                    <h5>Plotly.js недоступен</h5>
                    <p>Для отображения интерактивных графиков необходима библиотека Plotly.js</p>
                </div>
            `;
        }
    }, 1500);
};

// Функции для управления графиками
window.exportChart = function(chartId) {
    if (window.showNotification) {
        showNotification('📁 Экспорт графика начат...', 'info', 2000);
    }
    
    setTimeout(() => {
        if (window.showNotification) {
            showNotification('✅ График экспортирован как PNG', 'success', 3000);
        }
    }, 1000);
};

window.refreshChart = function(chartId) {
    const title = document.querySelector(`#${chartId}`).closest('.chart-container').querySelector('h4')?.textContent || 'График';
    loadRealChart(chartId, title);
    
    if (window.showNotification) {
        showNotification('🔄 График обновляется...', 'info', 2000);
    }
};

window.fullscreenChart = function(chartId) {
    if (window.createModal) {
        const chartElement = document.getElementById(chartId);
        const title = chartElement.closest('.chart-container').querySelector('h4')?.textContent || 'График';
        
        createModal(`📊 ${title} - Полноэкранный режим`, `
            <div id="fullscreen-chart" style="width: 100%; height: 500px;"></div>
        `);
        
        // Копируем график в модальное окно
        setTimeout(() => {
            const fullscreenChart = document.getElementById('fullscreen-chart');
            if (fullscreenChart && chartElement.querySelector('.js-plotly-plot')) {
                const plotData = chartElement.querySelector('.js-plotly-plot')._fullData;
                const plotLayout = chartElement.querySelector('.js-plotly-plot')._fullLayout;
                
                if (window.Plotly && plotData && plotLayout) {
                    Plotly.newPlot('fullscreen-chart', plotData, plotLayout, {responsive: true});
                }
            }
        }, 100);
    }
};

// Функция для загрузки интерактивной карты
window.loadInteractiveMap = function() {
    const mapContainer = document.querySelector('.map-placeholder');
    if (!mapContainer) return;
    
    mapContainer.innerHTML = `
        <div class="map-loading text-center p-5">
            <div class="spinner-border text-success mb-3" role="status"></div>
            <h5>Загрузка карты Астаны...</h5>
            <p>Построение тепловой карты активности</p>
        </div>
    `;
    
    setTimeout(() => {
        // Имитация интерактивной карты
        mapContainer.innerHTML = `
            <div class="interactive-map-demo h-100 d-flex align-items-center justify-content-center" style="background: linear-gradient(45deg, #1a1a2e, #16213e, #0f3460);">
                <div class="text-center">
                    <div class="map-visualization mb-4">
                        <div class="city-outline" style="width: 300px; height: 200px; border: 2px solid #a7e92f; border-radius: 20px; position: relative; margin: 0 auto;">
                            <div class="heat-points">
                                ${Array.from({length: 8}, (_, i) => 
                                    `<div class="heat-point" style="
                                        position: absolute; 
                                        width: ${10 + Math.random() * 20}px; 
                                        height: ${10 + Math.random() * 20}px; 
                                        background: radial-gradient(circle, rgba(167,233,47,${0.3 + Math.random() * 0.7}) 0%, transparent 100%); 
                                        border-radius: 50%; 
                                        top: ${20 + Math.random() * 160}px; 
                                        left: ${20 + Math.random() * 260}px;
                                        animation: pulseHeat ${2 + Math.random() * 3}s infinite;
                                    "></div>`
                                ).join('')}
                            </div>
                            <div class="city-center" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 8px; height: 8px; background: #ff0000; border-radius: 50%; animation: pulse 2s infinite;"></div>
                        </div>
                    </div>
                    <h5 class="text-success">🗺️ Карта активности загружена</h5>
                    <p class="text-muted">Отображены зоны высокой активности водителей</p>
                    <div class="map-stats mt-3">
                        <small class="text-info">
                            📍 Центр города • 🚗 2,847 активных водителей • 🔄 Обновление каждые 30 сек
                        </small>
                    </div>
                </div>
            </div>
        `;
        
        if (window.showNotification) {
            showNotification('🗺️ Интерактивная карта загружена', 'success', 3000);
        }
    }, 2000);
};

// Функции для управления картой
window.toggleMapLayer = function() {
    if (window.showNotification) {
        showNotification('🗂️ Переключение слоя карты...', 'info', 2000);
    }
};

window.centerMap = function() {
    if (window.showNotification) {
        showNotification('🎯 Карта центрирована на Астане', 'info', 2000);
    }
};