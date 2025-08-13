from django.shortcuts import render, redirect
from django.core.cache import cache, caches
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
import requests
import logging
import urllib.parse
import base64
import json
import re
import os
import time

# Import API client with fallback
from .api_client import api_client, make_api_request, get_api_stats, api_health_check, APIResponse

# Configure logging
logger = logging.getLogger(__name__)
performance_logger = logging.getLogger('stream.performance')

BASE_URL = 'http://apigatway.humanmade.my.id:8080'

# Circuit breaker state
CIRCUIT_BREAKER_KEY = 'api_circuit_breaker'
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 10  # Increased from 5 to be less sensitive
CIRCUIT_BREAKER_TIMEOUT = 60  # Reduced from 5 minutes to 1 minute


def get_seo_context(request, page_type, **kwargs):
    """Generate SEO context including breadcrumbs and meta data"""
    category = kwargs.get('category', '')
    anime_title = kwargs.get('anime_title', '')
    episode_title = kwargs.get('episode_title', '')
    search_query = kwargs.get('search_query', '')
    
    # Build breadcrumbs based on page type
    breadcrumbs = []
    
    if page_type == 'home':
        breadcrumbs = [
            {'name': 'Home', 'url': '/', 'icon': 'home'},
        ]
        if category and category != 'all':
            breadcrumbs.append({
                'name': category.title(),
                'url': f'/{category}/',
                'icon': 'tv',
                'active': True
            })
        else:
            breadcrumbs[0]['active'] = True
            
    elif page_type == 'anime_detail':
        breadcrumbs = [
            {'name': 'Home', 'url': '/', 'icon': 'home'},
            {'name': 'Anime', 'url': '/anime/', 'icon': 'tv'},
            {'name': anime_title or 'Detail', 'active': True}
        ]
        
    elif page_type == 'episode_detail':
        breadcrumbs = [
            {'name': 'Home', 'url': '/', 'icon': 'home'},
            {'name': 'Episode', 'url': '/episode/', 'icon': 'play'},
            {'name': episode_title or 'Watch', 'active': True}
        ]
        
    elif page_type == 'search':
        breadcrumbs = [
            {'name': 'Home', 'url': '/', 'icon': 'home'},
            {'name': 'Search', 'url': '/search/', 'icon': 'search'},
        ]
        if search_query:
            breadcrumbs.append({
                'name': f'"{search_query}"',
                'active': True
            })
        else:
            breadcrumbs[-1]['active'] = True
            
    elif page_type == 'latest':
        breadcrumbs = [
            {'name': 'Home', 'url': '/', 'icon': 'home'},
            {'name': 'Latest Episodes', 'url': '/latest/', 'icon': 'star', 'active': True}
        ]
        
    elif page_type == 'schedule':
        breadcrumbs = [
            {'name': 'Home', 'url': '/', 'icon': 'home'},
            {'name': 'Schedule', 'url': '/schedule/', 'icon': 'calendar', 'active': True}
        ]

    elif page_type == 'history':
        breadcrumbs = [
            {'name': 'Home', 'url': '/', 'icon': 'home'},
            {'name': 'History', 'url': '/history/', 'icon': 'clock', 'active': True}
        ]

    elif page_type == 'watchlist':
        breadcrumbs = [
            {'name': 'Home', 'url': '/', 'icon': 'home'},
            {'name': 'Watchlist', 'url': '/watchlist/', 'icon': 'bookmark', 'active': True}
        ]
    
    return {
        'breadcrumbs': breadcrumbs,
        'page_type': page_type,
        'canonical_url': request.build_absolute_uri(request.path),
        'meta': {
            'robots': 'index, follow',
            'author': 'KortekStream Team',
            'language': 'id-ID',
            'category': category,
        }
    }


def is_circuit_breaker_open():
    """Check if circuit breaker is open (API is considered down)"""
    breaker_data = cache.get(CIRCUIT_BREAKER_KEY, {'failures': 0, 'last_failure': 0})
    
    # If we have too many failures recently, circuit is open
    if breaker_data['failures'] >= CIRCUIT_BREAKER_FAILURE_THRESHOLD:
        time_since_last_failure = time.time() - breaker_data['last_failure']
        if time_since_last_failure < CIRCUIT_BREAKER_TIMEOUT:
            logger.info(f"Circuit breaker is open. Time since last failure: {time_since_last_failure:.2f}s, timeout: {CIRCUIT_BREAKER_TIMEOUT}s")
            return True
        else:
            # Reset circuit breaker after timeout
            logger.info("Circuit breaker timeout reached, resetting...")
            cache.delete(CIRCUIT_BREAKER_KEY)
            return False
    
    return False

