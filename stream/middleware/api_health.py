"""
API Health Middleware
Monitors API health and logs issues
"""

import logging
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger('stream.api')


class APIHealthMiddleware(MiddlewareMixin):
    """
    Middleware to monitor API health
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        
    def process_response(self, request, response):
        """
        Log API health issues
        """
        # Only monitor API endpoints
        if not request.path.startswith('/api/'):
            return response
            
        # Log 4xx and 5xx responses
        if response.status_code >= 400:
            logger.warning(
                f"API health issue: {request.method} {request.path} "
                f"returned {response.status_code}"
            )
            
        return response