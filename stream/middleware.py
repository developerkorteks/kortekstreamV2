"""
Custom middleware for KortekStream application
Provides rate limiting, API health monitoring, and performance tracking
"""

import time
import json
import logging
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.utils import timezone
from collections import defaultdict
import hashlib

# Setup loggers
performance_logger = logging.getLogger('stream.performance')
api_logger = logging.getLogger('stream.api')


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware to prevent abuse and ensure fair usage
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, request):
        """Check if the request should be rate limited"""
        if not getattr(settings, 'RATE_LIMIT_ENABLE', True):
            return False
        
        # Skip rate limiting for admin and health check endpoints
        try:
            url_name = resolve(request.path_info).url_name
            if url_name in ['admin', 'api_health_check', 'favicon']:
                return False
        except:
            pass
        
        client_ip = self.get_client_ip(request)
        current_time = int(time.time())
        
        # Rate limit keys
        minute_key = f"rate_limit_minute:{client_ip}:{current_time // 60}"
        hour_key = f"rate_limit_hour:{client_ip}:{current_time // 3600}"
        burst_key = f"rate_limit_burst:{client_ip}:{current_time // 10}"  # 10-second window
        
        # Get current counts
        minute_count = cache.get(minute_key, 0)
        hour_count = cache.get(hour_key, 0)
        burst_count = cache.get(burst_key, 0)
        
        # Check limits
        per_minute_limit = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60)
        per_hour_limit = getattr(settings, 'RATE_LIMIT_PER_HOUR', 1000)
        burst_limit = getattr(settings, 'RATE_LIMIT_BURST', 10)
        
        if burst_count >= burst_limit:
            api_logger.warning(f"Burst rate limit exceeded for IP {client_ip}: {burst_count}/{burst_limit}")
            return True
        
        if minute_count >= per_minute_limit:
            api_logger.warning(f"Per-minute rate limit exceeded for IP {client_ip}: {minute_count}/{per_minute_limit}")
            return True
        
        if hour_count >= per_hour_limit:
            api_logger.warning(f"Per-hour rate limit exceeded for IP {client_ip}: {hour_count}/{per_hour_limit}")
            return True
        
        # Increment counters
        cache.set(minute_key, minute_count + 1, timeout=60)
        cache.set(hour_key, hour_count + 1, timeout=3600)
        cache.set(burst_key, burst_count + 1, timeout=10)
        
        return False
    
    def process_request(self, request):
        """Process incoming request for rate limiting"""
        if self.is_rate_limited(request):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please slow down.',
                'retry_after': 60
            }, status=429)
        
        return None


class APIHealthMiddleware(MiddlewareMixin):
    """
    Middleware to monitor API health and performance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Start timing the request"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log performance metrics and API health"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log performance data
            performance_data = {
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'timestamp': timezone.now().isoformat(),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],
                'ip': self.get_client_ip(request)
            }
            
            # Log slow requests
            if duration > 2.0:  # Requests taking more than 2 seconds
                performance_logger.warning(f"Slow request: {json.dumps(performance_data)}")
            elif duration > 5.0:  # Very slow requests
                performance_logger.error(f"Very slow request: {json.dumps(performance_data)}")
            else:
                performance_logger.info(json.dumps(performance_data))
            
            # Update API health metrics in cache
            self.update_health_metrics(request.path, response.status_code, duration)
            
            # Add performance headers for debugging
            if settings.DEBUG:
                response['X-Response-Time'] = f"{duration:.3f}s"
                response['X-Timestamp'] = str(int(time.time()))
        
        return response
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def update_health_metrics(self, path, status_code, duration):
        """Update health metrics in cache"""
        try:
            current_time = int(time.time())
            hour_key = f"health_metrics:{current_time // 3600}"
            
            # Get existing metrics
            metrics = cache.get(hour_key, {
                'total_requests': 0,
                'error_count': 0,
                'avg_response_time': 0,
                'slow_requests': 0,
                'status_codes': defaultdict(int)
            })
            
            # Update metrics
            metrics['total_requests'] += 1
            if status_code >= 400:
                metrics['error_count'] += 1
            if duration > 2.0:
                metrics['slow_requests'] += 1
            
            # Update average response time (simple moving average)
            current_avg = metrics['avg_response_time']
            total_requests = metrics['total_requests']
            metrics['avg_response_time'] = ((current_avg * (total_requests - 1)) + duration) / total_requests
            
            # Update status code counts
            metrics['status_codes'][str(status_code)] += 1
            
            # Store updated metrics
            cache.set(hour_key, metrics, timeout=3600)
            
        except Exception as e:
            api_logger.error(f"Failed to update health metrics: {str(e)}")


class SecurityMiddleware(MiddlewareMixin):
    """
    Additional security middleware for production
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_response(self, request, response):
        """Add security headers"""
        if getattr(settings, 'IS_PRODUCTION', False):
            # Add security headers
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'SAMEORIGIN'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Content Security Policy for media content
            if 'stream' in request.path:
                response['Content-Security-Policy'] = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' *.googleapis.com *.gstatic.com; "
                    "style-src 'self' 'unsafe-inline' *.googleapis.com; "
                    "img-src 'self' data: https:; "
                    "media-src 'self' https:; "
                    "connect-src 'self' https:; "
                    "font-src 'self' *.googleapis.com *.gstatic.com;"
                )
        
        return response


class CacheControlMiddleware(MiddlewareMixin):
    """
    Smart cache control middleware
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_response(self, request, response):
        """Add appropriate cache headers"""
        # Static files - long cache
        if request.path.startswith('/static/'):
            response['Cache-Control'] = 'public, max-age=31536000'  # 1 year
            return response
        
        # API endpoints - short cache with validation
        if '/api/' in request.path:
            response['Cache-Control'] = 'public, max-age=60, must-revalidate'  # 1 minute
            return response
        
        # Dynamic content - moderate cache
        if response.status_code == 200:
            try:
                url_name = resolve(request.path_info).url_name
                
                # Home and category pages - 5 minutes
                if url_name in ['root', 'home', 'latest']:
                    response['Cache-Control'] = 'public, max-age=300, must-revalidate'
                
                # Detail pages - 15 minutes
                elif url_name in ['anime_detail', 'episode_detail']:
                    response['Cache-Control'] = 'public, max-age=900, must-revalidate'
                
                # Search results - 2 minutes
                elif url_name == 'search':
                    response['Cache-Control'] = 'public, max-age=120, must-revalidate'
                
                # Default - 5 minutes
                else:
                    response['Cache-Control'] = 'public, max-age=300, must-revalidate'
                    
            except:
                # Fallback cache control
                response['Cache-Control'] = 'public, max-age=300, must-revalidate'
        
        return response