def record_api_failure():
    """Record an API failure for circuit breaker"""
    breaker_data = cache.get(CIRCUIT_BREAKER_KEY, {'failures': 0, 'last_failure': 0})
    breaker_data['failures'] += 1
    breaker_data['last_failure'] = time.time()
    cache.set(CIRCUIT_BREAKER_KEY, breaker_data, timeout=CIRCUIT_BREAKER_TIMEOUT * 2)
    logger.warning(f"API failure recorded. Total failures: {breaker_data['failures']}")

def record_api_success():
    """Record an API success for circuit breaker"""
    cache.delete(CIRCUIT_BREAKER_KEY)
    logger.info("API success recorded. Circuit breaker reset.")

def make_api_request_with_retry(url, params=None, max_retries=3, timeout=15, backoff_factor=1):
    """
    Make API request with retry mechanism and exponential backoff
    """
    # Check circuit breaker first, but allow occasional test requests
    if is_circuit_breaker_open():
        # Try to make a test request every 10th time to see if API is back
        breaker_data = cache.get(CIRCUIT_BREAKER_KEY, {'failures': 0, 'last_failure': 0})
        time_since_last_failure = time.time() - breaker_data['last_failure']
        
        # If it's been more than 30 seconds, try one test request
        if time_since_last_failure > 30:
            logger.info("Circuit breaker is open, but trying one test request...")
        else:
            logger.warning("Circuit breaker is open, skipping API request")
            raise requests.exceptions.ConnectionError("API circuit breaker is open - service temporarily unavailable")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"API Request attempt {attempt + 1}/{max_retries}: {url} with params={params}")
            
            # Increase timeout for each retry
            current_timeout = timeout + (attempt * 5)
            
            response = requests.get(url, params=params, timeout=current_timeout)
            response.raise_for_status()
            
            logger.info(f"API Request successful on attempt {attempt + 1}")
            record_api_success()  # Record success for circuit breaker
            return response
            
        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout on attempt {attempt + 1}: {str(e)}")
            record_api_failure()  # Record failure for circuit breaker
            if attempt == max_retries - 1:
                raise
                
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
            record_api_failure()  # Record failure for circuit breaker
            if attempt == max_retries - 1:
                raise
                
        except requests.exceptions.HTTPError as e:
            # For 5xx errors, retry. For 4xx errors, don't retry
            if e.response.status_code >= 500:
                logger.warning(f"Server error {e.response.status_code} on attempt {attempt + 1}: {str(e)}")
                record_api_failure()  # Record failure for circuit breaker
                if attempt == max_retries - 1:
                    raise
            else:
                # Client error, don't retry
                logger.error(f"Client error {e.response.status_code}: {str(e)}")
                # Don't record 4xx errors as circuit breaker failures
                raise
                
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            record_api_failure()  # Record failure for circuit breaker
            if attempt == max_retries - 1:
                raise
        
        # Wait before retrying (exponential backoff)
        if attempt < max_retries - 1:
            wait_time = backoff_factor * (2 ** attempt)
            logger.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    # This should never be reached, but just in case
    raise Exception("Max retries exceeded")

def encode_episode_id(episode_data, category='all'):
    """
    Encode episode data into a base64 string for cleaner URLs
    """
    data = {
        'id': episode_data.get('id', ''),
        'slug': episode_data.get('slug', ''),
        'episode_slug': episode_data.get('episode_slug', ''),
        'episode_url': episode_data.get('episode_url', ''),
        'category': category
    }
    # Remove empty values
    data = {k: v for k, v in data.items() if v}
    
    # Convert to JSON and encode to base64
    json_str = json.dumps(data)
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    return encoded

def decode_episode_id(encoded_id):
    """
    Decode a base64 string back to episode data
    """
    try:
        # Decode base64 to JSON
        json_str = base64.urlsafe_b64decode(encoded_id.encode()).decode()
        data = json.loads(json_str)
        return data
    except Exception as e:
        logger.error(f"Error decoding episode ID: {str(e)}")
        return {}

