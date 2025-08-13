/**
 * Enhanced Image Handler for KortekStream
 * Optimized for high traffic with progressive loading, lazy loading, and error handling
 */
class ImageHandler {
    constructor() {
        this.placeholderImage = '/static/images/placeholder-anime.jpg';
        this.placeholderEpisode = '/static/images/placeholder-episode.jpg';
        this.observedImages = new Set();
        this.observer = null;
        this.supportsWebP = null;
        this.supportsAvif = null;
        this.devicePixelRatio = window.devicePixelRatio || 1;
        this.connectionType = this.getConnectionType();
        this.init();
    }
    
    /**
     * Initialize image handler
     */
    init() {
        // Check for modern image format support
        this.checkImageFormatSupport();
        
        // Initialize intersection observer for lazy loading
        this.initIntersectionObserver();
        
        // Process all images on page load
        document.addEventListener('DOMContentLoaded', () => {
            this.processAllImages();
            
            // Listen for dynamic content changes
            this.observeDOMChanges();
        });
        
        // Listen for network changes
        this.listenForNetworkChanges();
    }
    
    /**
     * Check which image formats are supported
     */
    checkImageFormatSupport() {
        // Check WebP support
        const webpImage = new Image();
        webpImage.onload = () => { this.supportsWebP = true; };
        webpImage.onerror = () => { this.supportsWebP = false; };
        webpImage.src = 'data:image/webp;base64,UklGRiQAAABXRUJQVlA4IBgAAAAwAQCdASoBAAEAAwA0JaQAA3AA/vuUAAA=';
        
        // Check AVIF support
        const avifImage = new Image();
        avifImage.onload = () => { this.supportsAvif = true; };
        avifImage.onerror = () => { this.supportsAvif = false; };
        avifImage.src = 'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgANogQEAwgMg8f8D///8WfhwB8+ErK42A=';
    }
    
    /**
     * Get connection type if available
     */
    getConnectionType() {
        if (navigator.connection) {
            return navigator.connection.effectiveType || 'unknown';
        }
        return 'unknown';
    }
    
