import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.cache import patch_response_headers
from django.shortcuts import redirect
from django.urls import reverse
import re

logger = logging.getLogger(__name__)


class SEOMiddleware(MiddlewareMixin):
    """Middleware for SEO optimizations"""
    
    def process_request(self, request):
        # Force trailing slash for consistency
        if not request.path.endswith('/') and not request.path.startswith('/static/') and not request.path.startswith('/media/'):
            if '.' not in request.path.split('/')[-1]:  # Don't redirect files
                return redirect(request.path + '/', permanent=True)
        
        # Add canonical URL to request
        request.canonical_url = request.build_absolute_uri()
        
        return None
    
    def process_response(self, request, response):
        # Add SEO headers
        if response.status_code == 200:
            # Add canonical header
            response['Link'] = f'<{request.canonical_url}>; rel="canonical"'
            
            # Add language header
            response['Content-Language'] = 'id'
            
            # Add cache headers for static content
            if request.path.startswith('/static/') or request.path.startswith('/media/'):
                patch_response_headers(response, cache_timeout=86400)  # 24 hours
        
        return response


class PerformanceMiddleware(MiddlewareMixin):
    """Middleware for performance optimizations"""
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        # Calculate response time
        if hasattr(request, 'start_time'):
            response_time = time.time() - request.start_time
            response['X-Response-Time'] = f'{response_time:.3f}s'
            
            # Log slow requests
            if response_time > 2.0:  # Log requests slower than 2 seconds
                logger.warning(f'Slow request: {request.path} took {response_time:.3f}s')
        
        # Add performance headers
        if response.status_code == 200:
            # Enable browser caching
            if request.path.startswith('/static/'):
                response['Cache-Control'] = 'public, max-age=31536000'  # 1 year
            elif request.path.startswith('/media/'):
                response['Cache-Control'] = 'public, max-age=86400'  # 1 day
            else:
                response['Cache-Control'] = 'public, max-age=300'  # 5 minutes
        
        return response


class CompressionMiddleware(MiddlewareMixin):
    """Middleware for response compression"""
    
    def process_response(self, request, response):
        # Add compression hints
        if response.get('Content-Type', '').startswith(('text/', 'application/json', 'application/javascript')):
            response['Vary'] = 'Accept-Encoding'
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware for security headers that also help with SEO"""
    
    def process_response(self, request, response):
        # Security headers that improve SEO trust
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (basic)
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "frame-src 'self';"
            )
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware"""
    
    def process_request(self, request):
        if not settings.RATE_LIMIT_ENABLE:
            return None
        
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Check rate limit
        cache_key = f'rate_limit_{ip}'
        requests = cache.get(cache_key, 0)
        
        if requests >= settings.RATE_LIMIT_PER_MINUTE:
            return HttpResponse('Rate limit exceeded', status=429)
        
        # Increment counter
        cache.set(cache_key, requests + 1, 60)  # 1 minute window
        
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class APIHealthMiddleware(MiddlewareMixin):
    """Middleware to monitor API health"""
    
    def process_exception(self, request, exception):
        # Log API errors for monitoring
        if request.path.startswith('/api/'):
            logger.error(f'API Error: {request.path} - {str(exception)}')
        return None


class CacheControlMiddleware(MiddlewareMixin):
    """Smart cache control middleware"""
    
    def process_response(self, request, response):
        # Don't cache error pages
        if response.status_code >= 400:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        
        # Cache static files aggressively
        if request.path.startswith('/static/'):
            response['Cache-Control'] = 'public, max-age=31536000, immutable'
        elif request.path.startswith('/media/'):
            response['Cache-Control'] = 'public, max-age=86400'
        elif request.path in ['/', '/latest/', '/schedule/']:
            # Cache main pages for shorter time
            response['Cache-Control'] = 'public, max-age=300'
        elif '/detail/' in request.path:
            # Cache detail pages longer
            response['Cache-Control'] = 'public, max-age=1800'
        
        return response