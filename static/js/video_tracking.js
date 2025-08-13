// Video tracking functionality for KortekStream

// Track video progress
function trackVideoProgress() {
  // Get all video elements
  const videos = document.querySelectorAll('video');
  
  if (!videos.length) return;
  
  // Get episode data from the page
  const episodeDataElement = document.getElementById('episode-data-json');
  if (!episodeDataElement) {
    console.warn("Episode data element not found");
    return;
  }
  
  let episodeData;
  try {
    episodeData = JSON.parse(episodeDataElement.textContent);
  } catch (e) {
    console.error("Error parsing episode data:", e);
    return;
  }
  
  // Make sure we have the minimum required data
  if (!episodeData.id) {
    console.warn("Missing episode ID, cannot track history");
    return;
  }
  
  // Log the data we're working with for debugging
  console.log("Episode data for tracking:", episodeData);
  
  // Set up tracking for each video
  videos.forEach(video => {
    let progressInterval;
    let watchTime = 0;
    const minWatchTimeForHistory = 30; // 30 seconds minimum to count as watched
    
    // Start tracking when video starts playing
    video.addEventListener('play', () => {
      // Clear any existing interval
      if (progressInterval) clearInterval(progressInterval);
      
      // Set up interval to track watch time
      progressInterval = setInterval(() => {
        if (!video.paused && !video.ended) {
          watchTime++;
          
          // Add to history after watching for minWatchTimeForHistory seconds
          if (watchTime === minWatchTimeForHistory) {
            try {
              // Make sure we have valid URL
              if (!episodeData.url || episodeData.url === 'undefined') {
                episodeData.url = window.location.href;
              }
              
              // Add to history
              addToHistory(episodeData);
              console.log(`Added to history after ${minWatchTimeForHistory} seconds of watching`);
            } catch (e) {
              console.error("Error adding to history:", e);
            }
          }
        }
      }, 1000); // Check every second
    });
    
    // Clear interval when video is paused or ended
    video.addEventListener('pause', () => {
      if (progressInterval) clearInterval(progressInterval);
    });
    
    video.addEventListener('ended', () => {
      if (progressInterval) clearInterval(progressInterval);
    });
  });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  trackVideoProgress();
});