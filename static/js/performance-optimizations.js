/**
 * Performance optimizations for KortekStream
 * Optimized for high traffic with 1000+ concurrent users
 */

// Initialize performance monitoring
const KortekPerformance = {
    metrics: {},
    marks: {},
    
    /**
     * Initialize performance monitoring
     */
    init() {
        // Check if Performance API is available
        if (!window.performance || !window.performance.mark) {
            console.warn('Performance API not supported in this browser');
            return;
        }
        
        // Set initial page load mark
        this.mark('page_load_start');
        
        // Listen for window load event
        window.addEventListener('load', () => {
            this.mark('page_load_end');
            this.measure('page_load', 'page_load_start', 'page_load_end');
            
            // Report initial page load metrics
            this.reportPageLoadMetrics();
            
            // Initialize observers after page load
            this.initObservers();
        });
        
        // Listen for visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.mark('page_visible');
            } else {
                this.mark('page_hidden');
            }
        });
        
        // Initialize resource timing buffer
        this.initResourceTiming();
    },
    
    /**
     * Set a performance mark
     */
    mark(name) {
        if (window.performance && window.performance.mark) {
            const markName = `korteks_${name}`;
            window.performance.mark(markName);
            this.marks[name] = markName;
            return markName;
        }
        return null;
    },
    
    /**
     * Measure time between marks
     */
    measure(name, startMark, endMark) {
        if (window.performance && window.performance.measure) {
            try {
                const startMarkName = this.marks[startMark] || startMark;
                const endMarkName = this.marks[endMark] || endMark;
                
                const measureName = `korteks_${name}`;
                window.performance.measure(measureName, startMarkName, endMarkName);
                
                const entries = window.performance.getEntriesByName(measureName);
                if (entries.length > 0) {
                    this.metrics[name] = entries[0].duration;
                    return entries[0].duration;
                }
            } catch (e) {
                console.warn(`Error measuring ${name}:`, e);
            }
        }
        return null;
    },
    
    /**
     * Initialize resource timing buffer
     */
    initResourceTiming() {
        // Set up buffer management
        if (window.performance && window.performance.setResourceTimingBufferSize) {
            // Increase buffer size to capture more resources
            window.performance.setResourceTimingBufferSize(300);
        }
        
        // Clear buffer periodically to prevent overflow
        setInterval(() => {
            if (window.performance && window.performance.clearResourceTimings) {
                window.performance.clearResourceTimings();
            }
        }, 60000); // Clear every minute
    },
    
    /**
     * Initialize performance observers
     */
    initObservers() {
        // Initialize Long Task observer
        if (window.PerformanceObserver && PerformanceObserver.supportedEntryTypes && PerformanceObserver.supportedEntryTypes.includes('longtask')) {
            const longTaskObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    console.warn('Long task detected:', entry.duration, 'ms');
                    
                    // Report long tasks that might affect user experience
                    if (entry.duration > 100) {
                        this.reportLongTask(entry);
                    }
                }
            });
            
            longTaskObserver.observe({ entryTypes: ['longtask'] });
        }
        
        // Initialize Layout Shift observer
        if (window.PerformanceObserver && PerformanceObserver.supportedEntryTypes && PerformanceObserver.supportedEntryTypes.includes('layout-shift')) {
            let cumulativeLayoutShift = 0;
            
            const layoutShiftObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    // Only count layout shifts without recent user input
                    if (!entry.hadRecentInput) {
                        cumulativeLayoutShift += entry.value;
                    }
                }
                
                // Store CLS metric
                this.metrics.cls = cumulativeLayoutShift;
            });
            
            layoutShiftObserver.observe({ entryTypes: ['layout-shift'] });
        }
        
        // Initialize Largest Contentful Paint observer
        if (window.PerformanceObserver && PerformanceObserver.supportedEntryTypes && PerformanceObserver.supportedEntryTypes.includes('largest-contentful-paint')) {
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                
                // Store LCP metric
                this.metrics.lcp = lastEntry.startTime;
            });
            
            lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        }
        
        // Initialize First Input Delay observer
        if (window.PerformanceObserver && PerformanceObserver.supportedEntryTypes && PerformanceObserver.supportedEntryTypes.includes('first-input')) {
            const fidObserver = new PerformanceObserver((list) => {
                const entry = list.getEntries()[0];
                
                // Store FID metric
                this.metrics.fid = entry.processingStart - entry.startTime;
            });
            
            fidObserver.observe({ entryTypes: ['first-input'] });
        }
    },
    
    /**
     * Report page load metrics
     */
    reportPageLoadMetrics() {
        // Calculate navigation timing metrics
        if (window.performance && window.performance.timing) {
            const timing = window.performance.timing;
            
            const navigationStart = timing.navigationStart;
            const responseEnd = timing.responseEnd;
            const domComplete = timing.domComplete;
            const loadEventEnd = timing.loadEventEnd;
            
            // Time to First Byte (TTFB)
            const ttfb = timing.responseStart - timing.navigationStart;
            
            // DOM Content Loaded
            const domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart;
            
            // Total page load time
            const pageLoadTime = timing.loadEventEnd - timing.navigationStart;
            
            // Store metrics
            this.metrics.ttfb = ttfb;
            this.metrics.domContentLoaded = domContentLoaded;
            this.metrics.pageLoadTime = pageLoadTime;
            
            // Log metrics
            console.log('Page Load Metrics:', {
                'Time to First Byte (ms)': ttfb,
                'DOM Content Loaded (ms)': domContentLoaded,
                'Total Page Load Time (ms)': pageLoadTime
            });
            
            // Send metrics to server if needed
            this.sendMetricsToServer();
        }
    },
    
    /**
     * Report long task
     */
    reportLongTask(entry) {
        console.warn('Long Task:', {
            duration: entry.duration,
            startTime: entry.startTime,
            name: entry.name
        });
    },
    
    /**
     * Send metrics to server
     */
    sendMetricsToServer() {
        // Only send metrics if we have data and the page is fully loaded
        if (Object.keys(this.metrics).length === 0 || document.readyState !== 'complete') {
            return;
        }
        
        // Don't send metrics for prerendering or background tabs
        if (document.visibilityState !== 'visible') {
            return;
        }
        
        // Prepare data to send
        const data = {
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: Date.now(),
            metrics: this.metrics,
            connection: navigator.connection ? {
                effectiveType: navigator.connection.effectiveType,
                rtt: navigator.connection.rtt,
                downlink: navigator.connection.downlink
            } : null
        };
        
        // Use sendBeacon for reliable delivery even if page is unloading
        if (navigator.sendBeacon) {
            try {
                navigator.sendBeacon('/api/metrics/', JSON.stringify(data));
                return;
            } catch (e) {
                console.warn('Failed to send metrics via beacon:', e);
            }
        }
        
        // Fallback to fetch with keepalive
        fetch('/api/metrics/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data),
            keepalive: true
        }).catch(error => {
            console.warn('Failed to send metrics:', error);
        });
    }
};

