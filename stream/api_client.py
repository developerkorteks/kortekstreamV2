"""
Robust API client with connection pooling, circuit breaker, and advanced caching
Designed to handle high-traffic scenarios and API instability
"""

import time
import json
import hashlib
import logging
import threading
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from django.core.cache import cache, caches
from django.conf import settings
from django.utils import timezone

# Setup loggers
api_logger = logging.getLogger('stream.api')
performance_logger = logging.getLogger('stream.performance')


@dataclass
class APIResponse:
    """Structured API response with metadata"""
    data: Any
    status_code: int
    response_time: float
    cached: bool = False
    stale: bool = False
    source: str = 'api'
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = timezone.now()


class CircuitBreaker:
    """
    Circuit breaker implementation to handle API failures gracefully
    """
    
    def __init__(self, failure_threshold: int = 10, timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                    api_logger.info("Circuit breaker moving to HALF_OPEN state")
                else:
                    raise Exception("Circuit breaker is OPEN - API temporarily unavailable")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.timeout
    
    def _on_success(self):
        """Handle successful API call"""
        self.failure_count = 0
        self.state = 'CLOSED'
        api_logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed API call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            api_logger.error(f"Circuit breaker opened after {self.failure_count} failures")


class SmartCache:
    """
    Advanced caching system with multiple cache layers and stale-while-revalidate
    """
    
    def __init__(self):
        self.default_cache = cache
        try:
            self.fast_cache = caches['fast']
        except KeyError:
            self.fast_cache = cache
    
    def get_cache_key(self, url: str, params: Dict = None) -> str:
        """Generate consistent cache key"""
        if params:
            # Sort params for consistent key generation
            sorted_params = sorted(params.items())
            param_string = urlencode(sorted_params)
            key_data = f"{url}?{param_string}"
        else:
            key_data = url
        
        # Create hash for long URLs
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"api_cache:{key_hash}"
    
    def get(self, key: str) -> Tuple[Any, bool]:
        """Get data from cache, return (data, is_stale)"""
        # Try fast cache first
        data = self.fast_cache.get(key)
        if data:
            return data, False
        
        # Try default cache
        data = self.default_cache.get(key)
        if data:
            return data, False
        
        # Try stale cache
        stale_key = f"{key}:stale"
        stale_data = self.default_cache.get(stale_key)
        if stale_data:
            return stale_data, True
        
        return None, False
    
    def set(self, key: str, data: Any, timeout: int = 300):
        """Set data in multiple cache layers"""
        # Store in fast cache for frequently accessed data
        if timeout <= 60:
            self.fast_cache.set(key, data, timeout=timeout)
        
        # Store in default cache
        self.default_cache.set(key, data, timeout=timeout)
        
        # Store as stale cache for fallback (24 hours)
        stale_key = f"{key}:stale"
        self.default_cache.set(stale_key, data, timeout=86400)
    
    def delete(self, key: str):
        """Delete from all cache layers"""
        self.fast_cache.delete(key)
        self.default_cache.delete(key)
        self.default_cache.delete(f"{key}:stale")


class RobustAPIClient:
    """
    Production-ready API client with all optimizations
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.cache = SmartCache()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=getattr(settings, 'API_CIRCUIT_BREAKER_THRESHOLD', 10),
            timeout=getattr(settings, 'API_CIRCUIT_BREAKER_TIMEOUT', 300)
        )
        
        # Setup session with connection pooling
        self.session = self._create_session()
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'api_errors': 0,
            'avg_response_time': 0
        }
    
    def _create_session(self) -> requests.Session:
        """Create optimized requests session"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=getattr(settings, 'API_MAX_RETRIES', 3),
            backoff_factor=getattr(settings, 'API_BACKOFF_FACTOR', 1.5),
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        # HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,  # Number of connection pools
            pool_maxsize=50,      # Max connections per pool
            pool_block=False      # Don't block when pool is full
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Default headers
        session.headers.update({
            'User-Agent': 'KortekStream/1.0 (Production)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        return session
    
    def get(self, endpoint: str, params: Dict = None, 
            cache_timeout: int = 300, force_refresh: bool = False) -> APIResponse:
        """
        Make GET request with caching and circuit breaker
        """
        start_time = time.time()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Generate cache key
        cache_key = self.cache.get_cache_key(url, params)
        
        # Try cache first (unless force refresh)
        if not force_refresh:
            cached_data, is_stale = self.cache.get(cache_key)
            if cached_data:
                self.stats['cache_hits'] += 1
                
                # If data is stale, trigger background refresh
                if is_stale:
                    self._background_refresh(url, params, cache_key, cache_timeout)
                
                response_time = time.time() - start_time
                return APIResponse(
                    data=cached_data,
                    status_code=200,
                    response_time=response_time,
                    cached=True,
                    stale=is_stale,
                    source='cache'
                )
        
        # Make API request
        try:
            self.stats['cache_misses'] += 1
            response = self.circuit_breaker.call(
                self._make_request, url, params
            )
            
            response_time = time.time() - start_time
            self.stats['total_requests'] += 1
            
            # Update average response time
            total_requests = self.stats['total_requests']
            current_avg = self.stats['avg_response_time']
            self.stats['avg_response_time'] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
            
            # Parse response
            try:
                data = response.json()
            except ValueError:
                data = {'error': 'Invalid JSON response', 'raw': response.text[:500]}
            
            # Cache successful responses
            if response.status_code == 200 and 'error' not in data:
                self.cache.set(cache_key, data, timeout=cache_timeout)
            
            # Log performance
            performance_logger.info(json.dumps({
                'endpoint': endpoint,
                'response_time_ms': round(response_time * 1000, 2),
                'status_code': response.status_code,
                'cached': False,
                'params': params
            }))
            
            return APIResponse(
                data=data,
                status_code=response.status_code,
                response_time=response_time,
                cached=False,
                source='api'
            )
            
        except Exception as e:
            self.stats['api_errors'] += 1
            api_logger.error(f"API request failed for {url}: {str(e)}")
            
            # Try to return stale cache data as fallback
            cached_data, is_stale = self.cache.get(cache_key)
            if cached_data:
                api_logger.info(f"Returning stale cache data for {url}")
                response_time = time.time() - start_time
                return APIResponse(
                    data=cached_data,
                    status_code=200,
                    response_time=response_time,
                    cached=True,
                    stale=True,
                    source='stale_cache'
                )
            
            # No cache available, return error
            response_time = time.time() - start_time
            return APIResponse(
                data={'error': str(e), 'message': 'Service temporarily unavailable'},
                status_code=503,
                response_time=response_time,
                source='error'
            )
    
    def _make_request(self, url: str, params: Dict = None) -> requests.Response:
        """Make the actual HTTP request"""
        timeout = getattr(settings, 'API_TIMEOUT', 15)
        
        response = self.session.get(
            url, 
            params=params, 
            timeout=timeout
        )
        response.raise_for_status()
        return response
    
    def _background_refresh(self, url: str, params: Dict, cache_key: str, cache_timeout: int):
        """Refresh stale cache data in background"""
        def refresh():
            try:
                response = self._make_request(url, params)
                data = response.json()
                if response.status_code == 200 and 'error' not in data:
                    self.cache.set(cache_key, data, timeout=cache_timeout)
                    api_logger.info(f"Background refresh completed for {url}")
            except Exception as e:
                api_logger.warning(f"Background refresh failed for {url}: {str(e)}")
        
        # Run in background thread
        import threading
        thread = threading.Thread(target=refresh)
        thread.daemon = True
        thread.start()
    
    def get_stats(self) -> Dict:
        """Get client statistics"""
        return {
            **self.stats,
            'circuit_breaker_state': self.circuit_breaker.state,
            'circuit_breaker_failures': self.circuit_breaker.failure_count
        }
    
    def health_check(self) -> Dict:
        """Perform health check"""
        try:
            start_time = time.time()
            response = self.session.get(
                f"{self.base_url}/api/categories/names",
                timeout=5
            )
            response_time = time.time() - start_time
            
            return {
                'healthy': response.status_code == 200,
                'response_time': response_time,
                'status_code': response.status_code,
                'circuit_breaker_state': self.circuit_breaker.state
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'circuit_breaker_state': self.circuit_breaker.state
            }


# Global API client instance
api_client = RobustAPIClient(
    base_url=getattr(settings, 'API_BASE_URL', 'http://apigatway.humanmade.my.id:8080')
)


# Convenience functions for backward compatibility
def make_api_request(endpoint: str, params: Dict = None, 
                    cache_timeout: int = 300, force_refresh: bool = False) -> APIResponse:
    """Make API request using the global client"""
    return api_client.get(endpoint, params, cache_timeout, force_refresh)


def get_api_stats() -> Dict:
    """Get API client statistics"""
    return api_client.get_stats()


def api_health_check() -> Dict:
    """Perform API health check"""
    return api_client.health_check()