#!/usr/bin/env python3
"""
Test script untuk menguji resilience API episode detail
"""

import os
import sys
import django
import requests
import time

# Setup Django environment
sys.path.append('/home/korteks/Documents/project/fekortekstream/kortekstreamV2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from stream.views import make_api_request_with_retry, is_circuit_breaker_open, record_api_failure, record_api_success
from django.core.cache import cache

def test_api_endpoint():
    """Test API endpoint dengan berbagai skenario"""
    
    print("=== Testing API Resilience ===")
    
    # Test 1: Normal API call
    print("\n1. Testing normal API call...")
    try:
        url = "http://apigatway.humanmade.my.id:8080/api/v1/episode-detail"
        params = {
            'episode_url': 'https://v1.samehadaku.how/anime/one-piece/',
            'category': 'anime'
        }
        
        response = make_api_request_with_retry(url, params=params, max_retries=2, timeout=10)
        print(f"✅ API call successful: {response.status_code}")
        
    except Exception as e:
        print(f"❌ API call failed: {str(e)}")
    
    # Test 2: Check circuit breaker status
    print(f"\n2. Circuit breaker status: {'OPEN' if is_circuit_breaker_open() else 'CLOSED'}")
    
    # Test 3: Simulate failures to test circuit breaker
    print("\n3. Testing circuit breaker...")
    for i in range(3):
        record_api_failure()
        print(f"   Recorded failure {i+1}")
    
    print(f"   Circuit breaker status after failures: {'OPEN' if is_circuit_breaker_open() else 'CLOSED'}")
    
    # Test 4: Test cache
    print("\n4. Testing cache...")
    cache_key = "test_episode_detail_cache"
    test_data = {"test": "data", "timestamp": time.time()}
    
    cache.set(cache_key, test_data, timeout=60)
    cached_data = cache.get(cache_key)
    
    if cached_data:
        print("✅ Cache is working properly")
    else:
        print("❌ Cache is not working")
    
    # Reset circuit breaker
    record_api_success()
    print(f"\n5. Circuit breaker reset: {'OPEN' if is_circuit_breaker_open() else 'CLOSED'}")

if __name__ == "__main__":
    test_api_endpoint()