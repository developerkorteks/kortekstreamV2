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
function addToHistory(itemData) {
  if (typeof(Storage) === "undefined") return;
  
  try {
    // Handle both object and individual parameters
    let itemId, itemType, itemTitle, itemImage, itemUrl, itemCategory;
    
    if (typeof itemData === 'object' && itemData !== null) {
      // If first parameter is an object with all data
      itemId = itemData.id;
      itemType = itemData.type || 'episode';
      itemTitle = itemData.title;
      itemImage = itemData.coverUrl;
      itemUrl = itemData.url;
      itemCategory = itemData.category || 'anime';
    } else {
      // Legacy support for individual parameters
      itemId = arguments[0];
      itemType = arguments[1];
      itemTitle = arguments[2];
      itemImage = arguments[3];
      itemUrl = arguments[4];
      itemCategory = arguments[5];
    }
    
    const history = JSON.parse(localStorage.getItem('viewHistory')) || [];
    
    // Remove if already exists (to move to top)
    const filteredHistory = history.filter(item => !(item.id === itemId && item.type === itemType));
    
    // Make sure we have valid data
    if (!itemId) {
      console.warn("Missing item ID, cannot add to history");
      return;
    }
    
    // Make sure URL is valid
    const validUrl = itemUrl || window.location.href;
    
    // Add new item at beginning
    filteredHistory.unshift({
      id: itemId,
      type: itemType || 'episode',
      title: itemTitle || 'Episode',
      image: itemImage || '',
      url: validUrl,
      category: itemCategory || 'anime',
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

// Remove item from history
function removeFromHistory(itemId, itemType) {
  if (typeof(Storage) === "undefined") return;
  
  try {
    const history = JSON.parse(localStorage.getItem('viewHistory')) || [];
    
    // Filter out the item
    const filteredHistory = history.filter(item => !(item.id === itemId && item.type === itemType));
    
    // Save back to storage
    localStorage.setItem('viewHistory', JSON.stringify(filteredHistory));
    
    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('historyUpdated', {
      detail: { history: filteredHistory }
    }));
  } catch (e) {
    console.error("Error removing from history:", e);
  }
}

// Render history section on root page
function renderHistorySection() {
  const container = document.getElementById('watch-history-container');
  if (!container) return;
  
  const history = getHistory();
  
  if (!history || history.length === 0) {
    container.style.display = 'none';
    return;
  }
  
  // Only show up to 6 items on the root page
  const displayHistory = history.slice(0, 6);
  
  let html = `
    <div class="mb-16 stagger-item">
      <div class="flex items-center justify-between mb-8">
        <div>
          <h3 class="text-3xl font-bold text-gray-800 dark:text-white mb-2">Continue Watching</h3>
          <p class="text-gray-600 dark:text-gray-400">Pick up where you left off</p>
        </div>
        <a href="/history/" class="group flex items-center space-x-2 text-gold-600 dark:text-korteks-red hover:text-gold-700 dark:hover:text-korteks-darkred transition-colors duration-300">
          <span class="font-medium">View All</span>
          <svg class="h-5 w-5 transform group-hover:translate-x-1 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </a>
      </div>
      
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
  `;
  
  displayHistory.forEach(item => {
    html += `
      <div class="group">
        <a href="${item.url}" class="block">
          <div class="modern-card bg-white/70 dark:bg-gray-800/70 backdrop-blur-lg rounded-3xl shadow-xl hover:shadow-2xl transition-all duration-500 overflow-hidden group-hover:scale-105 group-hover:-translate-y-2">
            <div class="relative aspect-[3/4] overflow-hidden">
              <img src="${item.image}" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" alt="${item.title}" loading="lazy" onerror="this.src='https://via.placeholder.com/300x400/1f1f1f/ffffff?text=No+Image';this.onerror='';" />
              <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div class="absolute top-2 right-2 bg-gray-900/50 text-white text-xs px-2 py-1 rounded-full">${item.category ? item.category.toUpperCase() : 'ANIME'}</div>
            </div>
            <div class="p-4">
              <h3 class="font-bold text-gray-800 dark:text-white text-sm line-clamp-1 group-hover:text-blue-600 dark:group-hover:text-red-400 transition-colors duration-300" title="${item.title}">${item.title}</h3>
              <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                <span class="inline-flex items-center">
                  <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
                  </svg>
                  ${new Date(item.timestamp).toLocaleDateString()}
                </span>
              </p>
            </div>
          </div>
        </a>
      </div>
    `;
  });
  
  html += `
      </div>
    </div>
  `;
  
  container.innerHTML = html;
  container.style.display = 'block';
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
      const url = this.getAttribute('data-track-url') || this.href;
      const category = this.getAttribute('data-track-category');
      
      if (id && type) {
        addToHistory(id, type, title, image, url, category);
      }
    });
  });
  
  // Render history section if on root page
  if (document.getElementById('watch-history-container')) {
    renderHistorySection();
    
    // Update when history changes
    document.addEventListener('historyUpdated', function() {
      renderHistorySection();
    });
  }
});