#!/usr/bin/env python3
"""
Investigate Lesson Content Styling
==================================

Analyze the styling used in the "Introduction to YITP: Your Learning Journey Begins" lesson
and prepare to apply it to other lessons in Course 6, Module 1.
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

class LessonStyleAnalyzer:
    def __init__(self):
        self.course_id = 6
        self.module_id = 14
        self.analysis_report = {
            'introduction_lesson': None,
            'other_lessons': [],
            'styling_analysis': {
                'inline_styles': [],
                'css_classes': [],
                'html_structure': [],
                'content_patterns': []
            },
            'recommendations': []
        }

    def find_introduction_lesson(self):
        """Find the Introduction to YITP lesson"""
        print("🔍 SEARCHING FOR INTRODUCTION LESSON")
        print("=" * 50)
        
        try:
            course = Course.objects.get(id=self.course_id)
            print(f"📚 Course: {course.title}")
            
            # Search for introduction lesson by title pattern
            intro_patterns = [
                "Introduction to YITP",
                "Your Learning Journey Begins",
                "Introduction",
                "Welcome"
            ]
            
            intro_lesson = None
            all_lessons = Lesson.objects.filter(module__course=course).order_by('module__sort_order', 'sort_order')
            
            print(f"📄 Total lessons in course: {all_lessons.count()}")
            print(f"\n📋 ALL LESSONS IN COURSE:")
            
            for lesson in all_lessons:
                print(f"   Lesson {lesson.id}: {lesson.title}")
                print(f"      Module: {lesson.module.title}")
                print(f"      Sort Order: {lesson.sort_order}")
                
                # Check if this matches introduction pattern
                for pattern in intro_patterns:
                    if pattern.lower() in lesson.title.lower():
                        intro_lesson = lesson
                        print(f"      ✅ FOUND INTRODUCTION LESSON!")
                        break
                print()
            
            if intro_lesson:
                self.analysis_report['introduction_lesson'] = {
                    'id': intro_lesson.id,
                    'title': intro_lesson.title,
                    'module': intro_lesson.module.title,
                    'content_length': len(intro_lesson.content) if intro_lesson.content else 0
                }
                print(f"✅ Introduction lesson found: {intro_lesson.title}")
                return intro_lesson
            else:
                print(f"❌ No introduction lesson found with patterns: {intro_patterns}")
                # Return first lesson as fallback
                first_lesson = all_lessons.first()
                if first_lesson:
                    print(f"📝 Using first lesson as reference: {first_lesson.title}")
                    self.analysis_report['introduction_lesson'] = {
                        'id': first_lesson.id,
                        'title': first_lesson.title,
                        'module': first_lesson.module.title,
                        'content_length': len(first_lesson.content) if first_lesson.content else 0
                    }
                    return first_lesson
                return None
                
        except Exception as e:
            print(f"❌ Error finding introduction lesson: {str(e)}")
            return None

    def analyze_lesson_content(self, lesson):
        """Analyze the HTML content and styling of a lesson"""
        print(f"\n🔍 ANALYZING LESSON CONTENT: {lesson.title}")
        print("=" * 60)
        
        if not lesson.content:
            print("❌ No content found in lesson")
            return None
        
        content = lesson.content
        print(f"📊 Content length: {len(content)} characters")
        
        # Extract inline styles
        inline_styles = re.findall(r'style="([^"]*)"', content, re.IGNORECASE)
        print(f"🎨 Inline styles found: {len(inline_styles)}")
        for i, style in enumerate(inline_styles[:5]):  # Show first 5
            print(f"   {i+1}. {style}")
        if len(inline_styles) > 5:
            print(f"   ... and {len(inline_styles) - 5} more")
        
        # Extract CSS classes
        css_classes = re.findall(r'class="([^"]*)"', content, re.IGNORECASE)
        unique_classes = set()
        for class_attr in css_classes:
            unique_classes.update(class_attr.split())
        
        print(f"📝 CSS classes found: {len(unique_classes)}")
        for cls in sorted(unique_classes):
            print(f"   - {cls}")
        
        # Extract HTML structure patterns
        html_tags = re.findall(r'<(\w+)[^>]*>', content, re.IGNORECASE)
        tag_counts = {}
        for tag in html_tags:
            tag_counts[tag.lower()] = tag_counts.get(tag.lower(), 0) + 1
        
        print(f"🏗️ HTML structure:")
        for tag, count in sorted(tag_counts.items()):
            print(f"   {tag}: {count}")
        
        # Look for specific YITP styling patterns
        yitp_patterns = [
            r'yitp[^"]*',
            r'color:\s*#ff5d15',
            r'color:\s*#1a2e53',
            r'background[^;]*#ff5d15',
            r'background[^;]*#1a2e53'
        ]
        
        print(f"🎯 YITP-specific patterns:")
        for pattern in yitp_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"   Pattern '{pattern}': {len(matches)} matches")
                for match in matches[:3]:
                    print(f"      - {match}")
        
        # Store analysis results
        analysis = {
            'lesson_id': lesson.id,
            'lesson_title': lesson.title,
            'content_length': len(content),
            'inline_styles': inline_styles,
            'css_classes': list(unique_classes),
            'html_tags': tag_counts,
            'yitp_patterns': []
        }
        
        # Extract first 500 characters as sample
        content_sample = content[:500] + "..." if len(content) > 500 else content
        print(f"\n📄 Content sample:")
        print("-" * 40)
        print(content_sample)
        print("-" * 40)
        
        return analysis

    def get_module_lessons(self):
        """Get all lessons in Module 1 for comparison"""
        print(f"\n📚 GETTING ALL LESSONS IN MODULE 1")
        print("=" * 50)
        
        try:
            module = Module.objects.get(id=self.module_id)
            lessons = Lesson.objects.filter(module=module).order_by('sort_order')
            
            print(f"📖 Module: {module.title}")
            print(f"📄 Total lessons: {lessons.count()}")
            
            lesson_data = []
            for lesson in lessons:
                lesson_info = {
                    'id': lesson.id,
                    'title': lesson.title,
                    'sort_order': lesson.sort_order,
                    'content_length': len(lesson.content) if lesson.content else 0,
                    'has_content': bool(lesson.content)
                }
                lesson_data.append(lesson_info)
                print(f"   Lesson {lesson.id}: {lesson.title}")
                print(f"      Content: {'Yes' if lesson.content else 'No'} ({lesson_info['content_length']} chars)")
            
            self.analysis_report['other_lessons'] = lesson_data
            return lessons
            
        except Exception as e:
            print(f"❌ Error getting module lessons: {str(e)}")
            return []

    def compare_lesson_styling(self, intro_lesson, other_lessons):
        """Compare styling between introduction lesson and others"""
        print(f"\n🔄 COMPARING LESSON STYLING")
        print("=" * 50)
        
        # Analyze introduction lesson
        intro_analysis = self.analyze_lesson_content(intro_lesson)
        if not intro_analysis:
            print("❌ Could not analyze introduction lesson")
            return
        
        print(f"\n📊 STYLING COMPARISON RESULTS:")
        print("-" * 40)
        
        # Compare with other lessons
        styling_differences = []
        for lesson in other_lessons:
            if lesson.id == intro_lesson.id:
                continue
                
            lesson_analysis = self.analyze_lesson_content(lesson)
            if not lesson_analysis:
                continue
            
            # Compare styling elements
            differences = {
                'lesson_id': lesson.id,
                'lesson_title': lesson.title,
                'missing_classes': set(intro_analysis['css_classes']) - set(lesson_analysis['css_classes']),
                'extra_classes': set(lesson_analysis['css_classes']) - set(intro_analysis['css_classes']),
                'style_count_diff': len(lesson_analysis['inline_styles']) - len(intro_analysis['inline_styles'])
            }
            
            styling_differences.append(differences)
            
            print(f"\n📝 {lesson.title}:")
            print(f"   Missing classes: {differences['missing_classes']}")
            print(f"   Extra classes: {differences['extra_classes']}")
            print(f"   Style count difference: {differences['style_count_diff']}")
        
        return styling_differences

    def generate_recommendations(self, intro_analysis, styling_differences):
        """Generate recommendations for applying consistent styling"""
        print(f"\n💡 GENERATING RECOMMENDATIONS")
        print("=" * 50)
        
        recommendations = []
        
        if intro_analysis and intro_analysis['css_classes']:
            recommendations.append({
                'type': 'css_classes',
                'action': 'Apply consistent CSS classes',
                'details': f"Add these classes to all lessons: {', '.join(intro_analysis['css_classes'])}"
            })
        
        if intro_analysis and intro_analysis['inline_styles']:
            recommendations.append({
                'type': 'inline_styles',
                'action': 'Standardize inline styling',
                'details': f"Apply consistent inline styles found in introduction lesson"
            })
        
        # Check if we need database updates
        needs_db_update = any(diff['missing_classes'] or diff['style_count_diff'] != 0 
                             for diff in styling_differences)
        
        if needs_db_update:
            recommendations.append({
                'type': 'database_update',
                'action': 'Update lesson content in database',
                'details': 'Modify lesson.content field to include consistent styling'
            })
        
        recommendations.append({
            'type': 'template_css',
            'action': 'Add template-level CSS',
            'details': 'Consider adding CSS classes to lesson detail template for consistent styling'
        })
        
        self.analysis_report['recommendations'] = recommendations
        
        print("📋 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec['action']}")
            print(f"      {rec['details']}")
        
        return recommendations

    def execute_analysis(self):
        """Execute the complete styling analysis"""
        print("🚀 LESSON STYLING ANALYSIS")
        print("=" * 60)
        
        # Find introduction lesson
        intro_lesson = self.find_introduction_lesson()
        if not intro_lesson:
            print("❌ Could not find introduction lesson")
            return False
        
        # Get all module lessons
        module_lessons = self.get_module_lessons()
        if not module_lessons:
            print("❌ Could not get module lessons")
            return False
        
        # Analyze introduction lesson content
        intro_analysis = self.analyze_lesson_content(intro_lesson)
        if not intro_analysis:
            print("❌ Could not analyze introduction lesson content")
            return False
        
        # Compare with other lessons
        styling_differences = self.compare_lesson_styling(intro_lesson, module_lessons)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(intro_analysis, styling_differences)
        
        # Generate report
        self.generate_analysis_report()
        
        return True

    def generate_analysis_report(self):
        """Generate comprehensive analysis report"""
        report_filename = f"lesson_styling_analysis_report.md"
        
        report_content = f"""# Lesson Styling Analysis Report

