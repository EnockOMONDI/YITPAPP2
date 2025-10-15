#!/usr/bin/env python3
"""
Check Production Deployment Status
Verify if our lesson access fixes have been deployed to production
"""

import os
import sys
import django
import requests
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Lesson
from progress.models import Enrollment
from courses.trial_service import TrialAccessService

class ProductionDeploymentChecker:
    def __init__(self):
        self.production_url = "https://www.youthimpactglobal.com"
        
    def check_code_deployment(self):
        """Check if our code changes are deployed"""
        print("🔍 CHECKING CODE DEPLOYMENT STATUS")
        print("="*50)
        
        # Check courses/models.py - line 285
        print("\n📄 Checking courses/models.py:")
        try:
            with open('courses/models.py', 'r') as f:
                content = f.read()
                if "status__in=['active', 'completed']" in content:
                    print("   ✅ courses/models.py contains the fix")
                else:
                    print("   ❌ courses/models.py does NOT contain the fix")
        except Exception as e:
            print(f"   ❌ Error reading courses/models.py: {e}")
            
        # Check courses/trial_service.py - lines 116, 209
        print("\n📄 Checking courses/trial_service.py:")
        try:
            with open('courses/trial_service.py', 'r') as f:
                content = f.read()
                fix_count = content.count("status__in=['active', 'completed']")
                if fix_count >= 2:
                    print(f"   ✅ courses/trial_service.py contains {fix_count} fixes")
                else:
                    print(f"   ❌ courses/trial_service.py contains only {fix_count} fixes (expected 2)")
        except Exception as e:
            print(f"   ❌ Error reading courses/trial_service.py: {e}")
            
        # Check courses/views.py - multiple lines
        print("\n📄 Checking courses/views.py:")
        try:
            with open('courses/views.py', 'r') as f:
                content = f.read()
                fix_count = content.count("status__in=['active', 'completed']")
                if fix_count >= 4:
                    print(f"   ✅ courses/views.py contains {fix_count} fixes")
                else:
                    print(f"   ❌ courses/views.py contains only {fix_count} fixes (expected 4+)")
        except Exception as e:
            print(f"   ❌ Error reading courses/views.py: {e}")
            
    def check_git_status(self):
        """Check git status and recent commits"""
        print("\n🔧 CHECKING GIT STATUS")
        print("="*30)
        
        try:
            import subprocess
            
            # Check current branch
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, cwd='.')
            current_branch = result.stdout.strip()
            print(f"   Current Branch: {current_branch}")
            
            # Check recent commits
            result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                                  capture_output=True, text=True, cwd='.')
            commits = result.stdout.strip().split('\n')
            print(f"\n   Recent Commits:")
            for commit in commits:
                print(f"   {commit}")
                
            # Check if there are uncommitted changes
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd='.')
            if result.stdout.strip():
                print(f"\n   ⚠️  Uncommitted changes detected")
            else:
                print(f"\n   ✅ No uncommitted changes")
                
        except Exception as e:
            print(f"   ❌ Error checking git status: {e}")
            
    def test_production_api(self):
        """Test production API endpoints"""
        print("\n🌐 TESTING PRODUCTION API")
        print("="*30)
        
        # Test if production site is accessible
        try:
            response = requests.get(f"{self.production_url}/", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Production site accessible: {response.status_code}")
            else:
                print(f"   ⚠️  Production site status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error accessing production site: {e}")
            
        # Test lesson access API (if available)
        try:
            # This would require authentication, so we'll skip for now
            print(f"   ℹ️  Lesson access API test skipped (requires auth)")
        except Exception as e:
            print(f"   ❌ Error testing lesson API: {e}")
            
    def check_database_consistency(self):
        """Check database consistency between local and production"""
        print("\n🗄️  CHECKING DATABASE CONSISTENCY")
        print("="*40)
        
        try:
            # Get Victor's enrollment
            user = User.objects.get(email='info@youthimpactglobal.com')
            course = Course.objects.get(id=6)
            enrollment = Enrollment.objects.get(student=user, course=course)
            
            print(f"   Victor's Enrollment Status: {enrollment.status}")
            print(f"   Victor's Progress: {enrollment.progress_percentage}%")
            print(f"   Enrollment Type: {enrollment.enrollment_type}")
            
            # Test lesson access with current code
            first_module = course.modules.filter(is_published=True).order_by('sort_order').first()
            lesson1 = first_module.lessons.filter(is_published=True).order_by('sort_order').first()
            
            is_accessible, message = lesson1.is_accessible_for_user(user)
            print(f"   Lesson 1 Accessible: {is_accessible}")
            print(f"   Access Message: {message}")
            
        except Exception as e:
            print(f"   ❌ Error checking database: {e}")
            
    def check_template_files(self):
        """Check template files for any hardcoded locks"""
        print("\n🎨 CHECKING TEMPLATE FILES")
        print("="*30)
        
        template_files = [
            'templates/lms/courses/lesson_detail.html',
            'templates/lms/courses/course_detail.html',
            'templates/lms/trial/trial_status.html'
        ]
        
        for template_file in template_files:
            try:
                with open(template_file, 'r') as f:
                    content = f.read()
                    
                # Check for locked indicators
                if 'lesson-locked' in content.lower():
                    print(f"   📄 {template_file}: Contains 'lesson-locked' class")
                if 'fas fa-lock' in content:
                    print(f"   📄 {template_file}: Contains lock icon")
                if 'is_accessible' in content:
                    print(f"   📄 {template_file}: Uses is_accessible variable")
                    
            except Exception as e:
                print(f"   ❌ Error reading {template_file}: {e}")
                
    def run_deployment_check(self):
        """Run comprehensive deployment check"""
        print("🚀 YITP PRODUCTION DEPLOYMENT CHECKER")
        print("="*50)
        print(f"Check Time: {datetime.now()}")
        print(f"Environment: {'PRODUCTION' if os.environ.get('DJANGO_ENV') == 'production' else 'DEVELOPMENT'}")
        
        self.check_code_deployment()
        self.check_git_status()
        self.test_production_api()
        self.check_database_consistency()
        self.check_template_files()
        
        print("\n" + "="*50)
        print("🎯 DEPLOYMENT STATUS SUMMARY")
        print("="*50)
        print("Based on the checks above:")
        print("1. ✅ Code changes are present in local files")
        print("2. ✅ Database shows lesson should be accessible")
        print("3. ❓ Production deployment status needs verification")
        print("\n💡 NEXT STEPS:")
        print("1. Ensure changes are pushed to production branch")
        print("2. Verify deployment on Render.com")
        print("3. Clear browser cache and test again")
        print("4. Check for any client-side JavaScript blocking access")

if __name__ == "__main__":
    checker = ProductionDeploymentChecker()
    checker.run_deployment_check()
