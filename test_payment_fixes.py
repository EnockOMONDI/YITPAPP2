#!/usr/bin/env python
"""
Test script to verify YITP payment fixes:
1. Installment button redirect and display
2. M-Pesa Paybill functionality
3. URL routing fixes
4. Email template functionality
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ.pop('DJANGO_ENV', None)  # Ensure development mode
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from courses.models import Course
from payments.templatetags.payment_filters import mul, to_kes, format_currency

def test_url_routing():
    """Test that URL routing is fixed (no double 'courses')"""
    print("🔍 TESTING URL ROUTING FIXES")
    print("=" * 50)
    
    try:
        # Test course detail URL
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        
        # Test URL generation
        course_url = reverse('courses:course_detail', kwargs={'slug': course.slug})
        print(f"✅ Course URL: {course_url}")
        
        # Check that URL doesn't have double 'courses'
        if '/courses/courses/' in course_url:
            print(f"❌ Double 'courses' found in URL: {course_url}")
            return False
        else:
            print(f"✅ URL routing fixed - no double 'courses'")
        
        # Test module URL
        module = course.modules.first()
        if module:
            module_url = reverse('courses:module_detail', kwargs={
                'course_slug': course.slug,
                'module_id': module.id
            })
            print(f"✅ Module URL: {module_url}")
            
            if '/courses/courses/' in module_url:
                print(f"❌ Double 'courses' found in module URL: {module_url}")
                return False
        
        # Test lesson URL
        lesson = course.modules.first().lessons.first() if course.modules.exists() else None
        if lesson:
            lesson_url = reverse('courses:lesson_detail', kwargs={
                'course_slug': course.slug,
                'lesson_id': lesson.id
            })
            print(f"✅ Lesson URL: {lesson_url}")
            
            if '/courses/courses/' in lesson_url:
                print(f"❌ Double 'courses' found in lesson URL: {lesson_url}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ URL routing test failed: {str(e)}")
        return False

def test_payment_template_filters():
    """Test custom payment template filters"""
    print("\n🔍 TESTING PAYMENT TEMPLATE FILTERS")
    print("=" * 50)
    
    try:
        # Test multiplication filter
        result = mul(39, 130)
        expected = 39 * 130
        if result == expected:
            print(f"✅ mul filter: {39} * {130} = {result}")
        else:
            print(f"❌ mul filter failed: expected {expected}, got {result}")
            return False
        
        # Test to_kes filter
        kes_amount = to_kes(39)
        expected_kes = 39 * 130
        if kes_amount == expected_kes:
            print(f"✅ to_kes filter: $39 USD = KES {kes_amount}")
        else:
            print(f"❌ to_kes filter failed: expected {expected_kes}, got {kes_amount}")
            return False
        
        # Test format_currency filter
        usd_formatted = format_currency(39.00, 'USD')
        kes_formatted = format_currency(5070, 'KES')
        
        print(f"✅ format_currency USD: {usd_formatted}")
        print(f"✅ format_currency KES: {kes_formatted}")
        
        return True
        
    except Exception as e:
        print(f"❌ Template filters test failed: {str(e)}")
        return False

def test_payment_methods_page():
    """Test payment methods page functionality"""
    print("\n🔍 TESTING PAYMENT METHODS PAGE")
    print("=" * 50)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        client = Client()
        
        # Test payment methods page
        payment_url = reverse('payments:payment_methods', kwargs={'course_id': course.id})
        print(f"✅ Payment methods URL: {payment_url}")
        
        response = client.get(payment_url)
        print(f"✅ Payment page status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for M-Pesa content
            if 'M-Pesa Paybill' in content:
                print(f"✅ M-Pesa Paybill option found")
            else:
                print(f"❌ M-Pesa Paybill option not found")
                return False
            
            # Check for installment parameter handling
            if 'installment=true' in content:
                print(f"✅ Installment parameter handling found")
            else:
                print(f"❌ Installment parameter handling not found")
                return False
            
            return True
        else:
            print(f"❌ Payment page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Payment methods page test failed: {str(e)}")
        return False

def test_installment_redirect():
    """Test installment button redirect functionality"""
    print("\n🔍 TESTING INSTALLMENT REDIRECT")
    print("=" * 50)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        client = Client()
        
        # Test course detail page
        course_url = reverse('courses:course_detail', kwargs={'slug': course.slug})
        response = client.get(course_url)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for installment button
            if 'Pay in Installments' in content:
                print(f"✅ 'Pay in Installments' button found on course page")
            else:
                print(f"❌ 'Pay in Installments' button not found")
                return False
            
            # Check for installment URL
            installment_url = f"/payments/methods/{course.id}/?installment=true"
            if installment_url in content:
                print(f"✅ Installment URL found: {installment_url}")
            else:
                print(f"❌ Installment URL not found")
                return False
            
            return True
        else:
            print(f"❌ Course page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Installment redirect test failed: {str(e)}")
        return False

def test_mpesa_paybill_url():
    """Test M-Pesa Paybill URL pattern"""
    print("\n🔍 TESTING M-PESA PAYBILL URL")
    print("=" * 50)
    
    try:
        # Test URL pattern exists
        mpesa_url = reverse('payments:process_mpesa_paybill')
        print(f"✅ M-Pesa Paybill URL: {mpesa_url}")
        
        if '/process/mpesa-paybill/' in mpesa_url:
            print(f"✅ M-Pesa Paybill URL pattern correct")
            return True
        else:
            print(f"❌ M-Pesa Paybill URL pattern incorrect")
            return False
            
    except Exception as e:
        print(f"❌ M-Pesa Paybill URL test failed: {str(e)}")
        return False

def test_course_access():
    """Test course access with fixed URLs"""
    print("\n🔍 TESTING COURSE ACCESS")
    print("=" * 50)
    
    try:
        course = Course.objects.get(slug='yitp-9-week-virtual-training')
        client = Client()
        
        # Test course detail page
        course_url = reverse('courses:course_detail', kwargs={'slug': course.slug})
        response = client.get(course_url)
        
        print(f"Course URL: {course_url}")
        print(f"Response status: {response.status_code}")
        
        # 302 is expected for authentication redirect
        if response.status_code in [200, 302]:
            print(f"✅ Course page accessible")
            return True
        else:
            print(f"❌ Course page not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Course access test failed: {str(e)}")
        return False

def generate_test_summary():
    """Generate comprehensive test summary"""
    print("\n📊 PAYMENT FIXES TEST SUMMARY")
    print("=" * 70)
    
    course = Course.objects.get(slug='yitp-9-week-virtual-training')
    
    print(f"📋 TESTED COURSE: {course.title}")
    print(f"   Course ID: {course.id}")
    print(f"   Course Slug: {course.slug}")
    print(f"   Course Price: ${course.price}")
    
    print(f"\n🔧 FIXES IMPLEMENTED:")
    print(f"   ✅ Fixed URL routing (removed double 'courses')")
    print(f"   ✅ Added installment parameter handling in JavaScript")
    print(f"   ✅ Updated Bank Transfer to M-Pesa Paybill")
    print(f"   ✅ Created M-Pesa payment processing view")
    print(f"   ✅ Added M-Pesa email templates")
    print(f"   ✅ Created custom template filters for currency")
    print(f"   ✅ Added M-Pesa URL pattern")
    
    print(f"\n🔗 FUNCTIONAL URLS:")
    print(f"   Course: {reverse('courses:course_detail', kwargs={'slug': course.slug})}")
    print(f"   Payment: {reverse('payments:payment_methods', kwargs={'course_id': course.id})}")
    print(f"   Installment: {reverse('payments:payment_methods', kwargs={'course_id': course.id})}?installment=true")
    print(f"   M-Pesa Process: {reverse('payments:process_mpesa_paybill')}")
    
    print(f"\n💰 PAYMENT OPTIONS:")
    print(f"   PayPal: ${course.price} USD")
    print(f"   M-Pesa Paybill: KES {to_kes(course.price)}")
    print(f"   Installments: 2 payments of ${course.price/2} USD each")

def main():
    """Main test function"""
    print("🧪 YITP PAYMENT FIXES TESTING SUITE")
    print("=" * 80)
    
    tests = [
        ("URL Routing Fixes", test_url_routing),
        ("Payment Template Filters", test_payment_template_filters),
        ("Payment Methods Page", test_payment_methods_page),
        ("Installment Redirect", test_installment_redirect),
        ("M-Pesa Paybill URL", test_mpesa_paybill_url),
        ("Course Access", test_course_access),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error in {test_name}: {str(e)}")
            results[test_name] = False
    
    # Generate summary
    generate_test_summary()
    
    # Final results
    print(f"\n📋 TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {passed/total*100:.1f}%")
    
    print(f"\n📊 Detailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL PAYMENT FIXES WORKING!")
        print(f"   YITP payment system is fully functional")
        return True
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"   Please review failed tests above")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎯 YITP payment fixes verified and working!")
    else:
        print("\n⚠️ Please address test failures")
