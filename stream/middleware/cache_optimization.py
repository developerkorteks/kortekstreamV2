"""
Cache Optimization Middleware
Improves caching behavior for static assets and specific views
"""

import re
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CacheOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware to optimize cache headers for better performance
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        
        # Compile regex patterns for matching URLs
        self.static_file_pattern = re.compile(r'\.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$')
        self.episode_detail_pattern = re.compile(r'/episode/([a-zA-Z0-9\-_]+)/?$')
        
    def process_response(self, request, response):
        """
        Add appropriate cache headers based on content type and URL
        """
        path = request.path_info.lstrip('/')
        
        # Don't modify cache headers in debug mode
        if settings.DEBUG:
            return response
            
        # Don't add cache headers for authenticated users
        if request.user.is_authenticated:
            return response
            
        # Static files - long cache time
        if self.static_file_pattern.search(path):
            # Cache static files for 1 week
            response['Cache-Control'] = 'public, max-age=604800, stale-while-revalidate=86400'
            return response
            
        # Episode detail pages - moderate cache time
        if self.episode_detail_pattern.search(request.path_info):
            # Cache episode detail pages for 1 hour, allow stale content for 1 day
            response['Cache-Control'] = 'public, max-age=3600, stale-while-revalidate=86400'
            return response
            
        # Default - no caching for dynamic content
        if 'Cache-Control' not in response:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        return response