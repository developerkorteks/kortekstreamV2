"""
Simple API client for development and fallback
Provides basic functionality without complex dependencies
"""

import time
import json
import logging
import requests
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('stream.api')


@dataclass
class SimpleAPIResponse:
    """Simple API response structure"""
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


class SimpleAPIClient:
    """
    Simple API client with basic caching and error handling
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'KortekStream/1.0',
            'Accept': 'application/json',
        })
    
    def get(self, endpoint: str, params: Dict = None, 
            cache_timeout: int = 300, force_refresh: bool = False) -> SimpleAPIResponse:
        """Make GET request with basic caching"""
        start_time = time.time()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Generate cache key
        cache_key = self._get_cache_key(url, params)
        
        # Try cache first
        if not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                response_time = time.time() - start_time
                return SimpleAPIResponse(
                    data=cached_data,
                    status_code=200,
                    response_time=response_time,
                    cached=True,
                    source='cache'
                )
        
        # Make API request
        try:
            response = self.session.get(
                url, 
                params=params, 
                timeout=getattr(settings, 'API_TIMEOUT', 15)
            )
            response_time = time.time() - start_time
            
            # Parse response
            try:
                data = response.json()
            except ValueError:
                data = {'error': 'Invalid JSON response', 'raw': response.text[:500]}
            
            # Cache successful responses
            if response.status_code == 200 and 'error' not in data:
                cache.set(cache_key, data, timeout=cache_timeout)
            
            return SimpleAPIResponse(
                data=data,
                status_code=response.status_code,
                response_time=response_time,
                cached=False,
                source='api'
            )
            
        except Exception as e:
            logger.error(f"API request failed for {url}: {str(e)}")
            
            # Try to return cached data as fallback
            cached_data = cache.get(cache_key)
            if cached_data:
                response_time = time.time() - start_time
                return SimpleAPIResponse(
                    data=cached_data,
                    status_code=200,
                    response_time=response_time,
                    cached=True,
                    stale=True,
                    source='stale_cache'
                )
            
            # No cache available, return error
            response_time = time.time() - start_time
            return SimpleAPIResponse(
                data={'error': str(e), 'message': 'Service temporarily unavailable'},
                status_code=503,
                response_time=response_time,
                source='error'
            )
    
    def _get_cache_key(self, url: str, params: Dict = None) -> str:
        """Generate cache key"""
        import hashlib
        if params:
            from urllib.parse import urlencode
            sorted_params = sorted(params.items())
            param_string = urlencode(sorted_params)
            key_data = f"{url}?{param_string}"
        else:
            key_data = url
        
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"simple_api_cache:{key_hash}"
    
    def health_check(self) -> Dict:
        """Simple health check"""
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
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }


# Global simple client instance
simple_api_client = SimpleAPIClient(
    base_url=getattr(settings, 'API_BASE_URL', 'http://apigatway.humanmade.my.id:8080')
)


# Fallback functions
def simple_make_api_request(endpoint: str, params: Dict = None, 
                           cache_timeout: int = 300, force_refresh: bool = False) -> SimpleAPIResponse:
    """Simple API request function"""
    return simple_api_client.get(endpoint, params, cache_timeout, force_refresh)


def simple_get_api_stats() -> Dict:
    """Simple API stats (placeholder)"""
    return {
        'total_requests': 0,
        'cache_hits': 0,
        'cache_misses': 0,
        'api_errors': 0,
        'avg_response_time': 0
    }


def simple_api_health_check() -> Dict:
    """Simple API health check"""
    return simple_api_client.health_check()