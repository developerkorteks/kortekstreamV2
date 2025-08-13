"""
Compression Middleware
Compresses response content for faster delivery
"""

from django.utils.deprecation import MiddlewareMixin


class CompressionMiddleware(MiddlewareMixin):
    """
    Middleware to compress response content
    Note: This is a placeholder as Django already has GZipMiddleware
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        
    def process_response(self, request, response):
        """
        Add compression-related headers
        """
        # Set Vary header to ensure proper caching with compression
        if 'Vary' in response:
            if 'Accept-Encoding' not in response['Vary']:
                response['Vary'] += ', Accept-Encoding'
        else:
            response['Vary'] = 'Accept-Encoding'
            
        return response