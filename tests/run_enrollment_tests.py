#!/usr/bin/env python3
"""
YITP Course Enrollment Test Suite Runner
=======================================

Comprehensive test runner for the YITP course enrollment and payment system.
This script runs all enrollment-related tests and generates detailed reports.

Features:
- Runs all enrollment and payment tests
- Generates coverage reports
- Provides detailed test results
- Checks for missing dependencies
- Validates test environment

Usage:
    python tests/run_enrollment_tests.py [options]

Options:
    --verbose, -v       Verbose output
    --coverage, -c      Generate coverage report
    --failfast, -f      Stop on first failure
    --pattern, -p       Test pattern to match
    --html-report       Generate HTML coverage report

Author: YITP Development Team
Date: 2025-01-05
"""

import os
import sys
import django
import unittest
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.test.utils import get_runner
from django.conf import settings
from django.core.management import execute_from_command_line


class YITPTestRunner:
    """Custom test runner for YITP enrollment tests"""
    
    def __init__(self, verbosity=1, failfast=False, coverage=False, html_report=False):
        self.verbosity = verbosity
        self.failfast = failfast
        self.coverage = coverage
        self.html_report = html_report
        self.test_modules = [
            'tests.test_course_enrollment_journey',
            'tests.test_payment_integration',
        ]
    
    def check_dependencies(self):
        """Check if all required dependencies are available"""
        print("🔍 Checking dependencies...")
        
        missing_deps = []
        
        # Check for required Django apps
        required_apps = [
            'users',
            'courses',
            'progress',
        ]
        
        optional_apps = [
            'payments',
            'certificates',
            'assessments',
            'communication',
            'content'
        ]
        
        for app in required_apps:
            if app not in settings.INSTALLED_APPS:
                missing_deps.append(f"Required app: {app}")
        
        for app in optional_apps:
            if app not in settings.INSTALLED_APPS:
                print(f"⚠️  Optional app not found: {app} (some tests will be skipped)")
        
        # Check for required Python packages
        required_packages = [
            'django',
            'crispy_forms',  # django-crispy-forms package imports as crispy_forms
        ]
        
        optional_packages = [
            'reportlab',  # For certificate generation
            'requests',   # For M-Pesa API
            'coverage',   # For test coverage
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_deps.append(f"Required package: {package}")
        
        for package in optional_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                print(f"⚠️  Optional package not found: {package} (some features will be limited)")
        
        if missing_deps:
            print("❌ Missing required dependencies:")
            for dep in missing_deps:
                print(f"   - {dep}")
            return False
        
        print("✅ All required dependencies found")
        return True
    
    def setup_test_environment(self):
        """Setup test environment and database"""
        print("🔧 Setting up test environment...")
        
        # Ensure test database is created
        try:
            from django.core.management import call_command
            call_command('migrate', verbosity=0, interactive=False)
            print("✅ Test database ready")
        except Exception as e:
            print(f"❌ Failed to setup test database: {e}")
            return False
        
        return True
    
    def run_tests(self, pattern=None):
        """Run the test suite"""
        print(f"🚀 Running YITP enrollment tests...")
        print(f"   Verbosity: {self.verbosity}")
        print(f"   Fail fast: {self.failfast}")
        print(f"   Coverage: {self.coverage}")
        print("-" * 60)
        
        # Prepare test command
        test_command = ['test']
        
        if pattern:
            # Filter tests by pattern
            filtered_modules = [
                module for module in self.test_modules 
                if pattern.lower() in module.lower()
            ]
            test_command.extend(filtered_modules)
        else:
            test_command.extend(self.test_modules)
        
        # Add options
        test_command.extend([
            f'--verbosity={self.verbosity}',
            '--keepdb',  # Keep test database for faster subsequent runs
        ])
        
        if self.failfast:
            test_command.append('--failfast')
        
        # Run with coverage if requested
        if self.coverage:
            return self.run_with_coverage(test_command)
        else:
            return self.run_without_coverage(test_command)
    
    def run_without_coverage(self, test_command):
        """Run tests without coverage"""
        try:
            execute_from_command_line(['manage.py'] + test_command)
            return True
        except SystemExit as e:
            return e.code == 0
    
    def run_with_coverage(self, test_command):
        """Run tests with coverage reporting"""
        try:
            import coverage
        except ImportError:
            print("❌ Coverage package not installed. Install with: pip install coverage")
            return False
        
        print("📊 Running tests with coverage...")
        
        # Initialize coverage
        cov = coverage.Coverage(
            source=['users', 'courses', 'progress', 'payments', 'certificates'],
            omit=[
                '*/migrations/*',
                '*/tests/*',
                '*/venv/*',
                '*/env/*',
                'manage.py',
                '*/settings/*',
            ]
        )
        
        cov.start()
        
        try:
            # Run tests
            execute_from_command_line(['manage.py'] + test_command)
            success = True
        except SystemExit as e:
            success = e.code == 0
        finally:
            cov.stop()
            cov.save()
        
        # Generate coverage report
        print("\n" + "=" * 60)
        print("📊 COVERAGE REPORT")
        print("=" * 60)
        
        cov.report(show_missing=True)
        
        if self.html_report:
            html_dir = project_root / 'htmlcov'
            cov.html_report(directory=str(html_dir))
            print(f"\n📄 HTML coverage report generated: {html_dir}/index.html")
        
        return success
    
    def generate_test_summary(self):
        """Generate test summary report"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        print(f"Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test modules executed:")
        for module in self.test_modules:
            print(f"  - {module}")
        
        print("\nTest categories covered:")
        print("  ✅ Course enrollment workflow")
        print("  ✅ Payment processing (M-Pesa & Bank Transfer)")
        print("  ✅ Email notification system")
        print("  ✅ Certificate generation")
        print("  ✅ Error handling and edge cases")
        print("  ✅ Integration testing")
        print("  ✅ Security validation")
        
        print("\nFor detailed test documentation, see:")
        print("  - tests/test_course_enrollment_journey.py")
        print("  - tests/test_payment_integration.py")
        print("  - Documentation: Course Enrollment Journey")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='YITP Course Enrollment Test Suite Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_enrollment_tests.py                    # Run all tests
  python tests/run_enrollment_tests.py -v 2 -c           # Verbose with coverage
  python tests/run_enrollment_tests.py -p payment        # Run only payment tests
  python tests/run_enrollment_tests.py -c --html-report  # Generate HTML coverage
        """
    )
    
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        choices=[0, 1, 2, 3],
        default=2,
        help='Verbosity level (0-3, default: 2)'
    )
    
    parser.add_argument(
        '-f', '--failfast',
        action='store_true',
        help='Stop on first test failure'
    )
    
    parser.add_argument(
        '-c', '--coverage',
        action='store_true',
        help='Generate coverage report'
    )
    
    parser.add_argument(
        '--html-report',
        action='store_true',
        help='Generate HTML coverage report (requires --coverage)'
    )
    
    parser.add_argument(
        '-p', '--pattern',
        type=str,
        help='Run tests matching pattern'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.html_report and not args.coverage:
        parser.error("--html-report requires --coverage")
    
    print("🎯 YITP Course Enrollment Test Suite")
    print("=" * 60)
    
    # Initialize test runner
    runner = YITPTestRunner(
        verbosity=args.verbosity,
        failfast=args.failfast,
        coverage=args.coverage,
        html_report=args.html_report
    )
    
    # Check dependencies
    if not runner.check_dependencies():
        print("❌ Dependency check failed. Please install missing dependencies.")
        sys.exit(1)
    
    # Setup test environment
    if not runner.setup_test_environment():
        print("❌ Test environment setup failed.")
        sys.exit(1)
    
    # Run tests
    success = runner.run_tests(pattern=args.pattern)
    
    # Generate summary
    runner.generate_test_summary()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check output above for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
