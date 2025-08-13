/**
 * Enhanced API Handler for KortekStream
 * Handles slow APIs, loading states, and progressive content loading
 * Optimized for high traffic and resilience
 */

class KortekStreamAPI {
    constructor() {
        this.baseUrl = window.location.origin;
        this.retryDelay = 1000; // Start with 1 second
        this.maxRetries = 5; // Increased from 3 to 5
        this.loadingElements = new Map();
        this.requestTimeouts = new Map(); // Track request timeouts
        this.apiHealthy = true;
        this.lastHealthCheck = null;
        this.consecutiveFailures = 0;
        this.circuitBreakerThreshold = 8; // Increased from 5 to 8
        this.circuitBreakerResetTime = 30000; // Reduced from 60s to 30s for faster recovery
        this.staleContentCache = new Map(); // For stale-while-revalidate pattern
        this.requestQueue = []; // Queue for failed requests
        this.localStorageEnabled = this.checkLocalStorageAvailable();
        this.sessionStorageEnabled = this.checkSessionStorageAvailable();
        this.indexedDBEnabled = this.checkIndexedDBAvailable();
        this.offlineMode = false;
        this.concurrentRequests = 0;
        this.maxConcurrentRequests = 8; // Limit concurrent API requests
        this.requestsWaiting = [];
        this.networkStatus = navigator.onLine;
        this.init();
    }
    
    /**
     * Check if localStorage is available
     */
    checkLocalStorageAvailable() {
        try {
            const test = 'test';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }
    
    /**
     * Check if sessionStorage is available
     */
    checkSessionStorageAvailable() {
        try {
            const test = 'test';
            sessionStorage.setItem(test, test);
            sessionStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }
    
    /**
     * Check if IndexedDB is available
     */
    checkIndexedDBAvailable() {
        return 'indexedDB' in window;
    }

    init() {
        // Initialize loading states and progressive loading
        this.initLoadingStates();
        this.initProgressiveLoading();
        
        // Initialize network status monitoring
        this.initNetworkMonitoring();
        
        // Initialize offline support if available
        if (this.indexedDBEnabled) {
            this.initOfflineSupport();
        }
        
        // Check API status immediately and periodically
        this.checkAPIStatus();
        setInterval(() => this.checkAPIStatus(), 30000);
        
        // Initialize request queue processor
        this.processRequestQueue();
        
        // Add event listeners for page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                // When page becomes visible again, check API status
                this.checkAPIStatus();
                // Process any pending requests
                this.processRequestQueue();
            }
        });
        
