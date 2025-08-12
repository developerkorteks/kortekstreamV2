"""
Management command for warming up cache with popular content
"""

import time
import logging
from django.core.management.base import BaseCommand
from django.core.cache import cache
from stream.api_client import make_api_request
from stream.views import get_categories

logger = logging.getLogger('stream.api')


class Command(BaseCommand):
    help = 'Warm up cache with popular content to improve performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            nargs='+',
            help='Specific categories to warm (default: all)'
        )
        parser.add_argument(
            '--pages',
            type=int,
            default=3,
            help='Number of pages to warm per category (default: 3)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh existing cache entries'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='Delay between requests in seconds (default: 0.5)'
        )

    def handle(self, *args, **options):
        categories = options.get('categories') or get_categories()
        pages = options['pages']
        force_refresh = options['force']
        delay = options['delay']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting cache warming for categories: {", ".join(categories)}')
        )
        
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        
        # Warm up home pages
        for category in categories:
            self.stdout.write(f'Warming home page for category: {category}')
            try:
                response = make_api_request(
                    'api/v1/home',
                    params={'category': category},
                    force_refresh=force_refresh
                )
                if response.status_code == 200:
                    successful_requests += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Home page cached (cached: {response.cached})')
                    )
                else:
                    failed_requests += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed to cache home page: {response.status_code}')
                    )
                total_requests += 1
                time.sleep(delay)
            except Exception as e:
                failed_requests += 1
                total_requests += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error caching home page: {str(e)}')
                )
        
        # Warm up latest content
        for category in categories:
            for page in range(1, pages + 1):
                self.stdout.write(f'Warming latest page {page} for category: {category}')
                try:
                    response = make_api_request(
                        'api/v1/anime-terbaru',
                        params={'category': category, 'page': page},
                        force_refresh=force_refresh
                    )
                    if response.status_code == 200:
                        successful_requests += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Latest page {page} cached (cached: {response.cached})')
                        )
                    else:
                        failed_requests += 1
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Failed to cache latest page {page}: {response.status_code}')
                        )
                    total_requests += 1
                    time.sleep(delay)
                except Exception as e:
                    failed_requests += 1
                    total_requests += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error caching latest page {page}: {str(e)}')
                    )
        
        # Warm up schedule data
        for category in categories:
            self.stdout.write(f'Warming schedule for category: {category}')
            try:
                response = make_api_request(
                    'api/v1/jadwal-rilis',
                    params={'category': category},
                    force_refresh=force_refresh
                )
                if response.status_code == 200:
                    successful_requests += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Schedule cached (cached: {response.cached})')
                    )
                else:
                    failed_requests += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed to cache schedule: {response.status_code}')
                    )
                total_requests += 1
                time.sleep(delay)
            except Exception as e:
                failed_requests += 1
                total_requests += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error caching schedule: {str(e)}')
                )
        
        # Warm up categories
        self.stdout.write('Warming categories list')
        try:
            response = make_api_request(
                'api/categories/names',
                force_refresh=force_refresh
            )
            if response.status_code == 200:
                successful_requests += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Categories cached (cached: {response.cached})')
                )
            else:
                failed_requests += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to cache categories: {response.status_code}')
                )
            total_requests += 1
        except Exception as e:
            failed_requests += 1
            total_requests += 1
            self.stdout.write(
                self.style.ERROR(f'  ✗ Error caching categories: {str(e)}')
            )
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('CACHE WARMING SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Total Requests: {total_requests}')
        self.stdout.write(f'Successful: {successful_requests}')
        self.stdout.write(f'Failed: {failed_requests}')
        self.stdout.write(f'Success Rate: {(successful_requests/total_requests*100):.1f}%' if total_requests > 0 else 'N/A')
        
        if failed_requests > 0:
            self.stdout.write(
                self.style.WARNING(f'\n{failed_requests} requests failed. Check logs for details.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nAll cache warming requests completed successfully!')
            )