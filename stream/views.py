from django.shortcuts import render, redirect
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
import requests
import logging
import urllib.parse
import base64
import json
import re
import os
import time

# Configure logging
logger = logging.getLogger(__name__)

BASE_URL = 'http://apigatway.humanmade.my.id:8080'

# Circuit breaker state
CIRCUIT_BREAKER_KEY = 'api_circuit_breaker'
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 10  # Increased from 5 to be less sensitive
CIRCUIT_BREAKER_TIMEOUT = 60  # Reduced from 5 minutes to 1 minute

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
    """Helper function to get available categories from API"""
    cache_key = "available_categories"
    categories = cache.get(cache_key)
    
    if not categories:
        try:
            res = requests.get(BASE_URL + '/api/categories/names', timeout=5)
            res.raise_for_status()
            data = res.json()
            categories = data.get('data', ['all'])  # Default to 'all' if API fails
            
            # Cache the categories for 1 hour
            cache.set(cache_key, categories, timeout=3600)
        except Exception as e:
            # Fallback to default categories if API fails
            categories = ['anime', 'all']
    
    return categories

def root(request):
    # Get available categories from API
    categories = get_categories()
    
    # Get content for the "all" category to show all available content
    default_category = "all"
    cache_key_content = f"home_data_{default_category}"
    content_data = cache.get(cache_key_content)
    
    if not content_data:
        try:
            res = requests.get(BASE_URL + '/api/v1/home', params={'category': default_category}, timeout=10)
            res.raise_for_status()
            content_data = res.json()
            
            # Cache the content data for 60 seconds
            cache.set(cache_key_content, content_data, timeout=60)
        except Exception as e:
            content_data = {"error": str(e)}
    
    context = {
        "categories": categories,
        "datas": content_data,
        "category": default_category,
        "is_root": True,  # Flag to indicate this is the root page
        "active_page": "home"  # For navigation active state
    }
    
    return render(request, 'stream/root.html', context)

