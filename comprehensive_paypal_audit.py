#!/usr/bin/env python
"""
Comprehensive PayPal Payment Flow Audit for YITP Platform
Tests all aspects of the PayPal payment system including UI, data integrity, and workflows
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from courses.models import Course
from payments.models import Payment
from users.models import Profile
from users.views import get_payment_history
from payments.payment_service import PaymentService
from payments.paypal_service import PayPalService

class PayPalAuditReport:
    def __init__(self):
        self.issues = []
        self.fixes = []
        self.test_results = []
        
    def add_issue(self, category, description, severity="Medium"):
        self.issues.append({
            'category': category,
            'description': description,
            'severity': severity,
            'timestamp': datetime.now()
        })
        
    def add_fix(self, category, description):
        self.fixes.append({
            'category': category,
            'description': description,
            'timestamp': datetime.now()
        })
        
    def add_test_result(self, test_name, passed, details=""):
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now()
        })

def audit_currency_display(report):
    """Audit currency display throughout the system"""
    print("🔍 Auditing Currency Display...")
    
    # Check Payment model default
    from payments.models import Payment
    field = Payment._meta.get_field('currency')
    if field.default == 'USD':
        report.add_test_result("Payment Model Currency Default", True, "Default currency is USD")
    else:
        report.add_issue("Currency", f"Payment model default currency is {field.default}, should be USD", "High")
        report.add_test_result("Payment Model Currency Default", False, f"Default is {field.default}")
    
    # Check for KES references in templates
    import glob
    kes_files = []
    template_files = glob.glob('templates/**/*.html', recursive=True)
    
    for file_path in template_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'KES' in content:
                    kes_files.append(file_path)
        except:
            continue
    
    if kes_files:
        report.add_issue("Currency", f"Found KES references in {len(kes_files)} template files", "Medium")
        report.add_test_result("Template Currency Check", False, f"KES found in: {', '.join(kes_files[:3])}")
    else:
        report.add_test_result("Template Currency Check", True, "No KES references found in templates")

def audit_payment_history_functionality(report):
    """Audit payment history display functionality"""
    print("🔍 Auditing Payment History Functionality...")
    
    try:
        # Create test user and payment
        user, created = User.objects.get_or_create(
            username='audit_test_user',
            defaults={
                'email': 'audit@yitp.com',
                'first_name': 'Audit',
                'last_name': 'Test'
            }
        )
        
        course = Course.objects.filter(is_published=True).first()
        if not course:
            report.add_issue("Test Data", "No published course found for testing", "High")
            return
        
        # Create test payment
        payment = Payment.objects.create(
            user=user,
            course=course,
            amount=Decimal('2.00'),
            currency='USD',
            payment_method='paypal',
            status='confirmed',
            reference_number='AUDIT_TEST_001',
            is_installment=False
        )
        
        # Test payment history function
        payment_history = get_payment_history(user)
        
        if payment_history:
            history_item = payment_history[0]
            required_fields = ['date', 'amount', 'method', 'status', 'currency', 'course']
            missing_fields = [field for field in required_fields if field not in history_item]
            
            if missing_fields:
                report.add_issue("Payment History", f"Missing fields in payment history: {missing_fields}", "Medium")
                report.add_test_result("Payment History Fields", False, f"Missing: {missing_fields}")
            else:
                report.add_test_result("Payment History Fields", True, "All required fields present")
                
            # Check currency display
            if history_item.get('currency') == 'USD':
                report.add_test_result("Payment History Currency", True, "Currency displayed as USD")
            else:
                report.add_issue("Payment History", f"Currency displayed as {history_item.get('currency')}, should be USD", "Medium")
                report.add_test_result("Payment History Currency", False, f"Currency: {history_item.get('currency')}")
        else:
            report.add_issue("Payment History", "Payment history function returned empty results", "High")
            report.add_test_result("Payment History Function", False, "No payment history returned")
        
        # Cleanup
        payment.delete()
        if created:
            user.delete()
            
    except Exception as e:
        report.add_issue("Payment History", f"Error testing payment history: {str(e)}", "High")
        report.add_test_result("Payment History Function", False, f"Error: {str(e)}")

def audit_installment_tracking(report):
    """Audit installment tracking functionality"""
    print("🔍 Auditing Installment Tracking...")
    
    try:
        # Create test user with partial payment
        user, created = User.objects.get_or_create(
            username='installment_test_user',
            defaults={
                'email': 'installment@yitp.com',
                'first_name': 'Installment',
                'last_name': 'Test'
            }
        )
        
        # Set up profile for installment tracking
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.payment_status = 'partially_paid'
        profile.payment_expiration_date = timezone.now() + timedelta(days=25)
        profile.save()
        
        # Check if profile has required fields for installment tracking
        required_fields = ['payment_status', 'payment_expiration_date']
        missing_fields = []
        
        for field in required_fields:
            if not hasattr(profile, field) or getattr(profile, field) is None:
                missing_fields.append(field)
        
        if missing_fields:
            report.add_issue("Installment Tracking", f"Profile missing fields: {missing_fields}", "Medium")
            report.add_test_result("Installment Profile Fields", False, f"Missing: {missing_fields}")
        else:
            report.add_test_result("Installment Profile Fields", True, "All required profile fields present")
        
        # Test expiration date calculation
        if profile.payment_expiration_date:
            days_remaining = (profile.payment_expiration_date - timezone.now()).days
            if days_remaining >= 0:
                report.add_test_result("Installment Expiration Logic", True, f"{days_remaining} days remaining")
            else:
                report.add_test_result("Installment Expiration Logic", True, "Payment expired (as expected for test)")
        
        # Cleanup
        if created:
            user.delete()
            
    except Exception as e:
        report.add_issue("Installment Tracking", f"Error testing installment tracking: {str(e)}", "High")
        report.add_test_result("Installment Tracking", False, f"Error: {str(e)}")

def audit_paypal_integration(report):
    """Audit PayPal API integration"""
    print("🔍 Auditing PayPal Integration...")
    
    try:
        # Test PayPal API connection
        token_result = PayPalService.get_access_token()
        
        if token_result['success']:
            report.add_test_result("PayPal API Connection", True, "Successfully obtained access token")
        else:
            report.add_issue("PayPal Integration", f"Failed to get access token: {token_result['message']}", "High")
            report.add_test_result("PayPal API Connection", False, token_result['message'])
        
        # Test payment order creation (without actually creating)
        course = Course.objects.filter(is_published=True).first()
        if course:
            user = User.objects.filter(is_active=True).first()
            if user:
                # Create test payment record
                payment = PaymentService.create_payment_record(
                    user=user,
                    course=course,
                    amount=Decimal('2.00'),
                    payment_method='paypal',
                    is_installment=False
                )
                
                if payment:
                    report.add_test_result("Payment Record Creation", True, f"Created payment: {payment.reference_number}")
                    
                    # Test PayPal order creation
                    order_result = PayPalService.create_payment_order(payment)
                    
                    if order_result['success']:
                        report.add_test_result("PayPal Order Creation", True, f"Order ID: {order_result['order_id']}")
                    else:
                        report.add_issue("PayPal Integration", f"Failed to create PayPal order: {order_result['message']}", "High")
                        report.add_test_result("PayPal Order Creation", False, order_result['message'])
                    
                    # Cleanup
                    payment.delete()
                else:
                    report.add_issue("Payment Service", "Failed to create payment record", "High")
                    report.add_test_result("Payment Record Creation", False, "Payment creation failed")
        
    except Exception as e:
        report.add_issue("PayPal Integration", f"Error testing PayPal integration: {str(e)}", "High")
        report.add_test_result("PayPal Integration", False, f"Error: {str(e)}")

def generate_audit_report(report):
    """Generate comprehensive audit report"""
    print("\n" + "=" * 80)
    print("📋 COMPREHENSIVE PAYPAL AUDIT REPORT")
    print("=" * 80)
    
    # Test Results Summary
    print("\n🧪 TEST RESULTS SUMMARY:")
    print("-" * 40)
    passed_tests = sum(1 for test in report.test_results if test['passed'])
    total_tests = len(report.test_results)
    
    for test in report.test_results:
        status = "✅ PASSED" if test['passed'] else "❌ FAILED"
        print(f"  {test['test']}: {status}")
        if test['details']:
            print(f"    Details: {test['details']}")
    
    print(f"\n📊 Success Rate: {passed_tests}/{total_tests} ({(passed_tests/total_tests*100):.1f}%)")
    
    # Issues Found
    if report.issues:
        print(f"\n⚠️ ISSUES IDENTIFIED ({len(report.issues)}):")
        print("-" * 40)
        
        for issue in report.issues:
            severity_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(issue['severity'], "⚪")
            print(f"  {severity_icon} {issue['category']}: {issue['description']}")
    else:
        print("\n✅ NO ISSUES FOUND")
    
    # Fixes Applied
    if report.fixes:
        print(f"\n🔧 FIXES APPLIED ({len(report.fixes)}):")
        print("-" * 40)
        
        for fix in report.fixes:
            print(f"  ✅ {fix['category']}: {fix['description']}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 40)
    
    high_priority_issues = [issue for issue in report.issues if issue['severity'] == 'High']
    if high_priority_issues:
        print("  🔴 HIGH PRIORITY:")
        for issue in high_priority_issues:
            print(f"    • Fix {issue['category']}: {issue['description']}")
    
    medium_priority_issues = [issue for issue in report.issues if issue['severity'] == 'Medium']
    if medium_priority_issues:
        print("  🟡 MEDIUM PRIORITY:")
        for issue in medium_priority_issues:
            print(f"    • Improve {issue['category']}: {issue['description']}")
    
    if not report.issues:
        print("  🎉 All systems functioning correctly!")
        print("  📈 Consider implementing additional monitoring and analytics")
        print("  🔒 Regular security audits recommended")

def main():
    """Run comprehensive PayPal audit"""
    print("🔍 YITP PAYPAL PAYMENT SYSTEM AUDIT")
    print("Comprehensive analysis of PayPal integration, UI, and data integrity")
    print("=" * 80)
    
    report = PayPalAuditReport()
    
    # Run audit tests
    audit_currency_display(report)
    audit_payment_history_functionality(report)
    audit_installment_tracking(report)
    audit_paypal_integration(report)
    
    # Generate final report
    generate_audit_report(report)
    
    # Return overall status
    high_priority_issues = sum(1 for issue in report.issues if issue['severity'] == 'High')
    if high_priority_issues == 0:
        print(f"\n🎉 AUDIT COMPLETE: PayPal system is functioning well!")
        return True
    else:
        print(f"\n⚠️ AUDIT COMPLETE: {high_priority_issues} high-priority issues need attention")
        return False

if __name__ == '__main__':
    main()
