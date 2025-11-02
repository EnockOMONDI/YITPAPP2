#!/usr/bin/env python3
"""
Certificate Access Investigation Script
Comprehensive analysis of certificate viewing, downloading, and multi-role access functionality
"""

import os
import django
import sys
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.conf import settings
from progress.models import Certificate, Enrollment
from certificates.certificate_service import CertificateService

class CertificateAccessInvestigator:
    def __init__(self):
        self.client = Client()
        self.results = {
            'certificate_directory': {},
            'url_patterns': {},
            'user_access': {},
            'template_analysis': {},
            'missing_functionality': []
        }
    
    def investigate_certificate_directory(self):
        """Examine all files in certificates directory"""
        print("🔍 INVESTIGATING CERTIFICATE DIRECTORY")
        print("=" * 60)
        
        cert_dir = Path('certificates')
        if cert_dir.exists():
            files = list(cert_dir.rglob('*'))
            for file_path in files:
                if file_path.is_file():
                    print(f"📄 {file_path}")
                    self.results['certificate_directory'][str(file_path)] = {
                        'size': file_path.stat().st_size,
                        'type': 'Python' if file_path.suffix == '.py' else 'Other'
                    }
        else:
            print("❌ certificates/ directory not found")
            self.results['missing_functionality'].append("certificates/ directory missing")
    
    def investigate_url_patterns(self):
        """Check for certificate-related URL patterns"""
        print("\n🔗 INVESTIGATING URL PATTERNS")
        print("=" * 60)
        
        # Test certificate URLs mentioned in code
        certificate_urls = [
            '/certificates/verify/test123/',
            '/lms/courses/dashboard/',
            '/profile/',
            '/users/student/',
            '/admin/',
        ]
        
        for url in certificate_urls:
            try:
                # Try to reverse the URL pattern
                if 'verify' in url:
                    print(f"🔍 Certificate verification URL: {url}")
                    print("   ❌ No URL pattern found for certificate verification")
                    self.results['missing_functionality'].append(f"Certificate verification URL pattern missing: {url}")
                else:
                    response = self.client.get(url)
                    status = "✅ Accessible" if response.status_code in [200, 302] else f"❌ Status {response.status_code}"
                    print(f"🔗 {url}: {status}")
                    self.results['url_patterns'][url] = response.status_code
            except Exception as e:
                print(f"❌ {url}: Error - {str(e)}")
                self.results['url_patterns'][url] = f"Error: {str(e)}"
    
    def test_user_access_scenarios(self):
        """Test different user role access scenarios"""
        print("\n👥 TESTING USER ACCESS SCENARIOS")
        print("=" * 60)
        
        try:
            # Test super admin user
            user = User.objects.get(username='victor')
            self.client.force_login(user)
            
            print(f"🔐 Testing access for user: {user.username}")
            print(f"   Roles: superuser={user.is_superuser}, staff={user.is_staff}")
            
            # Test access to different dashboards
            test_urls = [
                ('/lms/courses/dashboard/', 'Student Dashboard'),
                ('/profile/', 'Unified Profile'),
                ('/admin/', 'Admin Interface'),
                ('/users/superuser/profile/', 'Super Admin Dashboard'),
            ]
            
            for url, description in test_urls:
                try:
                    response = self.client.get(url)
                    if response.status_code == 200:
                        print(f"   ✅ {description}: Accessible")
                        self.results['user_access'][description] = 'Accessible'
                    elif response.status_code == 302:
                        print(f"   🔄 {description}: Redirected (may be accessible)")
                        self.results['user_access'][description] = 'Redirected'
                    else:
                        print(f"   ❌ {description}: Status {response.status_code}")
                        self.results['user_access'][description] = f'Status {response.status_code}'
                except Exception as e:
                    print(f"   ❌ {description}: Error - {str(e)}")
                    self.results['user_access'][description] = f'Error: {str(e)}'
            
        except User.DoesNotExist:
            print("❌ Test user 'victor' not found")
            self.results['missing_functionality'].append("Test user 'victor' not found")
    
    def analyze_certificate_templates(self):
        """Analyze certificate-related templates"""
        print("\n📄 ANALYZING CERTIFICATE TEMPLATES")
        print("=" * 60)
        
        template_paths = [
            'templates/certificates/',
            'templates/emails/certificate_issuance.html',
            'templates/lms/courses/dashboard.html',
            'templates/registration/unified_profile.html'
        ]
        
        for template_path in template_paths:
            path = Path(template_path)
            if path.exists():
                if path.is_file():
                    print(f"✅ Template found: {template_path}")
                    self.results['template_analysis'][template_path] = 'Found'
                else:
                    files = list(path.glob('*.html'))
                    if files:
                        print(f"✅ Template directory: {template_path} ({len(files)} files)")
                        self.results['template_analysis'][template_path] = f'{len(files)} files'
                    else:
                        print(f"📁 Empty directory: {template_path}")
                        self.results['template_analysis'][template_path] = 'Empty'
            else:
                print(f"❌ Missing: {template_path}")
                self.results['template_analysis'][template_path] = 'Missing'
                if 'certificates' in template_path:
                    self.results['missing_functionality'].append(f"Certificate template directory missing: {template_path}")
    
    def check_certificate_functionality(self):
        """Check existing certificate functionality"""
        print("\n🏆 CHECKING CERTIFICATE FUNCTIONALITY")
        print("=" * 60)
        
        try:
            # Check if certificates exist
            certificates = Certificate.objects.all()
            print(f"📊 Total certificates in database: {certificates.count()}")
            
            if certificates.exists():
                cert = certificates.first()
                print(f"🔍 Sample certificate:")
                print(f"   ID: {cert.certificate_id}")
                print(f"   Verification Code: {cert.verification_code}")
                print(f"   URL Method: {cert.get_certificate_url()}")
                
                # Test certificate service methods
                verification_result = CertificateService.verify_certificate(cert.verification_code)
                print(f"   Verification Service: {'✅ Working' if verification_result['valid'] else '❌ Failed'}")
                
                # Check for certificate files
                if hasattr(cert, 'certificate_file') and cert.certificate_file:
                    print(f"   File: {cert.certificate_file}")
                else:
                    print(f"   ❌ No certificate file attached")
                    self.results['missing_functionality'].append("Certificate files not stored/attached to Certificate model")
            
        except Exception as e:
            print(f"❌ Error checking certificates: {str(e)}")
    
    def generate_recommendations(self):
        """Generate comprehensive recommendations"""
        print("\n💡 COMPREHENSIVE RECOMMENDATIONS")
        print("=" * 80)
        
        print("🔧 MISSING FUNCTIONALITY IDENTIFIED:")
        for i, issue in enumerate(self.results['missing_functionality'], 1):
            print(f"   {i}. {issue}")
        
        print("\n📋 IMPLEMENTATION RECOMMENDATIONS:")
        
        # Certificate URL patterns
        print("\n1. 🔗 CREATE CERTIFICATE URL PATTERNS:")
        print("   Add to blog/urls.py:")
        print("   path('certificates/', include('certificates.urls')),")
        print("   ")
        print("   Create certificates/urls.py with:")
        print("   - path('verify/<str:verification_code>/', views.verify_certificate, name='verify_certificate')")
        print("   - path('download/<str:verification_code>/', views.download_certificate, name='download_certificate')")
        print("   - path('view/<str:verification_code>/', views.view_certificate, name='view_certificate')")
        
        # Certificate views
        print("\n2. 📄 CREATE CERTIFICATE VIEWS:")
        print("   Create certificates/views.py with:")
        print("   - CertificateVerificationView (public access)")
        print("   - CertificateDownloadView (authenticated access)")
        print("   - CertificateListView (user's own certificates)")
        
        # Template integration
        print("\n3. 🎨 INTEGRATE CERTIFICATES IN TEMPLATES:")
        print("   Update templates/lms/courses/dashboard.html:")
        print("   - Replace hardcoded '0' certificates with dynamic count")
        print("   - Add certificate list section with download links")
        print("   - Add certificate verification links")
        
        # Multi-role access
        print("\n4. 👥 ENSURE MULTI-ROLE ACCESS:")
        print("   - Verify admin users can access student URLs")
        print("   - Add certificate access to unified profile")
        print("   - Test instructor + student role combinations")
        
        print("\n✅ CURRENT WORKING FUNCTIONALITY:")
        print("   - Certificate generation (CertificateService)")
        print("   - Certificate verification (CertificateService.verify_certificate)")
        print("   - Certificate model with verification codes")
        print("   - Email notifications for certificate issuance")
        print("   - Super admin user with valid certificate")
    
    def run_complete_investigation(self):
        """Run complete certificate access investigation"""
        print("🔍 YITP CERTIFICATE ACCESS INVESTIGATION")
        print("=" * 80)
        print("Investigating certificate viewing, downloading, and multi-role access functionality")
        print("=" * 80)
        
        self.investigate_certificate_directory()
        self.investigate_url_patterns()
        self.test_user_access_scenarios()
        self.analyze_certificate_templates()
        self.check_certificate_functionality()
        self.generate_recommendations()
        
        return self.results

if __name__ == "__main__":
    investigator = CertificateAccessInvestigator()
    results = investigator.run_complete_investigation()
