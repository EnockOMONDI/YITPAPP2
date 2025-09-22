#!/usr/bin/env python3
"""
YITP JSON Schema Validator
Validates generated course JSON against YITP LMS requirements

Usage:
python json_schema_validator.py --input pi_training_module2.json
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime


class YITPJSONValidator:
    """Validates YITP course JSON structure and content"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Define required fields and their types
        self.schema = {
            'course_level': {
                'required_fields': {
                    'session_id': str,
                    'course_title': str,
                    'course_description': str,
                    'course_category': str,
                    'difficulty_level': str,
                    'estimated_duration': (int, float),
                    'price': (int, float),
                    'currency': str,
                    'weeks': int,
                    'total_sessions': int,
                    'modules': list,
                    'created_at': str,
                    'status': str
                },
                'optional_fields': {
                    'prerequisites': str,
                    'learning_outcomes': str,
                    'instructor': str,
                    'thumbnail_url': str
                }
            },
            'module_level': {
                'required_fields': {
                    'title': str,
                    'description': str,
                    'lessons': list
                },
                'optional_fields': {
                    'week': int,
                    'sort_order': int,
                    'unlock_criteria': dict,
                    'estimated_duration': int
                }
            },
            'lesson_level': {
                'required_fields': {
                    'id': str,
                    'title': str,
                    'content_type': str,
                    'estimated_duration': int,
                    'learning_objectives': str,
                    'primary_content': str,
                    'sort_order': int,
                    'is_preview': bool
                },
                'optional_fields': {
                    'additional_resources': list,
                    'assessment': dict,
                    'video_url': str,
                    'document_url': str,
                    'audio_url': str
                }
            },
            'quiz_level': {
                'required_fields': {
                    'title': str,
                    'description': str,
                    'instructions': str,
                    'max_attempts': int,
                    'passing_score': int,
                    'is_randomized': bool,
                    'show_results': bool,
                    'questions': list
                },
                'optional_fields': {
                    'time_limit': (int, type(None)),
                    'category': str
                }
            },
            'question_level': {
                'required_fields': {
                    'question_text': str,
                    'question_type': str,
                    'correct_answer': str,
                    'points': (int, float),
                    'explanation': str,
                    'sort_order': int
                },
                'optional_fields': {
                    'options': list,
                    'difficulty': str,
                    'category': str
                }
            }
        }
        
        # Valid values for specific fields
        self.valid_values = {
            'difficulty_level': ['beginner', 'intermediate', 'advanced'],
            'content_type': ['text', 'video', 'document', 'audio', 'presentation', 'exercise', 'enhanced'],
            'question_type': ['true_false', 'multiple_choice', 'short_answer', 'essay', 'matching'],
            'status': ['draft', 'in_review', 'approved', 'published'],
            'currency': ['USD', 'EUR', 'GBP', 'KES']
        }
    
    def validate_json_structure(self, data: Dict) -> bool:
        """Validate the overall JSON structure"""
        self.info.append("🔍 Starting JSON structure validation...")
        
        # Validate course level
        if not self._validate_level(data, 'course_level', 'Course'):
            return False
        
        # Validate modules
        if 'modules' not in data or not isinstance(data['modules'], list):
            self.errors.append("❌ 'modules' field is required and must be a list")
            return False
        
        if len(data['modules']) == 0:
            self.errors.append("❌ At least one module is required")
            return False
        
        # Validate each module
        for i, module in enumerate(data['modules']):
            if not self._validate_level(module, 'module_level', f'Module {i+1}'):
                return False
            
            # Validate lessons in module
            if 'lessons' not in module or not isinstance(module['lessons'], list):
                self.errors.append(f"❌ Module {i+1}: 'lessons' field is required and must be a list")
                return False
            
            if len(module['lessons']) == 0:
                self.errors.append(f"❌ Module {i+1}: At least one lesson is required")
                return False
            
            # Validate each lesson
            for j, lesson in enumerate(module['lessons']):
                if not self._validate_level(lesson, 'lesson_level', f'Module {i+1}, Lesson {j+1}'):
                    return False
                
                # Validate assessment if present
                if 'assessment' in lesson and lesson['assessment']:
                    if 'quiz' in lesson['assessment']:
                        quiz = lesson['assessment']['quiz']
                        if not self._validate_level(quiz, 'quiz_level', f'Module {i+1}, Lesson {j+1} Quiz'):
                            return False
                        
                        # Validate questions
                        if 'questions' in quiz and isinstance(quiz['questions'], list):
                            for k, question in enumerate(quiz['questions']):
                                if not self._validate_level(question, 'question_level', 
                                                          f'Module {i+1}, Lesson {j+1}, Question {k+1}'):
                                    return False
        
        self.info.append("✅ JSON structure validation completed")
        return True
    
    def _validate_level(self, data: Dict, level: str, context: str) -> bool:
        """Validate a specific level of the JSON structure"""
        schema_level = self.schema[level]
        
        # Check required fields
        for field, expected_type in schema_level['required_fields'].items():
            if field not in data:
                self.errors.append(f"❌ {context}: Missing required field '{field}'")
                return False
            
            if not isinstance(data[field], expected_type):
                self.errors.append(f"❌ {context}: Field '{field}' must be of type {expected_type.__name__}")
                return False
        
        # Check field values against valid options
        for field, value in data.items():
            if field in self.valid_values:
                if value not in self.valid_values[field]:
                    self.errors.append(f"❌ {context}: Invalid value '{value}' for field '{field}'. "
                                     f"Valid options: {self.valid_values[field]}")
                    return False
        
        return True
    
    def validate_content_quality(self, data: Dict) -> bool:
        """Validate content quality and completeness"""
        self.info.append("🔍 Starting content quality validation...")
        
        # Check course-level content
        if len(data.get('course_title', '')) < 10:
            self.warnings.append("⚠️ Course title is very short (< 10 characters)")
        
        if len(data.get('course_description', '')) < 50:
            self.warnings.append("⚠️ Course description is very short (< 50 characters)")
        
        # Check module and lesson content
        total_lessons = 0
        total_duration = 0
        
        for i, module in enumerate(data.get('modules', [])):
            module_lessons = len(module.get('lessons', []))
            total_lessons += module_lessons
            
            if module_lessons < 3:
                self.warnings.append(f"⚠️ Module {i+1} has only {module_lessons} lessons (recommended: 3+)")
            
            for j, lesson in enumerate(module.get('lessons', [])):
                lesson_duration = lesson.get('estimated_duration', 0)
                total_duration += lesson_duration
                
                if lesson_duration < 30:
                    self.warnings.append(f"⚠️ Module {i+1}, Lesson {j+1}: Very short duration ({lesson_duration} min)")
                elif lesson_duration > 120:
                    self.warnings.append(f"⚠️ Module {i+1}, Lesson {j+1}: Very long duration ({lesson_duration} min)")
                
                # Check content length
                content = lesson.get('primary_content', '')
                if len(content) < 500:
                    self.warnings.append(f"⚠️ Module {i+1}, Lesson {j+1}: Content is very short (< 500 characters)")
                
                # Check for YITP styling
                if 'style=' not in content:
                    self.warnings.append(f"⚠️ Module {i+1}, Lesson {j+1}: Missing YITP styling in content")
                
                # Validate quiz if present
                if 'assessment' in lesson and 'quiz' in lesson.get('assessment', {}):
                    quiz = lesson['assessment']['quiz']
                    questions = quiz.get('questions', [])
                    
                    if len(questions) < 3:
                        self.warnings.append(f"⚠️ Module {i+1}, Lesson {j+1}: Quiz has only {len(questions)} questions (recommended: 4-6)")
                    elif len(questions) > 8:
                        self.warnings.append(f"⚠️ Module {i+1}, Lesson {j+1}: Quiz has {len(questions)} questions (recommended: 4-6)")
                    
                    # Check question type distribution
                    question_types = [q.get('question_type') for q in questions]
                    true_false_count = question_types.count('true_false')
                    total_questions = len(questions)
                    
                    if total_questions > 0:
                        tf_percentage = (true_false_count / total_questions) * 100
                        if tf_percentage < 40 or tf_percentage > 60:
                            self.warnings.append(f"⚠️ Module {i+1}, Lesson {j+1}: Quiz question type distribution "
                                               f"({tf_percentage:.1f}% True/False) should be around 50%")
        
        # Overall course validation
        if total_lessons < 4:
            self.warnings.append(f"⚠️ Course has only {total_lessons} lessons (recommended: 6+)")
        
        if total_duration < 240:  # 4 hours
            self.warnings.append(f"⚠️ Total course duration is {total_duration} minutes (recommended: 240+ min)")
        
        self.info.append("✅ Content quality validation completed")
        return True
    
    def validate_trial_system_compatibility(self, data: Dict) -> bool:
        """Validate compatibility with YITP trial system"""
        self.info.append("🔍 Starting trial system compatibility validation...")
        
        # Check if this is Module 2 (should require payment)
        course_title = data.get('course_title', '').lower()
        if 'module 2' in course_title or 'personal initiative' in course_title:
            self.info.append("📋 Detected Module 2 - validating trial system integration...")
            
            # Module 2 should not have preview lessons
            for i, module in enumerate(data.get('modules', [])):
                for j, lesson in enumerate(module.get('lessons', [])):
                    if lesson.get('is_preview', False):
                        self.warnings.append(f"⚠️ Module {i+1}, Lesson {j+1}: Module 2 lessons should not be preview "
                                           f"(trial users cannot access Module 2)")
            
            # Check for proper unlock criteria
            for i, module in enumerate(data.get('modules', [])):
                unlock_criteria = module.get('unlock_criteria', {})
                if not unlock_criteria:
                    self.warnings.append(f"⚠️ Module {i+1}: Missing unlock criteria for Module 2")
                else:
                    if not unlock_criteria.get('requires_payment', False):
                        self.warnings.append(f"⚠️ Module {i+1}: Should require payment for Module 2")
                    if unlock_criteria.get('requires_module_completion') != 1:
                        self.warnings.append(f"⚠️ Module {i+1}: Should require Module 1 completion")
        
        self.info.append("✅ Trial system compatibility validation completed")
        return True
    
    def validate_file(self, file_path: Path) -> Tuple[bool, Dict]:
        """Main validation function"""
        self.errors = []
        self.warnings = []
        self.info = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"❌ Invalid JSON format: {str(e)}")
            return False, self._get_results()
        except FileNotFoundError:
            self.errors.append(f"❌ File not found: {file_path}")
            return False, self._get_results()
        
        # Run all validations
        structure_valid = self.validate_json_structure(data)
        content_valid = self.validate_content_quality(data)
        trial_valid = self.validate_trial_system_compatibility(data)
        
        overall_valid = structure_valid and len(self.errors) == 0
        
        return overall_valid, self._get_results()
    
    def _get_results(self) -> Dict:
        """Get validation results summary"""
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'is_valid': len(self.errors) == 0
        }


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='YITP JSON Schema Validator')
    parser.add_argument('--input', type=str, required=True,
                       help='Input JSON file to validate')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed validation information')
    
    args = parser.parse_args()
    
    input_file = Path(args.input)
    
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        return
    
    # Create validator and run validation
    validator = YITPJSONValidator()
    is_valid, results = validator.validate_file(input_file)
    
    # Print results
    print(f"\n📋 YITP JSON Validation Results for: {input_file}")
    print("=" * 60)
    
    if args.verbose:
        for info in results['info']:
            print(info)
        print()
    
    if results['errors']:
        print("❌ ERRORS:")
        for error in results['errors']:
            print(f"   {error}")
        print()
    
    if results['warnings']:
        print("⚠️ WARNINGS:")
        for warning in results['warnings']:
            print(f"   {warning}")
        print()
    
    # Summary
    print(f"📊 SUMMARY:")
    print(f"   Errors: {results['error_count']}")
    print(f"   Warnings: {results['warning_count']}")
    print(f"   Status: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    if is_valid:
        print(f"\n🎉 JSON is valid and ready for YITP LMS import!")
    else:
        print(f"\n🔧 Please fix the errors above before importing to YITP LMS.")


if __name__ == "__main__":
    main()
