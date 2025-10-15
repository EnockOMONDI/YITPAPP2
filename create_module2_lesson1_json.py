#!/usr/bin/env python3
"""
Module 2 Lesson 1 JSON Creator
==============================

Creates a complete JSON structure for Module 2, Lesson 1 (Personal Initiative Fundamentals)
following the YITP LMS format and validation requirements.
"""

import json
import os
from datetime import datetime
from analyze_module2_html import Module2HTMLAnalyzer

class Module2Lesson1JSONCreator:
    def __init__(self):
        self.analyzer = Module2HTMLAnalyzer()
        self.lesson_data = None
        self.quiz_questions = None

    def extract_lesson_content(self):
        """Extract Lesson 1 content from HTML"""
        print("📖 EXTRACTING LESSON 1 CONTENT")
        print("=" * 50)
        
        # Extract lesson content
        self.lesson_data = self.analyzer.extract_lesson_content(1, 1, 9)
        if not self.lesson_data:
            print("❌ Failed to extract lesson content")
            return False
        
        # Generate quiz questions
        self.quiz_questions = self.analyzer.generate_quiz_questions(1, "Personal Initiative Fundamentals")
        if not self.quiz_questions:
            print("❌ Failed to generate quiz questions")
            return False
        
        print(f"✅ Content extracted: {self.lesson_data['pages_extracted']} pages")
        print(f"✅ Quiz questions generated: {len(self.quiz_questions)} questions")
        return True

    def create_lesson_json_structure(self):
        """Create complete JSON structure for Lesson 1"""
        print("\n🏗️ CREATING JSON STRUCTURE")
        print("=" * 50)
        
        # Base lesson structure following YITP format
        lesson_json = {
            "id": 118,  # Next lesson ID after Module 1 (103, 111-117)
            "title": "Lesson 1 – Personal Initiative Fundamentals (1 hour)",
            "content_type": "text",
            "learning_objectives": "Understand the concept of Personal Initiative; Identify key characteristics of proactive behavior; Recognize the importance of self-directed action in personal and professional development",
            "estimated_duration": 60,
            "sort_order": 1,
            "is_published": True,
            "is_mandatory": True,
            "content": self._wrap_content_with_yitp_styling(self.lesson_data['html_content']),
            "assessment": {
                "quiz": {
                    "id": 118,
                    "title": "Personal Initiative Fundamentals Quiz",
                    "lesson_id": 118,
                    "passing_score": 70,
                    "max_attempts": 15,
                    "time_limit": None,
                    "is_published": True,
                    "questions": self.quiz_questions
                }
            }
        }
        
        print(f"✅ JSON structure created for Lesson {lesson_json['id']}")
        print(f"📝 Content size: {len(lesson_json['content']):,} characters")
        print(f"❓ Quiz questions: {len(lesson_json['assessment']['quiz']['questions'])}")
        
        return lesson_json

    def _wrap_content_with_yitp_styling(self, html_content):
        """Wrap HTML content with YITP styling framework"""
        
        # Enhanced YITP wrapper with better styling
        yitp_wrapper = f'''<div class="yitp-lesson-content">
    <div class="lesson-header mb-4">
        <div class="alert alert-info">
            <h4><i class="fas fa-lightbulb me-2" style="color: #ff5d15;"></i>Personal Initiative Fundamentals</h4>
            <p class="mb-0">Welcome to Module 2: Personal Initiative & Assessments. In this lesson, you'll discover the foundational concepts of Personal Initiative and learn how proactive behavior can transform your personal and professional life.</p>
        </div>
    </div>
    
    <div class="lesson-content-wrapper">
        <style>
        .yitp-lesson-content {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        
        .yitp-lesson-content .module2-personal-initiative {{
            background: #fff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        
        .yitp-lesson-content .lesson-slide {{
            margin: 30px 0;
            padding: 20px;
            border-left: 4px solid #ff5d15;
            background: #f8f9fa;
            border-radius: 0 8px 8px 0;
        }}
        
        .yitp-lesson-content .pf {{
            position: relative;
            margin: 15px 0;
            background: white;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .yitp-lesson-content .pc {{
            position: relative;
            padding: 10px;
        }}
        
        .yitp-lesson-content .t {{
            position: absolute;
            white-space: pre;
            font-size: 14px;
            line-height: 1.4;
        }}
        
        /* Responsive adjustments */
        @media (max-width: 768px) {{
            .yitp-lesson-content .lesson-slide {{
                margin: 15px 0;
                padding: 15px;
            }}
            
            .yitp-lesson-content .t {{
                font-size: 12px;
                position: relative !important;
                white-space: normal !important;
            }}
        }}
        
        /* YITP brand colors */
        .yitp-lesson-content .highlight {{
            background-color: #ff5d15;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        
        .yitp-lesson-content .secondary-highlight {{
            background-color: #1a2e53;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        </style>
        
        {html_content}
    </div>
    
    <div class="lesson-footer mt-4">
        <div class="alert alert-success">
            <h5><i class="fas fa-check-circle me-2" style="color: #28a745;"></i>Lesson Complete</h5>
            <p class="mb-0">You have completed the Personal Initiative Fundamentals lesson. Take the quiz below to test your understanding and proceed to the next lesson.</p>
        </div>
    </div>
</div>'''
        
        return yitp_wrapper

    def validate_json_structure(self, lesson_json):
        """Validate the JSON structure against YITP requirements"""
        print("\n✅ VALIDATING JSON STRUCTURE")
        print("=" * 50)
        
        validation_results = {
            'structure_valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Required fields validation
        required_fields = ['id', 'title', 'content_type', 'content', 'assessment']
        for field in required_fields:
            if field not in lesson_json:
                validation_results['issues'].append(f"Missing required field: {field}")
                validation_results['structure_valid'] = False
        
        # Quiz validation
        if 'assessment' in lesson_json and 'quiz' in lesson_json['assessment']:
            quiz = lesson_json['assessment']['quiz']
            quiz_required = ['id', 'title', 'questions']
            for field in quiz_required:
                if field not in quiz:
                    validation_results['issues'].append(f"Missing required quiz field: {field}")
                    validation_results['structure_valid'] = False
            
            # Validate questions
            if 'questions' in quiz:
                for i, question in enumerate(quiz['questions']):
                    question_required = ['question_text', 'question_type', 'correct_answer']
                    for field in question_required:
                        if field not in question:
                            validation_results['issues'].append(f"Question {i+1} missing field: {field}")
                            validation_results['structure_valid'] = False
        
        # Content size check
        content_size = len(lesson_json.get('content', ''))
        if content_size > 1000000:  # 1MB limit
            validation_results['warnings'].append(f"Large content size: {content_size:,} characters")
        
        # Print validation results
        if validation_results['structure_valid']:
            print("✅ JSON structure validation PASSED")
        else:
            print("❌ JSON structure validation FAILED")
            for issue in validation_results['issues']:
                print(f"   • {issue}")
        
        if validation_results['warnings']:
            print("⚠️ Warnings:")
            for warning in validation_results['warnings']:
                print(f"   • {warning}")
        
        return validation_results

    def save_lesson_json(self, lesson_json):
        """Save the lesson JSON to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"module2_lesson1_personal_initiative_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(lesson_json, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(filename)
            print(f"\n💾 LESSON JSON SAVED")
            print(f"📁 File: {filename}")
            print(f"📊 Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            return filename
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")
            return None

    def create_complete_lesson(self):
        """Execute complete lesson creation process"""
        print("🚀 MODULE 2 LESSON 1 JSON CREATION")
        print("=" * 60)
        
        # Step 1: Extract content
        if not self.extract_lesson_content():
            return False
        
        # Step 2: Create JSON structure
        lesson_json = self.create_lesson_json_structure()
        if not lesson_json:
            return False
        
        # Step 3: Validate structure
        validation = self.validate_json_structure(lesson_json)
        if not validation['structure_valid']:
            print("❌ Validation failed - cannot proceed")
            return False
        
        # Step 4: Save to file
        filename = self.save_lesson_json(lesson_json)
        if not filename:
            return False
        
        print(f"\n🎉 LESSON 1 JSON CREATION COMPLETED!")
        print(f"📄 File: {filename}")
        print(f"✅ Ready for import validation")
        
        return True

if __name__ == "__main__":
    creator = Module2Lesson1JSONCreator()
    success = creator.create_complete_lesson()
    
    if success:
        print(f"\n✅ SUCCESS: Lesson 1 JSON created and validated")
        print(f"🔄 Next step: Run import validation script")
    else:
        print(f"\n❌ FAILED: Review errors above")
