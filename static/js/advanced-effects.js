// ===== УЛУЧШЕННЫЕ JAVASCRIPT ЭФФЕКТЫ =====

class AdvancedEffects {
    constructor() {
        this.init();
        this.setupThemeToggle();
        this.setupAdvancedAnimations();
        this.setupParticles();
        this.setupIntersectionObserver();
        this.setupAdvancedScrollEffects();
        this.setupCursorEffects();
        this.setupPerformanceOptimizations();
    }

    init() {
        console.log('🎨 Инициализация расширенных визуальных эффектов...');
        
        // Initialize AOS with enhanced settings
        if (typeof AOS !== 'undefined') {
            AOS.init({
                duration: 1200,
                easing: 'ease-out-cubic',
                once: false,
                offset: 50,
                anchorPlacement: 'top-bottom'
            });
        }
        
        // Setup advanced smooth scrolling
        this.setupSmoothScrolling();
        
        // Setup time update
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
    }

    setupThemeToggle() {
        // Create theme toggle button
        const themeToggle = document.createElement('div');
        themeToggle.className = 'theme-toggle';
        themeToggle.title = 'Переключить тему (Ctrl+D)';
        themeToggle.innerHTML = '<div class="theme-toggle-ball"></div>';
        document.body.appendChild(themeToggle);

        // Get current theme
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);

        // Theme toggle functionality
        themeToggle.addEventListener('click', () => {
            this.toggleTheme();
        });

        // Keyboard shortcut for theme toggle
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // Add transition class
        document.documentElement.classList.add('theme-transition');
        
        // Change theme
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Show theme change notification
        this.showToast(`🎨 Переключено на ${newTheme === 'dark' ? 'темную' : 'светлую'} тему`, 'success', 2000);
        
        // Remove transition class after animation
        setTimeout(() => {
            document.documentElement.classList.remove('theme-transition');
        }, 300);
        
        // Refresh AOS animations
        if (typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    }

    setupAdvancedAnimations() {
        // Enhanced loading animations for cards
        this.createAdvancedLoadingAnimations();
        
        // Setup stagger animations for lists
        this.setupStaggerAnimations();
        
        // Setup morphing animations
        this.setupMorphingAnimations();
        
        // Setup text reveal animations
        this.setupTextRevealAnimations();
    }

    createAdvancedLoadingAnimations() {
        const style = document.createElement('style');
        style.textContent = `
            .advanced-loader {
                position: relative;
                width: 60px;
                height: 60px;
                margin: 0 auto 20px;
            }
            
            .advanced-loader::before,
            .advanced-loader::after {
                content: '';
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                border: 3px solid transparent;
                border-top: 3px solid var(--primary-gradient);
                animation: spinAdvanced 1s linear infinite;
            }
            
            .advanced-loader::after {
                border-top: 3px solid var(--success-gradient);
                animation-delay: 0.5s;
                animation-direction: reverse;
            }
            
            @keyframes spinAdvanced {
                0% { transform: rotate(0deg) scale(1); }
                50% { transform: rotate(180deg) scale(1.1); }
                100% { transform: rotate(360deg) scale(1); }
            }
            
            .pulse-ring {
                position: relative;
                display: inline-block;
            }
            
            .pulse-ring::before {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 100%;
                height: 100%;
                border: 2px solid var(--primary-gradient);
                border-radius: 50%;
                transform: translate(-50%, -50%);
                animation: pulseRing 2s ease-out infinite;
            }
            
            @keyframes pulseRing {
                0% {
                    transform: translate(-50%, -50%) scale(0.8);
                    opacity: 1;
                }
                100% {
                    transform: translate(-50%, -50%) scale(2.5);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    setupStaggerAnimations() {
        // Stagger animation for statistics cards
        const statsCards = document.querySelectorAll('.stats-card');
        statsCards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('animate-fade-scale');
        });
        
        // Stagger animation for navigation items
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach((link, index) => {
            link.style.animationDelay = `${index * 0.05}s`;
        });
    }

    setupMorphingAnimations() {
        const morphingElements = document.querySelectorAll('.glass-morphism');
        morphingElements.forEach(element => {
            element.addEventListener('mouseenter', () => {
                element.classList.add('animate-morph');
            });
            
            element.addEventListener('mouseleave', () => {
                element.classList.remove('animate-morph');
            });
        });
    }

    setupTextRevealAnimations() {
        const titles = document.querySelectorAll('.section-title');
        titles.forEach(title => {
            const text = title.textContent;
            title.innerHTML = text.split('').map((char, index) => 
                `<span style="animation-delay: ${index * 0.05}s" class="char-reveal">${char}</span>`
            ).join('');
        });
        
        const style = document.createElement('style');
        style.textContent = `
            .char-reveal {
                opacity: 0;
                transform: translateY(20px);
                animation: charReveal 0.8s ease-out forwards;
            }
            
            @keyframes charReveal {
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }

    setupParticles() {
        const particlesContainer = document.getElementById('particles');
        if (!particlesContainer) return;
        
        // Clear existing particles
        particlesContainer.innerHTML = '';
        
        const particleCount = window.innerWidth < 768 ? 30 : 60;
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.classList.add('particle');
            particle.style.left = Math.random() * 100 + '%';
            particle.style.width = particle.style.height = Math.random() * 8 + 2 + 'px';
            particle.style.animationDelay = Math.random() * 20 + 's';
            particle.style.animationDuration = (Math.random() * 15 + 15) + 's';
            
            // Add random colors for particles
            const colors = ['rgba(167, 233, 47, 0.1)', 'rgba(79, 172, 254, 0.1)', 'rgba(255, 255, 255, 0.05)'];
            particle.style.background = colors[Math.floor(Math.random() * colors.length)];
            
            particlesContainer.appendChild(particle);
        }
        
        console.log(`✨ Создано ${particleCount} частиц`);
    }

