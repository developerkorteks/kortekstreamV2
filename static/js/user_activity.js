// User activity tracking for KortekStream

// Initialize history tracking
function initHistoryTracking() {
  // Check if localStorage is available
  if (typeof(Storage) === "undefined") {
    console.warn("LocalStorage not available, history tracking disabled");
    return;
  }
  
  // Initialize history if not exists
  if (!localStorage.getItem('viewHistory')) {
    localStorage.setItem('viewHistory', JSON.stringify([]));
  }
}

// Add item to history
function addToHistory(itemId, itemType, itemTitle, itemImage) {
  if (typeof(Storage) === "undefined") return;
  
  try {
    const history = JSON.parse(localStorage.getItem('viewHistory')) || [];
    
    // Remove if already exists (to move to top)
    const filteredHistory = history.filter(item => !(item.id === itemId && item.type === itemType));
    
    // Add new item at beginning
    filteredHistory.unshift({
      id: itemId,
      type: itemType,
      title: itemTitle,
      image: itemImage,
      timestamp: new Date().toISOString()
    });
    
    // Keep only last 20 items
    const trimmedHistory = filteredHistory.slice(0, 20);
    
    // Save back to storage
    localStorage.setItem('viewHistory', JSON.stringify(trimmedHistory));
    
    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('historyUpdated', {
      detail: { history: trimmedHistory }
    }));
  } catch (e) {
    console.error("Error updating history:", e);
  }
}

// Get viewing history
function getHistory() {
  if (typeof(Storage) === "undefined") return [];
  
  try {
    return JSON.parse(localStorage.getItem('viewHistory')) || [];
  } catch (e) {
    console.error("Error retrieving history:", e);
    return [];
  }
}

// Clear history
function clearHistory() {
  if (typeof(Storage) === "undefined") return;
  
  localStorage.setItem('viewHistory', JSON.stringify([]));
  
  // Dispatch event for other components
  document.dispatchEvent(new CustomEvent('historyUpdated', {
    detail: { history: [] }
  }));
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  initHistoryTracking();
  
  // Add click tracking to content items
  document.querySelectorAll('[data-track-id]').forEach(element => {
    element.addEventListener('click', function() {
      const id = this.getAttribute('data-track-id');
      const type = this.getAttribute('data-track-type');
      const title = this.getAttribute('data-track-title');
      const image = this.getAttribute('data-track-image');
      
      if (id && type) {
        addToHistory(id, type, title, image);
      }
    });
  });
});