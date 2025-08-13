"""
Cache Control Middleware
Provides smart cache control headers for different types of content
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CacheControlMiddleware(MiddlewareMixin):
    """
    Middleware to add appropriate cache control headers based on content type
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        
    def process_response(self, request, response):
        """
        Add appropriate cache headers based on content type
        """
        # Don't modify cache headers in debug mode
        if settings.DEBUG:
            return response
            
        # Don't add cache headers for authenticated users
        if request.user.is_authenticated:
            return response
            
        # If Cache-Control is already set, don't override it
        if 'Cache-Control' in response:
            return response
            
        # Set default cache control headers based on request path
        path = request.path_info
        
        # API endpoints - no caching
        if path.startswith('/api/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        # Home page - short cache time
        elif path == '/' or path == '/home/':
            response['Cache-Control'] = 'public, max-age=300'  # 5 minutes
            
        # Static content - longer cache time
        elif path.startswith('/static/') or path.startswith('/media/'):
            response['Cache-Control'] = 'public, max-age=86400'  # 1 day
            
        # Default for other pages
        else:
            response['Cache-Control'] = 'public, max-age=600'  # 10 minutes
            
        return response