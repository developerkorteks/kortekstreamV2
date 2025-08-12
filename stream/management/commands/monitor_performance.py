"""
Management command for monitoring system performance and health
"""

import time
import json
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.core.cache import cache, caches
from django.conf import settings
from stream.api_client import get_api_stats, api_health_check

logger = logging.getLogger('stream.performance')


class Command(BaseCommand):
    help = 'Monitor system performance and generate reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Monitoring duration in seconds (default: 60)'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=10,
            help='Check interval in seconds (default: 10)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for performance report'
        )
        parser.add_argument(
            '--alert-threshold',
            type=float,
            default=2.0,
            help='Alert threshold for response time in seconds (default: 2.0)'
        )

    def handle(self, *args, **options):
        duration = options['duration']
        interval = options['interval']
        output_file = options['output']
        alert_threshold = options['alert_threshold']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting performance monitoring for {duration} seconds...')
        )
        
        start_time = time.time()
        end_time = start_time + duration
        performance_data = []
        alerts = []
        
        while time.time() < end_time:
            check_start = time.time()
            
            # Collect performance metrics
            metrics = self.collect_metrics()
            metrics['timestamp'] = datetime.now().isoformat()
            metrics['check_duration'] = time.time() - check_start
            
            performance_data.append(metrics)
            
            # Check for alerts
            if metrics.get('api_response_time', 0) > alert_threshold:
                alert = {
                    'timestamp': metrics['timestamp'],
                    'type': 'high_response_time',
                    'value': metrics['api_response_time'],
                    'threshold': alert_threshold
                }
                alerts.append(alert)
                self.stdout.write(
                    self.style.WARNING(
                        f"ALERT: High API response time: {metrics['api_response_time']:.2f}s"
                    )
                )
            
            if not metrics.get('api_healthy', True):
                alert = {
                    'timestamp': metrics['timestamp'],
                    'type': 'api_unhealthy',
                    'details': metrics.get('api_error', 'Unknown error')
                }
                alerts.append(alert)
                self.stdout.write(
                    self.style.ERROR(f"ALERT: API is unhealthy: {alert['details']}")
                )
            
            # Display current status
            self.stdout.write(
                f"API: {'✓' if metrics.get('api_healthy') else '✗'} "
                f"({metrics.get('api_response_time', 0):.2f}s) | "
                f"Cache: {'✓' if metrics.get('cache_working') else '✗'} | "
                f"Memory: {metrics.get('memory_usage', {}).get('percent', 0):.1f}%"
            )
            
            # Wait for next check
            time.sleep(interval)
        
        # Generate report
        report = self.generate_report(performance_data, alerts, duration)
        
        # Output report
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            self.stdout.write(
                self.style.SUCCESS(f'Performance report saved to {output_file}')
            )
        else:
            self.stdout.write('\n' + '='*50)
            self.stdout.write('PERFORMANCE REPORT')
            self.stdout.write('='*50)
            self.print_report(report)

    def collect_metrics(self):
        """Collect current system metrics"""
        metrics = {}
        
        # API health check
        try:
            api_health = api_health_check()
            metrics['api_healthy'] = api_health.get('healthy', False)
            metrics['api_response_time'] = api_health.get('response_time', 0)
            if not metrics['api_healthy']:
                metrics['api_error'] = api_health.get('error', 'Unknown error')
        except Exception as e:
            metrics['api_healthy'] = False
            metrics['api_error'] = str(e)
            metrics['api_response_time'] = 0
        
        # API statistics
        try:
            api_stats = get_api_stats()
            metrics['api_stats'] = api_stats
        except Exception as e:
            metrics['api_stats'] = {'error': str(e)}
        
        # Cache health
        try:
            test_key = 'monitor_cache_test'
            test_value = {'test': True, 'timestamp': time.time()}
            cache.set(test_key, test_value, timeout=60)
            cached_value = cache.get(test_key)
            metrics['cache_working'] = cached_value is not None
            cache.delete(test_key)
        except Exception as e:
            metrics['cache_working'] = False
            metrics['cache_error'] = str(e)
        
        # Memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            metrics['memory_usage'] = {
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                'percent': round(process.memory_percent(), 2)
            }
        except ImportError:
            metrics['memory_usage'] = {'error': 'psutil not available'}
        except Exception as e:
            metrics['memory_usage'] = {'error': str(e)}
        
        # Database health
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                metrics['database_working'] = True
        except Exception as e:
            metrics['database_working'] = False
            metrics['database_error'] = str(e)
        
        return metrics

    def generate_report(self, performance_data, alerts, duration):
        """Generate comprehensive performance report"""
        if not performance_data:
            return {'error': 'No performance data collected'}
        
        # Calculate statistics
        api_response_times = [
            d.get('api_response_time', 0) for d in performance_data 
            if d.get('api_response_time') is not None
        ]
        
        memory_usage = [
            d.get('memory_usage', {}).get('percent', 0) for d in performance_data
            if isinstance(d.get('memory_usage'), dict) and 'percent' in d.get('memory_usage', {})
        ]
        
        api_healthy_count = sum(1 for d in performance_data if d.get('api_healthy', False))
        cache_working_count = sum(1 for d in performance_data if d.get('cache_working', False))
        database_working_count = sum(1 for d in performance_data if d.get('database_working', False))
        
        report = {
            'monitoring_duration': duration,
            'total_checks': len(performance_data),
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'api_health': {
                    'uptime_percentage': round((api_healthy_count / len(performance_data)) * 100, 2),
                    'avg_response_time': round(sum(api_response_times) / len(api_response_times), 3) if api_response_times else 0,
                    'max_response_time': max(api_response_times) if api_response_times else 0,
                    'min_response_time': min(api_response_times) if api_response_times else 0
                },
                'cache_health': {
                    'uptime_percentage': round((cache_working_count / len(performance_data)) * 100, 2)
                },
                'database_health': {
                    'uptime_percentage': round((database_working_count / len(performance_data)) * 100, 2)
                },
                'memory_usage': {
                    'avg_percent': round(sum(memory_usage) / len(memory_usage), 2) if memory_usage else 0,
                    'max_percent': max(memory_usage) if memory_usage else 0,
                    'min_percent': min(memory_usage) if memory_usage else 0
                }
            },
            'alerts': alerts,
            'recommendations': self.generate_recommendations(performance_data, alerts)
        }
        
        return report

    def generate_recommendations(self, performance_data, alerts):
        """Generate performance recommendations based on collected data"""
        recommendations = []
        
        # Check API performance
        api_response_times = [
            d.get('api_response_time', 0) for d in performance_data 
            if d.get('api_response_time') is not None
        ]
        
        if api_response_times:
            avg_response_time = sum(api_response_times) / len(api_response_times)
            if avg_response_time > 2.0:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'high',
                    'message': f'Average API response time is {avg_response_time:.2f}s. Consider implementing request caching or API optimization.'
                })
            elif avg_response_time > 1.0:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'message': f'API response time is {avg_response_time:.2f}s. Monitor for potential improvements.'
                })
        
        # Check memory usage
        memory_usage = [
            d.get('memory_usage', {}).get('percent', 0) for d in performance_data
            if isinstance(d.get('memory_usage'), dict) and 'percent' in d.get('memory_usage', {})
        ]
        
        if memory_usage:
            avg_memory = sum(memory_usage) / len(memory_usage)
            max_memory = max(memory_usage)
            
            if max_memory > 80:
                recommendations.append({
                    'type': 'resource',
                    'priority': 'high',
                    'message': f'Memory usage peaked at {max_memory:.1f}%. Consider increasing server memory or optimizing memory usage.'
                })
            elif avg_memory > 60:
                recommendations.append({
                    'type': 'resource',
                    'priority': 'medium',
                    'message': f'Average memory usage is {avg_memory:.1f}%. Monitor for memory leaks.'
                })
        
        # Check alert frequency
        if len(alerts) > len(performance_data) * 0.1:  # More than 10% of checks had alerts
            recommendations.append({
                'type': 'reliability',
                'priority': 'high',
                'message': f'High alert frequency ({len(alerts)} alerts in {len(performance_data)} checks). Investigate system stability.'
            })
        
        return recommendations

    def print_report(self, report):
        """Print report to console"""
        summary = report.get('summary', {})
        
        self.stdout.write(f"Monitoring Duration: {report.get('monitoring_duration')}s")
        self.stdout.write(f"Total Checks: {report.get('total_checks')}")
        self.stdout.write("")
        
        # API Health
        api_health = summary.get('api_health', {})
        self.stdout.write("API Health:")
        self.stdout.write(f"  Uptime: {api_health.get('uptime_percentage', 0)}%")
        self.stdout.write(f"  Avg Response Time: {api_health.get('avg_response_time', 0)}s")
        self.stdout.write(f"  Max Response Time: {api_health.get('max_response_time', 0)}s")
        self.stdout.write("")
        
        # Memory Usage
        memory = summary.get('memory_usage', {})
        self.stdout.write("Memory Usage:")
        self.stdout.write(f"  Average: {memory.get('avg_percent', 0)}%")
        self.stdout.write(f"  Peak: {memory.get('max_percent', 0)}%")
        self.stdout.write("")
        
        # Alerts
        alerts = report.get('alerts', [])
        if alerts:
            self.stdout.write(f"Alerts ({len(alerts)}):")
            for alert in alerts[-5:]:  # Show last 5 alerts
                self.stdout.write(f"  {alert.get('timestamp', '')}: {alert.get('type', '')} - {alert.get('value', alert.get('details', ''))}")
            self.stdout.write("")
        
        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            self.stdout.write("Recommendations:")
            for rec in recommendations:
                priority_color = self.style.ERROR if rec.get('priority') == 'high' else self.style.WARNING
                self.stdout.write(f"  {priority_color(rec.get('priority', '').upper())}: {rec.get('message', '')}")