        // Log initialization
        console.log('KortekStreamAPI initialized with capabilities:', {
            localStorage: this.localStorageEnabled,
            sessionStorage: this.sessionStorageEnabled,
            indexedDB: this.indexedDBEnabled,
            networkStatus: this.networkStatus
        });
    }
    
    /**
     * Initialize network status monitoring
     */
    initNetworkMonitoring() {
        // Listen for online/offline events
        window.addEventListener('online', () => {
            this.networkStatus = true;
            this.offlineMode = false;
            console.log('Network connection restored');
            
            // When back online, check API and process queue
            this.checkAPIStatus();
            this.processRequestQueue();
            
            // Notify user
            this.showToast('Connection restored. Refreshing content...', 'success', 3000);
            
            // Refresh stale content
            this.refreshStaleContent();
        });
        
        window.addEventListener('offline', () => {
            this.networkStatus = false;
            this.offlineMode = true;
            console.log('Network connection lost');
            
            // Notify user
            this.showToast('You are offline. Using cached content.', 'warning', 5000);
        });
        
        // Initial network status
        this.networkStatus = navigator.onLine;
        if (!this.networkStatus) {
            this.offlineMode = true;
            console.log('Starting in offline mode');
        }
    }
    
    /**
     * Initialize offline support using IndexedDB
     */
    initOfflineSupport() {
        // This would initialize IndexedDB for offline content
        // Implementation depends on specific requirements
        console.log('Offline support initialized');
    }
    
    /**
     * Process queued requests when possible
     */
    processRequestQueue() {
        if (this.requestQueue.length === 0 || !this.networkStatus || !this.apiHealthy) {
            return;
        }
        
        // Process up to 3 requests at a time
        const maxToProcess = Math.min(3, this.requestQueue.length);
        for (let i = 0; i < maxToProcess; i++) {
            const request = this.requestQueue.shift();
            if (request) {
                console.log('Processing queued request:', request.url);
                this.executeRequest(request.url, request.options, request.resolve, request.reject);
            }
        }
        
        // If there are more requests, schedule another processing
        if (this.requestQueue.length > 0) {
            setTimeout(() => this.processRequestQueue(), 1000);
        }
    }
    
    /**
     * Refresh stale content after being offline
     */
    refreshStaleContent() {
        // Find all content areas that might need refreshing
        const contentAreas = document.querySelectorAll('[data-content-url][data-loaded="true"]');
        contentAreas.forEach(element => {
            const url = element.dataset.contentUrl;
            if (url) {
                // Reload with force refresh
                this.loadContent(element, 0, true);
            }
        });
    }

    /**
     * Initialize loading states for various content areas
     */
    initLoadingStates() {
        // Add loading indicators to content areas that might be slow
        const contentAreas = document.querySelectorAll('[data-api-content]');
        contentAreas.forEach(element => {
            this.addLoadingState(element);
        });
    }

    /**
     * Add loading skeleton to an element
     */
    addLoadingState(element) {
        const loadingId = `loading-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        this.loadingElements.set(loadingId, element);

        // Create skeleton loading UI
        const skeleton = this.createSkeletonLoader(element);
        
        // Show skeleton if content is not loaded within 500ms
        const timer = setTimeout(() => {
            if (!element.dataset.loaded) {
                element.style.position = 'relative';
                element.appendChild(skeleton);
                element.classList.add('loading');
            }
        }, 500);

        // Store cleanup function
        element.dataset.loadingTimer = timer;
        element.dataset.loadingId = loadingId;
    }

    /**
     * Create skeleton loader based on element type
     */
    createSkeletonLoader(element) {
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton-loader';
        skeleton.innerHTML = `
            <div class="skeleton-overlay">
                <div class="skeleton-content">
                    ${this.generateSkeletonElements(element)}
                </div>
                <div class="skeleton-spinner">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gold-500"></div>
                </div>
                <div class="skeleton-message text-center mt-4">
                    <p class="text-gray-600 dark:text-gray-400">Loading content...</p>
                    <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">This might take a moment</p>
                </div>
            </div>
        `;
        
        return skeleton;
    }

    /**
     * Generate skeleton elements based on content type
     */
    generateSkeletonElements(element) {
        if (element.classList.contains('anime-grid') || element.querySelector('.anime-grid')) {
            // Grid skeleton for anime listings
            return Array.from({length: 12}, () => `
                <div class="skeleton-card">
                    <div class="skeleton-image h-48 bg-gray-300 dark:bg-gray-600 rounded-lg animate-pulse"></div>
                    <div class="skeleton-title h-4 bg-gray-300 dark:bg-gray-600 rounded mt-3 animate-pulse"></div>
                    <div class="skeleton-subtitle h-3 bg-gray-200 dark:bg-gray-700 rounded mt-2 animate-pulse w-3/4"></div>
                </div>
            `).join('');
        } else if (element.classList.contains('anime-detail') || element.querySelector('.anime-detail')) {
            // Detail page skeleton
            return `
                <div class="skeleton-detail flex flex-col md:flex-row gap-6">
                    <div class="skeleton-cover w-full md:w-1/3">
                        <div class="h-96 bg-gray-300 dark:bg-gray-600 rounded-lg animate-pulse"></div>
                    </div>
                    <div class="skeleton-info flex-1 space-y-4">
                        <div class="h-8 bg-gray-300 dark:bg-gray-600 rounded animate-pulse"></div>
                        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-5/6"></div>
                        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-4/6"></div>
                        <div class="space-y-2 mt-6">
                            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-5/6"></div>
                            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-4/6"></div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Generic skeleton
            return `
                <div class="skeleton-generic space-y-3">
                    <div class="h-6 bg-gray-300 dark:bg-gray-600 rounded animate-pulse"></div>
                    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-5/6"></div>
                </div>
            `;
        }
    }

    /**
     * Remove loading state when content is loaded
     */
    removeLoadingState(element) {
        if (element.dataset.loadingTimer) {
            clearTimeout(element.dataset.loadingTimer);
        }
        
        const skeleton = element.querySelector('.skeleton-loader');
        if (skeleton) {
            skeleton.style.opacity = '0';
            skeleton.style.transition = 'opacity 0.3s ease';
            setTimeout(() => skeleton.remove(), 300);
        }
        
        element.classList.remove('loading');
        element.dataset.loaded = 'true';
    }

    /**
     * Initialize progressive loading for content that loads in stages
     */
    initProgressiveLoading() {
        // Detect content that should load progressively
        const progressiveElements = document.querySelectorAll('[data-progressive-load]');
        progressiveElements.forEach(element => {
            this.setupProgressiveLoading(element);
        });
    }

    /**
     * Setup progressive loading for an element
     */
    setupProgressiveLoading(element) {
        const priority = element.dataset.progressiveLoad || 'normal';
        const delay = this.getLoadingDelay(priority);
        
        setTimeout(() => {
            this.loadContent(element);
        }, delay);
    }

    /**
     * Get loading delay based on priority
     */
    getLoadingDelay(priority) {
        switch (priority) {
            case 'high': return 0;
            case 'normal': return 100;
            case 'low': return 500;
            case 'lazy': return 1000;
            default: return 100;
        }
    }

    /**
     * Load content with enhanced retry mechanism and stale-while-revalidate
     * Optimized for high traffic with better caching and concurrency control
     * 
     * @param {HTMLElement} element - The element to load content into
     * @param {number} retries - Current retry count
     * @param {boolean} forceRefresh - Whether to force a refresh bypassing cache
     */
    async loadContent(element, retries = 0, forceRefresh = false) {
        const url = element.dataset.contentUrl;
        const contentType = element.dataset.contentType;
        const priority = element.dataset.priority || 'normal';
        const cacheKey = `${contentType}-${url}`;
        
        if (!url) return;
        
        // Track this request for analytics
        this.trackContentRequest(contentType, url);

        // Check if circuit breaker is open
        if (!this.apiHealthy && this.consecutiveFailures >= this.circuitBreakerThreshold) {
            this.handleCircuitBreakerOpen(element, cacheKey);
            return;
        }
        
        // Check if we're offline
        if (this.offlineMode) {
            this.handleOfflineMode(element, cacheKey);
            return;
        }
        
        // Check if we should use browser cache
        if (!forceRefresh && this.shouldUseBrowserCache(cacheKey)) {
            const cachedData = this.getFromBrowserCache(cacheKey);
            if (cachedData) {
                this.renderCachedContent(element, cachedData, false);
                
                // Refresh in background if data is older than threshold
                if (this.shouldRefreshInBackground(cachedData)) {
                    this.refreshContentInBackground(url, contentType, cacheKey);
                }
                
                return;
            }
        }

        try {
            // Show stale content immediately if available (unless force refresh)
            if (!forceRefresh) {
                const staleContent = this.getStaleContent(cacheKey);
                if (staleContent && retries === 0) {
                    this.renderStaleContent(element, staleContent);
                } else {
                    this.addLoadingState(element);
                }
            } else {
                this.addLoadingState(element);
            }
            
            // Check if we need to queue this request (too many concurrent requests)
            if (this.concurrentRequests >= this.maxConcurrentRequests && priority !== 'high') {
                return new Promise((resolve, reject) => {
                    this.requestQueue.push({
                        url,
                        options: { forceRefresh, contentType, cacheKey, element },
                        resolve,
                        reject,
                        priority: priority === 'low' ? 0 : 1,
                        timestamp: Date.now()
                    });
                    
                    console.log(`Request queued (${this.requestQueue.length} waiting): ${url}`);
                });
            }
            
            // Increment concurrent requests counter
            this.concurrentRequests++;
            
            // Setup request with timeout
            const controller = new AbortController();
            const timeoutMs = priority === 'high' ? 8000 : (priority === 'low' ? 20000 : 12000);
            const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
            
            this.requestTimeouts.set(url, { controller, timeoutId });
            
            // Add cache busting for force refresh
            const requestUrl = forceRefresh ? 
                `${url}${url.includes('?') ? '&' : '?'}_=${Date.now()}` : 
                url;
            
            // Make the request with appropriate headers
            const response = await fetch(requestUrl, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cache-Control': forceRefresh ? 'no-cache, no-store, must-revalidate' : 'max-age=0',
                    'Pragma': forceRefresh ? 'no-cache' : '',
                    'X-Priority': priority,
                    'X-Client-Version': this.getClientVersion()
                },
                signal: controller.signal,
                credentials: 'same-origin'
            });

            // Clean up timeout
            clearTimeout(timeoutId);
            this.requestTimeouts.delete(url);
            
            // Decrement concurrent requests counter
            this.concurrentRequests--;
            
            // Process next queued request if any
            if (this.requestQueue.length > 0) {
                setTimeout(() => this.processRequestQueue(), 50);
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Get response data
            const content = await response.text();
            
            // Parse JSON if it's API response
            let parsedData;
            try {
                parsedData = JSON.parse(content);
                // Validate content before using
                if (!this.isValidAPIResponse(parsedData)) {
                    throw new Error('Invalid API response format');
                }
            } catch (e) {
                // If not JSON, treat as HTML content
                parsedData = { html: content };
            }
            
            // Cache the fresh content in memory
            this.staleContentCache.set(cacheKey, {
                content: parsedData,
                timestamp: Date.now(),
                html: parsedData.html || content,
                etag: response.headers.get('ETag'),
                lastModified: response.headers.get('Last-Modified')
            });
            
            // Also cache in browser storage if available
            this.saveToLocalCache(cacheKey, {
                content: parsedData,
                timestamp: Date.now(),
                html: parsedData.html || content,
                etag: response.headers.get('ETag'),
                lastModified: response.headers.get('Last-Modified')
            });
            
            // Render the content
            this.renderContent(element, parsedData);
            this.removeLoadingState(element);
            
            // Reset failure counter on success
            this.consecutiveFailures = 0;
            this.apiHealthy = true;
            
            // Trigger any initialization for the new content
            this.initializeNewContent(element);
            
            // Return the data for promise chaining
            return parsedData;
            
        } catch (error) {
            // Decrement concurrent requests counter if error
            if (this.concurrentRequests > 0) {
                this.concurrentRequests--;
            }
            
            return this.handleLoadError(element, error, url, retries, cacheKey);
        }
    }
    
    /**
     * Get client version for cache invalidation
     */
    getClientVersion() {
        return document.querySelector('meta[name="app-version"]')?.content || '1.0';
    }
    
    /**
     * Track content request for analytics
     */
    trackContentRequest(contentType, url) {
        // Simple tracking for now - could be expanded
        if (!this._requestStats) {
            this._requestStats = {};
        }
        
        if (!this._requestStats[contentType]) {
            this._requestStats[contentType] = 0;
        }
        
        this._requestStats[contentType]++;
    }
    
    /**
     * Check if we should use browser cache
     */
    shouldUseBrowserCache(cacheKey) {
        // Use browser cache if available and not too old
        if (!this.localStorageEnabled && !this.sessionStorageEnabled) {
            return false;
        }
        
        const cachedData = this.getFromBrowserCache(cacheKey);
        if (!cachedData) {
            return false;
        }
        
        // Use cache if less than 5 minutes old
        const maxAge = 5 * 60 * 1000; // 5 minutes
        const age = Date.now() - cachedData.timestamp;
        return age < maxAge;
    }
    
    /**
     * Get content from browser cache
     */
    getFromBrowserCache(cacheKey) {
        try {
            // Try sessionStorage first (faster)
            if (this.sessionStorageEnabled) {
                const data = sessionStorage.getItem(`content_${cacheKey}`);
                if (data) {
                    return JSON.parse(data);
                }
            }
            
            // Then try localStorage
            if (this.localStorageEnabled) {
                const data = localStorage.getItem(`content_${cacheKey}`);
                if (data) {
                    return JSON.parse(data);
                }
            }
        } catch (e) {
            console.warn('Error reading from browser cache:', e);
        }
        
        return null;
    }
    
    /**
     * Save content to local cache
     */
    saveToLocalCache(cacheKey, data) {
        try {
            // Save to sessionStorage for current session
            if (this.sessionStorageEnabled) {
                sessionStorage.setItem(`content_${cacheKey}`, JSON.stringify(data));
            }
            
            // Also save important content to localStorage
            if (this.localStorageEnabled && (cacheKey.includes('home') || cacheKey.includes('detail'))) {
                localStorage.setItem(`content_${cacheKey}`, JSON.stringify(data));
            }
        } catch (e) {
            console.warn('Error saving to browser cache:', e);
        }
    }
    
    /**
     * Get stale content from memory cache
     */
    getStaleContent(cacheKey) {
        // First try memory cache
        const memoryCache = this.staleContentCache.get(cacheKey);
        if (memoryCache) {
            return memoryCache;
        }
        
        // Then try browser storage
        return this.getFromBrowserCache(cacheKey);
    }
    
    /**
     * Check if we should refresh content in background
     */
    shouldRefreshInBackground(cachedData) {
        if (!cachedData || !cachedData.timestamp) {
            return true;
        }
        
        // Refresh if older than 2 minutes
        const refreshAge = 2 * 60 * 1000; // 2 minutes
        const age = Date.now() - cachedData.timestamp;
        return age > refreshAge;
    }
    
    /**
     * Refresh content in background without blocking UI
     */
    refreshContentInBackground(url, contentType, cacheKey) {
        // Don't refresh if offline or circuit breaker is open
        if (this.offlineMode || !this.apiHealthy) {
            return;
        }
        
        console.log(`Background refresh for: ${url}`);
        
        // Use fetch with low priority
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Cache-Control': 'no-cache',
                'X-Priority': 'low',
                'X-Background-Refresh': 'true'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.text();
        })
        .then(content => {
            // Parse and cache the updated content
            try {
                let parsedData;
                try {
                    parsedData = JSON.parse(content);
                    if (!this.isValidAPIResponse(parsedData)) {
                        throw new Error('Invalid API response');
                    }
                } catch (e) {
                    parsedData = { html: content };
                }
                
                // Update cache
                this.staleContentCache.set(cacheKey, {
                    content: parsedData,
                    timestamp: Date.now(),
                    html: parsedData.html || content
                });
                
                // Update browser cache
                this.saveToLocalCache(cacheKey, {
                    content: parsedData,
                    timestamp: Date.now(),
                    html: parsedData.html || content
                });
                
                console.log(`Background refresh completed for: ${url}`);
            } catch (e) {
                console.warn(`Error in background refresh: ${e.message}`);
            }
        })
        .catch(error => {
            console.warn(`Background refresh failed: ${error.message}`);
        });
    }
    
    /**
     * Handle offline mode by showing cached content
     */
    handleOfflineMode(element, cacheKey) {
        const cachedData = this.getStaleContent(cacheKey);
        
        if (cachedData) {
            this.renderCachedContent(element, cachedData, true);
        } else {
            this.showOfflineMessage(element);
        }
    }
    
    /**
     * Render cached content with offline indicator
     */
    renderCachedContent(element, cachedData, isOffline) {
        if (!cachedData || (!cachedData.content && !cachedData.html)) {
            this.showLoadingError(element, new Error('No cached content available'));
            return;
        }
        
        // Render the content
        if (cachedData.content) {
            this.renderContent(element, cachedData.content);
        } else if (cachedData.html) {
            element.innerHTML = cachedData.html;
        }
        
        // Remove loading state
        this.removeLoadingState(element);
        
        // Mark as loaded
        element.dataset.loaded = 'true';
        element.dataset.fromCache = 'true';
        
        // Add offline indicator if needed
        if (isOffline) {
            this.addOfflineIndicator(element, cachedData.timestamp);
        } else {
            // Add cache age indicator
            const ageInMinutes = Math.floor((Date.now() - cachedData.timestamp) / 60000);
            if (ageInMinutes > 5) {
                this.addCacheAgeIndicator(element, ageInMinutes);
            }
        }
    }
    
    /**
     * Add offline indicator to element
     */
    addOfflineIndicator(element, timestamp) {
        // Remove any existing indicators
        const existingIndicator = element.querySelector('.offline-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        // Create offline indicator
        const indicator = document.createElement('div');
        indicator.className = 'offline-indicator';
        
        // Calculate age of cached content
        let timeInfo = '';
        if (timestamp) {
            const ageInMinutes = Math.floor((Date.now() - timestamp) / 60000);
            if (ageInMinutes < 60) {
                timeInfo = `${ageInMinutes} minute${ageInMinutes !== 1 ? 's' : ''} ago`;
            } else {
                const ageInHours = Math.floor(ageInMinutes / 60);
                timeInfo = `${ageInHours} hour${ageInHours !== 1 ? 's' : ''} ago`;
            }
        }
        
        indicator.innerHTML = `
            <div class="offline-badge">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 1l22 22M16.72 11.06A10.94 10.94 0 0119 12.55M5 12.55a10.94 10.94 0 015.17-2.39M10.71 5.05A16 16 0 0122.58 9M1.42 9a15.91 15.91 0 014.7-2.88M8.53 16.11a6 6 0 016.95 0M12 20h.01"></path>
                </svg>
                <span>Offline</span>
                ${timeInfo ? `<span class="offline-time">(Cached ${timeInfo})</span>` : ''}
            </div>
        `;
        
        // Add to element
        element.style.position = 'relative';
        element.appendChild(indicator);
    }
    
    /**
     * Add cache age indicator
     */
    addCacheAgeIndicator(element, ageInMinutes) {
        // Only add for older content
        if (ageInMinutes < 5) return;
        
        // Remove any existing indicators
        const existingIndicator = element.querySelector('.cache-age-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        // Format age text
        let ageText;
        if (ageInMinutes < 60) {
            ageText = `${ageInMinutes} minute${ageInMinutes !== 1 ? 's' : ''} ago`;
        } else {
            const ageInHours = Math.floor(ageInMinutes / 60);
            ageText = `${ageInHours} hour${ageInHours !== 1 ? 's' : ''} ago`;
        }
        
        // Create indicator
        const indicator = document.createElement('div');
        indicator.className = 'cache-age-indicator';
        indicator.innerHTML = `
            <div class="cache-badge">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                <span>Updated ${ageText}</span>
            </div>
        `;
        
        // Add to element
        element.appendChild(indicator);
    }
    
    /**
     * Show offline message when no cached content is available
     */
    showOfflineMessage(element) {
        this.removeLoadingState(element);
        
        element.innerHTML = `
            <div class="offline-message">
                <div class="offline-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M1 1l22 22M16.72 11.06A10.94 10.94 0 0119 12.55M5 12.55a10.94 10.94 0 015.17-2.39M10.71 5.05A16 16 0 0122.58 9M1.42 9a15.91 15.91 0 014.7-2.88M8.53 16.11a6 6 0 016.95 0M12 20h.01"></path>
                    </svg>
                </div>
                <h3>You're offline</h3>
                <p>This content isn't available offline. Please check your connection and try again.</p>
                <button class="retry-button" onclick="window.location.reload()">Retry</button>
            </div>
        `;
        
        element.dataset.loaded = 'true';
        element.dataset.offline = 'true';
    }
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = 3000) {
        // Remove any existing toast
        const existingToast = document.querySelector('.kortekstream-toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `kortekstream-toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-message">${message}</span>
                <button class="toast-close">&times;</button>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(toast);
        
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

    /**
     * Validate API response to avoid caching broken data
     */
    isValidAPIResponse(data) {
        if (!data || typeof data !== 'object') return false;
        
        // Check if it's an error response
        if (data.error && !data.data && !data.html) return false;
        
        // Check if it has valid content
        if (data.success === false && !data.html && !data.data) return false;
        
        // Check confidence score if present (avoid caching low confidence data)
        if (data.confidence_score !== undefined && data.confidence_score < 0.3) return false;
        
        return true;
    }

    /**
     * Handle loading errors with smarter retry logic
     */
    handleLoadError(element, error, url, retries, cacheKey) {
        console.warn(`Failed to load content for element (attempt ${retries + 1}):`, error);
        
        clearTimeout(this.requestTimeouts.get(url)?.timeoutId);
        this.requestTimeouts.delete(url);
        
        this.consecutiveFailures++;
        
        // If we have stale content and this is a timeout/network error, show stale content
        if ((error.name === 'AbortError' || error.message.includes('network')) && 
            this.staleContentCache.has(cacheKey)) {
            const staleData = this.staleContentCache.get(cacheKey);
            this.renderStaleContent(element, staleData, true); // Show with stale indicator
            this.removeLoadingState(element);
            return;
        }
        
        if (retries < this.maxRetries && this.consecutiveFailures < this.circuitBreakerThreshold) {
            // Exponential backoff with jitter
            const jitter = Math.random() * 1000;
            const delay = (this.retryDelay * Math.pow(2, retries)) + jitter;
            
            setTimeout(() => {
                this.loadContent(element, retries + 1);
            }, delay);
        } else {
            // Check if we can use stale content as fallback
            if (this.staleContentCache.has(cacheKey)) {
                const staleData = this.staleContentCache.get(cacheKey);
                this.renderStaleContent(element, staleData, true);
                this.removeLoadingState(element);
            } else {
                this.showLoadingError(element, error);
            }
            
            // Open circuit breaker if too many failures
            if (this.consecutiveFailures >= this.circuitBreakerThreshold) {
                this.apiHealthy = false;
                this.scheduleCircuitBreakerReset();
                this.showToast('API experiencing issues. Using cached content when available.', 'warning', 5000);
            }
        }
    }

    /**
     * Handle circuit breaker open state
     */
    handleCircuitBreakerOpen(element, cacheKey) {
        // Try to use stale content if available
        if (this.staleContentCache.has(cacheKey)) {
            const staleData = this.staleContentCache.get(cacheKey);
            this.renderStaleContent(element, staleData, true);
            this.removeLoadingState(element);
        } else {
            this.showCircuitBreakerMessage(element);
        }
    }

    /**
     * Schedule circuit breaker reset
     */
    scheduleCircuitBreakerReset() {
        setTimeout(() => {
            this.apiHealthy = true;
            this.consecutiveFailures = 0;
            this.showToast('Retrying API connections...', 'info', 3000);
        }, this.circuitBreakerResetTime);
    }

    /**
     * Render stale content with optional indicator
     */
    renderStaleContent(element, staleData, showStaleIndicator = false) {
        if (staleData.html) {
            element.innerHTML = staleData.html;
        } else if (staleData.content) {
            this.renderContent(element, staleData.content);
        }

        if (showStaleIndicator) {
            this.addStaleIndicator(element, staleData.timestamp);
        }

        this.initializeNewContent(element);
    }

    /**
     * Add stale content indicator
     */
    addStaleIndicator(element, timestamp) {
        const age = Date.now() - timestamp;
        const ageMinutes = Math.floor(age / 60000);
        
        const indicator = document.createElement('div');
        indicator.className = 'stale-indicator bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 text-yellow-800 dark:text-yellow-200 px-3 py-2 rounded-lg text-sm mb-4';
        indicator.innerHTML = `
            <div class="flex items-center space-x-2">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
                <span>Showing cached content from ${ageMinutes}m ago due to API issues</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-auto text-yellow-600 hover:text-yellow-800">×</button>
            </div>
        `;
        
        element.insertBefore(indicator, element.firstChild);
    }

    /**
     * Render content from API response
     */
    renderContent(element, data) {
        if (data.html) {
            element.innerHTML = data.html;
        } else if (data.data || Array.isArray(data)) {
            // Handle structured data - this would need to be customized per content type
            const content = data.data || data;
            if (Array.isArray(content) && content.length > 0) {
                // Generate HTML from data
                element.innerHTML = this.generateContentHTML(content, element.dataset.contentType);
            }
        }
    }

    /**
     * Generate HTML from structured data
     */
    generateContentHTML(data, contentType) {
        switch (contentType) {
            case 'home_recent':
            case 'home_popular':
                return this.generateAnimeGrid(data);
            case 'latest_episodes':
                return this.generateEpisodeList(data);
            case 'recommendations':
                return this.generateRecommendationList(data);
            default:
                return '<p class="text-center text-gray-500">Content not available</p>';
        }
    }

    /**
     * Generate anime grid HTML
     */
    generateAnimeGrid(animeList) {
        return `
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-7 gap-3 sm:gap-4">
                ${animeList.map(anime => `
                    <div class="anime-card bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-all duration-300">
                        <div class="relative aspect-[3/4] overflow-hidden rounded-t-lg">
                            <img src="${anime.thumbnail || '/static/images/placeholder-anime.jpg'}" 
                                 alt="${anime.title || anime.judul || 'Anime'}"
                                 class="w-full h-full object-cover"
                                 loading="lazy"
                                 onerror="this.src='/static/images/placeholder-anime.jpg'">
                        </div>
                        <div class="p-2">
                            <h3 class="font-medium text-sm text-gray-900 dark:text-white line-clamp-2">
                                ${anime.title || anime.judul || 'Untitled'}
                            </h3>
                            ${anime.status ? `<p class="text-xs text-gray-500 mt-1">${anime.status}</p>` : ''}
                        </div>
                        <a href="/detail/?anime_slug=${anime.slug || (anime.judul || '').toLowerCase()}" 
                           class="absolute inset-0 z-10"></a>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Generate episode list HTML
     */
    generateEpisodeList(episodeList) {
        return `
            <div class="space-y-3">
                ${episodeList.map(episode => `
                    <div class="episode-card bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
                        <div class="flex items-center space-x-4">
                            <img src="${episode.thumbnail || '/static/images/placeholder-episode.jpg'}" 
                                 alt="${episode.title || episode.judul || 'Episode'}"
                                 class="w-16 h-12 object-cover rounded"
                                 loading="lazy">
                            <div class="flex-1 min-w-0">
                                <h3 class="font-medium text-sm text-gray-900 dark:text-white">
                                    ${episode.title || episode.judul || 'Episode'}
                                </h3>
                                ${episode.anime_title ? `<p class="text-xs text-gray-500 mt-1">${episode.anime_title}</p>` : ''}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Generate recommendation list HTML
     */
    generateRecommendationList(recommendationList) {
        return `
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                ${recommendationList.map(anime => `
                    <div class="recommendation-card bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
                        <div class="flex space-x-3">
                            <img src="${anime.thumbnail || '/static/images/placeholder-anime.jpg'}" 
                                 alt="${anime.title || anime.judul || 'Anime'}"
                                 class="w-16 h-20 object-cover rounded"
                                 loading="lazy">
                            <div class="flex-1 min-w-0">
                                <h3 class="font-medium text-sm text-gray-900 dark:text-white">
                                    ${anime.title || anime.judul || 'Untitled'}
                                </h3>
                                ${anime.genres ? `<p class="text-xs text-gray-500 mt-1">${anime.genres.join(', ')}</p>` : ''}
                                ${anime.rating ? `<p class="text-xs text-yellow-500 mt-1">⭐ ${anime.rating}</p>` : ''}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Show circuit breaker message
     */
    showCircuitBreakerMessage(element) {
        this.removeLoadingState(element);
        
        const message = document.createElement('div');
        message.className = 'circuit-breaker-message p-6 text-center bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800';
        message.innerHTML = `
            <div class="mb-4">
                <svg class="h-12 w-12 text-orange-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
            <h3 class="text-lg font-medium text-orange-800 dark:text-orange-200 mb-2">Service Temporarily Unavailable</h3>
            <p class="text-orange-600 dark:text-orange-300 mb-4">We're experiencing high load. Please try again in a few minutes.</p>
            <button class="retry-circuit-btn bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors duration-200" 
                    onclick="kortekAPI.forceRetry(this.closest('[data-content-url]'))">
                Try Again
            </button>
        `;
        
        element.appendChild(message);
    }

    /**
     * Force retry (bypass circuit breaker)
     */
    forceRetry(element) {
        const message = element.querySelector('.circuit-breaker-message');
        if (message) {
            message.remove();
        }
        
        // Temporarily reset circuit breaker for this request
        const originalHealthy = this.apiHealthy;
        const originalFailures = this.consecutiveFailures;
        
        this.apiHealthy = true;
        this.consecutiveFailures = 0;
        
        this.loadContent(element).finally(() => {
            // Restore state if request fails
            if (!this.apiHealthy) {
                this.consecutiveFailures = originalFailures;
            }
        });
    }

    /**
     * Show error state with retry option
     */
    showLoadingError(element, error) {
        this.removeLoadingState(element);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-state p-6 text-center bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800';
        errorDiv.innerHTML = `
            <div class="error-icon mb-4">
                <svg class="h-12 w-12 text-red-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <h3 class="text-lg font-medium text-red-800 dark:text-red-200 mb-2">Content Unavailable</h3>
            <p class="text-red-600 dark:text-red-300 mb-4">Sorry, we're having trouble loading this content right now.</p>
            <button class="retry-btn bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors duration-200" 
                    onclick="kortekAPI.retryLoading(this.closest('[data-content-url]'))">
                Try Again
            </button>
        `;
        
        element.appendChild(errorDiv);
    }

    /**
     * Retry loading content
     */
    retryLoading(element) {
        const errorState = element.querySelector('.error-state');
        if (errorState) {
            errorState.remove();
        }
        
        this.loadContent(element);
    }

    /**
     * Initialize new content after loading
     */
    initializeNewContent(element) {
        // Re-run any initialization scripts for the new content
        const scripts = element.querySelectorAll('script');
        scripts.forEach(script => {
            if (script.textContent) {
                try {
                    eval(script.textContent);
                } catch (e) {
                    console.warn('Error executing script:', e);
                }
            }
        });
        
        // Initialize any new progressive loading elements
        const newProgressiveElements = element.querySelectorAll('[data-progressive-load]');
        newProgressiveElements.forEach(el => {
            this.setupProgressiveLoading(el);
        });
    }

    /**
     * Check API health status and show status indicator
     */
    async checkAPIStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/api/status/`);
            const status = await response.json();
            this.updateStatusIndicator(status);
        } catch (error) {
            console.warn('Failed to check API status:', error);
            this.updateStatusIndicator({ circuit_breaker_open: true });
        }
    }

    /**
     * Update API status indicator in the UI
     */
    updateStatusIndicator(status) {
        let indicator = document.getElementById('api-status-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'api-status-indicator';
            indicator.className = 'fixed bottom-4 right-4 z-50 transition-all duration-300';
            document.body.appendChild(indicator);
        }

        const isDown = status.circuit_breaker_open;
        const statusClass = isDown ? 'bg-red-500' : 'bg-green-500';
        const statusText = isDown ? 'API Issues' : 'All Systems OK';
        
        if (isDown) {
            indicator.innerHTML = `
                <div class="${statusClass} text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2">
                    <div class="w-3 h-3 bg-white rounded-full animate-pulse"></div>
                    <span class="text-sm font-medium">${statusText}</span>
                    <button onclick="this.parentElement.parentElement.style.display='none'" 
                            class="ml-2 text-white hover:text-gray-200">×</button>
                </div>
            `;
            indicator.style.display = 'block';
        } else if (!isDown && indicator.style.display !== 'none') {
            // Show briefly that everything is OK, then hide
            indicator.innerHTML = `
                <div class="${statusClass} text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2">
                    <div class="w-3 h-3 bg-white rounded-full"></div>
                    <span class="text-sm font-medium">${statusText}</span>
                </div>
            `;
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 3000);
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg text-white transition-all duration-300 transform translate-x-full`;
        
        const bgColor = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500'
        }[type] || 'bg-gray-500';
        
        toast.classList.add(bgColor);
        toast.innerHTML = `
            <div class="flex items-center space-x-3">
                <span>${message}</span>
                <button onclick="this.closest('.toast').remove()" class="text-white hover:text-gray-200">×</button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // Auto remove
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

// Initialize the API handler when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.kortekAPI = new KortekStreamAPI();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KortekStreamAPI;
}