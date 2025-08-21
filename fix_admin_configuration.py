#!/usr/bin/env python
"""
Fix Django admin configuration issues:
1. Remove duplicate fieldsets in CourseAdmin
2. Update Course model to use CKEditor5Field for rich text fields
3. Remove TinyMCE references from course builder templates
4. Fix payment system URL pattern mismatch
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

def analyze_admin_issues():
    """Analyze current admin configuration issues"""
    print("🔍 ANALYZING ADMIN CONFIGURATION ISSUES")
    print("=" * 60)
    
    issues_found = []
    
    # Check CourseAdmin fieldsets
    print("📋 Checking CourseAdmin configuration...")
    with open('courses/admin.py', 'r') as f:
        admin_content = f.read()
    
    # Count fieldsets definitions
    fieldsets_count = admin_content.count('fieldsets = (')
    if fieldsets_count > 1:
        issues_found.append("❌ DUPLICATE FIELDSETS: CourseAdmin has multiple fieldsets definitions")
        print(f"   Found {fieldsets_count} fieldsets definitions in CourseAdmin")
    else:
        print("   ✅ CourseAdmin fieldsets configuration looks correct")
    
    # Check if status field is in fieldsets
    if "'status'" in admin_content:
        print("   ✅ Status field found in admin configuration")
    else:
        issues_found.append("❌ MISSING STATUS FIELD: Status field not found in admin fieldsets")
    
    # Check Course model fields
    print("\n📝 Checking Course model field types...")
    with open('courses/models.py', 'r') as f:
        model_content = f.read()
    
    # Check for CKEditor5Field usage
    if 'CKEditor5Field' in model_content:
        print("   ✅ CKEditor5Field imported in Course model")
        
        # Check specific fields
        if 'description = models.TextField()' in model_content:
            issues_found.append("❌ PLAIN TEXTFIELD: Course description should use CKEditor5Field")
        
        if 'learning_objectives = models.TextField(' in model_content:
            issues_found.append("❌ PLAIN TEXTFIELD: Course learning_objectives should use CKEditor5Field")
    else:
        issues_found.append("❌ MISSING CKEDITOR5: CKEditor5Field not imported in Course model")
    
    # Check for TinyMCE references
    print("\n🔍 Checking for TinyMCE references...")
    tinymce_files = []
    
    # Check course builder templates
    template_files = [
        'templates/course_builder/wizard.html',
        'templates/course_builder/content_templates.html'
    ]
    
    for template_file in template_files:
        if os.path.exists(template_file):
            with open(template_file, 'r') as f:
                content = f.read()
                if 'tinymce' in content.lower():
                    tinymce_files.append(template_file)
    
    if tinymce_files:
        issues_found.append(f"❌ TINYMCE REFERENCES: Found TinyMCE in {len(tinymce_files)} template files")
        for file in tinymce_files:
            print(f"   TinyMCE found in: {file}")
    else:
        print("   ✅ No TinyMCE references found in templates")
    
    # Check payment URL pattern issue
    print("\n🔗 Checking payment URL patterns...")
    with open('payments/views.py', 'r') as f:
        payment_views = f.read()
    
    if "redirect('courses:course_detail', course_id=course.id)" in payment_views:
        issues_found.append("❌ URL PATTERN MISMATCH: Payment views using course_id instead of slug")
        print("   Found course_id parameter usage in payment views")
    else:
        print("   ✅ Payment URL patterns look correct")
    
    # Summary
    print(f"\n📊 ANALYSIS SUMMARY:")
    print(f"   Total Issues Found: {len(issues_found)}")
    
    if issues_found:
        print(f"\n🚨 ISSUES IDENTIFIED:")
        for issue in issues_found:
            print(f"   {issue}")
    else:
        print(f"\n✅ No configuration issues found!")
    
    return issues_found

def fix_course_admin_fieldsets():
    """Fix duplicate fieldsets in CourseAdmin"""
    print("\n🔧 FIXING COURSE ADMIN FIELDSETS")
    print("=" * 60)
    
    # Read current admin.py
    with open('courses/admin.py', 'r') as f:
        content = f.read()
    
    # Find and remove the duplicate fieldsets (lines 219-236)
    lines = content.split('\n')
    
    # Find the second fieldsets definition and remove it
    in_second_fieldsets = False
    start_line = None
    end_line = None
    
    for i, line in enumerate(lines):
        # Look for the second fieldsets definition (after line 200)
        if i > 200 and 'fieldsets = (' in line and not in_second_fieldsets:
            in_second_fieldsets = True
            start_line = i
        elif in_second_fieldsets and line.strip() == ')' and start_line is not None:
            end_line = i
            break
    
    if start_line is not None and end_line is not None:
        # Remove the duplicate fieldsets
        new_lines = lines[:start_line] + lines[end_line+1:]
        new_content = '\n'.join(new_lines)
        
        # Write back to file
        with open('courses/admin.py', 'w') as f:
            f.write(new_content)
        
        print(f"✅ Removed duplicate fieldsets (lines {start_line+1}-{end_line+1})")
        return True
    else:
        print("❌ Could not locate duplicate fieldsets to remove")
        return False

def update_course_model_fields():
    """Update Course model to use CKEditor5Field for rich text fields"""
    print("\n📝 UPDATING COURSE MODEL FIELDS")
    print("=" * 60)
    
    # Read current models.py
    with open('courses/models.py', 'r') as f:
        content = f.read()
    
    # Replace TextField with CKEditor5Field for description and learning_objectives
    replacements = [
        {
            'old': 'description = models.TextField()',
            'new': '''description = CKEditor5Field(
        'Description',
        config_name='course_content',
        blank=True,
        help_text="Rich text course description with formatting and media"
    )'''
        },
        {
            'old': 'learning_objectives = models.TextField(help_text="What students will learn")',
            'new': '''learning_objectives = CKEditor5Field(
        'Learning Objectives',
        config_name='course_content',
        blank=True,
        help_text="What students will learn - use rich text formatting"
    )'''
        }
    ]
    
    updated = False
    for replacement in replacements:
        if replacement['old'] in content:
            content = content.replace(replacement['old'], replacement['new'])
            updated = True
            print(f"✅ Updated: {replacement['old'].split('=')[0].strip()}")
    
    if updated:
        # Write back to file
        with open('courses/models.py', 'w') as f:
            f.write(content)
        print("✅ Course model fields updated to use CKEditor5Field")
        return True
    else:
        print("❌ No Course model fields needed updating")
        return False

def fix_payment_url_patterns():
    """Fix payment system URL pattern mismatches"""
    print("\n🔗 FIXING PAYMENT URL PATTERNS")
    print("=" * 60)
    
    # Read payment views
    with open('payments/views.py', 'r') as f:
        content = f.read()
    
    # Replace course_id with slug in redirects
    replacements = [
        {
            'old': "return redirect('courses:course_detail', course_id=course.id)",
            'new': "return redirect('courses:course_detail', slug=course.slug)"
        }
    ]
    
    updated = False
    for replacement in replacements:
        if replacement['old'] in content:
            content = content.replace(replacement['old'], replacement['new'])
            updated = True
            print(f"✅ Fixed URL pattern: course_id → slug")
    
    if updated:
        # Write back to file
        with open('payments/views.py', 'w') as f:
            f.write(content)
        print("✅ Payment URL patterns fixed")
        return True
    else:
        print("❌ No payment URL patterns needed fixing")
        return False

def update_ckeditor_config():
    """Update CKEditor5 configuration for course content"""
    print("\n⚙️ UPDATING CKEDITOR5 CONFIGURATION")
    print("=" * 60)
    
    # Read current settings
    with open('blog/settings.py', 'r') as f:
        content = f.read()
    
    # Check if course_content config exists
    if "'course_content'" not in content:
        # Add course_content configuration
        ckeditor_config = '''
    'course_content': {
        'toolbar': {
            'items': [
                'heading', '|',
                'bold', 'italic', 'underline', '|',
                'fontColor', 'fontBackgroundColor', '|',
                'alignment', '|',
                'numberedList', 'bulletedList', '|',
                'outdent', 'indent', '|',
                'link', 'insertImage', 'insertTable', '|',
                'blockQuote', 'codeBlock', '|',
                'undo', 'redo'
            ]
        },
        'language': 'en',
        'image': {
            'toolbar': [
                'imageTextAlternative', 'imageStyle:full', 'imageStyle:side'
            ]
        },
        'table': {
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells'
            ]
        },
        'height': 300,
    },'''
        
        # Find the CKEDITOR_5_CONFIGS section and add the new config
        if 'CKEDITOR_5_CONFIGS = {' in content:
            # Insert after the opening brace
            insert_pos = content.find('CKEDITOR_5_CONFIGS = {') + len('CKEDITOR_5_CONFIGS = {')
            new_content = content[:insert_pos] + ckeditor_config + content[insert_pos:]
            
            with open('blog/settings.py', 'w') as f:
                f.write(new_content)
            
            print("✅ Added course_content configuration to CKEditor5")
            return True
    else:
        print("✅ CKEditor5 course_content configuration already exists")
        return False

def generate_migration():
    """Generate migration for Course model field changes"""
    print("\n📦 GENERATING MIGRATION")
    print("=" * 60)
    
    try:
        import subprocess
        result = subprocess.run(
            ['python', 'manage.py', 'makemigrations', 'courses'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print("✅ Migration generated successfully")
            print(f"   Output: {result.stdout}")
            return True
        else:
            print(f"❌ Migration generation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error generating migration: {str(e)}")
        return False

def main():
    """Main function to fix all admin configuration issues"""
    print("🔧 YITP ADMIN CONFIGURATION FIX")
    print("=" * 80)
    
    # Analyze current issues
    issues = analyze_admin_issues()
    
    if not issues:
        print("\n🎉 No issues found - admin configuration is correct!")
        return True
    
    print(f"\n🛠️ APPLYING FIXES FOR {len(issues)} ISSUES")
    print("=" * 60)
    
    fixes_applied = []
    
    # Fix CourseAdmin fieldsets
    if any('DUPLICATE FIELDSETS' in issue for issue in issues):
        if fix_course_admin_fieldsets():
            fixes_applied.append("CourseAdmin fieldsets")
    
    # Update Course model fields
    if any('PLAIN TEXTFIELD' in issue for issue in issues):
        if update_course_model_fields():
            fixes_applied.append("Course model fields")
            
            # Update CKEditor config
            if update_ckeditor_config():
                fixes_applied.append("CKEditor5 configuration")
            
            # Generate migration
            if generate_migration():
                fixes_applied.append("Database migration")
    
    # Fix payment URL patterns
    if any('URL PATTERN MISMATCH' in issue for issue in issues):
        if fix_payment_url_patterns():
            fixes_applied.append("Payment URL patterns")
    
    # Summary
    print(f"\n📊 FIX SUMMARY")
    print("=" * 60)
    print(f"   Issues Found: {len(issues)}")
    print(f"   Fixes Applied: {len(fixes_applied)}")
    
    if fixes_applied:
        print(f"\n✅ FIXES APPLIED:")
        for fix in fixes_applied:
            print(f"   • {fix}")
        
        print(f"\n📝 NEXT STEPS:")
        print(f"   1. Run migration: python manage.py migrate")
        print(f"   2. Restart Django server")
        print(f"   3. Test course status updates in admin")
        print(f"   4. Verify rich text editing works")
        
        return True
    else:
        print(f"\n❌ No fixes could be applied automatically")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎉 Admin configuration fixes completed!")
    else:
        print("\n⚠️ Some issues may require manual intervention")
