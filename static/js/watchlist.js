// Watchlist functionality for KortekStream

// Initialize watchlist
function initWatchlist() {
  // Check if localStorage is available
  if (typeof(Storage) === "undefined") {
    console.warn("LocalStorage not available, watchlist disabled");
    return;
  }
  
  // Initialize watchlist if not exists
  if (!localStorage.getItem('watchlist')) {
    localStorage.setItem('watchlist', JSON.stringify([]));
  }
}

// Check if item is in watchlist
function isInWatchlist(itemId) {
  if (typeof(Storage) === "undefined") return false;
  
  try {
    const watchlist = JSON.parse(localStorage.getItem('watchlist')) || [];
    return watchlist.some(item => item.id === itemId);
  } catch (e) {
    console.error("Error checking watchlist:", e);
    return false;
  }
}

// Add item to watchlist
function addToWatchlist(item) {
  if (typeof(Storage) === "undefined") return;
  
  try {
    const watchlist = JSON.parse(localStorage.getItem('watchlist')) || [];
    
    // Don't add if already exists
    if (watchlist.some(existingItem => existingItem.id === item.id)) {
      return;
    }
    
    // Add new item
    watchlist.push({
      id: item.id,
      title: item.title,
      coverUrl: item.coverUrl,
      url: item.url,
      category: item.category,
      timestamp: new Date().toISOString()
    });
    
    // Save back to storage
    localStorage.setItem('watchlist', JSON.stringify(watchlist));
    
    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('watchlistUpdated', {
      detail: { watchlist: watchlist }
    }));
  } catch (e) {
    console.error("Error adding to watchlist:", e);
  }
}

// Remove item from watchlist
function removeFromWatchlist(itemId) {
  if (typeof(Storage) === "undefined") return;
  
  try {
    const watchlist = JSON.parse(localStorage.getItem('watchlist')) || [];
    
    // Filter out the item
    const filteredWatchlist = watchlist.filter(item => item.id !== itemId);
    
    // Save back to storage
    localStorage.setItem('watchlist', JSON.stringify(filteredWatchlist));
    
    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('watchlistUpdated', {
      detail: { watchlist: filteredWatchlist }
    }));
  } catch (e) {
    console.error("Error removing from watchlist:", e);
  }
}

// Get watchlist
function getWatchlist() {
  if (typeof(Storage) === "undefined") return [];
  
  try {
    return JSON.parse(localStorage.getItem('watchlist')) || [];
  } catch (e) {
    console.error("Error retrieving watchlist:", e);
    return [];
  }
}

// Clear watchlist
function clearWatchlist() {
  if (typeof(Storage) === "undefined") return;
  
  localStorage.setItem('watchlist', JSON.stringify([]));
  
  // Dispatch event for other components
  document.dispatchEvent(new CustomEvent('watchlistUpdated', {
    detail: { watchlist: [] }
  }));
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  initWatchlist();
});