/*!
 * YITP Performance Monitor
 * =======================
 * Monitors and reports page performance metrics
 * - Core Web Vitals tracking
 * - Preloader performance
 * - Resource loading times
 * - User experience metrics
 */

(function() {
    'use strict';
    
    // Performance monitoring configuration
    const PERF_CONFIG = {
        enableLogging: true,
        enableAnalytics: false, // Set to true when analytics is configured
        thresholds: {
            LCP: 2500,  // Largest Contentful Paint (ms)
            FID: 100,   // First Input Delay (ms)
            CLS: 0.1    // Cumulative Layout Shift
        }
    };
    
    // Performance data storage
    let performanceData = {
        navigationStart: performance.timeOrigin,
        preloaderStart: Date.now(),
        preloaderEnd: null,
        domContentLoaded: null,
        windowLoaded: null,
        firstPaint: null,
        firstContentfulPaint: null,
        largestContentfulPaint: null,
        firstInputDelay: null,
        cumulativeLayoutShift: 0
    };
    
    /**
     * Log performance data
     */
    function logPerformance(metric, value, unit = 'ms') {
        if (PERF_CONFIG.enableLogging && console.log) {
            console.log(`YITP Performance: ${metric} = ${value}${unit}`);
        }
    }
    
    /**
     * Send performance data to analytics
     */
    function sendToAnalytics(metric, value, category = 'Performance') {
        if (PERF_CONFIG.enableAnalytics && window.gtag) {
            gtag('event', metric.toLowerCase().replace(/\s+/g, '_'), {
                event_category: category,
                value: Math.round(value),
                custom_parameter_1: window.location.pathname
            });
        }
    }
    
    /**
     * Get Core Web Vitals
     */
    function measureCoreWebVitals() {
        // Largest Contentful Paint (LCP)
        if ('PerformanceObserver' in window) {
            try {
                const lcpObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    const lcp = lastEntry.startTime;
                    
                    performanceData.largestContentfulPaint = lcp;
                    logPerformance('Largest Contentful Paint', lcp.toFixed(2));
                    sendToAnalytics('largest_contentful_paint', lcp);
                    
                    // Check if LCP meets threshold
                    if (lcp > PERF_CONFIG.thresholds.LCP) {
                        console.warn(`YITP Performance Warning: LCP (${lcp.toFixed(2)}ms) exceeds threshold (${PERF_CONFIG.thresholds.LCP}ms)`);
                    }
                });
                
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            } catch (e) {
                console.warn('YITP Performance: LCP measurement not supported');
            }
            
            // First Input Delay (FID)
            try {
                const fidObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach((entry) => {
                        const fid = entry.processingStart - entry.startTime;
                        performanceData.firstInputDelay = fid;
                        logPerformance('First Input Delay', fid.toFixed(2));
                        sendToAnalytics('first_input_delay', fid);
                        
                        if (fid > PERF_CONFIG.thresholds.FID) {
                            console.warn(`YITP Performance Warning: FID (${fid.toFixed(2)}ms) exceeds threshold (${PERF_CONFIG.thresholds.FID}ms)`);
                        }
                    });
                });
                
                fidObserver.observe({ entryTypes: ['first-input'] });
            } catch (e) {
                console.warn('YITP Performance: FID measurement not supported');
            }
            
            // Cumulative Layout Shift (CLS)
            try {
                let clsValue = 0;
                const clsObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach((entry) => {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                        }
                    });
                    
                    performanceData.cumulativeLayoutShift = clsValue;
                    logPerformance('Cumulative Layout Shift', clsValue.toFixed(4), '');
                    sendToAnalytics('cumulative_layout_shift', clsValue * 1000); // Convert to integer for analytics
                    
                    if (clsValue > PERF_CONFIG.thresholds.CLS) {
                        console.warn(`YITP Performance Warning: CLS (${clsValue.toFixed(4)}) exceeds threshold (${PERF_CONFIG.thresholds.CLS})`);
                    }
                });
                
                clsObserver.observe({ entryTypes: ['layout-shift'] });
            } catch (e) {
                console.warn('YITP Performance: CLS measurement not supported');
            }
        }
    }
    
    /**
     * Measure paint metrics
     */
    function measurePaintMetrics() {
        if ('PerformanceObserver' in window) {
            try {
                const paintObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach((entry) => {
                        if (entry.name === 'first-paint') {
                            performanceData.firstPaint = entry.startTime;
                            logPerformance('First Paint', entry.startTime.toFixed(2));
                            sendToAnalytics('first_paint', entry.startTime);
                        } else if (entry.name === 'first-contentful-paint') {
                            performanceData.firstContentfulPaint = entry.startTime;
                            logPerformance('First Contentful Paint', entry.startTime.toFixed(2));
                            sendToAnalytics('first_contentful_paint', entry.startTime);
                        }
                    });
                });
                
                paintObserver.observe({ entryTypes: ['paint'] });
            } catch (e) {
                console.warn('YITP Performance: Paint metrics not supported');
            }
        }
    }
    
    /**
     * Measure resource loading times
     */
    function measureResourceTiming() {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const resources = performance.getEntriesByType('resource');
                const resourceSummary = {
                    total: resources.length,
                    images: 0,
                    scripts: 0,
                    stylesheets: 0,
                    totalSize: 0,
                    slowestResource: null,
                    slowestTime: 0
                };
                
                resources.forEach((resource) => {
                    const duration = resource.responseEnd - resource.startTime;
                    
                    // Categorize resources
                    if (resource.initiatorType === 'img') {
                        resourceSummary.images++;
                    } else if (resource.initiatorType === 'script') {
                        resourceSummary.scripts++;
                    } else if (resource.initiatorType === 'link') {
                        resourceSummary.stylesheets++;
                    }
                    
                    // Track transfer size if available
                    if (resource.transferSize) {
                        resourceSummary.totalSize += resource.transferSize;
                    }
                    
                    // Find slowest resource
                    if (duration > resourceSummary.slowestTime) {
                        resourceSummary.slowestTime = duration;
                        resourceSummary.slowestResource = resource.name;
                    }
                });
                
                logPerformance('Total Resources', resourceSummary.total, ' files');
                logPerformance('Images Loaded', resourceSummary.images, ' files');
                logPerformance('Scripts Loaded', resourceSummary.scripts, ' files');
                logPerformance('Stylesheets Loaded', resourceSummary.stylesheets, ' files');
                logPerformance('Total Transfer Size', (resourceSummary.totalSize / 1024).toFixed(2), ' KB');
                
                if (resourceSummary.slowestResource) {
                    logPerformance('Slowest Resource', `${resourceSummary.slowestResource} (${resourceSummary.slowestTime.toFixed(2)}ms)`);
                }
                
                sendToAnalytics('total_resources', resourceSummary.total);
                sendToAnalytics('total_transfer_size', resourceSummary.totalSize);
                sendToAnalytics('slowest_resource_time', resourceSummary.slowestTime);
                
            }, 1000);
        });
    }
    
    /**
     * Generate performance report
     */
    function generatePerformanceReport() {
        const report = {
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            connection: navigator.connection ? {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt
            } : null,
            metrics: performanceData
        };
        
        // Store in sessionStorage for debugging
        try {
            sessionStorage.setItem('yitp_performance_report', JSON.stringify(report, null, 2));
        } catch (e) {
            console.warn('YITP Performance: Could not store report in sessionStorage');
        }
        
        return report;
    }
    
    /**
     * Initialize performance monitoring
     */
    function initPerformanceMonitoring() {
        // Record navigation timing
        performanceData.domContentLoaded = Date.now();
        
        // Start measurements
        measureCoreWebVitals();
        measurePaintMetrics();
        measureResourceTiming();
        
        // Listen for preloader events
        document.addEventListener('yitpPreloaderHidden', (event) => {
            performanceData.preloaderEnd = Date.now();
            const preloaderDuration = performanceData.preloaderEnd - performanceData.preloaderStart;
            logPerformance('Preloader Duration', preloaderDuration);
            sendToAnalytics('preloader_duration', preloaderDuration);
        });
        
        // Record window load time
        window.addEventListener('load', () => {
            performanceData.windowLoaded = Date.now();
            const totalLoadTime = performanceData.windowLoaded - performanceData.navigationStart;
            logPerformance('Total Load Time', totalLoadTime);
            sendToAnalytics('total_load_time', totalLoadTime);
            
            // Generate final report after everything loads
            setTimeout(() => {
                const report = generatePerformanceReport();
                logPerformance('Performance Report Generated', 'Check sessionStorage for details');
                
                // Expose report globally for debugging
                window.YITPPerformanceReport = report;
            }, 2000);
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPerformanceMonitoring);
    } else {
        initPerformanceMonitoring();
    }
    
    // Expose API for manual reporting
    window.YITPPerformance = {
        getReport: generatePerformanceReport,
        getData: () => performanceData,
        config: PERF_CONFIG
    };
    
})();
