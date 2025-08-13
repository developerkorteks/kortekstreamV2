/**
 * Optimized Episode Player with Lazy Loading
 * This script optimizes the loading of video player resources
 * and improves performance on the episode detail page.
 */

// Flag to track if player scripts are loaded
window.playerScriptsLoaded = false;

// Flag to track if episode has been added to history
let hasBeenAddedToHistory = false;

// Lazy load player scripts
function loadPlayerScripts(callback) {
    // Set flag to prevent duplicate loading
    window.playerScriptsLoaded = true;
    
    // Load Plyr.io
    const plyrScript = document.createElement('script');
    plyrScript.src = 'https://cdn.plyr.io/3.7.8/plyr.polyfilled.js';
    
    // Load HLS.js after Plyr
    plyrScript.onload = function() {
        const hlsScript = document.createElement('script');
        hlsScript.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest';
        hlsScript.onload = callback;
        document.body.appendChild(hlsScript);
    };
    document.body.appendChild(plyrScript);
}

// Load tracking scripts asynchronously
function loadTrackingScripts() {
    const activityScript = document.createElement('script');
    activityScript.src = "/static/js/user_activity.js";
    
    activityScript.onload = function() {
        const trackingScript = document.createElement('script');
        trackingScript.src = "/static/js/video_tracking.js";
        document.body.appendChild(trackingScript);
    };
    document.body.appendChild(activityScript);
}

// History tracking function
function trackPlayerForHistory(player) {
    if (!player) return;
    
    // Make sure addToHistory is available
    if (typeof addToHistory === 'function') {
        const episodeDataElement = document.getElementById('episode-data-json');
        if (episodeDataElement) {
            const episodeData = JSON.parse(episodeDataElement.textContent);
            
            player.on('timeupdate', () => {
                if (!hasBeenAddedToHistory && player.currentTime > 30) {
                    addToHistory(episodeData);
                    hasBeenAddedToHistory = true;
                    player.off('timeupdate'); // Remove listener after adding
                }
            });
        }
    }
}

// Add iframe to history
function addIframeToHistory() {
    if (!hasBeenAddedToHistory && typeof addToHistory === 'function') {
        const episodeDataElement = document.getElementById('episode-data-json');
        if (episodeDataElement) {
            const episodeData = JSON.parse(episodeDataElement.textContent);
            addToHistory(episodeData);
            hasBeenAddedToHistory = true;
        }
    }
}

// Function for the flat structure player
function setupVideoPlayerFlat(url, serverName) {
    // If player scripts aren't loaded yet, load them first
    if (!window.playerScriptsLoaded) {
        loadPlayerScripts(function() {
            setupVideoPlayerFlatImpl(url, serverName);
        });
    } else {
        setupVideoPlayerFlatImpl(url, serverName);
    }
}

// Implementation of flat player setup (only called after scripts are loaded)
function setupVideoPlayerFlatImpl(url, serverName) {
    const playerWrapper = document.getElementById('player-wrapper-flat');
    const hlsWrapper = document.getElementById('hls-player-wrapper-flat');
    const iframeWrapper = document.getElementById('iframe-player-wrapper-flat');
    
    if (!playerWrapper || !hlsWrapper || !iframeWrapper) return;
    
    [playerWrapper, hlsWrapper, iframeWrapper].forEach(w => w.style.display = 'none');

    if (url.includes('.m3u8')) {
        hlsWrapper.style.display = 'block';
        const video = document.getElementById('hls-player-flat');
        if (Hls.isSupported()) {
            const hls = new Hls({
                maxBufferLength: 30,  // Optimize buffer for better performance
                maxMaxBufferLength: 60
            });
            hls.loadSource(url);
            hls.attachMedia(video);
            const player = new Plyr(video, {
                preload: 'metadata',  // Only preload metadata for faster initial load
                speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] }
            });
            trackPlayerForHistory(player);
        }
    } else if (url.includes('.mp4')) {
        playerWrapper.style.display = 'block';
        const video = document.getElementById('player-flat');
        video.src = url;
        video.preload = 'metadata';  // Only preload metadata
        const player = new Plyr(video, {
            preload: 'metadata',
            speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] }
        });
        trackPlayerForHistory(player);
    } else {
        iframeWrapper.style.display = 'block';
        const iframe = document.getElementById('iframe-player-flat');
        iframe.src = url;
        
        // Add to history after 30 seconds for iframe players
        setTimeout(addIframeToHistory, 30000);
    }
    
    // Update active server button
    document.querySelectorAll('.server-button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.server === serverName) {
            btn.classList.add('active');
        }
    });
}

