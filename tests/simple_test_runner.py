#!/usr/bin/env python
"""
Simple test runner for YITP Course Enrollment tests
Runs a subset of tests to verify basic functionality
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal

# Import YITP models
from courses.models import Course, Category
from progress.models import Enrollment

class SimpleEnrollmentTest(TestCase):
    """Simple test to verify basic enrollment functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@yitp.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category
        self.category, _ = Category.objects.get_or_create(
            slug="technology",
            defaults={
                'name': "Technology",
                'description': "Technology courses"
            }
        )
        
        # Create a simple course
        self.course = Course.objects.create(
            title="Test Course",
            slug="test-course",
            description="A test course",
            learning_objectives="Learn testing",
            category=self.category,
            price=Decimal('0.00'),
            estimated_duration=10,
            instructor=self.admin_user,
            is_published=True
        )
    
    def test_course_creation(self):
        """Test that course was created successfully"""
        self.assertEqual(self.course.title, "Test Course")
        self.assertEqual(self.course.price, Decimal('0.00'))
        self.assertTrue(self.course.is_published)
        print("✅ Course creation test passed")
    
    def test_user_creation(self):
        """Test that users were created successfully"""
        self.assertEqual(self.regular_user.username, 'testuser')
        self.assertEqual(self.admin_user.username, 'admin')
        self.assertTrue(self.admin_user.is_staff)
        print("✅ User creation test passed")
    
    def test_basic_enrollment(self):
        """Test basic enrollment creation"""
        enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.course,
            status='active'
        )
        
        self.assertEqual(enrollment.student, self.regular_user)
        self.assertEqual(enrollment.course, self.course)
        self.assertEqual(enrollment.status, 'active')
        print("✅ Basic enrollment test passed")
    
    def test_enrollment_uniqueness(self):
        """Test that duplicate enrollments are prevented"""
        # Create first enrollment
        Enrollment.objects.create(
            student=self.regular_user,
            course=self.course,
            status='active'
        )
        
        # Try to create duplicate enrollment
        with self.assertRaises(Exception):
            Enrollment.objects.create(
                student=self.regular_user,
                course=self.course,
                status='active'
            )
        print("✅ Enrollment uniqueness test passed")

def run_simple_tests():
    """Run the simple tests"""
    print("🎯 YITP Simple Enrollment Tests")
    print("=" * 50)
    
    # Import Django test runner
    from django.test.utils import get_runner
    from django.conf import settings
    
    # Get test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    
    # Run tests
    test_labels = ['tests.simple_test_runner.SimpleEnrollmentTest']
    failures = test_runner.run_tests(test_labels)
    
    if failures:
        print(f"❌ {failures} test(s) failed")
        return False
    else:
        print("✅ All simple tests passed!")
        return True

if __name__ == '__main__':
    success = run_simple_tests()
    sys.exit(0 if success else 1)