def get_categories():
    """Helper function to get available categories from API using robust client"""
    try:
        response = make_api_request(
            'api/categories/names',
            cache_timeout=getattr(settings, 'CACHE_TIMEOUT_LONG', 3600)
        )
        
        if response.status_code == 200 and 'data' in response.data:
            return response.data.get('data', ['anime', 'all'])
        else:
            logger.warning(f"Categories API returned unexpected response: {response.data}")
            return ['anime', 'all']
            
    except Exception as e:
        logger.error(f"Failed to get categories: {str(e)}")
        return ['anime', 'all']  # Fallback categories

@cache_page(getattr(settings, 'CACHE_TIMEOUT_SHORT', 60))
@vary_on_headers('User-Agent')
def root(request):
    """Root page with optimized caching and error handling"""
    start_time = time.time()
    
    # Get available categories from API
    categories = get_categories()
    
    # Get content for the "all" category to show all available content
    default_category = "all"
    
    try:
        response = make_api_request(
            'api/v1/home',
            params={'category': default_category},
            cache_timeout=getattr(settings, 'CACHE_TIMEOUT_SHORT', 60)
        )
        
        content_data = response.data
        
        # Add metadata about the response
        if response.cached:
            content_data['_response_meta'] = {
                'cached': True,
                'stale': response.stale,
                'source': response.source
            }
            
    except Exception as e:
        logger.error(f"Root page API error: {str(e)}")
        content_data = {
            "error": "Service temporarily unavailable",
            "message": "Please try again later",
            "debug_info": str(e) if settings.DEBUG else None
        }
    
    # Log performance
    response_time = time.time() - start_time
    performance_logger.info(json.dumps({
        'view': 'root',
        'category': default_category,
        'response_time_ms': round(response_time * 1000, 2),
        'has_error': 'error' in content_data
    }))
    
    context = {
        "categories": categories,
        "datas": content_data,
        "category": default_category,
        "is_root": True,
        "active_page": "home",
        "seo_context": get_seo_context(request, 'home', category='all')
    }
    
    return render(request, 'stream/root.html', context)

@cache_page(getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 300))
@vary_on_headers('User-Agent')
def home(request, category):
    """Category home page with robust error handling and caching"""
    start_time = time.time()
    
    # Get available categories
    categories = get_categories()
    
    # Validate category
    if category not in categories:
        logger.warning(f"Invalid category requested: {category}")
        category = categories[0] if categories else 'all'
    
    error_details = None
    
    try:
        response = make_api_request(
            'api/v1/home',
            params={'category': category},
            cache_timeout=getattr(settings, 'CACHE_TIMEOUT_SHORT', 60)
        )
        
        data = response.data
        
        # Validate confidence score if present
        confidence_score = data.get("confidence_score", 1.0)
        if confidence_score <= 0.5:
            error_details = f"Low confidence score: {confidence_score}"
            logger.warning(f"Low confidence score for category {category}: {confidence_score}")
            data = {
                "message": "Data quality is low, please try again",
                "confidence_score": confidence_score,
                "error_details": error_details
            }
        
        # Add response metadata
        if response.cached:
            data['_response_meta'] = {
                'cached': True,
                'stale': response.stale,
                'source': response.source,
                'response_time': response.response_time
            }
            
        logger.info(f"Home page loaded for category {category}: confidence={confidence_score}")
        
    except Exception as e:
        error_details = f"Service Error: {str(e)}" if settings.DEBUG else "Service temporarily unavailable"
        logger.error(f"Home page error for category {category}: {str(e)}")
        data = {
            "error": "Service temporarily unavailable",
            "message": "Please try again later",
            "error_details": error_details,
            "debug_info": str(e) if settings.DEBUG else None
        }
    
    # Log performance
    response_time = time.time() - start_time
    performance_logger.info(json.dumps({
        'view': 'home',
        'category': category,
        'response_time_ms': round(response_time * 1000, 2),
        'has_error': 'error' in data,
        'confidence_score': data.get('confidence_score', 'N/A')
    }))
    
    context = {
        "datas": data,
        "category": category,
        "categories": categories,
        "error_details": error_details,
        "debug": settings.DEBUG,
        "active_page": "category",
        "seo_context": get_seo_context(request, 'home', category=category)
    }
    return render(request, 'stream/index.html', context)

