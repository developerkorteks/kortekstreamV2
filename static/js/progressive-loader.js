/**
 * Progressive Content Loader for KortekStream
 * Handles lazy loading, infinite scroll, and load more functionality
 */

class ProgressiveLoader {
    constructor() {
        this.loadingQueue = new Map();
        this.retryDelays = new Map();
        this.maxRetries = 3;
        this.debounceTimers = new Map();
        this.intersectionObserver = null;
        this.init();
    }

    init() {
        this.initIntersectionObserver();
        this.initLoadMoreButtons();
        this.initInfiniteScroll();
        
        // Initialize progressive loading on DOM ready
        document.addEventListener('DOMContentLoaded', () => {
            this.loadInitialContent();
        });
    }

    /**
     * Initialize Intersection Observer for lazy loading
     */
    initIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            this.intersectionObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.handleIntersection(entry.target);
                    }
                });
            }, {
                root: null,
                rootMargin: '50px',
                threshold: 0.1
            });

            // Observe lazy load elements
            this.observeLazyElements();
        }
    }

    /**
     * Observe elements for lazy loading
     */
    observeLazyElements() {
        const lazyElements = document.querySelectorAll('[data-lazy-load]');
        lazyElements.forEach(element => {
            this.intersectionObserver.observe(element);
        });
    }

    /**
     * Handle intersection for lazy loading
     */
    handleIntersection(element) {
        const contentType = element.dataset.lazyLoad;
        if (contentType && !element.dataset.loaded) {
            this.loadContentSection(element, contentType);
            this.intersectionObserver.unobserve(element);
        }
    }

    /**
     * Initialize load more buttons
     */
    initLoadMoreButtons() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('.load-more-btn, [data-load-more]')) {
                e.preventDefault();
                this.handleLoadMore(e.target);
            }
        });
    }

    /**
     * Initialize infinite scroll for specific sections
     */
    initInfiniteScroll() {
        let scrollTimer;
        
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimer);
            scrollTimer = setTimeout(() => {
                this.checkInfiniteScroll();
            }, 100); // Debounce scroll events
        });
    }

    /**
     * Check if we should trigger infinite scroll
     */
    checkInfiniteScroll() {
        const infiniteElements = document.querySelectorAll('[data-infinite-scroll="true"]');
        
        infiniteElements.forEach(element => {
            const rect = element.getBoundingClientRect();
            const isNearBottom = rect.bottom <= window.innerHeight + 200;
            
            if (isNearBottom && !element.dataset.loading && !element.dataset.allLoaded) {
                const loadMoreBtn = element.querySelector('.load-more-btn');
                if (loadMoreBtn) {
                    this.handleLoadMore(loadMoreBtn);
                }
            }
        });
    }

    /**
     * Load initial content sections
     */
    loadInitialContent() {
        const contentSections = document.querySelectorAll('[data-progressive-load]');
        
        contentSections.forEach((section, index) => {
            const priority = section.dataset.progressiveLoad;
            const delay = this.getLoadDelay(priority, index);
            
            setTimeout(() => {
                this.loadContentSection(section);
            }, delay);
        });
    }

    /**
     * Get loading delay based on priority
     */
    getLoadDelay(priority, index = 0) {
        const baseDelay = index * 100; // Stagger loading
        
        switch (priority) {
            case 'critical': return baseDelay;
            case 'high': return baseDelay + 200;
            case 'normal': return baseDelay + 500;
            case 'low': return baseDelay + 1000;
            case 'lazy': return baseDelay + 2000;
            default: return baseDelay + 500;
        }
    }

    /**
     * Load content section
     */
    async loadContentSection(element, contentType = null) {
        if (element.dataset.loading === 'true') {
            return;
        }
        
        // Allow loading more content even if already loaded (for pagination)
        if (element.dataset.loaded === 'true' && !element.dataset.appendMode) {
            return;
        }

        const type = contentType || element.dataset.contentType || element.dataset.progressiveLoad;
        const category = element.dataset.category || 'anime';
        const page = element.dataset.page || '1';
        
        if (!type) {
            console.warn('No content type specified for progressive loading');
            return;
        }

        try {
            element.dataset.loading = 'true';
            this.showLoadingState(element);

            const response = await this.fetchContent(type, category, page);
            
            if (response.success) {
                this.renderContent(element, response);
                element.dataset.loaded = 'true';
            } else {
                throw new Error(response.error || 'Failed to load content');
            }

        } catch (error) {
            console.error('Error loading progressive content:', error);
            this.handleLoadError(element, error, type, category, page);
        } finally {
            element.dataset.loading = 'false';
            this.hideLoadingState(element);
        }
    }

    /**
     * Fetch content from API
     */
    async fetchContent(type, category, page) {
        const url = new URL(`${window.location.origin}/api/load-content/`);
        url.searchParams.set('type', type);
        url.searchParams.set('category', category);
        url.searchParams.set('page', page);

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(15000) // 15 second timeout
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Render content in element
     */
    renderContent(element, response) {
        if (response.html) {
            // For load more, append to existing content
            if (element.dataset.appendMode === 'true') {
                const progressiveContent = element.querySelector('.progressive-content');
                const gridContainer = progressiveContent?.querySelector('.grid');
                
                if (gridContainer) {
                    // Parse new content
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = response.html;
                    const newProgressiveContent = tempDiv.querySelector('.progressive-content');
                    const newGridContainer = newProgressiveContent?.querySelector('.grid');
                    
                    if (newGridContainer) {
                        // Append new grid items with animation
                        Array.from(newGridContainer.children).forEach((child, index) => {
                            child.style.opacity = '0';
                            child.style.transform = 'translateY(20px)';
                            gridContainer.appendChild(child);
                            
                            // Stagger animation
                            setTimeout(() => {
                                child.style.transition = 'all 0.5s ease';
                                child.style.opacity = '1';
                                child.style.transform = 'translateY(0)';
                            }, index * 100);
                        });
                    }
                    
                    // Handle load more button
                    this.updateLoadMoreButton(element, response);
                    
                } else {
                    // Fallback: try to find any grid container or append to progressive content
                    const contentContainer = element.querySelector('.progressive-content') || element;
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = response.html;
                    
                    const newContent = tempDiv.querySelector('.progressive-content');
                    if (newContent && contentContainer) {
                        // Try to append just the grid part
                        const newGrid = newContent.querySelector('.grid');
                        const existingGrid = contentContainer.querySelector('.grid');
                        
                        if (newGrid && existingGrid) {
                            Array.from(newGrid.children).forEach(child => {
                                existingGrid.appendChild(child);
                            });
                        } else {
                            // Last resort: append all children
                            Array.from(newContent.children).forEach(child => {
                                if (!child.querySelector('.load-more-btn')) { // Skip load more button
                                    contentContainer.appendChild(child);
                                }
                            });
                        }
                    }
                    
                    // Handle load more button
                    this.updateLoadMoreButton(element, response);
                }
            } else {
                element.innerHTML = response.html;
            }

            // Update pagination data from response
            if (response.has_more !== undefined) {
                element.dataset.hasMore = response.has_more ? 'true' : 'false';
            }
            if (response.next_page !== undefined && response.next_page !== null) {
                element.dataset.page = response.next_page.toString();
            }
            if (response.has_more === false) {
                element.dataset.allLoaded = 'true';
            }

            // Add fade-in animation to new content
            this.animateNewContent(element);

            // Re-observe new lazy elements
            if (this.intersectionObserver) {
                const newLazyElements = element.querySelectorAll('[data-lazy-load]:not([data-observed])');
                newLazyElements.forEach(el => {
                    el.dataset.observed = 'true';
                    this.intersectionObserver.observe(el);
                });
            }

            // Clean up append mode
            delete element.dataset.appendMode;
        }
    }
    
    /**
     * Update load more button after content append
     */
    updateLoadMoreButton(element, response) {
        const existingLoadMore = element.querySelector('.load-more-btn');
        
        if (response.has_more && response.next_page) {
            if (existingLoadMore) {
                existingLoadMore.dataset.page = response.next_page.toString();
            }
        } else {
            if (existingLoadMore) {
                // Get content type to customize message
                const contentType = existingLoadMore.dataset.loadMore || element.dataset.contentType;
                
                if (contentType === 'home_recent') {
                    this.hideButtonWithMessage(existingLoadMore, '✓ All recent content loaded');
                } else if (contentType === 'home_popular') {
                    this.hideButtonWithMessage(existingLoadMore, '✓ All popular content loaded');
                } else if (contentType === 'latest_episodes') {
                    this.hideButtonWithMessage(existingLoadMore, '✓ All episodes loaded');
                } else {
                    this.hideButtonWithMessage(existingLoadMore, '✓ All content loaded');
                }
            }
        }
    }

    /**
     * Handle load more button click
     */
    async handleLoadMore(button) {
        // Look for container in hierarchy
        let container = button.closest('[data-progressive-load]');
        if (!container) {
            container = button.closest('[data-content-container]');
        }
        if (!container) {
            container = button.closest('.progressive-content-container');
        }
        if (!container) {
            container = button.closest('.progressive-content');
        }
        if (!container) {
            container = button.closest('[data-content-type]');
        }
        if (!container) {
            // Search up the DOM tree more extensively
            let parent = button.parentElement;
            while (parent && !container) {
                if (parent.dataset.progressiveLoad || 
                    parent.dataset.contentType || 
                    parent.classList.contains('progressive-content-container') ||
                    parent.classList.contains('progressive-content')) {
                    container = parent;
                    break;
                }
                parent = parent.parentElement;
            }
        }
        
        if (!container) {
            console.error('No container found for load more button');
            return;
        }
        
        if (container.dataset.loading === 'true') {
            return;
        }

        const contentType = button.dataset.loadMore || container.dataset.contentType;
        const category = button.dataset.category || container.dataset.category || 'anime';
        const currentPage = parseInt(button.dataset.page || container.dataset.page || '2');

        container.dataset.appendMode = 'true'; // Mark as append mode
        container.dataset.page = currentPage.toString();

        // Show modern loading state
        this.showButtonLoading(button);

        try {
            await this.loadContentSection(container, contentType);
            
            // Update button for next page
            if (container.dataset.hasMore === 'true') {
                button.dataset.page = container.dataset.page;
                // Use appropriate text based on content type
                if (contentType === 'home_recent') {
                    this.hideButtonLoading(button, 'Load More Recent');
                } else if (contentType === 'home_popular') {
                    this.hideButtonLoading(button, 'Load More Popular');
                } else if (contentType === 'latest_episodes') {
                    this.hideButtonLoading(button, 'Load More Episodes');
                } else {
                    this.hideButtonLoading(button, 'Load More');
                }
            } else {
                // No more content, hide button with elegant animation
                if (contentType === 'home_recent') {
                    this.hideButtonWithMessage(button, '✓ All recent content loaded');
                } else if (contentType === 'home_popular') {
                    this.hideButtonWithMessage(button, '✓ All popular content loaded');
                } else if (contentType === 'latest_episodes') {
                    this.hideButtonWithMessage(button, '✓ All episodes loaded');
                } else {
                    this.hideButtonWithMessage(button, '✓ All content loaded');
                }
            }

        } catch (error) {
            console.error('Load more error:', error);
            this.showButtonError(button);
        }
    }

    /**
     * Show loading state on button
     */
    showButtonLoading(button) {
        button.disabled = true;
        button.classList.add('btn-loading');
        
        // Show loading spinner
        const spinner = button.querySelector('.loading-spinner');
        const buttonText = button.querySelector('.button-text');
        
        if (spinner && buttonText) {
            spinner.classList.remove('hidden');
            // Find the text span within button-text and update only that
            const textSpan = buttonText.querySelector('span');
            if (textSpan) {
                textSpan.textContent = 'Loading...';
            } else {
                // If no span found, update the whole button-text but preserve structure
                buttonText.innerHTML = '<span class="mr-2">Loading...</span>';
            }
        } else {
            // Fallback for simple buttons
            button.textContent = 'Loading...';
        }
    }

    /**
     * Hide loading state on button
     */
    hideButtonLoading(button, originalText = 'Load More') {
        button.disabled = false;
        button.classList.remove('btn-loading');
        
        // Hide loading spinner
        const spinner = button.querySelector('.loading-spinner');
        const buttonText = button.querySelector('.button-text');
        
        if (spinner && buttonText) {
            spinner.classList.add('hidden');
            // Find the text span within button-text and update only that
            const textSpan = buttonText.querySelector('span');
            if (textSpan) {
                textSpan.textContent = originalText;
            } else {
                // If no span found, restore with proper structure
                buttonText.innerHTML = `
                    <span class="mr-2">${originalText}</span>
                    <svg class="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>
                    </svg>
                `;
            }
        } else {
            // Fallback for simple buttons
            button.textContent = originalText;
        }
    }

    /**
     * Show error state on button
     */
    showButtonError(button) {
        button.disabled = false;
        button.classList.remove('btn-loading');
        button.classList.add('bg-red-600', 'hover:bg-red-700', 'dark:bg-red-700', 'dark:hover:bg-red-800');
        
        const buttonText = button.querySelector('.button-text');
        if (buttonText) {
            buttonText.innerHTML = `
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                <span>Try Again</span>
            `;
        } else {
            button.textContent = 'Try Again';
        }
    }

    /**
     * Hide button with success message
     */
    hideButtonWithMessage(button, message) {
        const container = button.parentElement;
        
        // Create success message
        const successDiv = document.createElement('div');
        successDiv.className = 'text-center mt-4 py-4';
        successDiv.innerHTML = `
            <div class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold rounded-xl shadow-lg">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                ${message}
            </div>
        `;
        
        // Fade out button and replace with message
        button.style.transition = 'opacity 0.3s ease';
        button.style.opacity = '0';
        
        setTimeout(() => {
            container.replaceChild(successDiv, button);
        }, 300);
    }

    /**
     * Show loading state
     */
    showLoadingState(element) {
        // Add loading class for CSS animations
        element.classList.add('content-loading');

        // Create loading indicator if not exists
        if (!element.querySelector('.progressive-loading-indicator')) {
            const loading = document.createElement('div');
            loading.className = 'progressive-loading-indicator absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-gray-900/80 z-10';
            loading.innerHTML = `
                <div class="flex flex-col items-center space-y-3">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 dark:border-red-500"></div>
                    <p class="text-sm text-gray-600 dark:text-gray-400">Loading content<span class="loading-dots">...</span></p>
                </div>
            `;
            
            element.style.position = 'relative';
            element.appendChild(loading);
        }
    }

    /**
     * Hide loading state
     */
    hideLoadingState(element) {
        element.classList.remove('content-loading');
        
        const loadingIndicator = element.querySelector('.progressive-loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.opacity = '0';
            loadingIndicator.style.transition = 'opacity 0.3s ease';
            setTimeout(() => loadingIndicator.remove(), 300);
        }
    }

    /**
     * Handle loading errors
     */
    handleLoadError(element, error, type, category, page) {
        const retryKey = `${type}-${category}-${page}`;
        const retryCount = this.retryDelays.get(retryKey) || 0;

        if (retryCount < this.maxRetries) {
            // Retry with exponential backoff
            const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
            this.retryDelays.set(retryKey, retryCount + 1);

            setTimeout(() => {
                this.loadContentSection(element, type);
            }, delay);

            // Show retry message
            this.showRetryMessage(element, retryCount + 1, this.maxRetries);
        } else {
            // Max retries reached, show error state
            this.showErrorState(element, error);
        }
    }

    /**
     * Show retry message
     */
    showRetryMessage(element, currentRetry, maxRetries) {
        const retryDiv = document.createElement('div');
        retryDiv.className = 'retry-message text-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg';
        retryDiv.innerHTML = `
            <p class="text-yellow-800 dark:text-yellow-200 text-sm">
                Loading failed. Retrying... (${currentRetry}/${maxRetries})
            </p>
        `;
        
        element.innerHTML = '';
        element.appendChild(retryDiv);
    }

    /**
     * Show error state
     */
    showErrorState(element, error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-state text-center p-6 bg-red-50 dark:bg-red-900/20 rounded-lg';
        errorDiv.innerHTML = `
            <div class="error-icon mb-4">
                <svg class="h-12 w-12 text-red-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <h3 class="text-lg font-medium text-red-800 dark:text-red-200 mb-2">Content Unavailable</h3>
            <p class="text-red-600 dark:text-red-300 mb-4">We're having trouble loading this content. Please try again later.</p>
            <button class="retry-section-btn bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors duration-200" 
                    onclick="progressiveLoader.reloadSection(this.closest('[data-progressive-load]'))">
                Try Again
            </button>
        `;
        
        element.innerHTML = '';
        element.appendChild(errorDiv);
    }

    /**
     * Reload a section
     */
    reloadSection(element) {
        element.dataset.loaded = 'false';
        element.dataset.loading = 'false';
        this.loadContentSection(element);
    }

    /**
     * Animate new content
     */
    animateNewContent(element) {
        const newItems = element.querySelectorAll('.anime-card, .episode-card, .recommendation-card');
        
        newItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 50); // Stagger animation
        });
    }

    /**
     * Debounce function calls
     */
    debounce(func, wait, immediate = false) {
        return function executedFunction(...args) {
            const later = () => {
                this.debounceTimers.delete(func);
                if (!immediate) func.apply(this, args);
            };
            
            const callNow = immediate && !this.debounceTimers.has(func);
            
            if (this.debounceTimers.has(func)) {
                clearTimeout(this.debounceTimers.get(func));
            }
            
            this.debounceTimers.set(func, setTimeout(later, wait));
            
            if (callNow) func.apply(this, args);
        }.bind(this);
    }

    /**
     * Preload critical content
     */
    preloadCriticalContent() {
        const criticalElements = document.querySelectorAll('[data-progressive-load="critical"]');
        criticalElements.forEach(element => {
            this.loadContentSection(element);
        });
    }

    /**
     * Cleanup function
     */
    destroy() {
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        
        this.loadingQueue.clear();
        this.retryDelays.clear();
        this.debounceTimers.forEach(timer => clearTimeout(timer));
        this.debounceTimers.clear();
    }
}

// Initialize progressive loader
let progressiveLoader;

document.addEventListener('DOMContentLoaded', () => {
    progressiveLoader = new ProgressiveLoader();
    
    // Make it globally available
    window.progressiveLoader = progressiveLoader;
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (progressiveLoader) {
        progressiveLoader.destroy();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProgressiveLoader;
}