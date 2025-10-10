/*!
 * YITP Optimized Preloader JavaScript
 * ===================================
 * High-performance preloader with smart timeout and progressive loading
 * - Uses DOMContentLoaded instead of window.load for faster response
 * - Implements maximum timeout of 3 seconds
 * - Progressive loading with fallbacks
 * - No jQuery dependency
 * - Optimized for Core Web Vitals
 */

(function() {
    'use strict';
    
    // Configuration
    const PRELOADER_CONFIG = {
        maxTimeout: 3000,        // Maximum 3 seconds
        fadeOutDuration: 500,    // 0.5 second fade out
        checkInterval: 100,      // Check every 100ms
        criticalResources: [     // Critical resources to wait for
            'css',
            'fonts'
        ]
    };
    
    // State management
    let preloaderState = {
        isLoaded: false,
        startTime: Date.now(),
        timeoutId: null,
        intervalId: null,
        criticalResourcesLoaded: false
    };
    
    // Get preloader element
    const preloader = document.getElementById('loading');
    if (!preloader) {
        console.warn('YITP Preloader: #loading element not found');
        return;
    }
    
    /**
     * Hide preloader with smooth animation
     */
    function hidePreloader() {
        if (preloaderState.isLoaded) return;
        
        preloaderState.isLoaded = true;
        
        // Clear timers
        if (preloaderState.timeoutId) {
            clearTimeout(preloaderState.timeoutId);
        }
        if (preloaderState.intervalId) {
            clearInterval(preloaderState.intervalId);
        }
        
        // Add loaded class for CSS transition
        preloader.classList.add('loaded');
        
        // Remove from DOM after animation
        setTimeout(() => {
            if (preloader.parentNode) {
                preloader.parentNode.removeChild(preloader);
            }
            
            // Trigger custom event for other scripts
            document.dispatchEvent(new CustomEvent('yitpPreloaderHidden', {
                detail: {
                    loadTime: Date.now() - preloaderState.startTime,
                    method: preloaderState.criticalResourcesLoaded ? 'natural' : 'timeout'
                }
            }));
            
        }, PRELOADER_CONFIG.fadeOutDuration);
        
        // Performance logging
        if (window.console && console.log) {
            const loadTime = Date.now() - preloaderState.startTime;
            console.log(`YITP Preloader: Hidden after ${loadTime}ms`);
        }
    }
    
    /**
     * Check if critical resources are loaded
     */
    function checkCriticalResources() {
        // Check if CSS is loaded (basic heuristic)
        const testElement = document.createElement('div');
        testElement.style.cssText = 'position:absolute;visibility:hidden;';
        testElement.className = 'yitp-css-test';
        document.body.appendChild(testElement);
        
        const computedStyle = window.getComputedStyle(testElement);
        const cssLoaded = computedStyle.position === 'absolute';
        
        document.body.removeChild(testElement);
        
        // Check if fonts are loaded (if Font Loading API is available)
        let fontsLoaded = true;
        if (document.fonts && document.fonts.ready) {
            fontsLoaded = document.fonts.status === 'loaded';
        }
        
        return cssLoaded && fontsLoaded;
    }
    
    /**
     * Progressive loading check
     */
    function progressiveLoadingCheck() {
        // Check if critical resources are ready
        if (checkCriticalResources()) {
            preloaderState.criticalResourcesLoaded = true;
            hidePreloader();
            return;
        }
        
        // Check if we've exceeded maximum time
        const elapsed = Date.now() - preloaderState.startTime;
        if (elapsed >= PRELOADER_CONFIG.maxTimeout) {
            console.warn('YITP Preloader: Timeout reached, hiding preloader');
            hidePreloader();
            return;
        }
    }
    
    /**
     * Initialize preloader with smart loading detection
     */
    function initPreloader() {
        // Start the loading check interval
        preloaderState.intervalId = setInterval(progressiveLoadingCheck, PRELOADER_CONFIG.checkInterval);
        
        // Set maximum timeout as fallback
        preloaderState.timeoutId = setTimeout(() => {
            console.warn('YITP Preloader: Maximum timeout reached');
            hidePreloader();
        }, PRELOADER_CONFIG.maxTimeout);
        
        // Listen for DOMContentLoaded (faster than window.load)
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                // Small delay to allow CSS to apply
                setTimeout(progressiveLoadingCheck, 100);
            });
        } else {
            // DOM is already ready
            setTimeout(progressiveLoadingCheck, 100);
        }
        
        // Also listen for window.load as backup
        if (document.readyState !== 'complete') {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    if (!preloaderState.isLoaded) {
                        preloaderState.criticalResourcesLoaded = true;
                        hidePreloader();
                    }
                }, 200);
            });
        }
        
        // Listen for font loading if supported
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(() => {
                setTimeout(progressiveLoadingCheck, 50);
            });
        }
    }
    
    /**
     * Handle visibility change (tab switching)
     */
    function handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden, pause timers to save resources
            if (preloaderState.intervalId) {
                clearInterval(preloaderState.intervalId);
            }
        } else {
            // Page is visible again, resume if not loaded
            if (!preloaderState.isLoaded && !preloaderState.intervalId) {
                preloaderState.intervalId = setInterval(progressiveLoadingCheck, PRELOADER_CONFIG.checkInterval);
            }
        }
    }
    
    /**
     * Handle page errors
     */
    function handlePageError(event) {
        console.warn('YITP Preloader: Page error detected, hiding preloader', event);
        setTimeout(hidePreloader, 500);
    }
    
    // Initialize when script loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPreloader);
    } else {
        initPreloader();
    }
    
    // Add event listeners
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('error', handlePageError);
    
    // Expose API for manual control (if needed)
    window.YITPPreloader = {
        hide: hidePreloader,
        isLoaded: () => preloaderState.isLoaded,
        getLoadTime: () => Date.now() - preloaderState.startTime,
        config: PRELOADER_CONFIG
    };
    
    // Performance monitoring
    if (window.performance && performance.mark) {
        performance.mark('yitp-preloader-start');
        
        document.addEventListener('yitpPreloaderHidden', function(event) {
            performance.mark('yitp-preloader-end');
            performance.measure('yitp-preloader-duration', 'yitp-preloader-start', 'yitp-preloader-end');
            
            // Log to analytics if available
            if (window.gtag) {
                gtag('event', 'preloader_hidden', {
                    'custom_parameter_1': event.detail.loadTime,
                    'custom_parameter_2': event.detail.method
                });
            }
        });
    }
    
})();
