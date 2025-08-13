"""
SEO Middleware
Enhances SEO capabilities for the application
"""

from django.utils.deprecation import MiddlewareMixin


class SEOMiddleware(MiddlewareMixin):
    """
    Middleware to enhance SEO capabilities
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        
    def process_response(self, request, response):
        """
        Add SEO-related headers to response
        """
        # Add canonical URL header if not present
        if 'Link' not in response:
            canonical_url = request.build_absolute_uri(request.path)
            response['Link'] = f'<{canonical_url}>; rel="canonical"'
            
        return response