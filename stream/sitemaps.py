from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
import requests
import logging

logger = logging.getLogger(__name__)


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.9
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            'stream:index', 
            'stream:latest', 
            'stream:schedule',
            'stream:search'
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, obj):
        return timezone.now()

    def priority_for_item(self, item):
        priorities = {
            'stream:index': 1.0,
            'stream:latest': 0.9,
            'stream:schedule': 0.8,
            'stream:search': 0.7,
        }
        return priorities.get(item, 0.8)


class CategorySitemap(Sitemap):
    """Sitemap for category pages"""
    priority = 0.8
    changefreq = 'daily'
    protocol = 'https'

    def items(self):
        # Popular anime categories with SEO value
        return [
            'anime', 'movie', 'ova', 'special', 
            'ongoing', 'completed', 'popular', 
            'action', 'adventure', 'comedy', 
            'drama', 'fantasy', 'romance', 
            'sci-fi', 'slice-of-life'
        ]

    def location(self, item):
        try:
            return reverse('stream:category', kwargs={'category': item})
        except:
            return f'/category/{item}/'

    def lastmod(self, obj):
        return timezone.now()

    def priority_for_item(self, item):
        high_priority_categories = ['anime', 'movie', 'ongoing', 'completed', 'popular']
        return 0.9 if item in high_priority_categories else 0.7


class AnimeListSitemap(Sitemap):
    """Dynamic sitemap for anime list pages"""
    priority = 0.8
    changefreq = 'daily' 
    protocol = 'https'
    limit = 1000

    def items(self):
        """Get popular anime from API for sitemap"""
        cache_key = 'sitemap_anime_list'
        anime_list = cache.get(cache_key)
        
        if not anime_list:
            try:
                # Fetch from your API
                response = requests.get(
                    'http://apigatway.humanmade.my.id:8080/api/home',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    anime_list = []
                    
                    # Extract anime from different sections
                    for section in ['ongoing_anime', 'completed_anime', 'movie_anime']:
                        if section in data.get('data', {}):
                            anime_list.extend(data['data'][section][:20])  # Limit to 20 per section
                    
                    # Cache for 6 hours
                    cache.set(cache_key, anime_list, 60 * 60 * 6)
                else:
                    anime_list = []
            except Exception as e:
                logger.error(f"Error fetching anime for sitemap: {e}")
                anime_list = []

        return anime_list[:self.limit]

    def location(self, item):
        slug = item.get('slug') or item.get('endpoint', '').replace('/', '')
        if slug:
            return f'/anime/{slug}/'
        return None

    def lastmod(self, obj):
        return timezone.now()

    def priority_for_item(self, item):
        # Higher priority for ongoing/popular anime
        if 'ongoing' in str(item.get('status', '')).lower():
            return 0.9
        return 0.7

    def changefreq_for_item(self, item):
        if 'ongoing' in str(item.get('status', '')).lower():
            return 'daily'
        return 'weekly'


class EpisodeListSitemap(Sitemap):
    """Dynamic sitemap for recent episodes"""
    priority = 0.6
    changefreq = 'hourly'
    protocol = 'https'
    limit = 500

    def items(self):
        """Get recent episodes from API for sitemap"""
        cache_key = 'sitemap_episode_list'
        episode_list = cache.get(cache_key)
        
        if not episode_list:
            try:
                # Fetch recent episodes from your API
                response = requests.get(
                    'http://apigatway.humanmade.my.id:8080/api/latest',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    episode_list = data.get('data', [])[:self.limit]
                    
                    # Cache for 2 hours
                    cache.set(cache_key, episode_list, 60 * 60 * 2)
                else:
                    episode_list = []
            except Exception as e:
                logger.error(f"Error fetching episodes for sitemap: {e}")
                episode_list = []

        return episode_list

    def location(self, item):
        slug = item.get('slug') or item.get('endpoint', '').replace('/', '')
        if slug:
            return f'/episode/{slug}/'
        return None

    def lastmod(self, obj):
        # Recent episodes should show recent timestamp
        return timezone.now() - timedelta(hours=2)

    def priority_for_item(self, item):
        # Newer episodes get higher priority
        return 0.8

    def changefreq_for_item(self, item):
        return 'daily'


class SearchSitemap(Sitemap):
    """Sitemap for search and utility pages"""
    priority = 0.5
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            'search',
            'about',
            'contact',
            'privacy',
            'terms'
        ]

    def location(self, item):
        if item == 'search':
            return reverse('stream:search')
        return f'/{item}/'

    def lastmod(self, obj):
        return timezone.now()


class GenreSitemap(Sitemap):
    """Sitemap for genre pages"""
    priority = 0.6
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        # Popular anime genres for SEO
        return [
            'action', 'adventure', 'comedy', 'drama', 
            'ecchi', 'fantasy', 'harem', 'horror',
            'josei', 'magic', 'martial-arts', 'mecha',
            'military', 'music', 'mystery', 'psychological',
            'romance', 'school', 'sci-fi', 'seinen',
            'shoujo', 'shounen', 'slice-of-life', 'sports',
            'supernatural', 'thriller', 'vampire'
        ]

    def location(self, item):
        return f'/genre/{item}/'

    def lastmod(self, obj):
        return timezone.now()


# Dictionary of all sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
    'anime': AnimeListSitemap,
    'episodes': EpisodeListSitemap,
    'search': SearchSitemap,
    'genres': GenreSitemap,
}