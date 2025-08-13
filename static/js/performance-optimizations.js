// Performance optimizations for KortekStream

// Lazy loading images
document.addEventListener('DOMContentLoaded', function() {
  const lazyImages = document.querySelectorAll('img[data-src]');
  
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver(function(entries, observer) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          const image = entry.target;
          image.src = image.dataset.src;
          if (image.dataset.srcset) {
            image.srcset = image.dataset.srcset;
          }
          image.classList.add('fade-in');
          imageObserver.unobserve(image);
        }
      });
    });
    
    lazyImages.forEach(function(image) {
      imageObserver.observe(image);
    });
  } else {
    // Fallback for browsers without IntersectionObserver
    lazyImages.forEach(function(image) {
      image.src = image.dataset.src;
      if (image.dataset.srcset) {
        image.srcset = image.dataset.srcset;
      }
    });
  }
});

// Preconnect to important domains
function addPreconnect(url) {
  const link = document.createElement('link');
  link.rel = 'preconnect';
  link.href = url;
  document.head.appendChild(link);
}

// Add preconnect for important domains
addPreconnect('https://fonts.googleapis.com');
addPreconnect('https://fonts.gstatic.com');

// Defer non-critical JavaScript
function deferScript(src) {
  const script = document.createElement('script');
  script.src = src;
  script.defer = true;
  document.body.appendChild(script);
}

// Load non-critical scripts after page load
window.addEventListener('load', function() {
  // Add any non-critical scripts here
  console.log('Page fully loaded, loading non-critical resources');
});