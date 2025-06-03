#!/usr/bin/env python
"""
YITP Deployment Verification Script
Run this script after deployment to verify all components are working correctly.

Usage:
    python verify_deployment.py [DEPLOYMENT_URL]
    
Example:
    python verify_deployment.py https://yitp-django-app.onrender.com
"""

import sys
import requests
import time
from urllib.parse import urljoin

def test_endpoint(base_url, endpoint, expected_status=200, timeout=10):
    """Test a specific endpoint and return results."""
    url = urljoin(base_url, endpoint)
    try:
        print(f"🔍 Testing: {url}")
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == expected_status:
            print(f"   ✅ Status: {response.status_code} (Expected: {expected_status})")
            return True, response
        else:
            print(f"   ❌ Status: {response.status_code} (Expected: {expected_status})")
            return False, response
            
    except requests.exceptions.RequestException as e:
        print(f"   🚨 Error: {str(e)}")
        return False, None

def check_static_files(base_url):
    """Check if static files are being served correctly."""
    print("\n📁 Testing Static Files...")
    print("=" * 50)
    
    static_files = [
        '/static/assets/css/style.css',
        '/static/assets/css/messages.css',
        '/static/assets/js/main.js',
        '/static/assets/img/logo/youthImpact.png'
    ]
    
    success_count = 0
    for static_file in static_files:
        success, response = test_endpoint(base_url, static_file)
        if success:
            success_count += 1
            if response and 'content-length' in response.headers:
                size = response.headers['content-length']
                print(f"   📊 Size: {size} bytes")
    
    print(f"\n📊 Static Files: {success_count}/{len(static_files)} working")
    return success_count == len(static_files)

def check_core_pages(base_url):
    """Check core YITP pages."""
    print("\n🌐 Testing Core Pages...")
    print("=" * 50)
    
    pages = [
        ('/', 'Homepage'),
        ('/about/', 'About Page'),
        ('/registration/', 'Registration Page'),
        ('/admin/', 'Admin Panel'),
        ('/courses/', 'Courses Page'),
    ]
    
    success_count = 0
    for endpoint, name in pages:
        print(f"\n📄 {name}")
        success, response = test_endpoint(base_url, endpoint)
        
        if success and response:
            # Check for YITP-specific content
            content = response.text.lower()
            if 'yitp' in content or 'youth impact' in content:
                print(f"   ✅ YITP content detected")
                success_count += 1
            else:
                print(f"   ⚠️  YITP content not found")
        elif endpoint == '/admin/' and response and response.status_code == 302:
            # Admin redirect to login is expected
            print(f"   ✅ Admin redirect working (302)")
            success_count += 1
    
    print(f"\n📊 Core Pages: {success_count}/{len(pages)} working")
    return success_count >= len(pages) - 1  # Allow one failure

def check_responsive_design(base_url):
    """Check if responsive design elements are present."""
    print("\n📱 Testing Responsive Design...")
    print("=" * 50)
    
    success, response = test_endpoint(base_url, '/')
    if not success or not response:
        return False
    
    content = response.text.lower()
    responsive_indicators = [
        'viewport',
        'bootstrap',
        'col-lg',
        'col-md',
        'col-sm',
        '@media'
    ]
    
    found_indicators = []
    for indicator in responsive_indicators:
        if indicator in content:
            found_indicators.append(indicator)
            print(f"   ✅ Found: {indicator}")
        else:
            print(f"   ⚪ Missing: {indicator}")
    
    responsive_score = len(found_indicators) / len(responsive_indicators)
    print(f"\n📊 Responsive Score: {responsive_score:.1%}")
    return responsive_score >= 0.7

def check_performance(base_url):
    """Basic performance check."""
    print("\n⚡ Testing Performance...")
    print("=" * 50)
    
    start_time = time.time()
    success, response = test_endpoint(base_url, '/')
    end_time = time.time()
    
    if success:
        load_time = end_time - start_time
        print(f"   ⏱️  Page Load Time: {load_time:.2f} seconds")
        
        if load_time < 3.0:
            print(f"   ✅ Performance: Excellent (< 3s)")
            return True
        elif load_time < 5.0:
            print(f"   ⚠️  Performance: Good (< 5s)")
            return True
        else:
            print(f"   ❌ Performance: Needs improvement (> 5s)")
            return False
    
    return False

def main():
    """Main verification function."""
    if len(sys.argv) != 2:
        print("❌ Usage: python verify_deployment.py [DEPLOYMENT_URL]")
        print("📝 Example: python verify_deployment.py https://yitp-django-app.onrender.com")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print("🚀 YITP Deployment Verification")
    print("=" * 50)
    print(f"🌐 Testing URL: {base_url}")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("Core Pages", check_core_pages),
        ("Static Files", check_static_files),
        ("Responsive Design", check_responsive_design),
        ("Performance", check_performance),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func(base_url)
            results.append((test_name, result))
        except Exception as e:
            print(f"🚨 Error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DEPLOYMENT VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    success_rate = passed / len(results)
    print(f"\n🎯 Overall Success Rate: {success_rate:.1%} ({passed}/{len(results)})")
    
    if success_rate >= 0.75:
        print("🎉 Deployment verification SUCCESSFUL!")
        print("🌐 YITP is ready for production use!")
        sys.exit(0)
    else:
        print("⚠️  Deployment verification FAILED!")
        print("🔧 Please review the failed tests and fix issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
