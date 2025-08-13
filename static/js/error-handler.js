/**
 * Enhanced Error Handler for KortekStream
 * Provides graceful error handling and recovery for frontend
 */

class ErrorHandler {
    constructor() {
        this.errorCount = 0;
        this.lastErrorTime = null;
        this.errorThreshold = 5; // Max errors before taking action
        this.errorTimeWindow = 60000; // 1 minute window for counting errors
        this.recoveryStrategies = {
            'network': this.handleNetworkError.bind(this),
            'api': this.handleApiError.bind(this),
            'rendering': this.handleRenderingError.bind(this),
            'resource': this.handleResourceError.bind(this),
            'unknown': this.handleUnknownError.bind(this)
        };
        
        this.init();
    }
    
    /**
     * Initialize error handler
     */
    init() {
        // Set up global error handling
        window.addEventListener('error', this.handleGlobalError.bind(this));
        window.addEventListener('unhandledrejection', this.handlePromiseRejection.bind(this));
        
        // Monitor network status
        window.addEventListener('online', () => {
            this.showNotification('Connection restored', 'success');
            this.refreshStaleContent();
        });
        
        window.addEventListener('offline', () => {
            this.showNotification('You are offline. Some features may be unavailable.', 'warning');
        });
        
        // Set up console error tracking
        this.setupConsoleErrorTracking();
        
        console.log('ErrorHandler initialized');
    }
    
    /**
     * Handle global JavaScript errors
     */
    handleGlobalError(event) {
        // Prevent default browser error handling
        event.preventDefault();
        
        const error = {
            message: event.message || 'Unknown error',
            source: event.filename || 'Unknown source',
            lineno: event.lineno || 0,
            colno: event.colno || 0,
            error: event.error || null,
            timestamp: new Date().toISOString(),
            type: 'global'
        };
        
        this.processError(error);
        
        return true; // Prevent default error handling
    }
    
    /**
     * Handle unhandled promise rejections
     */
    handlePromiseRejection(event) {
        const error = {
            message: event.reason?.message || 'Promise rejected',
            source: 'Promise',
            error: event.reason || null,
            timestamp: new Date().toISOString(),
            type: 'promise'
        };
        
        this.processError(error);
        
        return true; // Prevent default error handling
    }
    
    /**
     * Set up console error tracking
     */
    setupConsoleErrorTracking() {
        const originalConsoleError = console.error;
        
        console.error = (...args) => {
            // Call original console.error
            originalConsoleError.apply(console, args);
            
            // Process the error
            const errorMessage = args.map(arg => {
                if (arg instanceof Error) {
                    return arg.message;
                } else if (typeof arg === 'object') {
                    try {
                        return JSON.stringify(arg);
                    } catch (e) {
                        return String(arg);
                    }
                } else {
                    return String(arg);
                }
            }).join(' ');
            
            const error = {
                message: errorMessage,
                source: 'console.error',
                timestamp: new Date().toISOString(),
                type: 'console'
            };
            
            this.processError(error);
        };
    }
    
    /**
     * Process an error and determine how to handle it
     */
    processError(error) {
        // Log the error
        this.logError(error);
        
        // Increment error count
        this.trackError();
        
        // Determine error category
        const errorCategory = this.categorizeError(error);
        
        // Apply recovery strategy based on category
        if (this.recoveryStrategies[errorCategory]) {
            this.recoveryStrategies[errorCategory](error);
        } else {
            this.recoveryStrategies.unknown(error);
        }
        
        // Check if we need to take drastic action due to too many errors
        this.checkErrorThreshold();
    }
    
    /**
     * Log error to console and potentially to server
     */
    logError(error) {
        // Always log to console
        console.group('Error Details');
        console.error(error.message);
        console.info('Source:', error.source);
        console.info('Timestamp:', error.timestamp);
        console.info('Type:', error.type);
        if (error.error && error.error.stack) {
            console.info('Stack:', error.error.stack);
        }
        console.groupEnd();
        
        // Log to server if appropriate
        if (this.shouldReportToServer(error)) {
            this.reportErrorToServer(error);
        }
    }
    
    /**
     * Track error frequency
     */
    trackError() {
        const now = Date.now();
        
        // Reset count if outside time window
        if (this.lastErrorTime && (now - this.lastErrorTime > this.errorTimeWindow)) {
            this.errorCount = 0;
        }
        
        this.errorCount++;
        this.lastErrorTime = now;
    }
    
    /**
     * Check if we've hit the error threshold and need to take action
     */
    checkErrorThreshold() {
        if (this.errorCount >= this.errorThreshold) {
            // Too many errors, take action
            this.handleExcessiveErrors();
        }
    }
    
    /**
     * Handle case where too many errors are occurring
     */
    handleExcessiveErrors() {
        console.warn('Excessive errors detected. Taking recovery action.');
        
        // Show user notification
        this.showNotification(
            'We\'re experiencing some technical difficulties. Trying to recover...',
            'error',
            10000
        );
        
        // Try some recovery strategies
        this.clearCaches();
        this.refreshPage(3000); // Refresh after 3 seconds
    }
    
