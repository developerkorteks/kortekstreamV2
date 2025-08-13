/**
 * KortekStream User Activity Manager
 * Handles Watch History and Watch List functionality using Local Storage.
 */

document.addEventListener('DOMContentLoaded', () => {
    // This script is now loaded and can be used by other scripts.
    console.log('User Activity Manager Loaded.');
});

const HISTORY_KEY = 'kortek_watch_history';
const WATCHLIST_KEY = 'kortek_watch_list';
const MAX_HISTORY_ITEMS = 100;

// --- Generic Local Storage Functions ---

/**
 * Safely retrieves and parses JSON data from Local Storage.
 * @param {string} key The key for the Local Storage item.
 * @returns {any} The parsed data or null if not found or invalid.
 */
function getUserActivity(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : [];
    } catch (error) {
        console.error(`Error reading from Local Storage (${key}):`, error);
        return [];
    }
}

/**
 * Safely stringifies and saves data to Local Storage.
 * @param {string} key The key for the Local Storage item.
 * @param {any} data The data to be saved.
 */
function setUserActivity(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error(`Error writing to Local Storage (${key}):`, error);
    }
}

// --- Watch History Functions ---

/**
 * Adds an episode to the watch history.
 * Moves the episode to the top if it already exists.
 * @param {object} episodeData - The episode data to save.
 * Example: { id: 'unique-ep-id', title: 'Ep 1', animeTitle: 'Anime', coverUrl: '...', url: '...', category: 'anime', watchedAt: '...' }
 */
function addToHistory(episodeData) {
    if (!episodeData || !episodeData.id) {
        console.error('Invalid episode data provided to addToHistory.');
        return;
    }

    let history = getUserActivity(HISTORY_KEY);

    // Remove existing entry to move it to the top
    history = history.filter(item => item.id !== episodeData.id);

    // Add new entry to the beginning
    episodeData.watchedAt = new Date().toISOString();
    history.unshift(episodeData);

    // Enforce history limit
    if (history.length > MAX_HISTORY_ITEMS) {
        history = history.slice(0, MAX_HISTORY_ITEMS);
    }

    setUserActivity(HISTORY_KEY, history);
    console.log('Added to history:', episodeData.title);
}

/**
 * Retrieves the entire watch history.
 * @returns {Array} An array of episode objects.
 */
function getHistory() {
    return getUserActivity(HISTORY_KEY);
}

// --- Watch List Functions ---

/**
 * Adds an anime to the watch list.
 * @param {object} animeData - The anime data to save.
 * Example: { id: 'unique-anime-slug', title: 'Anime Title', coverUrl: '...', url: '...', category: 'anime', addedAt: '...' }
 */
function addToWatchlist(animeData) {
    if (!animeData || !animeData.id) {
        console.error('Invalid anime data provided to addToWatchlist.');
        return;
    }

    let watchlist = getUserActivity(WATCHLIST_KEY);

    // Check if it already exists
    if (watchlist.some(item => item.id === animeData.id)) {
        console.log('Already in watchlist:', animeData.title);
        return; // Already in the list
    }

    animeData.addedAt = new Date().toISOString();
    watchlist.unshift(animeData); // Add to the beginning
    setUserActivity(WATCHLIST_KEY, watchlist);
    console.log('Added to watchlist:', animeData.title);
}

/**
 * Removes an anime from the watch list.
 * @param {string} animeId - The unique ID (slug) of the anime to remove.
 */
function removeFromWatchlist(animeId) {
    if (!animeId) return;
    let watchlist = getUserActivity(WATCHLIST_KEY);
    const initialLength = watchlist.length;
    watchlist = watchlist.filter(item => item.id !== animeId);

    if (watchlist.length < initialLength) {
        setUserActivity(WATCHLIST_KEY, watchlist);
        console.log('Removed from watchlist:', animeId);
    } 
}

/**
 * Checks if an anime is in the watch list.
 * @param {string} animeId - The unique ID (slug) of the anime.
 * @returns {boolean}
 */
function isInWatchlist(animeId) {
    if (!animeId) return false;
    const watchlist = getUserActivity(WATCHLIST_KEY);
    return watchlist.some(item => item.id === animeId);
}

/**
 * Retrieves the entire watch list.
 * @returns {Array} An array of anime objects.
 */
function getWatchlist() {
    return getUserActivity(WATCHLIST_KEY);
}