def anime_detail(request):
    # Get parameters from request
    anime_id = request.GET.get('id')
    slug = request.GET.get('slug')
    anime_slug = request.GET.get('anime_slug')
    
    # Get available categories
    categories = get_categories()
    default_category = categories[0] if categories else 'all'
    category = request.GET.get('category', default_category)
    
    # Use the first non-empty parameter as the identifier
    identifier = anime_slug or slug or anime_id
    
    if not identifier:
        return render(request, 'stream/detail.html', {
            "error": "No anime identifier provided",
            "category": category,
            "categories": categories
        })

    error_details = None
    
    try:
        # Prepare parameters for API request
        params = {}
        if anime_id:
            params['id'] = anime_id
        if slug:
            params['slug'] = slug
        if anime_slug:
            params['anime_slug'] = anime_slug
        if category:
            params['category'] = category
            
        # Make API request using the robust client
        response = make_api_request(
            'api/v1/anime-detail',
            params=params,
            cache_timeout=getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 300) # 5 minutes cache
        )
        
        data = response.data

        if response.source == 'error':
            error_details = data.get('message', 'Service temporarily unavailable')
            logger.error(f"API error in anime_detail for identifier {identifier}: {data.get('error')}")
            data['error_message_for_user'] = error_details

    except Exception as e:
        error_details = f"Unexpected view error: {str(e)}"
        logger.error(f"Unexpected view error in anime_detail for identifier {identifier}: {str(e)}")
        data = {
            "error": error_details,
            "error_message_for_user": "An unexpected error occurred in the application."
        }

    # Normalize the data structure for the template
    # Some APIs return data.data (nested), others return data directly
    normalized_data = data.copy()
    
    # Check if we have a nested data structure (data.data)
    if 'data' in data and isinstance(data['data'], dict) and 'data' in data['data'] and isinstance(data['data']['data'], dict):
        # We have a nested structure, keep it as is
        pass
    elif 'data' in data and isinstance(data['data'], dict):
        # We have a flat structure, create a nested one for consistency
        normalized_data['data'] = {
            'data': data['data']
        }
    
    # Handle _metadata field - Django templates don't allow attributes starting with underscore
    if '_metadata' in normalized_data:
        normalized_data['metadata'] = normalized_data.pop('_metadata')
    
    # Extract anime title for SEO context
    anime_title = ''
    if 'data' in normalized_data and 'data' in normalized_data['data']:
        anime_title = normalized_data['data']['data'].get('judul', '')
    elif 'data' in normalized_data:
        anime_title = normalized_data['data'].get('judul', '')
    
    context = {
        "detail": normalized_data,
        "category": category,
        "anime_slug": identifier,
        "categories": categories,
        "active_page": "detail",  # For navigation active state
        "seo_context": get_seo_context(request, 'anime_detail', anime_title=anime_title, category=category),
        "error_occurred": response.source == 'error' if 'response' in locals() else True
    }
    
    return render(request, 'stream/detail.html', context)

