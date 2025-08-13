"""
Rate Limit Middleware
Implements rate limiting for API endpoints
"""

import time
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import HttpResponse


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware to implement rate limiting
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        
    def process_request(self, request):
        """
        Check rate limits for API requests
        """
        # Only rate limit API endpoints
        if not request.path.startswith('/api/'):
            return None
            
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Create cache key
        cache_key = f"ratelimit:{client_ip}:{request.path}"
        
        # Get current request count
        request_count = cache.get(cache_key, 0)
        
        # Check if rate limit exceeded
        if request_count > 100:  # 100 requests per minute
            return HttpResponse('Rate limit exceeded. Please try again later.', status=429)
            
        # Increment request count
        cache.set(cache_key, request_count + 1, 60)  # 1 minute expiry
        
        return None
        
    def _get_client_ip(self, request):
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip