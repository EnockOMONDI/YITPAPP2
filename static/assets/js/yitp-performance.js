/**
 * YITP Performance Optimization Script
 * Handles lazy loading, image optimization, and performance monitoring
 */

(function() {
    'use strict';

    // Performance monitoring
    const YITPPerformance = {
        // Initialize performance monitoring
        init: function() {
            this.setupLazyLoading();
            this.setupImageOptimization();
            this.setupCriticalResourceHints();
            this.monitorCoreWebVitals();
            this.setupServiceWorker();
        },

        // Lazy loading for images and iframes
        setupLazyLoading: function() {
            if ('IntersectionObserver' in window) {
                const lazyImages = document.querySelectorAll('img[data-src], iframe[data-src]');
                const imageObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.classList.remove('lazy');
                            img.classList.add('loaded');
                            observer.unobserve(img);
                        }
                    });
                }, {
                    rootMargin: '50px 0px',
                    threshold: 0.01
                });

                lazyImages.forEach(img => imageObserver.observe(img));
            } else {
                // Fallback for browsers without IntersectionObserver
                const lazyImages = document.querySelectorAll('img[data-src]');
                lazyImages.forEach(img => {
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    img.classList.add('loaded');
                });
            }
        },

        // Image optimization and WebP support
        setupImageOptimization: function() {
            // Check WebP support
            const supportsWebP = (function() {
                const canvas = document.createElement('canvas');
                canvas.width = 1;
                canvas.height = 1;
                return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
            })();

            if (supportsWebP) {
                document.documentElement.classList.add('webp');
                
                // Replace image sources with WebP versions if available
                const images = document.querySelectorAll('img[data-webp]');
                images.forEach(img => {
                    img.src = img.dataset.webp;
                });
            }

            // Add loading="lazy" to images below the fold
            const images = document.querySelectorAll('img:not([loading])');
            images.forEach((img, index) => {
                if (index > 2) { // Skip first 3 images (likely above the fold)
                    img.setAttribute('loading', 'lazy');
                }
            });
        },

        // Setup critical resource hints
        setupCriticalResourceHints: function() {
            // Preload critical fonts
            const criticalFonts = [
                '/static/assets/fonts/inter/Inter-Regular.woff2',
                '/static/assets/fonts/inter/Inter-Bold.woff2'
            ];

            criticalFonts.forEach(font => {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.as = 'font';
                link.type = 'font/woff2';
                link.crossOrigin = 'anonymous';
                link.href = font;
                document.head.appendChild(link);
            });

            // Prefetch likely next pages
            const prefetchLinks = [
                '/courses/',
                '/about/',
                '/contact/'
            ];

            prefetchLinks.forEach(url => {
                const link = document.createElement('link');
                link.rel = 'prefetch';
                link.href = url;
                document.head.appendChild(link);
            });
        },

        // Monitor Core Web Vitals
        monitorCoreWebVitals: function() {
            // Only load if analytics is available
            if (typeof gtag === 'function') {
                // Import web-vitals library dynamically
                import('https://unpkg.com/web-vitals@3/dist/web-vitals.js')
                    .then(({getCLS, getFID, getFCP, getLCP, getTTFB}) => {
                        const sendToAnalytics = (metric) => {
                            gtag('event', metric.name, {
                                event_category: 'Web Vitals',
                                event_label: metric.id,
                                value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
                                non_interaction: true,
                                custom_map: {
                                    metric_id: metric.id,
                                    metric_value: metric.value,
                                    metric_delta: metric.delta
                                }
                            });
                        };

                        getCLS(sendToAnalytics);
                        getFID(sendToAnalytics);
                        getFCP(sendToAnalytics);
                        getLCP(sendToAnalytics);
                        getTTFB(sendToAnalytics);
                    })
                    .catch(err => console.warn('Web Vitals library failed to load:', err));
            }
        },

        // Setup Service Worker for caching
        setupServiceWorker: function() {
            if ('serviceWorker' in navigator && location.protocol === 'https:') {
                window.addEventListener('load', () => {
                    navigator.serviceWorker.register('/sw.js')
                        .then(registration => {
                            console.log('SW registered: ', registration);
                        })
                        .catch(registrationError => {
                            console.log('SW registration failed: ', registrationError);
                        });
                });
            }
        }
    };

    // CSS optimization utilities
    const YITPStyles = {
        // Load non-critical CSS asynchronously
        loadCSS: function(href, media = 'all') {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            link.media = 'print';
            link.onload = function() {
                this.media = media;
            };
            document.head.appendChild(link);
        },

        // Remove unused CSS classes (basic implementation)
        removeUnusedCSS: function() {
            // This is a simplified version - in production, use tools like PurgeCSS
            const usedClasses = new Set();
            const elements = document.querySelectorAll('*');
            
            elements.forEach(el => {
                el.classList.forEach(cls => usedClasses.add(cls));
            });

            // Log unused classes for development
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                console.log('Used CSS classes:', Array.from(usedClasses).sort());
            }
        }
    };

    // Form optimization
    const YITPForms = {
        // Add CSRF protection and validation
        enhanceForms: function() {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                // Add loading states
                form.addEventListener('submit', function() {
                    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                    if (submitBtn) {
                        submitBtn.disabled = true;
                        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                    }
                });

                // Add client-side validation
                const requiredFields = form.querySelectorAll('[required]');
                requiredFields.forEach(field => {
                    field.addEventListener('blur', function() {
                        if (!this.value.trim()) {
                            this.classList.add('is-invalid');
                        } else {
                            this.classList.remove('is-invalid');
                            this.classList.add('is-valid');
                        }
                    });
                });
            });
        }
    };

    // Accessibility enhancements
    const YITPAccessibility = {
        // Enhance keyboard navigation
        enhanceKeyboardNavigation: function() {
            // Skip to main content link
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.textContent = 'Skip to main content';
            skipLink.className = 'sr-only sr-only-focusable';
            skipLink.style.cssText = `
                position: absolute;
                top: -40px;
                left: 6px;
                z-index: 1000;
                padding: 8px 16px;
                background: var(--yitp-orange);
                color: white;
                text-decoration: none;
                border-radius: 4px;
            `;
            skipLink.addEventListener('focus', function() {
                this.style.top = '6px';
            });
            skipLink.addEventListener('blur', function() {
                this.style.top = '-40px';
            });
            document.body.insertBefore(skipLink, document.body.firstChild);

            // Enhance focus indicators
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Tab') {
                    document.body.classList.add('keyboard-navigation');
                }
            });

            document.addEventListener('mousedown', function() {
                document.body.classList.remove('keyboard-navigation');
            });
        },

        // Add ARIA labels where missing
        addARIALabels: function() {
            // Add labels to buttons without text
            const iconButtons = document.querySelectorAll('button:not([aria-label]):empty, a:not([aria-label]):empty');
            iconButtons.forEach(btn => {
                const icon = btn.querySelector('i[class*="fa-"]');
                if (icon) {
                    const iconClass = Array.from(icon.classList).find(cls => cls.startsWith('fa-'));
                    if (iconClass) {
                        const label = iconClass.replace('fa-', '').replace('-', ' ');
                        btn.setAttribute('aria-label', label);
                    }
                }
            });
        }
    };

    // Initialize everything when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            YITPPerformance.init();
            YITPForms.enhanceForms();
            YITPAccessibility.enhanceKeyboardNavigation();
            YITPAccessibility.addARIALabels();
        });
    } else {
        YITPPerformance.init();
        YITPForms.enhanceForms();
        YITPAccessibility.enhanceKeyboardNavigation();
        YITPAccessibility.addARIALabels();
    }

    // Expose utilities globally for debugging
    window.YITP = {
        Performance: YITPPerformance,
        Styles: YITPStyles,
        Forms: YITPForms,
        Accessibility: YITPAccessibility
    };

})();
