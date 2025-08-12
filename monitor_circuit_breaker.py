#!/usr/bin/env python3
"""
Script untuk monitoring dan reset circuit breaker
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

from stream.views import is_circuit_breaker_open, record_api_success, CIRCUIT_BREAKER_KEY
from django.core.cache import cache

def check_circuit_breaker_status():
    """Check current circuit breaker status"""
    print("=== Circuit Breaker Status ===")
    
    is_open = is_circuit_breaker_open()
    breaker_data = cache.get(CIRCUIT_BREAKER_KEY, {'failures': 0, 'last_failure': 0})
    
    print(f"Circuit Breaker: {'OPEN' if is_open else 'CLOSED'}")
    print(f"Failures: {breaker_data['failures']}")
    
    if breaker_data['last_failure'] > 0:
        last_failure_time = time.time() - breaker_data['last_failure']
        print(f"Last failure: {last_failure_time:.2f} seconds ago")
    else:
        print("Last failure: Never")
    
    return is_open

def reset_circuit_breaker():
    """Reset circuit breaker manually"""
    print("\n=== Resetting Circuit Breaker ===")
    cache.delete(CIRCUIT_BREAKER_KEY)
    print("✅ Circuit breaker has been reset")

def test_api_endpoint():
    """Test API endpoint directly"""
    print("\n=== Testing API Endpoint ===")
    
    try:
        url = "http://apigatway.humanmade.my.id:8080/api/categories/names"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ API is reachable and responding")
            record_api_success()
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

def main():
    print("Circuit Breaker Monitor & Reset Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Check circuit breaker status")
        print("2. Reset circuit breaker")
        print("3. Test API endpoint")
        print("4. Auto-fix (reset + test)")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            check_circuit_breaker_status()
            
        elif choice == '2':
            reset_circuit_breaker()
            check_circuit_breaker_status()
            
        elif choice == '3':
            test_api_endpoint()
            
        elif choice == '4':
            print("\n=== Auto-Fix Mode ===")
            is_open = check_circuit_breaker_status()
            
            if is_open:
                reset_circuit_breaker()
                time.sleep(1)
                
            api_ok = test_api_endpoint()
            
            if api_ok:
                print("✅ System is now healthy!")
            else:
                print("❌ API is still not responding. Please check the API gateway.")
                
        elif choice == '5':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()