// Initialize performance monitoring
KortekPerformance.init();

/**
 * Optimize resource loading
 */
document.addEventListener('DOMContentLoaded', function() {
    // Lazy load non-critical resources
    lazyLoadResources();
    
    // Initialize intersection observer for content visibility
    initContentVisibility();
    
    // Optimize event handlers
    optimizeEventHandlers();
    
    // Prefetch likely navigation targets
    prefetchLikelyDestinations();
});

/**
 * Lazy load non-critical resources
 */
function lazyLoadResources() {
    // Lazy load non-critical CSS
    const lazyCSS = document.querySelectorAll('link[data-lazy]');
    lazyCSS.forEach(link => {
        const href = link.getAttribute('data-href');
        if (href) {
            setTimeout(() => {
                link.setAttribute('href', href);
                link.removeAttribute('data-lazy');
                link.removeAttribute('data-href');
            }, 200);
        }
    });
    
    // Lazy load non-critical JavaScript
    const lazyScripts = document.querySelectorAll('script[data-lazy]');
    lazyScripts.forEach(script => {
        const src = script.getAttribute('data-src');
        if (src) {
            setTimeout(() => {
                const newScript = document.createElement('script');
                newScript.src = src;
                document.body.appendChild(newScript);
            }, 500);
        }
    });
}

/**
 * Initialize content visibility for better rendering performance
 */
function initContentVisibility() {
    if ('IntersectionObserver' in window) {
        const contentSections = document.querySelectorAll('.lazy-section');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '200px'
        });
        
        contentSections.forEach(section => {
            observer.observe(section);
        });
    }
}

/**
 * Optimize event handlers to prevent performance issues
 */
function optimizeEventHandlers() {
    // Use event delegation for common actions
    document.addEventListener('click', function(event) {
        // Handle all button clicks with a single listener
        if (event.target.matches('.btn, button, [role="button"]')) {
            handleButtonClick(event);
        }
        
        // Handle all link clicks with a single listener
        if (event.target.matches('a') || event.target.closest('a')) {
            handleLinkClick(event);
        }
    });
    
    // Throttle scroll and resize events
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        if (!scrollTimeout) {
            scrollTimeout = setTimeout(function() {
                scrollTimeout = null;
                handleScroll();
            }, 100);
        }
    });
    
    let resizeTimeout;
    window.addEventListener('resize', function() {
        if (!resizeTimeout) {
            resizeTimeout = setTimeout(function() {
                resizeTimeout = null;
                handleResize();
            }, 100);
        }
    });
}

/**
 * Handle button clicks
 */
function handleButtonClick(event) {
    const button = event.target.closest('button, .btn, [role="button"]');
    if (!button) return;
    
    // Add active state
    button.classList.add('active');
    
    // Remove active state after animation
    setTimeout(() => {
        button.classList.remove('active');
    }, 200);
}

/**
 * Handle link clicks
 */
function handleLinkClick(event) {
    const link = event.target.closest('a');
    if (!link) return;
    
    // Check if it's an external link
    const isExternal = link.hostname !== window.location.hostname;
    
    // Add security for external links
    if (isExternal && !link.rel.includes('noopener')) {
        link.setAttribute('rel', 'noopener noreferrer');
    }
}

/**
 * Handle scroll events
 */
function handleScroll() {
    // Implement scroll-based optimizations here
}

/**
 * Handle resize events
 */
function handleResize() {
    // Implement resize-based optimizations here
}

/**
 * Prefetch likely navigation destinations
 */
function prefetchLikelyDestinations() {
    // Wait until the page is fully loaded and idle
    if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
            prefetchLinks();
        });
    } else {
        setTimeout(prefetchLinks, 2000);
    }
}

/**
 * Prefetch important links
 */
function prefetchLinks() {
    // Find navigation links and popular content links
    const importantLinks = document.querySelectorAll('nav a, .popular-content a');
    
    // Limit the number of prefetched links
    const linksToPreload = Array.from(importantLinks).slice(0, 5);
    
    linksToPreload.forEach(link => {
        const url = link.getAttribute('href');
        
        // Only prefetch internal links
        if (url && url.startsWith('/') && !url.includes('#')) {
            const prefetchLink = document.createElement('link');
            prefetchLink.rel = 'prefetch';
            prefetchLink.href = url;
            document.head.appendChild(prefetchLink);
        }
    });
}