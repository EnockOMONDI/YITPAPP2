#!/usr/bin/env python3
"""
Module 2 Phase 1 Validation Script
==================================

Comprehensive validation of the complete Module 2 Phase 1 JSON file
to ensure it's ready for production import.
"""

import json
import os
from datetime import datetime

class Module2Phase1Validator:
    def __init__(self, json_file):
        self.json_file = json_file
        self.validation_results = {
            'overall_status': 'UNKNOWN',
            'critical_issues': [],
            'warnings': [],
            'statistics': {},
            'recommendations': []
        }

    def load_and_parse_json(self):
        """Load and parse the JSON file"""
        print("📄 LOADING JSON FILE")
        print("=" * 50)
        
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            file_size = os.path.getsize(self.json_file)
            print(f"✅ JSON file loaded successfully")
            print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            return True
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            self.validation_results['critical_issues'].append(f"JSON parsing error: {e}")
            return False
        except FileNotFoundError:
            print(f"❌ File not found: {self.json_file}")
            self.validation_results['critical_issues'].append(f"File not found: {self.json_file}")
            return False

    def validate_module_structure(self):
        """Validate overall module structure"""
        print("\n🏗️ VALIDATING MODULE STRUCTURE")
        print("=" * 50)
        
        # Check required top-level fields
        required_fields = ['module_info', 'lessons', 'implementation_notes']
        for field in required_fields:
            if field not in self.data:
                self.validation_results['critical_issues'].append(f"Missing top-level field: {field}")
        
        # Validate module_info
        if 'module_info' in self.data:
            module_info = self.data['module_info']
            required_module_fields = ['id', 'title', 'total_lessons', 'estimated_duration_minutes']
            for field in required_module_fields:
                if field not in module_info:
                    self.validation_results['critical_issues'].append(f"Missing module_info field: {field}")
        
        # Validate lessons array
        if 'lessons' not in self.data:
            self.validation_results['critical_issues'].append("Missing lessons array")
        elif not isinstance(self.data['lessons'], list):
            self.validation_results['critical_issues'].append("Lessons must be an array")
        elif len(self.data['lessons']) == 0:
            self.validation_results['critical_issues'].append("No lessons found")
        
        print(f"📚 Module: {self.data.get('module_info', {}).get('title', 'Unknown')}")
        print(f"📖 Lessons: {len(self.data.get('lessons', []))}")
        
        return len(self.validation_results['critical_issues']) == 0

    def validate_lessons(self):
        """Validate all lessons"""
        print("\n📖 VALIDATING LESSONS")
        print("=" * 50)
        
        if 'lessons' not in self.data:
            return False
        
        lessons = self.data['lessons']
        lesson_ids = []
        total_content_size = 0
        
        for i, lesson in enumerate(lessons):
            lesson_num = i + 1
            print(f"\n📝 Validating Lesson {lesson_num}...")
            
            # Check required lesson fields
            required_lesson_fields = ['id', 'title', 'content_type', 'content', 'assessment']
            for field in required_lesson_fields:
                if field not in lesson:
                    self.validation_results['critical_issues'].append(f"Lesson {lesson_num} missing field: {field}")
            
            # Check for duplicate IDs
            lesson_id = lesson.get('id')
            if lesson_id in lesson_ids:
                self.validation_results['critical_issues'].append(f"Duplicate lesson ID: {lesson_id}")
            else:
                lesson_ids.append(lesson_id)
            
            # Validate content
            content = lesson.get('content', '')
            content_size = len(content)
            total_content_size += content_size
            
            if content_size == 0:
                self.validation_results['critical_issues'].append(f"Lesson {lesson_num} has empty content")
            elif content_size > 2000000:  # 2MB limit per lesson
                self.validation_results['warnings'].append(f"Lesson {lesson_num} has large content: {content_size:,} characters")
            
            # Validate assessment/quiz
            if 'assessment' in lesson and 'quiz' in lesson['assessment']:
                quiz = lesson['assessment']['quiz']
                self._validate_quiz(quiz, lesson_num)
            else:
                self.validation_results['critical_issues'].append(f"Lesson {lesson_num} missing quiz")
            
            print(f"   ✅ Lesson {lesson_num}: {lesson.get('title', 'Unknown')}")
            print(f"   📊 Content size: {content_size:,} characters")
        
        self.validation_results['statistics']['total_content_size'] = total_content_size
        self.validation_results['statistics']['average_content_size'] = total_content_size // len(lessons) if lessons else 0
        
        print(f"\n📊 Total content size: {total_content_size:,} characters")
        print(f"📊 Average per lesson: {self.validation_results['statistics']['average_content_size']:,} characters")
        
        return True

    def _validate_quiz(self, quiz, lesson_num):
        """Validate quiz structure"""
        required_quiz_fields = ['id', 'title', 'questions']
        for field in required_quiz_fields:
            if field not in quiz:
                self.validation_results['critical_issues'].append(f"Lesson {lesson_num} quiz missing field: {field}")
        
        # Validate questions
        questions = quiz.get('questions', [])
        if len(questions) == 0:
            self.validation_results['critical_issues'].append(f"Lesson {lesson_num} quiz has no questions")
        
        for q_num, question in enumerate(questions, 1):
            required_question_fields = ['question_text', 'question_type', 'correct_answer']
            for field in required_question_fields:
                if field not in question:
                    self.validation_results['critical_issues'].append(f"Lesson {lesson_num} question {q_num} missing field: {field}")
            
            # Validate question types
            valid_types = ['multiple_choice', 'true_false', 'short_answer', 'essay']
            q_type = question.get('question_type')
            if q_type not in valid_types:
                self.validation_results['critical_issues'].append(f"Lesson {lesson_num} question {q_num} invalid type: {q_type}")
            
            # Validate multiple choice options
            if q_type == 'multiple_choice' and 'options' not in question:
                self.validation_results['critical_issues'].append(f"Lesson {lesson_num} question {q_num} missing options for multiple choice")

    def validate_content_quality(self):
        """Validate content quality and YITP compliance"""
        print("\n🎨 VALIDATING CONTENT QUALITY")
        print("=" * 50)
        
        yitp_indicators = 0
        responsive_indicators = 0
        
        for i, lesson in enumerate(self.data.get('lessons', []), 1):
            content = lesson.get('content', '')
            
            # Check for YITP styling
            if 'yitp-lesson-content' in content:
                yitp_indicators += 1
            
            # Check for responsive design
            if '@media' in content and 'max-width' in content:
                responsive_indicators += 1
            
            # Check for YITP brand colors
            if '#ff5d15' in content or '#1a2e53' in content:
                yitp_indicators += 1
        
        total_lessons = len(self.data.get('lessons', []))
        
        if yitp_indicators < total_lessons:
            self.validation_results['warnings'].append(f"Some lessons may be missing YITP styling")
        
        if responsive_indicators < total_lessons:
            self.validation_results['warnings'].append(f"Some lessons may not be mobile responsive")
        
        print(f"🎨 YITP styling indicators: {yitp_indicators}/{total_lessons}")
        print(f"📱 Responsive design indicators: {responsive_indicators}/{total_lessons}")

    def check_import_readiness(self):
        """Check if module is ready for production import"""
        print("\n🚀 CHECKING IMPORT READINESS")
        print("=" * 50)
        
        # Critical checks
        critical_passed = len(self.validation_results['critical_issues']) == 0
        
        # Performance checks
        total_size = self.validation_results['statistics'].get('total_content_size', 0)
        size_warning = total_size > 10000000  # 10MB total limit
        
        if size_warning:
            self.validation_results['warnings'].append(f"Large total content size: {total_size:,} characters")
        
        # Set overall status
        if critical_passed and not size_warning:
            self.validation_results['overall_status'] = 'READY'
        elif critical_passed:
            self.validation_results['overall_status'] = 'READY_WITH_WARNINGS'
        else:
            self.validation_results['overall_status'] = 'NOT_READY'
        
        # Generate recommendations
        if self.validation_results['overall_status'] == 'READY':
            self.validation_results['recommendations'] = [
                "✅ Module is ready for production import",
                "🔄 Proceed with database import",
                "📊 Monitor performance after deployment",
                "👥 Conduct user acceptance testing"
            ]
        elif self.validation_results['overall_status'] == 'READY_WITH_WARNINGS':
            self.validation_results['recommendations'] = [
                "⚠️ Module can be imported but monitor warnings",
                "📊 Test performance thoroughly",
                "🔍 Address warnings before full deployment",
                "👥 Limited user testing recommended"
            ]
        else:
            self.validation_results['recommendations'] = [
                "❌ Fix critical issues before import",
                "🔧 Review validation errors above",
                "🔄 Re-run validation after fixes",
                "⏸️ Do not proceed with import"
            ]

    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"module2_phase1_validation_report_{timestamp}.md"
        
        status_emoji = {
            'READY': '✅',
            'READY_WITH_WARNINGS': '⚠️',
            'NOT_READY': '❌'
        }
        
        report_content = f"""# Module 2 Phase 1 Validation Report

**Validation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**JSON File:** {self.json_file}  
**Overall Status:** {status_emoji.get(self.validation_results['overall_status'], '❓')} {self.validation_results['overall_status']}

## 📊 Validation Summary

### Critical Issues: {len(self.validation_results['critical_issues'])}
{chr(10).join([f"❌ {issue}" for issue in self.validation_results['critical_issues']]) if self.validation_results['critical_issues'] else "✅ No critical issues found"}

### Warnings: {len(self.validation_results['warnings'])}
{chr(10).join([f"⚠️ {warning}" for warning in self.validation_results['warnings']]) if self.validation_results['warnings'] else "✅ No warnings"}

## 📈 Statistics

- **Total Content Size:** {self.validation_results['statistics'].get('total_content_size', 0):,} characters
- **Average Lesson Size:** {self.validation_results['statistics'].get('average_content_size', 0):,} characters
- **Total Lessons:** {len(self.data.get('lessons', []))}
- **Module Duration:** {self.data.get('module_info', {}).get('estimated_duration_minutes', 0)} minutes

## 🎯 Recommendations

{chr(10).join([f"- {rec}" for rec in self.validation_results['recommendations']])}

## 📋 Next Steps

Based on the validation status: **{self.validation_results['overall_status']}**

{'### ✅ PROCEED WITH IMPORT' if self.validation_results['overall_status'] == 'READY' else '### ⚠️ REVIEW BEFORE IMPORT' if self.validation_results['overall_status'] == 'READY_WITH_WARNINGS' else '### ❌ FIX ISSUES BEFORE IMPORT'}

---
**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_filename

    def run_complete_validation(self):
        """Run complete validation process"""
        print("🔍 MODULE 2 PHASE 1 VALIDATION")
        print("=" * 60)
        
        # Step 1: Load JSON
        if not self.load_and_parse_json():
            return False
        
        # Step 2: Validate structure
        self.validate_module_structure()
        
        # Step 3: Validate lessons
        self.validate_lessons()
        
        # Step 4: Validate content quality
        self.validate_content_quality()
        
        # Step 5: Check import readiness
        self.check_import_readiness()
        
        # Step 6: Generate report
        report_file = self.generate_validation_report()
        
        # Print final results
        print(f"\n🎯 VALIDATION COMPLETED")
        print("=" * 60)
        print(f"📊 Overall Status: {self.validation_results['overall_status']}")
        print(f"❌ Critical Issues: {len(self.validation_results['critical_issues'])}")
        print(f"⚠️ Warnings: {len(self.validation_results['warnings'])}")
        print(f"📄 Report: {report_file}")
        
        if self.validation_results['overall_status'] == 'READY':
            print(f"\n🎉 MODULE IS READY FOR PRODUCTION IMPORT!")
        elif self.validation_results['overall_status'] == 'READY_WITH_WARNINGS':
            print(f"\n⚠️ MODULE CAN BE IMPORTED BUT REVIEW WARNINGS")
        else:
            print(f"\n❌ MODULE NOT READY - FIX CRITICAL ISSUES")
        
        return self.validation_results['overall_status'] in ['READY', 'READY_WITH_WARNINGS']

if __name__ == "__main__":
    import sys
    
    # Find the most recent module file
    json_files = [f for f in os.listdir('.') if f.startswith('module2_phase1_complete_') and f.endswith('.json')]
    
    if not json_files:
        print("❌ No Module 2 Phase 1 JSON files found")
        sys.exit(1)
    
    # Use the most recent file
    latest_file = sorted(json_files)[-1]
    print(f"🎯 Validating: {latest_file}")
    
    validator = Module2Phase1Validator(latest_file)
    success = validator.run_complete_validation()
    
    sys.exit(0 if success else 1)
