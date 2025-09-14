// ===== ОПТИМИЗИРОВАННАЯ СИСТЕМА UI =====

class OptimizedUI {
    constructor() {
        this.notifications = [];
        this.modals = new Map();
        this.tooltips = new Map();
        this.init();
    }

    init() {
        // Быстрая инициализация только критических элементов
        this.setupPageLoader();
        this.setupNotificationSystem();
        this.setupTooltips();
        this.setupTabSystem();
        this.setupAccordions();
        this.setupContextMenus();
        this.setupModalSystem();
        
        console.log('✅ Оптимизированный UI инициализирован');
    }

    // Система загрузки страницы
    setupPageLoader() {
        const loader = document.createElement('div');
        loader.className = 'page-loader';
        loader.id = 'pageLoader';
        document.body.appendChild(loader);

        // Анимация загрузки
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) {
                progress = 90;
                clearInterval(interval);
            }
            loader.style.width = progress + '%';
        }, 100);

        // Завершение загрузки
        window.addEventListener('load', () => {
            loader.style.width = '100%';
            setTimeout(() => {
                loader.style.opacity = '0';
                setTimeout(() => loader.remove(), 300);
            }, 200);
        });
    }

    // Система уведомлений
    setupNotificationSystem() {
        this.notificationContainer = document.createElement('div');
        this.notificationContainer.id = 'notification-container';
        this.notificationContainer.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 3000;
            pointer-events: none;
        `;
        document.body.appendChild(this.notificationContainer);
    }

    showNotification(message, type = 'info', duration = 4000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center;">
                    <span style="margin-right: 10px;">${this.getNotificationIcon(type)}</span>
                    <span>${message}</span>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; color: white; font-size: 18px; cursor: pointer; padding: 0; margin-left: 10px;">×</button>
            </div>
        `;
        
        this.notificationContainer.appendChild(notification);
        
        // Анимация появления
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Автоудаление
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 400);
        }, duration);
        
        return notification;
    }

    getNotificationIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    // Система всплывающих подсказок
    setupTooltips() {
        document.addEventListener('mouseenter', (e) => {
            if (e.target.hasAttribute('data-tooltip')) {
                this.showTooltip(e.target);
            }
        }, true);

        document.addEventListener('mouseleave', (e) => {
            if (e.target.hasAttribute('data-tooltip')) {
                this.hideTooltip(e.target);
            }
        }, true);
    }

    showTooltip(element) {
        const text = element.getAttribute('data-tooltip');
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip-popup';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: absolute;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
            z-index: 4000;
            pointer-events: none;
            white-space: nowrap;
            opacity: 0;
            transition: opacity 0.2s;
        `;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
        
        requestAnimationFrame(() => {
            tooltip.style.opacity = '1';
        });
        
        this.tooltips.set(element, tooltip);
    }

    hideTooltip(element) {
        const tooltip = this.tooltips.get(element);
        if (tooltip) {
            tooltip.style.opacity = '0';
            setTimeout(() => tooltip.remove(), 200);
            this.tooltips.delete(element);
        }
    }

    // Система вкладок
    setupTabSystem() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-button')) {
                this.switchTab(e.target);
            }
        });
    }

    switchTab(button) {
        const container = button.closest('.tabs-container');
        const tabId = button.getAttribute('data-tab');
        
        // Убираем активность со всех кнопок и содержимого
        container.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        container.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Активируем выбранную вкладку
        button.classList.add('active');
        const content = container.querySelector(`[data-tab-content="${tabId}"]`);
        if (content) {
            content.classList.add('active');
        }
    }

    // Система аккордеонов
    setupAccordions() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('accordion-header') || e.target.closest('.accordion-header')) {
                const header = e.target.classList.contains('accordion-header') ? e.target : e.target.closest('.accordion-header');
                this.toggleAccordion(header);
            }
        });
    }

    toggleAccordion(header) {
        const content = header.nextElementSibling;
        const isActive = content.classList.contains('active');
        
        if (isActive) {
            content.classList.remove('active');
            content.style.maxHeight = '0';
        } else {
            content.classList.add('active');
            content.style.maxHeight = content.scrollHeight + 'px';
        }
    }

    // Контекстные меню
    setupContextMenus() {
        document.addEventListener('contextmenu', (e) => {
            if (e.target.hasAttribute('data-context-menu')) {
                e.preventDefault();
                this.showContextMenu(e, e.target.getAttribute('data-context-menu'));
            }
        });

        document.addEventListener('click', () => {
            this.hideContextMenus();
        });
    }

    showContextMenu(e, menuId) {
        this.hideContextMenus();
        
        const menu = document.getElementById(menuId);
        if (menu) {
            menu.style.display = 'block';
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
            
            // Проверяем границы экрана
            const rect = menu.getBoundingClientRect();
            if (rect.right > window.innerWidth) {
                menu.style.left = e.pageX - rect.width + 'px';
            }
            if (rect.bottom > window.innerHeight) {
                menu.style.top = e.pageY - rect.height + 'px';
            }
        }
    }

    hideContextMenus() {
        document.querySelectorAll('.context-menu').forEach(menu => {
            menu.style.display = 'none';
        });
    }

    // Система модальных окон
    setupModalSystem() {
        document.addEventListener('click', (e) => {
            if (e.target.hasAttribute('data-modal')) {
                this.showModal(e.target.getAttribute('data-modal'));
            }
            if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('modal-close')) {
                this.hideModal(e.target.closest('.modal-overlay'));
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideAllModals();
            }
        });
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    hideModal(modal) {
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    hideAllModals() {
        document.querySelectorAll('.modal-overlay.active').forEach(modal => {
            this.hideModal(modal);
        });
    }

    // Создание модального окна программно
    createModal(title, content, options = {}) {
        const modalId = 'modal-' + Date.now();
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.id = modalId;
        modal.innerHTML = `
            <div class="modal-content">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: white;">${title}</h4>
                    <button class="modal-close" style="background: none; border: none; color: white; font-size: 24px; cursor: pointer;">×</button>
                </div>
                <div>${content}</div>
                ${options.footer ? `<div style="margin-top: 1.5rem; text-align: right;">${options.footer}</div>` : ''}
            </div>
        `;
        
        document.body.appendChild(modal);
        this.showModal(modalId);
        
        return modal;
    }

    // Система прогресс-баров
    createProgressBar(container, value = 0, options = {}) {
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-enhanced';
        progressBar.innerHTML = `
            <div class="progress-bar-enhanced" style="width: ${value}%"></div>
        `;
        
        if (typeof container === 'string') {
            document.getElementById(container).appendChild(progressBar);
        } else {
            container.appendChild(progressBar);
        }
        
        return {
            setValue: (newValue) => {
                const bar = progressBar.querySelector('.progress-bar-enhanced');
                bar.style.width = newValue + '%';
            },
            element: progressBar
        };
    }

    // Drag and Drop
    setupDragAndDrop(element, options = {}) {
        element.addEventListener('dragover', (e) => {
            e.preventDefault();
            element.classList.add('dragover');
        });

        element.addEventListener('dragleave', () => {
            element.classList.remove('dragover');
        });

        element.addEventListener('drop', (e) => {
            e.preventDefault();
            element.classList.remove('dragover');
            
            const files = Array.from(e.dataTransfer.files);
            if (options.onDrop) {
                options.onDrop(files);
            }
        });
    }

    // Утилиты для работы с данными
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    formatNumber(num) {
        return new Intl.NumberFormat('ru-RU').format(num);
    }

    // Debounce функция
    debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }
}

// Глобальная инициализация
let optimizedUI;

document.addEventListener('DOMContentLoaded', () => {
    optimizedUI = new OptimizedUI();
    
    // Делаем доступным глобально для совместимости
    window.showNotification = (message, type, duration) => {
        return optimizedUI.showNotification(message, type, duration);
    };
    
    window.createModal = (title, content, options) => {
        return optimizedUI.createModal(title, content, options);
    };
    
    window.createProgressBar = (container, value, options) => {
        return optimizedUI.createProgressBar(container, value, options);
    };
});

// Экспорт для модульного использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OptimizedUI;
}