#!/usr/bin/env python
"""
YITP Production Deployment Verification Script
Verifies that all components are working correctly in production
"""

import requests
import time
from urllib.parse import urljoin

class ProductionVerifier:
    def __init__(self):
        self.base_urls = [
            "https://www.youthimpactglobal.com",
            "https://youthimpactglobal.com"
        ]
        self.results = []
    
    def test_url_accessibility(self, url, expected_status=200):
        """Test if a URL is accessible"""
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            success = response.status_code == expected_status
            return {
                'url': url,
                'status_code': response.status_code,
                'success': success,
                'response_time': response.elapsed.total_seconds(),
                'error': None
            }
        except requests.exceptions.RequestException as e:
            return {
                'url': url,
                'status_code': None,
                'success': False,
                'response_time': None,
                'error': str(e)
            }
    
    def test_admin_login_page(self):
        """Test admin login page accessibility"""
        print("🔐 Testing Admin Login Page...")
        
        for base_url in self.base_urls:
            admin_url = urljoin(base_url, '/admin/')
            result = self.test_url_accessibility(admin_url, expected_status=200)
            
            if result['success']:
                print(f"✅ {admin_url} - Accessible ({result['response_time']:.2f}s)")
            else:
                print(f"❌ {admin_url} - Failed: {result['error'] or f'Status {result['status_code']}'}")
            
            self.results.append(('Admin Login Page', result['success']))
    
    def test_homepage(self):
        """Test homepage accessibility"""
        print("🏠 Testing Homepage...")
        
        for base_url in self.base_urls:
            result = self.test_url_accessibility(base_url)
            
            if result['success']:
                print(f"✅ {base_url} - Accessible ({result['response_time']:.2f}s)")
            else:
                print(f"❌ {base_url} - Failed: {result['error'] or f'Status {result['status_code']}'}")
            
            self.results.append(('Homepage', result['success']))
    
    def test_static_files(self):
        """Test static files accessibility"""
        print("📁 Testing Static Files...")
        
        static_files = [
            '/static/unfold/css/unfold.css',
            '/static/assets/css/style.css',
            '/static/admin/css/yitp-blog-admin.css'
        ]
        
        for base_url in self.base_urls[:1]:  # Test only one domain for static files
            for static_file in static_files:
                static_url = urljoin(base_url, static_file)
                result = self.test_url_accessibility(static_url)
                
                if result['success']:
                    print(f"✅ Static file accessible: {static_file}")
                else:
                    print(f"⚠️  Static file issue: {static_file} - {result['error'] or f'Status {result['status_code']}'}")
                
                self.results.append(('Static Files', result['success']))
    
    def test_sitemap_and_robots(self):
        """Test SEO files"""
        print("🔍 Testing SEO Files...")
        
        seo_files = [
            '/sitemap.xml',
            '/robots.txt'
        ]
        
        for base_url in self.base_urls[:1]:  # Test only one domain
            for seo_file in seo_files:
                seo_url = urljoin(base_url, seo_file)
                result = self.test_url_accessibility(seo_url)
                
                if result['success']:
                    print(f"✅ SEO file accessible: {seo_file}")
                else:
                    print(f"❌ SEO file issue: {seo_file} - {result['error'] or f'Status {result['status_code']}'}")
                
                self.results.append(('SEO Files', result['success']))
    
    def test_blog_pages(self):
        """Test blog functionality"""
        print("📝 Testing Blog Pages...")
        
        blog_urls = [
            '/blog/',
            '/admin/blogapp/post/'
        ]
        
        for base_url in self.base_urls[:1]:  # Test only one domain
            for blog_path in blog_urls:
                blog_url = urljoin(base_url, blog_path)
                result = self.test_url_accessibility(blog_url)
                
                if result['success']:
                    print(f"✅ Blog page accessible: {blog_path}")
                else:
                    print(f"⚠️  Blog page issue: {blog_path} - {result['error'] or f'Status {result['status_code']}'}")
                
                self.results.append(('Blog Pages', result['success']))
    
    def check_deployment_status(self):
        """Check if deployment is complete by testing key endpoints"""
        print("🚀 Checking Deployment Status...")
        
        # Test if the main site is responding
        main_url = "https://www.youthimpactglobal.com"
        result = self.test_url_accessibility(main_url)
        
        if result['success']:
            print("✅ Main site is responding - Deployment appears to be complete")
            return True
        else:
            print("❌ Main site not responding - Deployment may still be in progress")
            return False
    
    def wait_for_deployment(self, max_wait_minutes=10):
        """Wait for deployment to complete"""
        print(f"⏳ Waiting for deployment to complete (max {max_wait_minutes} minutes)...")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            if self.check_deployment_status():
                elapsed = (time.time() - start_time) / 60
                print(f"✅ Deployment completed in {elapsed:.1f} minutes")
                return True
            
            print("⏳ Still waiting... (checking again in 30 seconds)")
            time.sleep(30)
        
        print("⚠️  Deployment timeout reached")
        return False
    
    def run_full_verification(self):
        """Run complete verification suite"""
        print("=" * 60)
        print("🔍 YITP PRODUCTION DEPLOYMENT VERIFICATION")
        print("=" * 60)
        
        # Wait for deployment if needed
        if not self.check_deployment_status():
            if not self.wait_for_deployment():
                print("❌ Could not verify deployment completion")
                return False
        
        # Run all tests
        self.test_homepage()
        print()
        self.test_admin_login_page()
        print()
        self.test_static_files()
        print()
        self.test_sitemap_and_robots()
        print()
        self.test_blog_pages()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        
        # Count results by category
        categories = {}
        for category, success in self.results:
            if category not in categories:
                categories[category] = {'success': 0, 'total': 0}
            categories[category]['total'] += 1
            if success:
                categories[category]['success'] += 1
        
        total_success = 0
        total_tests = 0
        
        for category, stats in categories.items():
            success_rate = (stats['success'] / stats['total']) * 100
            status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
            print(f"{status} {category}: {stats['success']}/{stats['total']} ({success_rate:.0f}%)")
            
            total_success += stats['success']
            total_tests += stats['total']
        
        overall_success_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n🎯 OVERALL SUCCESS RATE: {total_success}/{total_tests} ({overall_success_rate:.0f}%)")
        
        if overall_success_rate >= 90:
            print("\n🎉 DEPLOYMENT VERIFICATION SUCCESSFUL!")
            print("✅ Production environment is ready for use")
        elif overall_success_rate >= 70:
            print("\n⚠️  DEPLOYMENT PARTIALLY SUCCESSFUL")
            print("🔧 Some issues detected - review failed tests")
        else:
            print("\n❌ DEPLOYMENT VERIFICATION FAILED")
            print("🚨 Significant issues detected - manual intervention required")
        
        print("\n🌐 Production URLs:")
        print("   • Homepage: https://www.youthimpactglobal.com")
        print("   • Admin: https://www.youthimpactglobal.com/admin/")
        print("   • Credentials: yiptadmin00 / admin123")
        print("=" * 60)

def main():
    """Main execution function"""
    verifier = ProductionVerifier()
    verifier.run_full_verification()

if __name__ == "__main__":
    main()