// Function for the nested structure player
function setupVideoPlayerNested(url, serverName) {
    // If player scripts aren't loaded yet, load them first
    if (!window.playerScriptsLoaded) {
        loadPlayerScripts(function() {
            setupVideoPlayerNestedImpl(url, serverName);
        });
    } else {
        setupVideoPlayerNestedImpl(url, serverName);
    }
}

// Implementation of nested player setup (only called after scripts are loaded)
function setupVideoPlayerNestedImpl(url, serverName) {
    const playerWrapper = document.getElementById('player-wrapper-nested');
    const hlsWrapper = document.getElementById('hls-player-wrapper-nested');
    const iframeWrapper = document.getElementById('iframe-player-wrapper-nested');
    
    if (!playerWrapper || !hlsWrapper || !iframeWrapper) return;
    
    [playerWrapper, hlsWrapper, iframeWrapper].forEach(w => w.style.display = 'none');

    if (url.includes('.m3u8')) {
        hlsWrapper.style.display = 'block';
        const video = document.getElementById('hls-player-nested');
        if (Hls.isSupported()) {
            const hls = new Hls({
                maxBufferLength: 30,
                maxMaxBufferLength: 60
            });
            hls.loadSource(url);
            hls.attachMedia(video);
            const player = new Plyr(video, {
                preload: 'metadata',
                speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] }
            });
            trackPlayerForHistory(player);
        }
    } else if (url.includes('.mp4')) {
        playerWrapper.style.display = 'block';
        const video = document.getElementById('player-nested');
        video.src = url;
        video.preload = 'metadata';
        const player = new Plyr(video, {
            preload: 'metadata',
            speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] }
        });
        trackPlayerForHistory(player);
    } else {
        iframeWrapper.style.display = 'block';
        const iframe = document.getElementById('iframe-player-wrapper-nested');
        iframe.src = url;
        
        // Add to history after 30 seconds for iframe players
        setTimeout(addIframeToHistory, 30000);
    }
    
    // Update active server button
    document.querySelectorAll('.server-button-nested').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.server === serverName) {
            btn.classList.add('active');
        }
    });
}

// Function to initialize player when user is likely to watch
function initializePlayer() {
    // Initialize with first server if available
    const firstServerFlat = document.querySelector('.server-button');
    if (firstServerFlat) {
        const url = firstServerFlat.dataset.url;
        const server = firstServerFlat.dataset.server;
        setupVideoPlayerFlat(url, server);
        return true;
    }

    const firstServerNested = document.querySelector('.server-button-nested');
    if (firstServerNested) {
        const url = firstServerNested.dataset.url;
        const server = firstServerNested.dataset.server;
        setupVideoPlayerNested(url, server);
        return true;
    }
    
    return false;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Setup server buttons for flat structure
    document.querySelectorAll('.server-button').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.dataset.url;
            const server = this.dataset.server;
            setupVideoPlayerFlat(url, server);
        });
    });

    // Setup server buttons for nested structure
    document.querySelectorAll('.server-button-nested').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.dataset.url;
            const server = this.dataset.server;
            setupVideoPlayerNested(url, server);
        });
    });
    
    // Lazy load player when user interacts with the page or after a delay
    let playerInitialized = false;
    
    function lazyInitPlayer() {
        if (!playerInitialized) {
            playerInitialized = initializePlayer();
            
            // Remove event listeners after initialization
            if (playerInitialized) {
                document.removeEventListener('scroll', lazyInitPlayer);
                document.removeEventListener('mousemove', lazyInitPlayer);
                document.removeEventListener('touchstart', lazyInitPlayer);
            }
        }
    }
    
    // Add event listeners for lazy loading
    document.addEventListener('scroll', lazyInitPlayer, {passive: true});
    document.addEventListener('mousemove', lazyInitPlayer, {passive: true});
    document.addEventListener('touchstart', lazyInitPlayer, {passive: true});
    
    // Also initialize after a delay if user hasn't interacted
    setTimeout(lazyInitPlayer, 3000);
    
    // Load tracking scripts after page load
    window.addEventListener('load', function() {
        setTimeout(loadTrackingScripts, 2000);
    });
});