    setupIntersectionObserver() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    
                    // Add special effects for different elements
                    if (entry.target.classList.contains('stats-card')) {
                        this.animateNumbers(entry.target);
                    }
                    
                    if (entry.target.classList.contains('chart-container')) {
                        this.addChartGlow(entry.target);
                    }
                }
            });
        }, observerOptions);
        
        // Observe elements
        document.querySelectorAll('.fade-in-up, .stats-card, .chart-container').forEach(el => {
            el.classList.add('fade-in-up');
            observer.observe(el);
        });
    }

    setupAdvancedScrollEffects() {
        let ticking = false;
        
        const updateScrollEffects = () => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            const opacity = 1 - scrolled / window.innerHeight;
            
            // Parallax effect for header
            const header = document.querySelector('.header-section');
            if (header) {
                header.style.transform = `translate3d(0, ${rate}px, 0)`;
                header.style.opacity = Math.max(opacity, 0.3);
            }
            
            // Update progress bar
            const progressBar = document.getElementById('scrollProgress');
            if (progressBar) {
                const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
                const scrollPercent = (scrolled / documentHeight) * 100;
                progressBar.style.width = scrollPercent + '%';
                
                // Add glow effect when scrolling
                if (scrollPercent > 0) {
                    progressBar.style.boxShadow = `0 0 10px rgba(167, 233, 47, 0.6)`;
                } else {
                    progressBar.style.boxShadow = 'none';
                }
            }
            
            // Show/hide FAB based on scroll position
            const fab = document.querySelector('.fab');
            if (fab) {
                if (scrolled > 300) {
                    fab.style.opacity = '1';
                    fab.style.transform = 'scale(1)';
                } else {
                    fab.style.opacity = '0';
                    fab.style.transform = 'scale(0.8)';
                }
            }
            
            ticking = false;
        };
        
        const requestScrollUpdate = () => {
            if (!ticking) {
                requestAnimationFrame(updateScrollEffects);
                ticking = true;
            }
        };
        
        window.addEventListener('scroll', requestScrollUpdate, { passive: true });
        
        // Initial call
        updateScrollEffects();
    }

    setupCursorEffects() {
        if (window.innerWidth < 768) return; // Skip on mobile
        
        // Create cursor trail
        const cursor = document.createElement('div');
        cursor.className = 'cursor-trail';
        cursor.style.cssText = `
            position: fixed;
            width: 20px;
            height: 20px;
            background: radial-gradient(circle, rgba(167, 233, 47, 0.6), transparent);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            transition: transform 0.1s ease;
            mix-blend-mode: difference;
        `;
        document.body.appendChild(cursor);
        
        document.addEventListener('mousemove', (e) => {
            cursor.style.left = e.clientX - 10 + 'px';
            cursor.style.top = e.clientY - 10 + 'px';
        });
        
        // Add hover effects for interactive elements
        const interactiveElements = document.querySelectorAll('a, button, .btn, .card, .stats-card');
        interactiveElements.forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursor.style.transform = 'scale(2)';
                cursor.style.background = 'radial-gradient(circle, rgba(79, 172, 254, 0.6), transparent)';
            });
            
            el.addEventListener('mouseleave', () => {
                cursor.style.transform = 'scale(1)';
                cursor.style.background = 'radial-gradient(circle, rgba(167, 233, 47, 0.6), transparent)';
            });
        });
    }

    setupPerformanceOptimizations() {
        // Debounce resize events
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.setupParticles();
                if (typeof AOS !== 'undefined') {
                    AOS.refresh();
                }
            }, 250);
        });
        
        // Lazy load images
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }

    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = anchor.getAttribute('href');
                const target = document.querySelector(targetId);
                
                if (target) {
                    const headerOffset = 100;
                    const elementPosition = target.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                    
                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                    
                    // Add highlight effect
                    target.style.boxShadow = '0 0 20px rgba(167, 233, 47, 0.5)';
                    setTimeout(() => {
                        target.style.boxShadow = '';
                    }, 2000);
                }
            });
        });
    }

    animateNumbers(card) {
        const numberElement = card.querySelector('h2');
        if (!numberElement) return;
        
        const finalNumber = parseFloat(numberElement.textContent.replace(/[^\d.-]/g, ''));
        if (isNaN(finalNumber)) return;
        
        const duration = 2000;
        const startTime = Date.now();
        const startNumber = 0;
        
        const updateNumber = () => {
            const currentTime = Date.now();
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            const currentNumber = startNumber + (finalNumber - startNumber) * easeOutCubic;
            
            if (numberElement.textContent.includes('км/ч')) {
                numberElement.textContent = currentNumber.toFixed(1);
            } else if (numberElement.textContent.includes('км²')) {
                numberElement.textContent = Math.floor(currentNumber);
            } else {
                numberElement.textContent = Math.floor(currentNumber).toLocaleString();
            }
            
            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            }
        };
        
        requestAnimationFrame(updateNumber);
    }

    addChartGlow(container) {
        container.style.boxShadow = '0 0 30px rgba(167, 233, 47, 0.3)';
        setTimeout(() => {
            container.style.boxShadow = '';
        }, 3000);
    }

    scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    showToast(message, type = 'info', duration = 3000) {
        // Remove existing toasts
        document.querySelectorAll('.toast-notification').forEach(toast => {
            toast.remove();
        });
        
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <span class="me-2">${message}</span>
                <button class="btn-close btn-close-white ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
        });
        
        // Auto remove
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 400);
        }, duration);
    }

    updateTime() {
        const timeElement = document.getElementById('current-time');
        if (!timeElement) return;
        
        const now = new Date();
        const timeString = now.toLocaleString('ru-RU', {
            timeZone: 'Asia/Almaty',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        timeElement.textContent = `Астана: ${timeString}`;
    }
}

// Enhanced loading functions
function showLoadingToast() {
    if (window.advancedEffects) {
        window.advancedEffects.showToast('🤖 Запускаем AI-анализ данных...', 'info', 3000);
    }
}

function showSuccessToast() {
    if (window.advancedEffects) {
        window.advancedEffects.showToast('🎉 Геоаналитическая панель готова к использованию!', 'success', 5000);
    }
}

function scrollToTop() {
    if (window.advancedEffects) {
        window.advancedEffects.scrollToTop();
    } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.advancedEffects = new AdvancedEffects();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedEffects;
}