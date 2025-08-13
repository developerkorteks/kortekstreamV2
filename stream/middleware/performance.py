"""
Performance Middleware
Monitors and logs performance metrics
"""

import time
import logging
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger('stream.performance')


class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware to monitor and log performance metrics
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        
    def process_request(self, request):
        """
        Set start time for request processing
        """
        request.start_time = time.time()
        
    def process_response(self, request, response):
        """
        Log request processing time
        """
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(f"Request to {request.path} took {duration:.4f}s")
            
            # Add Server-Timing header for performance monitoring
            response['Server-Timing'] = f'total;dur={duration * 1000:.0f}'
            
        return response