def latest(request):
    # Get category from query parameter, default to first available category
    categories = get_categories()
    default_category = categories[0] if categories else 'all'
    category = request.GET.get('category', default_category)
    # Get page from query parameter, default to 1
    page = request.GET.get('page', 1)
    
    error_details = None

    try:
        response = make_api_request(
            'api/v1/anime-terbaru',
            params={'category': category, 'page': page},
            cache_timeout=getattr(settings, 'CACHE_TIMEOUT_SHORT', 60) # 1 minute cache
        )
        data = response.data

        if response.source == 'error':
            error_details = data.get('message', 'Service temporarily unavailable')
            logger.error(f"API error in latest for category {category}: {data.get('error')}")
            data['error_message_for_user'] = error_details

    except Exception as e:
        error_details = f"Unexpected view error: {str(e)}"
        logger.error(f"Unexpected view error in latest for category {category}: {str(e)}")
        data = {
            "error": error_details,
            "error_message_for_user": "An unexpected error occurred in the application."
        }

    # Process the data to add encoded episode IDs
    if not data.get("error"):
        if category == 'all' and 'data_by_category' in data:
            # Process data for all categories
            for cat_name, cat_data in data['data_by_category'].items():
                if 'data' in cat_data:
                    for item in cat_data['data']:
                        # Create encoded ID for each episode
                        try:
                            if 'url' in item:
                                episode_data = {
                                    'episode_slug': item.get('url', ''),
                                    'episode_url': item.get('url', '')
                                }
                                item['encoded_id'] = encode_episode_id(episode_data, cat_name)
                            else:
                                # Ensure there's at least an empty string to avoid template errors
                                item['encoded_id'] = ''
                        except Exception as e:
                            logger.error(f"Error encoding episode ID in latest view: {str(e)}")
                            item['encoded_id'] = ''
        elif 'data' in data:
            # Process data for a specific category
            for item in data['data']:
                # Create encoded ID for each episode
                try:
                    if 'url' in item:
                        episode_data = {
                            'episode_slug': item.get('url', ''),
                            'episode_url': item.get('url', '')
                        }
                        item['encoded_id'] = encode_episode_id(episode_data, category)
                    else:
                        # Ensure there's at least an empty string to avoid template errors
                        item['encoded_id'] = ''
                except Exception as e:
                    logger.error(f"Error encoding episode ID in latest view: {str(e)}")
                    item['encoded_id'] = ''
    
    context = {
        "datas": data,
        "category": category,
        "page": int(page),
        "categories": categories,
        "active_page": "latest",  # For navigation active state
        "seo_context": get_seo_context(request, 'latest', category=category),
        "error_occurred": response.source == 'error' if 'response' in locals() else True
    }
    
    return render(request, 'stream/latest.html', context)

def schedule(request):
    # Get category from query parameter, default to first available category
    categories = get_categories()
    default_category = categories[0] if categories else 'all'
    category = request.GET.get('category', default_category)
    # Get day from query parameter, if provided
    day = request.GET.get('day')
    
    # Define days of the week (Indonesian names as used in API)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    error_details = None

    try:
        # Use the general schedule endpoint
        response = make_api_request(
            f"api/v1/jadwal-rilis",
            params={'category': category},
            cache_timeout=getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 300) # 5 minutes cache
        )
        data = response.data

        if response.source == 'error':
            error_details = data.get('message', 'Service temporarily unavailable')
            logger.error(f"API error in schedule for category {category}: {data.get('error')}")
            data['error_message_for_user'] = error_details

    except Exception as e:
        error_details = f"Unexpected view error: {str(e)}"
        logger.error(f"Unexpected view error in schedule for category {category}: {str(e)}")
        data = {
            "error": error_details,
            "error_message_for_user": "An unexpected error occurred in the application."
        }
    
    # Handle _metadata field - Django templates don't allow attributes starting with underscore
    if '_metadata' in data:
        data['metadata'] = data.pop('_metadata')
    
    # Handle nested data_by_category if it exists
    if 'data_by_category' in data:
        for cat_name, cat_data in data['data_by_category'].items():
            if '_metadata' in cat_data:
                cat_data['metadata'] = cat_data.pop('_metadata')
    
    context = {
        "datas": data,
        "category": category,
        "categories": categories,
        "selected_day": day,
        "days": days,
        "active_page": "schedule",  # For navigation active state
        "seo_context": get_seo_context(request, 'schedule', category=category),
        "error_occurred": response.source == 'error' if 'response' in locals() else True
    }
    
    return render(request, 'stream/schedule.html', context)

def search(request):
    """
    View function for searching content across categories
    """
    # Get search parameters from request
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    # Get available categories
    categories = get_categories()
    default_category = categories[0] if categories else 'all'
    category = request.GET.get('category', default_category)
    
    data = None
    error_details = None
    response = None

    # Only make API request if there's a search query
    if query:
        try:
            # Make the API request using the robust client
            response = make_api_request(
                'api/v1/search',
                params={
                    'q': query,
                    'category': category,
                    'page': page
                },
                cache_timeout=getattr(settings, 'CACHE_TIMEOUT_SHORT', 60) # 1 minute cache
            )
            data = response.data

            if response.source == 'error':
                error_details = data.get('message', 'Service temporarily unavailable')
                logger.error(f"API error in search for query '{query}': {data.get('error')}")
                data['error_message_for_user'] = error_details
            
            # Validate confidence_score
            elif data.get("confidence_score", 0) <= 0.5:
                error_details = f"Low confidence score: {data.get('confidence_score', 0)}"
                logger.warning(f"Low confidence score for '{query}': {data.get('confidence_score', 0)}")
                data['error_message_for_user'] = "Data quality is low, please try again"

        except Exception as e:
            error_details = f"Unexpected view error: {str(e)}"
            logger.error(f"Unexpected view error in search for query '{query}': {str(e)}")
            data = {
                "error": error_details,
                "error_message_for_user": "An unexpected error occurred in the application."
            }
    
    # Prepare context for the template
    context = {
        "datas": data,
        "category": category,
        "categories": categories,
        "page": int(page) if page else 1,
        "query": query,
        "error_details": error_details,
        "debug": settings.DEBUG,  # Pass DEBUG setting to template
        "active_page": "search",   # For navigation active state
        "seo_context": get_seo_context(request, 'search', search_query=query, category=category),
        "error_occurred": (response.source == 'error' if response else (True if query else False))
    }
    
    return render(request, 'stream/search_results.html', context)

