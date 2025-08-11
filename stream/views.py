from django.shortcuts import render, redirect
from django.core.cache import cache
import requests

BASE_URL = 'http://apigatway.humanmade.my.id:8080'

def get_categories():
    """Helper function to get available categories from API"""
    cache_key = "available_categories"
    categories = cache.get(cache_key)
    
    if not categories:
        try:
            res = requests.get(BASE_URL + '/api/categories/names', timeout=5)
            res.raise_for_status()
            data = res.json()
            categories = data.get('data', ['anime', 'all'])  # Default to these if API fails
            
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
        "is_root": True  # Flag to indicate this is the root page
    }
    
    return render(request, 'stream/root.html', context)

def home(request, category):
    # Get available categories
    categories = get_categories()
    
    cache_key = f"home_data_{category}"
    data = cache.get(cache_key)  # cek apakah sudah ada di cache
    if not data:
        try:
            res = requests.get(BASE_URL + '/api/v1/home', params={'category': category}, timeout=5)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            data = {"error": str(e)}
        # Validasi confidence_score
        if data.get("confidence_score", 0) <= 0.5:
            data = {
                "message": "Something went wrong",
                "confidence_score": data.get("confidence_score", 0)
            }
        # Simpan ke cache (misal 60 detik)
        cache.set(cache_key, data, timeout=60)
    context = {
        "datas": data,
        "category": category,
        "categories": categories
    }
    return render(request, 'stream/index.html', context)

def anime_detail(request):
    # Get parameters from request
    anime_id = request.GET.get('id')
    slug = request.GET.get('slug')
    anime_slug = request.GET.get('anime_slug')
    category = request.GET.get('category', 'anime')  # Default to 'anime' if not provided
    
    # Get available categories
    categories = get_categories()
    
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
        "categories": categories
    }
    
    return render(request, 'stream/detail.html', context)

def latest(request):
    # Get category from query parameter, default to 'anime'
    category = request.GET.get('category', 'anime')
    # Get page from query parameter, default to 1
    page = request.GET.get('page', 1)
    
    # Get available categories
    categories = get_categories()
    
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
    
    context = {
        "datas": data,
        "category": category,
        "page": int(page),
        "categories": categories
    }
    
    return render(request, 'stream/latest.html', context)

def schedule(request):
    # Get category from query parameter, default to 'anime'
    category = request.GET.get('category', 'anime')
    # Get day from query parameter, if provided
    day = request.GET.get('day')
    
    # Get available categories
    categories = get_categories()
    
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
        "days": days
    }
    
    return render(request, 'stream/schedule.html', context)

