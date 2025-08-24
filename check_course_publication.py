#!/usr/bin/env python
"""
Check Course Publication Status
"""

import os
import django

# Setup production environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'
django.setup()

from courses.models import Course

print("🔍 CHECKING COURSE PUBLICATION STATUS - PRODUCTION")
print("=" * 60)

course = Course.objects.filter(title='Youth Impact Training Programme (YITP)').first()

if course:
    print(f"✅ Course Found: {course.title}")
    print(f"   ID: {course.id}")
    print(f"   Slug: {course.slug}")
    print(f"   Status: {course.status}")
    print(f"   Is Published: {course.is_published}")
    print(f"   Is Featured: {course.is_featured}")
    print(f"   Instructor: {course.instructor.username}")
    print(f"   Price: ${course.price}")
    print()
    
    print("📊 PUBLICATION STATUS:")
    if course.is_published:
        print("✅ Course IS PUBLISHED - Visible to students")
        print("   Students can enroll and access the course")
    else:
        print("❌ Course IS NOT PUBLISHED - Not visible to students")
        print(f"   Current Status: {course.status}")
        print("   To publish the course:")
        print("   1. Set is_published = True")
        print("   2. Set status = 'published'")
        print()
        print("🔧 QUICK PUBLISH COMMAND:")
        print("   Use Django admin or run:")
        print(f"   course.is_published = True")
        print(f"   course.status = 'published'")
        print(f"   course.save()")
    
    print()
    print("🔗 COURSE ACCESS:")
    print(f"   Public URL: https://www.youthimpactglobal.com/lms/courses/{course.slug}/")
    print(f"   Admin URL: https://www.youthimpactglobal.com/admin/courses/course/{course.id}/change/")
    
else:
    print("❌ Course not found in production database")