@cache_page(getattr(settings, 'CACHE_TIMEOUT_LONG', 900))
@vary_on_headers('User-Agent')
def episode_detail(request, encoded_id=None):
    """
    Optimized episode detail view with robust error handling and caching
    Supports both encoded ID in URL path and legacy query parameters
    """
    start_time = time.time()
    
    # Get available categories
    categories = get_categories()
    default_category = categories[0] if categories else 'all'
    
    # Initialize parameters
    episode_id = None
    episode_url = None
    episode_slug = None
    category = default_category
    
    # Check if we have an encoded ID in the URL path
    if encoded_id:
        # Decode the ID to get the parameters
        decoded_data = decode_episode_id(encoded_id)
        episode_id = decoded_data.get('id')
        episode_url = decoded_data.get('episode_url')
        episode_slug = decoded_data.get('episode_slug', decoded_data.get('slug'))
        category = decoded_data.get('category', default_category)
    else:
        # Legacy mode: Get parameters from request query string
        episode_id = request.GET.get('id')
        episode_url = request.GET.get('episode_url')
        episode_slug = request.GET.get('episode_slug')
        category = request.GET.get('category', default_category)
    
    # Use the first non-empty parameter as the identifier
    identifier = episode_slug or episode_url or episode_id
    
    if not identifier:
        return render(request, 'stream/episode_detail.html', {
            "error": "No episode identifier provided",
            "category": category,
            "categories": categories,
            "active_page": "episode_detail"
        })
    
    error_details = None
    
    try:
        # Prepare parameters for API request
        params = {}
        if episode_id:
            params['id'] = episode_id
        if episode_url:
            params['episode_url'] = episode_url
        if episode_slug:
            params['episode_slug'] = episode_slug
        if category:
            params['category'] = category
        
        # Make API request using robust client
        response = make_api_request(
            'api/v1/episode-detail',
            params=params,
            cache_timeout=getattr(settings, 'CACHE_TIMEOUT_LONG', 900)  # 15 minutes
        )
        
        data = response.data
        
        # Add response metadata
        if response.cached or response.stale:
            data['_response_meta'] = {
                'cached': response.cached,
                'stale': response.stale,
                'source': response.source,
                'response_time': response.response_time
            }
            
        if response.stale:
            data['stale_message'] = "Data might be outdated due to service issues"
            
        logger.info(f"Episode detail loaded: {identifier} (category: {category})")
        
    except Exception as e:
        error_details = f"Service Error: {str(e)}" if settings.DEBUG else "Service temporarily unavailable"
        logger.error(f"Episode detail error for {identifier}: {str(e)}")
        data = {
            "error": "Service temporarily unavailable",
            "message": "Unable to load episode details",
            "error_details": error_details,
            "success": False,
            "debug_info": str(e) if settings.DEBUG else None
        }
    
    # Handle _metadata field - Django templates don't allow attributes starting with underscore
    if '_metadata' in data:
        data['metadata'] = data.pop('_metadata')
    
    # Normalize the data structure for the template
    # Some APIs return data.data (nested), others return data directly
    normalized_data = data.copy()
    
    # Check if we have a nested data structure (data.data)
    if 'data' in data and isinstance(data['data'], dict) and 'data' in data['data'] and isinstance(data['data']['data'], dict):
        # We have a nested structure, keep it as is
        pass
    elif 'data' in data and isinstance(data['data'], dict):
        # We have a flat structure, create a nested one for consistency
        normalized_data['data'] = {
            'data': data['data']
        }
    
    # Process data to add encoded IDs regardless of whether we have an encoded_id already
    if normalized_data and not normalized_data.get('error'):
        # Create a clean encoded ID for this episode if we don't have one
        if not encoded_id:
            episode_data = {
                'episode_slug': episode_slug,
                'episode_url': episode_url,
                'id': episode_id
            }
            encoded_id = encode_episode_id(episode_data, category)
        
        # Process other episodes to add encoded IDs
        if 'data' in normalized_data and 'other_episodes' in normalized_data['data']:
            for episode in normalized_data['data']['other_episodes']:
                if 'url' in episode:
                    try:
                        other_episode_data = {
                            'episode_slug': episode['url'],
                            'episode_url': episode['url']
                        }
                        episode['encoded_id'] = encode_episode_id(other_episode_data, category)
                    except Exception as e:
                        logger.error(f"Error encoding episode ID for {episode.get('title', 'unknown')}: {str(e)}")
                        # Ensure there's at least an empty string to avoid template errors
                        episode['encoded_id'] = ''
        
        # Add encoded IDs for navigation links
        if 'data' in normalized_data and 'navigation' in normalized_data['data']:
            nav = normalized_data['data']['navigation']
            
            # Previous episode
            if nav.get('previous_episode_url'):
                try:
                    prev_data = {
                        'episode_url': nav['previous_episode_url'],
                        'episode_slug': nav['previous_episode_url']
                    }
                    nav['previous_episode_encoded_id'] = encode_episode_id(prev_data, category)
                except Exception as e:
                    logger.error(f"Error encoding previous episode ID: {str(e)}")
                    nav['previous_episode_encoded_id'] = ''
            
            # Next episode
            if nav.get('next_episode_url'):
                try:
                    next_data = {
                        'episode_url': nav['next_episode_url'],
                        'episode_slug': nav['next_episode_url']
                    }
                    nav['next_episode_encoded_id'] = encode_episode_id(next_data, category)
                except Exception as e:
                    logger.error(f"Error encoding next episode ID: {str(e)}")
                    nav['next_episode_encoded_id'] = ''
    
    # Log performance
    response_time = time.time() - start_time
    performance_logger.info(json.dumps({
        'view': 'episode_detail',
        'identifier': identifier,
        'category': category,
        'response_time_ms': round(response_time * 1000, 2),
        'has_error': 'error' in normalized_data,
        'cached': normalized_data.get('_response_meta', {}).get('cached', False),
        'stale': normalized_data.get('_response_meta', {}).get('stale', False)
    }))
    
    # Add debug information
    if settings.DEBUG:
        logger.info(f"Episode data structure: {json.dumps(normalized_data, indent=2, default=str)}")
    
    # Extract episode title for SEO context
    episode_title = ''
    try:
        if 'data' in normalized_data:
            if 'data' in normalized_data['data']:
                episode_title = normalized_data['data']['data'].get('title', '')
            else:
                episode_title = normalized_data['data'].get('title', '')
    except:
        episode_title = 'Episode'
        
    context = {
        "episode_data": normalized_data,
        "category": category,
        "episode_identifier": identifier,
        "encoded_id": encoded_id,
        "categories": categories,
        "error_details": error_details,
        "debug": settings.DEBUG,
        "active_page": "episode_detail",
        "seo_context": get_seo_context(request, 'episode_detail', episode_title=episode_title, category=category)
    }
    
    return render(request, 'stream/episode_detail.html', context)