def home(request, category):
    # Get available categories
    categories = get_categories()
    
    cache_key = f"home_data_{category}"
    data = cache.get(cache_key)  # cek apakah sudah ada di cache
    
    # For debugging purposes, we'll add more detailed error information
    error_details = None
    
    if not data:
        try:
            # Print the URL we're trying to access for debugging
            api_url = f"{BASE_URL}/api/v1/home"
            logger.info(f"Fetching data from: {api_url} with category={category}")
            
            # Increase timeout to 10 seconds to allow for slower responses
            res = requests.get(api_url, params={'category': category}, timeout=10)
            
            # Check status code
            res.raise_for_status()
            
            # Parse the JSON response
            data = res.json()
            
            # Log the response for debugging
            logger.info(f"API Response: {data.get('message', 'No message')}, Confidence: {data.get('confidence_score', 'N/A')}")
            
            # Validasi confidence_score
            if data.get("confidence_score", 0) <= 0.5:
                error_details = f"Low confidence score: {data.get('confidence_score', 0)}"
                logger.warning(f"Low confidence score: {data.get('confidence_score', 0)}")
                data = {
                    "message": "Something went wrong",
                    "confidence_score": data.get("confidence_score", 0),
                    "error_details": error_details
                }
            else:
                # Only cache successful responses with good confidence score
                cache.set(cache_key, data, timeout=60)
                
        except requests.exceptions.RequestException as e:
            # More specific error handling for network issues
            error_details = f"API Connection Error: {str(e)}"
            logger.error(f"API Connection Error: {str(e)}")
            data = {
                "error": str(e),
                "message": "API Connection Error",
                "error_details": error_details
            }
        except ValueError as e:
            # Handle JSON parsing errors
            error_details = f"Invalid JSON Response: {str(e)}"
            logger.error(f"Invalid JSON Response: {str(e)}")
            data = {
                "error": str(e),
                "message": "Invalid API Response Format",
                "error_details": error_details
            }
        except Exception as e:
            # Catch-all for other errors
            error_details = f"Unexpected Error: {str(e)}"
            logger.error(f"Unexpected Error: {str(e)}")
            data = {
                "error": str(e),
                "message": "Unexpected Error",
                "error_details": error_details
            }
    
    context = {
        "datas": data,
        "category": category,
        "categories": categories,
        "error_details": error_details,
        "debug": settings.DEBUG,  # Pass DEBUG setting to template
        "active_page": "category"  # For navigation active state
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
    
    # Create cache key based on identifier and category
    cache_key = f"anime_detail_{identifier}_{category}"
    data = cache.get(cache_key)
    
    if not data:
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
                
            # Make API request
            res = requests.get(BASE_URL + '/api/v1/anime-detail', params=params, timeout=5)
            res.raise_for_status()
            data = res.json()
            
            # Cache the result for 5 minutes
            cache.set(cache_key, data, timeout=300)
        except Exception as e:
            data = {"error": str(e)}
    
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
    
    context = {
        "detail": normalized_data,
        "category": category,
        "anime_slug": identifier,
        "categories": categories,
        "active_page": "detail"  # For navigation active state
    }
    
    return render(request, 'stream/detail.html', context)

def latest(request):
    # Get category from query parameter, default to first available category
    categories = get_categories()
    default_category = categories[0] if categories else 'all'
    category = request.GET.get('category', default_category)
    # Get page from query parameter, default to 1
    page = request.GET.get('page', 1)
    
    cache_key = f"latest_data_{category}_page_{page}"
    data = cache.get(cache_key)
    
    if not data:
        try:
            res = requests.get(
                BASE_URL + '/api/v1/anime-terbaru', 
                params={'category': category, 'page': page}, 
                timeout=10
            )
            res.raise_for_status()
            data = res.json()
            
            # Cache the data for 60 seconds
            cache.set(cache_key, data, timeout=60)
        except Exception as e:
            data = {"error": str(e)}
    
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
        "active_page": "latest"  # For navigation active state
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
    
    # Create cache key based on whether we're fetching a specific day or all days
    cache_key = f"schedule_data_{category}_{day if day else 'all_days'}"
    data = cache.get(cache_key)
    
    if not data:
        try:
            # Use the general schedule endpoint
            res = requests.get(
                f"{BASE_URL}/api/v1/jadwal-rilis", 
                params={'category': category}, 
                timeout=10
            )
            res.raise_for_status()
            data = res.json()
            
            # Cache the data
            cache.set(cache_key, data, timeout=300)
            
        except Exception as e:
            data = {"error": f"Failed to retrieve schedule data: {str(e)}"}
    
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
        "active_page": "schedule"  # For navigation active state
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
    
    # Create a cache key based on search parameters
    # URL encode the query to handle special characters
    encoded_query = urllib.parse.quote(query)
    cache_key = f"search_data_{encoded_query}_{category}_{page}"
    data = cache.get(cache_key)
    
    # For debugging purposes, we'll add more detailed error information
    error_details = None
    
    # Only make API request if there's a search query
    if query and not data:
        try:
            # Prepare API request
            api_url = f"{BASE_URL}/api/v1/search"
            logger.info(f"Searching from: {api_url} with q={query}, category={category}, page={page}")
            
            # Make the API request
            res = requests.get(
                api_url, 
                params={
                    'q': query,
                    'category': category,
                    'page': page
                }, 
                timeout=10
            )
            
            # Check status code
            res.raise_for_status()
            
            # Parse the JSON response
            data = res.json()
            
            # Log the response for debugging
            logger.info(f"API Response: {data.get('message', 'No message')}, Confidence: {data.get('confidence_score', 'N/A')}")
            
            # Validate confidence_score
            if data.get("confidence_score", 0) <= 0.5:
                error_details = f"Low confidence score: {data.get('confidence_score', 0)}"
                logger.warning(f"Low confidence score: {data.get('confidence_score', 0)}")
                data = {
                    "message": "Something went wrong",
                    "confidence_score": data.get("confidence_score", 0),
                    "error_details": error_details
                }
            else:
                # Only cache successful responses with good confidence score
                cache.set(cache_key, data, timeout=60)
                
        except requests.exceptions.RequestException as e:
            # More specific error handling for network issues
            error_details = f"API Connection Error: {str(e)}"
            logger.error(f"API Connection Error: {str(e)}")
            data = {
                "error": str(e),
                "message": "API Connection Error",
                "error_details": error_details
            }
        except ValueError as e:
            # Handle JSON parsing errors
            error_details = f"Invalid JSON Response: {str(e)}"
            logger.error(f"Invalid JSON Response: {str(e)}")
            data = {
                "error": str(e),
                "message": "Invalid API Response Format",
                "error_details": error_details
            }
        except Exception as e:
            # Catch-all for other errors
            error_details = f"Unexpected Error: {str(e)}"
            logger.error(f"Unexpected Error: {str(e)}")
            data = {
                "error": str(e),
                "message": "Unexpected Error",
                "error_details": error_details
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
        "active_page": "search"   # For navigation active state
    }
    
    return render(request, 'stream/search_results.html', context)

def episode_detail(request, encoded_id=None):
    """
    View function for getting episode details
    Supports both encoded ID in URL path and legacy query parameters
    """
    # Get available categories
    categories = get_categories()
    
    # Initialize parameters
    episode_id = None
    episode_url = None
    episode_slug = None
    # Get available categories for default
    categories = get_categories()
    default_category = categories[0] if categories else 'all'
    category = default_category  # Default to first available category
    
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
    
    # Create cache key based on identifier and category
    cache_key = f"episode_detail_{identifier}_{category}"
    data = cache.get(cache_key)
    
    # For debugging purposes, we'll add more detailed error information
    error_details = None
    
    if not data:
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
                
            # Make API request with retry mechanism
            api_url = f"{BASE_URL}/api/v1/episode-detail"
            logger.info(f"Fetching episode detail from: {api_url} with params={params}")
            
            # Use retry mechanism with increased timeout
            res = make_api_request_with_retry(api_url, params=params, max_retries=3, timeout=15)
            data = res.json()
            
            # Log the response for debugging
            logger.info(f"API Response: {data.get('message', 'No message')}")
            
            # Cache the result for 15 minutes (increased from 5 minutes)
            cache.set(cache_key, data, timeout=900)
            
            # Also store as stale cache for 24 hours as fallback
            stale_cache_key = f"episode_detail_stale_{identifier}_{category}"
            cache.set(stale_cache_key, data, timeout=86400)  # 24 hours
            
        except requests.exceptions.RequestException as e:
            # More specific error handling for network issues
            error_details = f"API Connection Error: {str(e)}" if settings.DEBUG else "Service temporarily unavailable"
            logger.error(f"API Connection Error: {str(e)}")
            
            # Try to get stale cache data as fallback
            stale_cache_key = f"episode_detail_stale_{identifier}_{category}"
            stale_data = cache.get(stale_cache_key)
            
            if stale_data:
                logger.info("Using stale cache data as fallback")
                data = stale_data
                # Add a flag to indicate this is stale data
                data['is_stale'] = True
                data['stale_message'] = "Data might be outdated due to service issues"
            else:
                data = {
                    "error": "Service temporarily unavailable" if not settings.DEBUG else str(e),
                    "message": "Something went wrong",
                    "error_details": error_details,
                    "success": False
                }
        except ValueError as e:
            # Handle JSON parsing errors
            error_details = f"Invalid JSON Response: {str(e)}" if settings.DEBUG else "Service temporarily unavailable"
            logger.error(f"Invalid JSON Response: {str(e)}")
            
            # Try to get stale cache data as fallback
            stale_cache_key = f"episode_detail_stale_{identifier}_{category}"
            stale_data = cache.get(stale_cache_key)
            
            if stale_data:
                logger.info("Using stale cache data as fallback")
                data = stale_data
                data['is_stale'] = True
                data['stale_message'] = "Data might be outdated due to service issues"
            else:
                data = {
                    "error": "Service temporarily unavailable" if not settings.DEBUG else str(e),
                    "message": "Something went wrong",
                    "error_details": error_details,
                    "success": False
                }
        except Exception as e:
            # Catch-all for other errors
            error_details = f"Unexpected Error: {str(e)}" if settings.DEBUG else "Service temporarily unavailable"
            logger.error(f"Unexpected Error: {str(e)}")
            
            # Try to get stale cache data as fallback
            stale_cache_key = f"episode_detail_stale_{identifier}_{category}"
            stale_data = cache.get(stale_cache_key)
            
            if stale_data:
                logger.info("Using stale cache data as fallback")
                data = stale_data
                data['is_stale'] = True
                data['stale_message'] = "Data might be outdated due to service issues"
            else:
                data = {
                    "error": "Service temporarily unavailable" if not settings.DEBUG else str(e),
                    "message": "Something went wrong",
                    "error_details": error_details,
                    "success": False
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
    
    # Add debug information
    if settings.DEBUG:
        logger.info(f"Episode data structure: {json.dumps(normalized_data, indent=2, default=str)}")
        
    context = {
        "episode_data": normalized_data,
        "category": category,
        "episode_identifier": identifier,
        "encoded_id": encoded_id,
        "categories": categories,
        "error_details": error_details,
        "debug": settings.DEBUG,  # Pass DEBUG setting to template
        "active_page": "episode_detail"  # For navigation active state
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
    Health check endpoint untuk monitoring status API dan sistem
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'api_base_url': BASE_URL,
        'circuit_breaker_open': is_circuit_breaker_open(),
        'cache_working': False,
        'api_reachable': False
    }
    
    # Test cache
    try:
        test_key = 'health_check_cache_test'
        test_value = {'test': True, 'timestamp': time.time()}
        cache.set(test_key, test_value, timeout=60)
        cached_value = cache.get(test_key)
        health_status['cache_working'] = cached_value is not None
        cache.delete(test_key)
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        health_status['cache_working'] = False
    
    # Test API reachability (quick test)
    try:
        # Use a simple endpoint with short timeout
        test_response = requests.get(f"{BASE_URL}/api/categories/names", timeout=5)
        health_status['api_reachable'] = test_response.status_code == 200
        health_status['api_response_time'] = test_response.elapsed.total_seconds()
    except Exception as e:
        logger.error(f"API health check failed: {str(e)}")
        health_status['api_reachable'] = False
        health_status['api_error'] = str(e)
    
    # Get circuit breaker stats
    breaker_data = cache.get(CIRCUIT_BREAKER_KEY, {'failures': 0, 'last_failure': 0})
    health_status['circuit_breaker_failures'] = breaker_data['failures']
    health_status['circuit_breaker_last_failure'] = breaker_data['last_failure']
    
    # Determine overall health
    if not health_status['cache_working'] or health_status['circuit_breaker_open']:
        health_status['status'] = 'degraded'
    
    if not health_status['api_reachable']:
        health_status['status'] = 'unhealthy'
    
    # Return appropriate HTTP status code
    status_code = 200
    if health_status['status'] == 'degraded':
        status_code = 200  # Still OK but with warnings
    elif health_status['status'] == 'unhealthy':
        status_code = 503  # Service unavailable
    
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