    /**
     * Initialize intersection observer for lazy loading
     */
    initIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadImage(entry.target);
                        this.observer.unobserve(entry.target);
                        this.observedImages.delete(entry.target);
                    }
                });
            }, {
                rootMargin: '200px', // Load images when they're 200px from viewport
                threshold: 0.01
            });
        }
    }
    
    /**
     * Process all images on the page
     */
    processAllImages() {
        // Find all images
        const images = document.querySelectorAll('img:not([data-processed])');
        
        // Process each image
        images.forEach(img => this.prepareImage(img));
    }
    
    /**
     * Prepare image for optimized loading
     */
    prepareImage(img) {
        // Skip if already processed
        if (img.hasAttribute('data-processed')) {
            return;
        }
        
        // Mark as processed
        img.setAttribute('data-processed', 'true');
        
        // Store original src
        if (img.src && !img.hasAttribute('data-src') && !img.src.startsWith('data:')) {
            img.setAttribute('data-src', img.src);
        }
        
        // Add error handler
        this.addErrorHandler(img);
        
        // Add loading="lazy" attribute if not present
        if (!img.hasAttribute('loading')) {
            img.setAttribute('loading', 'lazy');
        }
        
        // Determine image type for placeholder
        const isEpisode = img.classList.contains('episode-img') || 
                         img.closest('.episode-card') || 
                         img.closest('.episode-thumbnail');
        
        // Set appropriate placeholder
        const placeholder = isEpisode ? this.placeholderEpisode : this.placeholderImage;
        
        // Use low-quality placeholder if available
        if (img.hasAttribute('data-placeholder')) {
            img.src = img.getAttribute('data-placeholder');
        } else {
            img.src = placeholder;
        }
        
        // Use intersection observer for lazy loading if available
        if (this.observer && !img.classList.contains('no-lazy')) {
            this.observer.observe(img);
            this.observedImages.add(img);
        } else {
            // Fallback to immediate loading for critical images
            this.loadImage(img);
        }
    }
    
    /**
     * Add error handler to image
     */
    addErrorHandler(img) {
        img.onerror = function() {
            // Determine image type for placeholder
            const isEpisode = this.classList.contains('episode-img') || 
                             this.closest('.episode-card') || 
                             this.closest('.episode-thumbnail');
            
            // Set appropriate placeholder
            const placeholder = isEpisode ? 
                '/static/images/placeholder-episode.jpg' : 
                '/static/images/placeholder-anime.jpg';
            
            // Set placeholder image
            this.src = placeholder;
            
            // Remove the onerror handler to prevent infinite loops
            this.onerror = null;
            
            // Add a class for styling
            this.classList.add('img-error');
            
            // Add alt text if missing
            if (!this.alt || this.alt === '') {
                this.alt = 'Image not available';
            }
        };
    }
    
    /**
     * Load image with optimal format and size
     */
    loadImage(img) {
        // Skip if no data-src
        if (!img.hasAttribute('data-src')) {
            return;
        }
        
        const originalSrc = img.getAttribute('data-src');
        
        // Skip data URLs
        if (originalSrc.startsWith('data:')) {
            return;
        }
        
        // Get optimal image URL based on device and connection
        const optimizedSrc = this.getOptimalImageUrl(originalSrc, img);
        
        // Create new image to preload
        const newImage = new Image();
        
        // When image loads, update the src
        newImage.onload = () => {
            img.src = optimizedSrc;
            img.classList.add('loaded');
            
            // Add fade-in animation
            if (!img.classList.contains('no-animation')) {
                img.style.transition = 'opacity 0.3s ease';
                img.style.opacity = '0';
                setTimeout(() => {
                    img.style.opacity = '1';
                }, 10);
            }
        };
        
        // If error, fall back to original
        newImage.onerror = () => {
            img.src = originalSrc;
        };
        
        // Start loading
        newImage.src = optimizedSrc;
    }
    
    /**
     * Get optimal image URL based on device and connection
     */
    getOptimalImageUrl(originalSrc, img) {
        // Skip optimization for external URLs
        if (originalSrc.startsWith('http') && !originalSrc.includes(window.location.hostname)) {
            return originalSrc;
        }
        
        // Parse URL
        let url = new URL(originalSrc, window.location.origin);
        let params = new URLSearchParams(url.search);
        
        // Get image dimensions
        const width = img.getAttribute('width') || img.clientWidth || 0;
        const height = img.getAttribute('height') || img.clientHeight || 0;
        
        // Calculate optimal size based on device pixel ratio
        const optimalWidth = width * this.devicePixelRatio;
        const optimalHeight = height * this.devicePixelRatio;
        
        // Add width/height parameters if dimensions are available
        if (optimalWidth > 0) {
            params.set('w', Math.round(optimalWidth));
        }
        
        if (optimalHeight > 0) {
            params.set('h', Math.round(optimalHeight));
        }
        
        // Set optimal format
        if (this.supportsAvif) {
            params.set('fm', 'avif');
        } else if (this.supportsWebP) {
            params.set('fm', 'webp');
        }
        
        // Set quality based on connection
        if (this.connectionType === '4g') {
            params.set('q', '85');
        } else if (this.connectionType === '3g') {
            params.set('q', '70');
        } else if (this.connectionType === '2g' || this.connectionType === 'slow-2g') {
            params.set('q', '60');
        }
        
        // Update URL with new parameters
        url.search = params.toString();
        return url.toString();
    }
    
    /**
     * Observe DOM changes to handle dynamically added images
     */
    observeDOMChanges() {
        // Use MutationObserver to detect new images
        if ('MutationObserver' in window) {
            const observer = new MutationObserver((mutations) => {
                let hasNewImages = false;
                
                mutations.forEach(mutation => {
                    // Check for new nodes
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        mutation.addedNodes.forEach(node => {
                            // Check if node is an element
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                // Check if node is an image
                                if (node.tagName === 'IMG' && !node.hasAttribute('data-processed')) {
                                    this.prepareImage(node);
                                    hasNewImages = true;
                                }
                                
                                // Check for images inside the node
                                const images = node.querySelectorAll('img:not([data-processed])');
                                if (images.length > 0) {
                                    images.forEach(img => this.prepareImage(img));
                                    hasNewImages = true;
                                }
                            }
                        });
                    }
                });
                
                // Log if new images were found
                if (hasNewImages) {
                    console.log('Processed dynamically added images');
                }
            });
            
            // Start observing
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }
    
    /**
     * Listen for network changes to adjust image quality
     */
    listenForNetworkChanges() {
        if (navigator.connection) {
            navigator.connection.addEventListener('change', () => {
                this.connectionType = navigator.connection.effectiveType || 'unknown';
                console.log(`Connection changed to ${this.connectionType}`);
            });
        }
    }
}

// Initialize image handler
const imageHandler = new ImageHandler();

// Export for use in other modules
window.imageHandler = imageHandler;