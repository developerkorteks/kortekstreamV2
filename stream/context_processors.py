from django.conf import settings
from django.urls import reverse, NoReverseMatch


def seo_context(request):
    """Global SEO context processor"""
    
    # Get current path info
    current_path = request.path
    current_url = request.build_absolute_uri()
    
    # Determine page type and breadcrumbs
    breadcrumbs = []
    page_type = 'website'
    
    if current_path == '/':
        page_type = 'website'
    elif '/detail/' in current_path:
        page_type = 'video.tv_show'
        breadcrumbs = [
            {'name': 'Anime', 'url': '/'},
            {'name': 'Detail', 'url': None}
        ]
    elif '/latest/' in current_path:
        breadcrumbs = [
            {'name': 'Latest Episodes', 'url': None}
        ]
    elif '/schedule/' in current_path:
        breadcrumbs = [
            {'name': 'Schedule', 'url': None}
        ]
    elif '/search/' in current_path:
        breadcrumbs = [
            {'name': 'Search Results', 'url': None}
        ]
    elif current_path.startswith('/category/'):
        category = current_path.split('/')[-2] if current_path.endswith('/') else current_path.split('/')[-1]
        breadcrumbs = [
            {'name': category.title(), 'url': None}
        ]
    
    # Generate structured data for organization
    organization_data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": settings.ORGANIZATION_NAME,
        "url": settings.ORGANIZATION_URL,
        "logo": {
            "@type": "ImageObject",
            "url": f"{request.scheme}://{request.get_host()}/static/images/logo.png"
        },
        "sameAs": [
            # Add social media URLs here if available
        ]
    }
    
    return {
        'seo_context': {
            'current_url': current_url,
            'canonical_url': current_url,
            'page_type': page_type,
            'breadcrumbs': breadcrumbs,
            'organization_data': organization_data,
            'site_name': settings.SITE_NAME,
            'site_description': settings.SITE_DESCRIPTION,
            'default_og_image': f"{request.scheme}://{request.get_host()}{settings.DEFAULT_OG_IMAGE}",
        }
    }


def performance_context(request):
    """Performance-related context"""
    return {
        'performance': {
            'enable_lazy_loading': True,
            'enable_webp': True,
            'enable_critical_css': not settings.DEBUG,
            'preload_fonts': True,
        }
    }