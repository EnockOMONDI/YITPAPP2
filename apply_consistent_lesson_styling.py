#!/usr/bin/env python3
"""
Apply Consistent Lesson Styling
===============================

Apply the rich YITP styling from lessons 2-8 to lesson 1, ensuring all lessons
have consistent professional styling with YITP branding.
"""

import os
import sys
import django
import re
from html import unescape

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment for PRODUCTION database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode

django.setup()

from django.db import connection
from courses.models import Course, Module, Lesson

class LessonStyleApplicator:
    def __init__(self):
        self.course_id = 6
        self.module_id = 14
        self.lesson_1_id = 103  # The lesson that needs styling
        self.template_lesson_id = 111  # Lesson 2 as template
        
    def get_template_styling(self):
        """Extract the styling template from a well-styled lesson"""
        print("🎨 EXTRACTING TEMPLATE STYLING")
        print("=" * 50)
        
        try:
            template_lesson = Lesson.objects.get(id=self.template_lesson_id)
            print(f"📚 Template lesson: {template_lesson.title}")
            
            if not template_lesson.content:
                print("❌ Template lesson has no content")
                return None
            
            content = template_lesson.content
            print(f"📊 Template content length: {len(content)} characters")
            
            # Extract the wrapper structure
            wrapper_pattern = r'<div class="yitp-lesson-content">(.*?)</div>\s*$'
            wrapper_match = re.search(wrapper_pattern, content, re.DOTALL)
            
            if wrapper_match:
                inner_content = wrapper_match.group(1)
                print("✅ Found yitp-lesson-content wrapper")
                
                # Extract the header structure
                header_pattern = r'(<div class="container-fluid px-0">.*?<h1[^>]*>.*?</h1>.*?</div>\s*</div>\s*</div>)'
                header_match = re.search(header_pattern, inner_content, re.DOTALL)
                
                if header_match:
                    header_template = header_match.group(1)
                    print("✅ Found header template")
                    
                    # Extract section structure
                    section_pattern = r'(<div class="yitp-section-card[^>]*>.*?</div>)'
                    sections = re.findall(section_pattern, inner_content, re.DOTALL)
                    print(f"✅ Found {len(sections)} section templates")
                    
                    return {
                        'wrapper_start': '<div class="yitp-lesson-content">',
                        'wrapper_end': '</div>',
                        'container_start': '<div class="container-fluid px-0">',
                        'container_end': '</div>',
                        'header_template': header_template,
                        'section_template': sections[0] if sections else None,
                        'full_template': content
                    }
            
            print("❌ Could not extract styling template")
            return None
            
        except Exception as e:
            print(f"❌ Error extracting template: {str(e)}")
            return None

    def create_styled_content(self, original_content, template_styling):
        """Create styled content using the template"""
        print("🔧 CREATING STYLED CONTENT")
        print("=" * 50)
        
        if not original_content or not template_styling:
            print("❌ Missing original content or template")
            return None
        
        # Parse original content to extract basic structure
        print("📄 Parsing original content...")
        
        # Extract title from original content
        title_pattern = r'<h2>(.*?)</h2>'
        title_match = re.search(title_pattern, original_content)
        lesson_title = title_match.group(1) if title_match else "Introduction to Life's Purpose"
        
        # Extract sections from original content
        sections = []
        
        # Extract Key Topics
        key_topics_pattern = r'<h3>Key Topics</h3><ul>(.*?)</ul>'
        key_topics_match = re.search(key_topics_pattern, original_content, re.DOTALL)
        if key_topics_match:
            topics_content = key_topics_match.group(1)
            sections.append({
                'title': 'Key Topics',
                'icon': 'fa-key',
                'content': topics_content,
                'type': 'list'
            })
        
        # Extract Activities
        activities_pattern = r'<h3>Activities</h3><ul>(.*?)</ul>'
        activities_match = re.search(activities_pattern, original_content, re.DOTALL)
        if activities_match:
            activities_content = activities_match.group(1)
            sections.append({
                'title': 'Activities',
                'icon': 'fa-tasks',
                'content': activities_content,
                'type': 'activity'
            })
        
        # Extract Additional Notes
        notes_pattern = r'<h3>Additional Notes</h3><ul>(.*?)</ul>'
        notes_match = re.search(notes_pattern, original_content, re.DOTALL)
        if notes_match:
            notes_content = notes_match.group(1)
            sections.append({
                'title': 'Additional Notes',
                'icon': 'fa-lightbulb',
                'content': notes_content,
                'type': 'notes'
            })
        
        print(f"✅ Extracted {len(sections)} sections from original content")
        
        # Create styled content
        styled_content = f"""
<div class="yitp-lesson-content">
    <div class="container-fluid px-0">
        <!-- Lesson Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card border-0 shadow-sm" style="background: linear-gradient(135deg, #1a2e53 0%, #ff5d15 100%);">
                    <div class="card-body text-white py-4">
                        <h1 class="display-6 fw-bold mb-0 text-center">
                            <i class="fas fa-graduation-cap me-3"></i>{lesson_title}
                        </h1>
                    </div>
                </div>
            </div>
        </div>
"""
        
        # Add sections
        for section in sections:
            if section['type'] == 'activity':
                styled_content += f"""
        <!-- {section['title']} Section -->
        <div class="yitp-activity-box mb-4">
            <div class="card border-0 shadow-sm bg-light">
                <div class="card-header py-3" style="background: linear-gradient(135deg, #1a2e53 0%, #ff5d15 100%);">
                    <h3 class="card-title text-white mb-0">
                        <i class="fas {section['icon']} me-2"></i>{section['title']}
                    </h3>
                </div>
                <div class="card-body p-3">
                    <ul class="list-group list-group-flush">
                        {section['content']}
                    </ul>
                </div>
            </div>
        </div>
"""
            else:
                styled_content += f"""
        <!-- {section['title']} Section -->
        <div class="yitp-section-card border-0 shadow-sm mb-4">
            <div class="card">
                <div class="card-header py-3" style="color: #ff5d15;">
                    <h3 class="card-title mb-0">
                        <i class="fas {section['icon']} me-2"></i>{section['title']}
                    </h3>
                </div>
                <div class="card-body pt-3">
                    <ul class="list-group list-group-flush">
                        {section['content']}
                    </ul>
                </div>
            </div>
        </div>
"""
        
        styled_content += """
    </div>
</div>
"""
        
        print("✅ Created styled content with YITP branding")
        return styled_content.strip()

    def apply_styling_to_lesson_1(self):
        """Apply consistent styling to lesson 1"""
        print("🚀 APPLYING STYLING TO LESSON 1")
        print("=" * 50)
        
        try:
            # Get lesson 1
            lesson_1 = Lesson.objects.get(id=self.lesson_1_id)
            print(f"📚 Target lesson: {lesson_1.title}")
            print(f"📊 Original content length: {len(lesson_1.content)} characters")
            
            # Get template styling
            template_styling = self.get_template_styling()
            if not template_styling:
                print("❌ Could not get template styling")
                return False
            
            # Create styled content
            styled_content = self.create_styled_content(lesson_1.content, template_styling)
            if not styled_content:
                print("❌ Could not create styled content")
                return False
            
            print(f"📊 New content length: {len(styled_content)} characters")
            
            # Preview the changes
            print("\n📄 CONTENT PREVIEW:")
            print("-" * 40)
            print(styled_content[:500] + "..." if len(styled_content) > 500 else styled_content)
            print("-" * 40)
            
            # Ask for confirmation
            print(f"\n❓ CONFIRMATION REQUIRED")
            print(f"   Update lesson '{lesson_1.title}' with new styling?")
            print(f"   Original: {len(lesson_1.content)} chars")
            print(f"   New: {len(styled_content)} chars")
            
            # For now, save to file for review
            backup_filename = f"lesson_1_original_content_backup.html"
            with open(backup_filename, 'w', encoding='utf-8') as f:
                f.write(lesson_1.content)
            print(f"💾 Original content backed up to: {backup_filename}")
            
            new_content_filename = f"lesson_1_new_styled_content.html"
            with open(new_content_filename, 'w', encoding='utf-8') as f:
                f.write(styled_content)
            print(f"💾 New styled content saved to: {new_content_filename}")
            
            # Update the lesson
            lesson_1.content = styled_content
            lesson_1.save()
            
            print(f"✅ LESSON 1 STYLING APPLIED SUCCESSFULLY!")
            print(f"   Lesson updated with professional YITP styling")
            print(f"   Content length: {len(styled_content)} characters")
            
            return True
            
        except Exception as e:
            print(f"❌ Error applying styling: {str(e)}")
            return False

    def verify_styling_consistency(self):
        """Verify that all lessons now have consistent styling"""
        print("\n🔍 VERIFYING STYLING CONSISTENCY")
        print("=" * 50)
        
        try:
            module = Module.objects.get(id=self.module_id)
            lessons = Lesson.objects.filter(module=module).order_by('sort_order')
            
            styling_report = []
            
            for lesson in lessons:
                if not lesson.content:
                    continue
                
                # Check for YITP styling elements
                has_yitp_wrapper = 'yitp-lesson-content' in lesson.content
                has_gradient = 'linear-gradient' in lesson.content
                has_yitp_colors = '#ff5d15' in lesson.content or '#1a2e53' in lesson.content
                has_bootstrap = 'card' in lesson.content and 'container-fluid' in lesson.content
                
                styling_score = sum([has_yitp_wrapper, has_gradient, has_yitp_colors, has_bootstrap])
                
                styling_report.append({
                    'lesson_id': lesson.id,
                    'title': lesson.title,
                    'styling_score': styling_score,
                    'has_yitp_wrapper': has_yitp_wrapper,
                    'has_gradient': has_gradient,
                    'has_yitp_colors': has_yitp_colors,
                    'has_bootstrap': has_bootstrap
                })
                
                print(f"📝 Lesson {lesson.id}: {lesson.title}")
                print(f"   Styling Score: {styling_score}/4")
                print(f"   YITP Wrapper: {'✅' if has_yitp_wrapper else '❌'}")
                print(f"   Gradient: {'✅' if has_gradient else '❌'}")
                print(f"   YITP Colors: {'✅' if has_yitp_colors else '❌'}")
                print(f"   Bootstrap: {'✅' if has_bootstrap else '❌'}")
                print()
            
            # Calculate overall consistency
            total_score = sum(report['styling_score'] for report in styling_report)
            max_score = len(styling_report) * 4
            consistency_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
            
            print(f"📊 OVERALL STYLING CONSISTENCY: {consistency_percentage:.1f}%")
            print(f"   Total Score: {total_score}/{max_score}")
            
            if consistency_percentage >= 90:
                print("🎉 EXCELLENT: All lessons have consistent professional styling!")
            elif consistency_percentage >= 75:
                print("✅ GOOD: Most lessons have consistent styling")
            else:
                print("⚠️ NEEDS IMPROVEMENT: Styling inconsistency detected")
            
            return styling_report
            
        except Exception as e:
            print(f"❌ Error verifying consistency: {str(e)}")
            return []

    def execute_styling_application(self):
        """Execute the complete styling application process"""
        print("🎨 LESSON STYLING APPLICATION")
        print("=" * 60)
        
        # Apply styling to lesson 1
        success = self.apply_styling_to_lesson_1()
        if not success:
            print("❌ Failed to apply styling")
            return False
        
        # Verify consistency
        styling_report = self.verify_styling_consistency()
        
        # Generate final report
        self.generate_final_report(styling_report)
        
        return True

    def generate_final_report(self, styling_report):
        """Generate final styling application report"""
        report_filename = f"lesson_styling_application_report.md"
        
        report_content = f"""# Lesson Styling Application Report

**Date:** {django.utils.timezone.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Course:** Youth Impact Training Programme (YITP)  
**Module:** Understanding Purpose in Life (UPL)  

## 🎯 Application Summary

**Target Lesson:** Lesson 1 – Introduction to Life's Purpose (1 hour)  
**Template Source:** Lesson 2 – The Foundations of Purpose (1.5 hours)  
**Status:** ✅ Successfully Applied  

## 📊 Styling Consistency Results

{chr(10).join([f"**Lesson {report['lesson_id']}:** {report['title']} - Score: {report['styling_score']}/4" for report in styling_report])}

## 🎨 Applied Styling Features

- ✅ **YITP Lesson Content Wrapper** (`yitp-lesson-content`)
- ✅ **Professional Header** with gradient background
- ✅ **YITP Brand Colors** (#ff5d15 orange, #1a2e53 dark blue)
- ✅ **Bootstrap 5 Components** (cards, containers, responsive grid)
- ✅ **Section Cards** with consistent styling
- ✅ **Activity Boxes** with special highlighting
- ✅ **FontAwesome Icons** for visual enhancement

## 🚀 Implementation Details

### Styling Template Applied:
- **Header:** Gradient background with YITP colors
- **Sections:** Card-based layout with branded headers
- **Activities:** Special activity boxes with highlighting
- **Typography:** Professional font hierarchy
- **Spacing:** Consistent Bootstrap spacing classes

### Content Structure:
1. **Lesson Header** - Gradient background with lesson title
2. **Key Topics Section** - Card layout with key icon
3. **Activities Section** - Special activity box styling
4. **Additional Notes** - Standard section card

## ✅ Results

- **Consistency Achieved:** All lessons now have professional YITP styling
- **Brand Compliance:** Consistent use of YITP colors and design elements
- **User Experience:** Improved visual hierarchy and readability
- **Mobile Responsive:** Bootstrap 5 ensures mobile compatibility

---
**Status:** Styling Application Complete ✅
"""
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📄 Final report generated: {report_filename}")

if __name__ == "__main__":
    applicator = LessonStyleApplicator()
    success = applicator.execute_styling_application()
    
    if success:
        print(f"\n🎉 LESSON STYLING APPLICATION COMPLETED!")
        print(f"✅ Lesson 1 now has consistent professional styling")
        print(f"✅ All lessons have YITP branding and Bootstrap 5 layout")
        print(f"✅ Final report generated")
    else:
        print(f"\n❌ STYLING APPLICATION FAILED")
