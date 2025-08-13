"""
Health check views for Docker and monitoring
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
import os
import psutil
import time

def health_check(request):
    """
    Comprehensive health check endpoint for Docker and monitoring
    """
    start_time = time.time()
    
    # Check database connection
    db_status = "ok"
    db_error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        db_status = "error"
        db_error = str(e)
    
    # Check Redis connection
    redis_status = "ok"
    redis_error = None
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        if result != 'ok':
            redis_status = "error"
            redis_error = "Cache test failed"
    except Exception as e:
        redis_status = "error"
        redis_error = str(e)
    
    # Check system resources
    system_status = {
        "cpu_usage": psutil.cpu_percent(interval=0.1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }
    
    # Overall status
    overall_status = "ok"
    if db_status != "ok" or redis_status != "ok":
        overall_status = "degraded"
    
    # Response time
    response_time = time.time() - start_time
    
    response = {
        "status": overall_status,
        "timestamp": time.time(),
        "components": {
            "database": {
                "status": db_status,
                "error": db_error
            },
            "redis": {
                "status": redis_status,
                "error": redis_error
            }
        },
        "system": system_status,
        "response_time": response_time
    }
    
    return JsonResponse(response)