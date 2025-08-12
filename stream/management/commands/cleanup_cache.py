"""
Management command for cleaning up corrupted or invalid cache entries
"""

import json
import time
import logging
from django.core.management.base import BaseCommand
from django.core.cache import cache, caches
from django.conf import settings

logger = logging.getLogger('stream.api')


class Command(BaseCommand):
    help = 'Clean up corrupted or invalid cache entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--pattern',
            type=str,
            help='Only clean cache keys matching this pattern'
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validate cache entries and remove corrupted ones'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear all cache (use with caution)'
        )
        parser.add_argument(
            '--older-than',
            type=int,
            help='Remove entries older than X seconds'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        pattern = options['pattern']
        validate = options['validate']
        clear_all = options['all']
        older_than = options['older_than']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        if clear_all:
            self.clear_all_cache(dry_run)
        elif validate:
            self.validate_cache_entries(dry_run, pattern)
        elif pattern:
            self.clean_by_pattern(pattern, dry_run)
        elif older_than:
            self.clean_old_entries(older_than, dry_run)
        else:
            self.clean_common_issues(dry_run)

    def clear_all_cache(self, dry_run=False):
        """Clear all cache entries"""
        self.stdout.write(
            self.style.WARNING('Clearing ALL cache entries...')
        )
        
        if not dry_run:
            # Clear default cache
            cache.clear()
            
            # Clear other caches if they exist
            try:
                fast_cache = caches.get('fast')
                if fast_cache:
                    fast_cache.clear()
            except:
                pass
            
            self.stdout.write(
                self.style.SUCCESS('All cache entries cleared')
            )
        else:
            self.stdout.write('Would clear all cache entries')

    def validate_cache_entries(self, dry_run=False, pattern=None):
        """Validate cache entries and remove corrupted ones"""
        self.stdout.write('Validating cache entries...')
        
        # Common cache key patterns to check
        patterns_to_check = [
            'api_cache:*',
            'home_data_*',
            'episode_detail_*',
            'latest_data_*',
            'search_data_*',
            'available_categories'
        ]
        
        if pattern:
            patterns_to_check = [pattern]
        
        corrupted_count = 0
        total_checked = 0
        
        for cache_pattern in patterns_to_check:
            self.stdout.write(f'Checking pattern: {cache_pattern}')
            
            # Since Django cache doesn't support pattern matching directly,
            # we'll check known cache keys
            test_keys = self.generate_test_keys(cache_pattern)
            
            for key in test_keys:
                total_checked += 1
                try:
                    value = cache.get(key)
                    if value is not None:
                        # Validate the cached data
                        if self.is_corrupted_data(value):
                            corrupted_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'  Corrupted entry found: {key}')
                            )
                            if not dry_run:
                                cache.delete(key)
                                self.stdout.write(f'    Deleted: {key}')
                            else:
                                self.stdout.write(f'    Would delete: {key}')
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(f'  Valid entry: {key}')
                            )
                except Exception as e:
                    corrupted_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  Error reading {key}: {str(e)}')
                    )
                    if not dry_run:
                        cache.delete(key)
                        self.stdout.write(f'    Deleted problematic key: {key}')
        
        self.stdout.write(f'\nValidation complete:')
        self.stdout.write(f'  Total checked: {total_checked}')
        self.stdout.write(f'  Corrupted found: {corrupted_count}')
        
        if corrupted_count > 0 and not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Cleaned up {corrupted_count} corrupted entries')
            )

    def clean_by_pattern(self, pattern, dry_run=False):
        """Clean cache entries matching a pattern"""
        self.stdout.write(f'Cleaning cache entries matching pattern: {pattern}')
        
        # Generate possible keys based on pattern
        test_keys = self.generate_test_keys(pattern)
        deleted_count = 0
        
        for key in test_keys:
            if cache.get(key) is not None:
                deleted_count += 1
                if not dry_run:
                    cache.delete(key)
                    self.stdout.write(f'  Deleted: {key}')
                else:
                    self.stdout.write(f'  Would delete: {key}')
        
        self.stdout.write(f'Cleaned {deleted_count} entries matching pattern: {pattern}')

    def clean_old_entries(self, older_than, dry_run=False):
        """Clean entries older than specified seconds"""
        self.stdout.write(f'Cleaning entries older than {older_than} seconds...')
        
        # This is a simplified implementation since Django cache doesn't
        # provide direct access to entry timestamps
        current_time = time.time()
        
        # Check entries that might have timestamp information
        timestamp_keys = [
            'health_check_cache_test',
            'monitor_cache_test'
        ]
        
        deleted_count = 0
        for key in timestamp_keys:
            try:
                value = cache.get(key)
                if value and isinstance(value, dict) and 'timestamp' in value:
                    entry_time = value['timestamp']
                    if current_time - entry_time > older_than:
                        deleted_count += 1
                        if not dry_run:
                            cache.delete(key)
                            self.stdout.write(f'  Deleted old entry: {key}')
                        else:
                            self.stdout.write(f'  Would delete old entry: {key}')
            except Exception as e:
                self.stdout.write(f'  Error checking {key}: {str(e)}')
        
        self.stdout.write(f'Cleaned {deleted_count} old entries')

    def clean_common_issues(self, dry_run=False):
        """Clean common cache issues"""
        self.stdout.write('Cleaning common cache issues...')
        
        issues_found = 0
        
        # Check for empty or null entries
        common_keys = [
            'available_categories',
            'home_data_all',
            'home_data_anime'
        ]
        
        for key in common_keys:
            try:
                value = cache.get(key)
                if value is not None and self.is_problematic_data(value):
                    issues_found += 1
                    self.stdout.write(
                        self.style.WARNING(f'  Found problematic data in: {key}')
                    )
                    if not dry_run:
                        cache.delete(key)
                        self.stdout.write(f'    Cleaned: {key}')
                    else:
                        self.stdout.write(f'    Would clean: {key}')
            except Exception as e:
                issues_found += 1
                self.stdout.write(
                    self.style.ERROR(f'  Error with {key}: {str(e)}')
                )
                if not dry_run:
                    cache.delete(key)
        
        self.stdout.write(f'Found and cleaned {issues_found} common issues')

    def generate_test_keys(self, pattern):
        """Generate test keys based on pattern"""
        # This is a simplified approach - in production you might want
        # to use Redis SCAN or similar for pattern matching
        test_keys = []
        
        if pattern == 'api_cache:*':
            # Generate some common API cache keys
            import hashlib
            common_urls = [
                'api/v1/home?category=all',
                'api/v1/home?category=anime',
                'api/v1/anime-terbaru?category=all&page=1',
                'api/categories/names'
            ]
            for url in common_urls:
                key_hash = hashlib.md5(url.encode()).hexdigest()
                test_keys.append(f'api_cache:{key_hash}')
        
        elif pattern.startswith('home_data_'):
            test_keys = ['home_data_all', 'home_data_anime']
        
        elif pattern.startswith('episode_detail_'):
            # Add some common episode detail keys
            test_keys = [
                'episode_detail_episode-1_all',
                'episode_detail_episode-2_anime'
            ]
        
        elif pattern == 'available_categories':
            test_keys = ['available_categories']
        
        else:
            # For other patterns, just use the pattern as-is
            test_keys = [pattern.replace('*', '')]
        
        return test_keys

    def is_corrupted_data(self, data):
        """Check if cached data is corrupted"""
        try:
            # Check for common corruption patterns
            if data is None:
                return True
            
            # If it's a string, try to parse as JSON
            if isinstance(data, str):
                try:
                    json.loads(data)
                except (json.JSONDecodeError, ValueError):
                    return True
            
            # Check for incomplete data structures
            if isinstance(data, dict):
                # Check for error indicators
                if data.get('error') and not data.get('message'):
                    return True
                
                # Check for empty critical fields
                if 'data' in data and data['data'] is None:
                    return True
            
            return False
            
        except Exception:
            return True

    def is_problematic_data(self, data):
        """Check if data has common problems"""
        try:
            if isinstance(data, dict):
                # Check for error states
                if data.get('error') and 'temporarily unavailable' in str(data.get('error', '')):
                    return True
                
                # Check for low confidence scores
                if data.get('confidence_score', 1.0) < 0.5:
                    return True
                
                # Check for empty data
                if 'data' in data and not data['data']:
                    return True
            
            return False
            
        except Exception:
            return True