**Date:** {django.utils.timezone.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Course:** Youth Impact Training Programme (YITP)  
**Module:** Understanding Purpose in Life (UPL)  

## 🎯 Analysis Summary

**Introduction Lesson Found:** {self.analysis_report['introduction_lesson']['title'] if self.analysis_report['introduction_lesson'] else 'None'}  
**Total Lessons Analyzed:** {len(self.analysis_report['other_lessons'])}  

## 📊 Styling Analysis Results

### Introduction Lesson Details
- **ID:** {self.analysis_report['introduction_lesson']['id'] if self.analysis_report['introduction_lesson'] else 'N/A'}
- **Title:** {self.analysis_report['introduction_lesson']['title'] if self.analysis_report['introduction_lesson'] else 'N/A'}
- **Content Length:** {self.analysis_report['introduction_lesson']['content_length'] if self.analysis_report['introduction_lesson'] else 0} characters

### Other Lessons
{chr(10).join([f"- Lesson {lesson['id']}: {lesson['title']} ({lesson['content_length']} chars)" for lesson in self.analysis_report['other_lessons']])}

## 💡 Recommendations

{chr(10).join([f"{i}. **{rec['action']}**{chr(10)}   {rec['details']}" for i, rec in enumerate(self.analysis_report['recommendations'], 1)])}

## 🚀 Next Steps

1. **Review Analysis:** Examine the styling patterns found in the introduction lesson
2. **Choose Implementation:** Decide between database updates or template-level CSS
3. **Apply Styling:** Implement consistent styling across all lessons
4. **Test Results:** Verify styling consistency in production

---
**Status:** Analysis Complete
"""
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📄 Analysis report generated: {report_filename}")

if __name__ == "__main__":
    analyzer = LessonStyleAnalyzer()
    success = analyzer.execute_analysis()
    
    if success:
        print(f"\n🎉 LESSON STYLING ANALYSIS COMPLETED!")
        print(f"✅ Analysis report generated")
        print(f"✅ Recommendations provided")
    else:
        print(f"\n❌ ANALYSIS FAILED")