@require_GET
def favicon_view(request):
    """
    Serve the favicon.ico file to prevent 404 errors and API calls for favicon.ico
    """
    # Path to your favicon file in the static directory
    favicon_path = os.path.join(settings.STATIC_ROOT, 'favicon.ico')
    
    # If the file exists, serve it
    if os.path.exists(favicon_path):
        with open(favicon_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='image/x-icon')
    
    # If not, return an empty response with the correct content type
    return HttpResponse('', content_type='image/x-icon')

@require_GET
def api_health_check(request):
    """
    Enhanced health check endpoint with comprehensive monitoring
    """
    start_time = time.time()
    
    # Get API client health
    api_health = api_health_check()
    api_stats = get_api_stats()
    
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'api_base_url': BASE_URL,
        'cache_working': False,
        'api_reachable': api_health.get('healthy', False),
        'api_response_time': api_health.get('response_time', 0),
        'circuit_breaker_state': api_health.get('circuit_breaker_state', 'UNKNOWN'),
        'api_stats': api_stats
    }
    
    # Test cache systems
    cache_tests = {}
    
    # Test default cache
    try:
        test_key = 'health_check_cache_test_default'
        test_value = {'test': True, 'timestamp': time.time()}
        cache.set(test_key, test_value, timeout=60)
        cached_value = cache.get(test_key)
        cache_tests['default'] = cached_value is not None
        cache.delete(test_key)
    except Exception as e:
        logger.error(f"Default cache health check failed: {str(e)}")
        cache_tests['default'] = False
    
    # Test fast cache if available
    try:
        from django.core.cache import caches
        fast_cache = caches['fast']
        test_key = 'health_check_cache_test_fast'
        test_value = {'test': True, 'timestamp': time.time()}
        fast_cache.set(test_key, test_value, timeout=60)
        cached_value = fast_cache.get(test_key)
        cache_tests['fast'] = cached_value is not None
        fast_cache.delete(test_key)
    except Exception as e:
        logger.error(f"Fast cache health check failed: {str(e)}")
        cache_tests['fast'] = False
    
    health_status['cache_working'] = cache_tests.get('default', False)
    health_status['cache_tests'] = cache_tests
    
    # Database health check
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['database_working'] = True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status['database_working'] = False
        health_status['database_error'] = str(e)
    
    # Memory usage (if available)
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        health_status['memory_usage'] = {
            'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
            'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
            'percent': round(process.memory_percent(), 2)
        }
    except ImportError:
        health_status['memory_usage'] = 'psutil not available'
    except Exception as e:
        health_status['memory_usage'] = f'Error: {str(e)}'
    
    # Performance metrics from cache
    try:
        current_time = int(time.time())
        hour_key = f"health_metrics:{current_time // 3600}"
        metrics = cache.get(hour_key, {})
        if metrics:
            health_status['performance_metrics'] = {
                'total_requests': metrics.get('total_requests', 0),
                'error_rate': round(metrics.get('error_count', 0) / max(metrics.get('total_requests', 1), 1) * 100, 2),
                'avg_response_time': round(metrics.get('avg_response_time', 0), 3),
                'slow_requests': metrics.get('slow_requests', 0)
            }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}")
    
    # Determine overall health status
    issues = []
    
    if not health_status['cache_working']:
        issues.append('cache_failure')
    
    if not health_status['api_reachable']:
        issues.append('api_unreachable')
    
    if not health_status.get('database_working', True):
        issues.append('database_failure')
    
    if health_status.get('circuit_breaker_state') == 'OPEN':
        issues.append('circuit_breaker_open')
    
    # Set status based on issues
    if not issues:
        health_status['status'] = 'healthy'
        status_code = 200
    elif len(issues) == 1 and 'circuit_breaker_open' in issues:
        health_status['status'] = 'degraded'
        status_code = 200
    elif 'api_unreachable' in issues or 'database_failure' in issues:
        health_status['status'] = 'unhealthy'
        status_code = 503
    else:
        health_status['status'] = 'degraded'
        status_code = 200
    
    health_status['issues'] = issues
    health_status['health_check_duration'] = round((time.time() - start_time) * 1000, 2)
    
    return JsonResponse(health_status, status=status_code)

@require_GET
def reset_circuit_breaker(request):
    """
    Reset circuit breaker secara manual
    """
    try:
        # Delete circuit breaker data
        cache.delete(CIRCUIT_BREAKER_KEY)
        logger.info("Circuit breaker has been manually reset")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Circuit breaker has been reset',
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to reset circuit breaker: {str(e)}',
            'timestamp': time.time()
        }, status=500)

def history_page(request):
    """Renders the watch history page."""
    context = {
        "categories": get_categories(),
        "active_page": "history",
        "seo_context": get_seo_context(request, 'history')
    }
    return render(request, 'stream/history.html', context)

def watchlist_page(request):
    """Renders the watch list page."""
    context = {
        "categories": get_categories(),
        "active_page": "watchlist",
        "seo_context": get_seo_context(request, 'watchlist')
    }
    return render(request, 'stream/watchlist.html', context)

