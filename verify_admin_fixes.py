#!/usr/bin/env python
"""
Verify that all admin configuration fixes have been applied correctly
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course
from django.contrib.admin.sites import site

def verify_course_model_fields():
    """Verify Course model now uses CKEditor5Field"""
    print("📝 VERIFYING COURSE MODEL FIELDS")
    print("=" * 50)
    
    # Check field types
    course_fields = Course._meta.get_fields()
    
    description_field = None
    learning_objectives_field = None
    
    for field in course_fields:
        if field.name == 'description':
            description_field = field
        elif field.name == 'learning_objectives':
            learning_objectives_field = field
    
    # Check if fields are CKEditor5Field
    from django_ckeditor_5.fields import CKEditor5Field
    
    if isinstance(description_field, CKEditor5Field):
        print("✅ Description field is now CKEditor5Field")
    else:
        print(f"❌ Description field is still {type(description_field).__name__}")
    
    if isinstance(learning_objectives_field, CKEditor5Field):
        print("✅ Learning objectives field is now CKEditor5Field")
    else:
        print(f"❌ Learning objectives field is still {type(learning_objectives_field).__name__}")
    
    return isinstance(description_field, CKEditor5Field) and isinstance(learning_objectives_field, CKEditor5Field)

def verify_admin_fieldsets():
    """Verify CourseAdmin has correct fieldsets configuration"""
    print("\n📋 VERIFYING ADMIN FIELDSETS")
    print("=" * 50)
    
    from courses.admin import CourseAdmin
    
    # Check if fieldsets is properly configured
    if hasattr(CourseAdmin, 'fieldsets') and CourseAdmin.fieldsets:
        fieldsets = CourseAdmin.fieldsets
        print(f"✅ CourseAdmin has {len(fieldsets)} fieldset sections")
        
        # Check if status field is included
        status_found = False
        for fieldset_name, fieldset_config in fieldsets:
            fields = fieldset_config.get('fields', [])
            if 'status' in fields:
                status_found = True
                print(f"✅ Status field found in '{fieldset_name}' section")
                break
        
        if not status_found:
            print("❌ Status field not found in any fieldset")
            return False
        
        # List all fieldset sections
        print("\n📋 Fieldset sections:")
        for i, (fieldset_name, fieldset_config) in enumerate(fieldsets, 1):
            fields = fieldset_config.get('fields', [])
            print(f"   {i}. {fieldset_name}: {len(fields)} fields")
            if 'status' in fields or 'is_published' in fields:
                print(f"      → Contains publishing fields")
        
        return True
    else:
        print("❌ CourseAdmin fieldsets not properly configured")
        return False

def verify_ckeditor_config():
    """Verify CKEditor5 configuration"""
    print("\n⚙️ VERIFYING CKEDITOR5 CONFIGURATION")
    print("=" * 50)
    
    from django.conf import settings
    
    if hasattr(settings, 'CKEDITOR_5_CONFIGS'):
        configs = settings.CKEDITOR_5_CONFIGS
        print(f"✅ CKEditor5 configurations found: {list(configs.keys())}")
        
        if 'course_content' in configs:
            print("✅ course_content configuration exists")
            course_config = configs['course_content']
            
            if 'toolbar' in course_config:
                toolbar_items = course_config['toolbar'].get('items', [])
                print(f"✅ Toolbar configured with {len(toolbar_items)} items")
            
            return True
        else:
            print("❌ course_content configuration missing")
            return False
    else:
        print("❌ CKEDITOR_5_CONFIGS not found in settings")
        return False

def verify_payment_urls():
    """Verify payment URL patterns are fixed"""
    print("\n🔗 VERIFYING PAYMENT URL PATTERNS")
    print("=" * 50)
    
    # Check payment views for correct URL patterns
    with open('payments/views.py', 'r') as f:
        content = f.read()
    
    # Check for fixed patterns
    if "redirect('courses:course_detail', slug=course.slug)" in content:
        print("✅ Payment views use correct slug parameter")
        return True
    elif "redirect('courses:course_detail', course_id=course.id)" in content:
        print("❌ Payment views still use incorrect course_id parameter")
        return False
    else:
        print("✅ No problematic redirect patterns found")
        return True

def verify_tinymce_removal():
    """Verify TinyMCE references have been removed"""
    print("\n🔍 VERIFYING TINYMCE REMOVAL")
    print("=" * 50)
    
    template_files = [
        'templates/course_builder/wizard.html',
        'templates/course_builder/content_templates.html'
    ]
    
    tinymce_found = False
    
    for template_file in template_files:
        if os.path.exists(template_file):
            with open(template_file, 'r') as f:
                content = f.read()
            
            if 'tinymce.init(' in content:
                print(f"❌ TinyMCE initialization still found in {template_file}")
                tinymce_found = True
            elif 'tinymce' in content.lower():
                print(f"⚠️ TinyMCE references found in {template_file} (may be comments)")
            else:
                print(f"✅ No TinyMCE found in {template_file}")
    
    return not tinymce_found

def test_course_status_update():
    """Test course status update functionality"""
    print("\n🧪 TESTING COURSE STATUS UPDATE")
    print("=" * 50)
    
    try:
        # Find the imported course
        course = Course.objects.get(slug='understanding-purpose-in-life-upl-101-complete')
        print(f"✅ Found test course: {course.title}")
        print(f"   Current status: {course.status}")
        print(f"   Current is_published: {course.is_published}")
        
        # Test status change
        original_status = course.status
        original_published = course.is_published
        
        # Try to change status to published
        course.status = 'published'
        course.save()
        
        # Reload from database
        course.refresh_from_db()
        
        if course.status == 'published':
            print("✅ Status successfully updated to 'published'")
            
            # Check if is_published was automatically set
            if course.is_published:
                print("✅ is_published automatically set to True")
            else:
                print("⚠️ is_published not automatically updated")
            
            # Restore original status for safety
            course.status = original_status
            course.is_published = original_published
            course.save()
            print(f"✅ Status restored to original: {original_status}")
            
            return True
        else:
            print(f"❌ Status update failed - still: {course.status}")
            return False
            
    except Course.DoesNotExist:
        print("❌ Test course not found")
        return False
    except Exception as e:
        print(f"❌ Error testing status update: {str(e)}")
        return False

def generate_admin_test_report():
    """Generate comprehensive admin test report"""
    print("\n📊 ADMIN CONFIGURATION TEST REPORT")
    print("=" * 60)
    
    tests = [
        ("Course Model Fields", verify_course_model_fields),
        ("Admin Fieldsets", verify_admin_fieldsets),
        ("CKEditor5 Configuration", verify_ckeditor_config),
        ("Payment URL Patterns", verify_payment_urls),
        ("TinyMCE Removal", verify_tinymce_removal),
        ("Course Status Update", test_course_status_update),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error in {test_name}: {str(e)}")
            results[test_name] = False
    
    # Summary
    print(f"\n📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {passed/total*100:.1f}%")
    
    print(f"\n📊 DETAILED RESULTS:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   Admin configuration is working correctly")
        print(f"   Course status updates should now work in Django admin")
        return True
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"   Please review failed tests above")
        return False

def main():
    """Main verification function"""
    print("🔍 YITP ADMIN CONFIGURATION VERIFICATION")
    print("=" * 80)
    
    success = generate_admin_test_report()
    
    if success:
        print(f"\n✅ VERIFICATION COMPLETE - ALL SYSTEMS WORKING")
        print(f"\n📝 NEXT STEPS:")
        print(f"   1. ✅ Django admin should now display course status field")
        print(f"   2. ✅ Course status changes should persist correctly")
        print(f"   3. ✅ Rich text editing available via CKEditor5")
        print(f"   4. ✅ Payment system URL errors resolved")
        print(f"   5. 🌐 Test in production admin interface")
    else:
        print(f"\n❌ VERIFICATION FAILED")
        print(f"   Some issues still need to be resolved")
    
    return success

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎯 Admin configuration verified and working!")
    else:
        print("\n⚠️ Please address remaining issues")
