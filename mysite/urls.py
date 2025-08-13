"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.sitemaps.views import sitemap
from stream.sitemaps import sitemaps

# Import views with error handling
try:
    from stream.views import favicon_view
    FAVICON_VIEW_AVAILABLE = True
except ImportError:
    FAVICON_VIEW_AVAILABLE = False

# Import SEO views with error handling
try:
    from stream.seo_views import (
        robots_txt, manifest_json, security_txt, 
        ads_txt, humans_txt, opensearch_xml
    )
    SEO_VIEWS_AVAILABLE = True
except ImportError:
    SEO_VIEWS_AVAILABLE = False

# Import health check views
try:
    from stream.views_health import health_check
    HEALTH_CHECK_AVAILABLE = True
except ImportError:
    HEALTH_CHECK_AVAILABLE = False


urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path('admin/', admin.site.urls),
    
    # SEO URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    
    # Main app URLs
    path('', include('stream.urls', namespace='stream')),
]

# Add health check endpoint for Docker
if HEALTH_CHECK_AVAILABLE:
    urlpatterns.append(path('health/', health_check, name='health_check'))

# Add favicon if view is available
if FAVICON_VIEW_AVAILABLE:
    urlpatterns.append(path('favicon.ico', favicon_view, name='favicon'))

# Add SEO URLs if views are available
if SEO_VIEWS_AVAILABLE:
    urlpatterns.extend([
        path('robots.txt', robots_txt, name='robots_txt'),
        path('manifest.json', manifest_json, name='manifest_json'),
        path('.well-known/security.txt', security_txt, name='security_txt'),
        path('ads.txt', ads_txt, name='ads_txt'),
        path('humans.txt', humans_txt, name='humans_txt'),
        path('opensearch.xml', opensearch_xml, name='opensearch_xml'),
    ])

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