    /**
     * Categorize error to determine best recovery strategy
     */
    categorizeError(error) {
        const message = error.message.toLowerCase();
        const source = (error.source || '').toLowerCase();
        
        // Network errors
        if (
            message.includes('network') ||
            message.includes('failed to fetch') ||
            message.includes('cors') ||
            message.includes('connection') ||
            !navigator.onLine
        ) {
            return 'network';
        }
        
        // API errors
        if (
            source.includes('api') ||
            message.includes('api') ||
            message.includes('status code') ||
            message.includes('json') ||
            message.includes('parse')
        ) {
            return 'api';
        }
        
        // Rendering errors
        if (
            message.includes('render') ||
            message.includes('dom') ||
            message.includes('undefined is not an object') ||
            message.includes('null is not an object') ||
            message.includes('cannot read property')
        ) {
            return 'rendering';
        }
        
        // Resource errors
        if (
            source.includes('.js') ||
            source.includes('.css') ||
            source.includes('.png') ||
            source.includes('.jpg') ||
            source.includes('script') ||
            message.includes('loading') ||
            message.includes('resource')
        ) {
            return 'resource';
        }
        
        return 'unknown';
    }
    
    /**
     * Determine if an error should be reported to the server
     */
    shouldReportToServer(error) {
        // Don't report network errors when offline
        if (!navigator.onLine && this.categorizeError(error) === 'network') {
            return false;
        }
        
        // Don't report certain common errors
        const message = error.message.toLowerCase();
        if (
            message.includes('script error') ||
            message.includes('extension') ||
            message.includes('adblock') ||
            message.includes('plugin')
        ) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Report error to server
     */
    reportErrorToServer(error) {
        try {
            // Add browser and user info
            const errorData = {
                ...error,
                url: window.location.href,
                userAgent: navigator.userAgent,
                screenSize: `${window.innerWidth}x${window.innerHeight}`,
                timestamp: new Date().toISOString()
            };
            
            // Use sendBeacon for reliability if available
            if (navigator.sendBeacon) {
                navigator.sendBeacon('/api/log/error', JSON.stringify(errorData));
                return;
            }
            
            // Fallback to fetch
            fetch('/api/log/error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(errorData),
                keepalive: true
            }).catch(e => console.error('Failed to report error:', e));
        } catch (e) {
            console.error('Error reporting to server:', e);
        }
    }
    
    /**
     * Handle network errors
     */
    handleNetworkError(error) {
        if (!navigator.onLine) {
            // We're offline
            this.showNotification('You are offline. Some features may be unavailable.', 'warning');
            document.body.classList.add('offline-mode');
        } else {
            // Network error while online
            this.showNotification('Network error. Retrying...', 'warning');
            
            // Try to refresh the problematic resource
            if (error.source && error.source.startsWith('http')) {
                this.retryResource(error.source);
            }
        }
    }
    
    /**
     * Handle API errors
     */
    handleApiError(error) {
        // Check if it's a server error (5xx)
        if (error.message.includes('500') || error.message.includes('503')) {
            this.showNotification('Server error. Please try again later.', 'error');
        } 
        // Check if it's an authentication error (401)
        else if (error.message.includes('401')) {
            this.showNotification('Your session has expired. Please log in again.', 'warning');
            // Redirect to login page after a delay
            setTimeout(() => {
                window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
            }, 2000);
        }
        // Check if it's a not found error (404)
        else if (error.message.includes('404')) {
            this.showNotification('The requested resource was not found.', 'warning');
        }
        // Other API errors
        else {
            this.showNotification('Error loading data. Retrying...', 'warning');
            
            // Try to refresh the content
            this.refreshContent();
        }
    }
    
    /**
     * Handle rendering errors
     */
    handleRenderingError(error) {
        // These are usually more serious and may require a page refresh
        this.showNotification('Display error. Trying to recover...', 'error');
        
        // Try to recover the page state
        this.recoverPageState();
    }
    
    /**
     * Handle resource errors (scripts, styles, images)
     */
    handleResourceError(error) {
        const source = error.source || '';
        
        // For image errors, we can just hide the image or show a placeholder
        if (source.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
            this.handleImageError(source);
        }
        // For script or CSS errors, we might need to reload the resource
        else if (source.match(/\.(js|css)$/i)) {
            this.retryResource(source);
        }
        // For other resources
        else {
            this.showNotification('Error loading resource. Some features may not work correctly.', 'warning');
        }
    }
    
    /**
     * Handle unknown errors
     */
    handleUnknownError(error) {
        // For unknown errors, log and notify but don't take drastic action
        this.showNotification('An error occurred. Some features may not work correctly.', 'warning');
    }
    
