"""
Security Headers Middleware
Adds security-related headers to responses
"""

from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security-related headers
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        
    def process_response(self, request, response):
        """
        Add security headers to response
        """
        # Content Security Policy
        if 'Content-Security-Policy' not in response:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plyr.io https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.plyr.io; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "media-src 'self' https:; "
                "object-src 'none'; "
                "frame-src 'self' https:; "
                "worker-src 'self'; "
                "frame-ancestors 'self';"
            )
            response['Content-Security-Policy'] = csp
            
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Referrer-Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        
        return response