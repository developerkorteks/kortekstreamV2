"""
Query optimization utilities for improving database performance
"""

import functools
import time
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('stream.performance')

def cached_api_call(cache_key_prefix, timeout=300):
    """
    Decorator for caching API calls with performance logging
    
    Args:
        cache_key_prefix: Prefix for the cache key
        timeout: Cache timeout in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate a cache key based on arguments
            key_parts = [cache_key_prefix]
            for arg in args:
                if hasattr(arg, '__str__'):
                    key_parts.append(str(arg))
            
            for k, v in sorted(kwargs.items()):
                if hasattr(v, '__str__'):
                    key_parts.append(f"{k}:{v}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for {cache_key}")
                return cached_result
            
            # Not in cache, call the function
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log performance
            logger.info(f"API call {func.__name__} took {execution_time:.4f}s")
            
            # Cache the result
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def optimize_episode_data(episode_data):
    """
    Optimize episode data structure for faster template rendering
    
    Args:
        episode_data: The episode data from API
    
    Returns:
        Optimized episode data
    """
    if not episode_data or not isinstance(episode_data, dict):
        return episode_data
    
    # Create a flattened structure for faster access
    optimized = {}
    
    # Extract common fields
    if 'data' in episode_data:
        data = episode_data['data']
        if isinstance(data, dict):
            # Extract nested data if present
            if 'data' in data and isinstance(data['data'], dict):
                nested_data = data['data']
                
                # Flatten important fields
                optimized['title'] = nested_data.get('title', '')
                optimized['description'] = nested_data.get('description', '')
                optimized['thumbnail_url'] = nested_data.get('thumbnail_url', '')
                
                # Keep reference to original structure
                optimized['original'] = episode_data
                
                # Optimize other episodes list
                if 'other_episodes' in data:
                    optimized['other_episodes'] = data['other_episodes']
            else:
                # Already flat structure
                optimized['title'] = data.get('title', '')
                optimized['description'] = data.get('description', '')
                optimized['thumbnail_url'] = data.get('thumbnail_url', '')
                optimized['original'] = episode_data
                
                if 'other_episodes' in data:
                    optimized['other_episodes'] = data['other_episodes']
    
    return optimized