    /**
     * Handle image loading errors
     */
    handleImageError(source) {
        // Find all images with this source
        const images = document.querySelectorAll(`img[src="${source}"]`);
        
        images.forEach(img => {
            // Add error class
            img.classList.add('img-error');
            
            // Set alt text if missing
            if (!img.alt) {
                img.alt = 'Image failed to load';
            }
            
            // Try to set a placeholder
            if (img.classList.contains('episode-img') || img.closest('.episode-card')) {
                img.src = '/static/images/placeholder-episode.jpg';
            } else {
                img.src = '/static/images/placeholder-anime.jpg';
            }
        });
    }
    
    /**
     * Retry loading a resource
     */
    retryResource(url) {
        // For scripts
        if (url.endsWith('.js')) {
            const script = document.createElement('script');
            script.src = `${url}?retry=${Date.now()}`;
            document.head.appendChild(script);
        }
        // For stylesheets
        else if (url.endsWith('.css')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = `${url}?retry=${Date.now()}`;
            document.head.appendChild(link);
        }
        // For images, find and reload
        else if (url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
            const images = document.querySelectorAll(`img[src="${url}"]`);
            images.forEach(img => {
                img.src = `${url}?retry=${Date.now()}`;
            });
        }
    }
    
    /**
     * Refresh content without full page reload
     */
    refreshContent() {
        // Find all content areas with data-content-url
        const contentAreas = document.querySelectorAll('[data-content-url]');
        
        if (contentAreas.length > 0) {
            contentAreas.forEach(element => {
                // If we have an API handler, use it
                if (window.apiHandler && typeof window.apiHandler.loadContent === 'function') {
                    window.apiHandler.loadContent(element, 0, true);
                }
                // Otherwise, try a simple fetch
                else {
                    const url = element.dataset.contentUrl;
                    if (url) {
                        fetch(url, {
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest',
                                'Cache-Control': 'no-cache'
                            }
                        })
                        .then(response => response.text())
                        .then(html => {
                            element.innerHTML = html;
                        })
                        .catch(err => {
                            console.error('Error refreshing content:', err);
                        });
                    }
                }
            });
        } else {
            // If no content areas found, refresh the page
            this.refreshPage(1000);
        }
    }
    
    /**
     * Refresh stale content after being offline
     */
    refreshStaleContent() {
        // Similar to refreshContent but only refresh content that's marked as stale
        const staleContent = document.querySelectorAll('[data-from-cache="true"]');
        
        staleContent.forEach(element => {
            if (window.apiHandler && typeof window.apiHandler.loadContent === 'function') {
                window.apiHandler.loadContent(element, 0, true);
            }
        });
    }
    
    /**
     * Try to recover page state without a full refresh
     */
    recoverPageState() {
        // Reset any broken UI elements
        this.resetUIState();
        
        // Refresh main content
        this.refreshContent();
    }
    
    /**
     * Reset UI state to recover from rendering errors
     */
    resetUIState() {
        // Reset modal dialogs
        const modals = document.querySelectorAll('.modal.show, .modal.active');
        modals.forEach(modal => {
            modal.classList.remove('show', 'active');
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) backdrop.remove();
        });
        
        // Reset body classes
        document.body.classList.remove('modal-open', 'overflow-hidden');
        
        // Reset any broken animations
        const animating = document.querySelectorAll('.animating, .transitioning');
        animating.forEach(el => {
            el.classList.remove('animating', 'transitioning');
        });
    }
    
    /**
     * Clear browser caches that might be causing issues
     */
    clearCaches() {
        // Clear session storage
        try {
            sessionStorage.clear();
        } catch (e) {
            console.error('Failed to clear sessionStorage:', e);
        }
        
        // Clear application cache if available
        if (window.applicationCache) {
            try {
                window.applicationCache.swapCache();
            } catch (e) {
                console.error('Failed to swap application cache:', e);
            }
        }
        
        // Clear service worker caches if available
        if (navigator.serviceWorker) {
            navigator.serviceWorker.getRegistrations().then(registrations => {
                registrations.forEach(registration => {
                    registration.update();
                });
            });
        }
    }
    
    /**
     * Refresh the page after a delay
     */
    refreshPage(delay = 0) {
        if (delay > 0) {
            setTimeout(() => {
                window.location.reload();
            }, delay);
        } else {
            window.location.reload();
        }
    }
    
    /**
     * Show a notification to the user
     */
    showNotification(message, type = 'info', duration = 5000) {
        // Check if we have a toast container
        let toastContainer = document.querySelector('.toast-container');
        
        if (!toastContainer) {
            // Create toast container
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-message">${message}</span>
                <button class="toast-close">&times;</button>
            </div>
        `;
        
        // Add to container
        toastContainer.appendChild(toast);
        
        // Show with animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // Add close handler
        const closeButton = toast.querySelector('.toast-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            });
        }
        
        // Auto-hide after duration
        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 300);
                }
            }, duration);
        }
        
        return toast;
    }
}

// Initialize error handler
const errorHandler = new ErrorHandler();

// Export for use in other modules
window.errorHandler = errorHandler;