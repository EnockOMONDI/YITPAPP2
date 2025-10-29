#!/usr/bin/env python3
"""
Fix Module Naming Inconsistency
Removes duplicate "Module X:" prefixes from module titles
"""

import os
import sys
import django
from django.db import transaction

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module

def fix_module_naming():
    """Fix module naming inconsistency by removing duplicate prefixes"""
    
    print("=== Module Naming Fix ===\n")
    
    try:
        # Get the YITP course
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        print(f"Found course: {course.title}")
        
        # Get all modules
        modules = Module.objects.filter(course=course).order_by('sort_order')
        
        print(f"\nCurrent module titles:")
        for module in modules:
            print(f"  Module {module.sort_order}: {module.title}")
        
        # Define the correct titles
        correct_titles = {
            1: "Understanding Purpose in Life (UPL)",
            2: "Personal Initiative & Assessments (Phase 1)", 
            3: "TPM 101 – The Power of Mindset",
            4: "Soft Skills for the Streets"  # Already correct
        }
        
        print(f"\nProposed changes:")
        changes_needed = []
        for module in modules:
            correct_title = correct_titles.get(module.sort_order)
            if correct_title and module.title != correct_title:
                print(f"  Module {module.sort_order}: '{module.title}' → '{correct_title}'")
                changes_needed.append((module, correct_title))
            else:
                print(f"  Module {module.sort_order}: '{module.title}' (no change needed)")
        
        if not changes_needed:
            print("\n✅ No changes needed - all module titles are correct!")
            return True
            
        # Confirm changes
        response = input(f"\nApply {len(changes_needed)} changes? (y/N): ")
        if response.lower() != 'y':
            print("Changes cancelled.")
            return False
        
        # Apply changes in a transaction
        with transaction.atomic():
            for module, new_title in changes_needed:
                old_title = module.title
                module.title = new_title
                module.save()
                print(f"✅ Updated Module {module.sort_order}: '{old_title}' → '{new_title}'")
        
        print(f"\n=== Final Module Titles ===")
        updated_modules = Module.objects.filter(course=course).order_by('sort_order')
        for module in updated_modules:
            lesson_count = module.lessons.count()
            print(f"  Module {module.sort_order}: {module.title} ({lesson_count} lessons)")
        
        return True
        
    except Course.DoesNotExist:
        print("ERROR: YITP course not found!")
        return False
    except Exception as e:
        print(f"Error during fix: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_module_naming()
    
    if success:
        print("\n✅ Module naming fix completed successfully!")
        print("\nNext steps:")
        print("1. Test the course detail page to verify consistent naming")
        print("2. Check that all modules display correctly")
    else:
        print("\n❌ Module naming fix failed!")
        print("Please check the error messages above and try again.")
