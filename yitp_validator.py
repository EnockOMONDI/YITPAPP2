#!/usr/bin/env python3
"""
YITP Course Validator - Quality Assurance Tool
Validates YITP course JSON for structure, content quality, and completeness

Usage:
python yitp_validator.py --input yitp_course.json --report validation_report.txt
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class YITPValidator:
    """Validates YITP course JSON structure and content quality"""
    
    def __init__(self):
        self.validation_results = {
            'structure': {'passed': 0, 'failed': 0, 'issues': []},
            'content': {'passed': 0, 'failed': 0, 'issues': []},
            'quiz': {'passed': 0, 'failed': 0, 'issues': []},
            'styling': {'passed': 0, 'failed': 0, 'issues': []},
            'overall': {'valid': False, 'score': 0}
        }
        
        # Required fields for course structure
        self.required_course_fields = [
            'session_id', 'course_title', 'course_description', 'course_category',
            'difficulty_level', 'estimated_duration', 'price', 'currency',
            'total_sessions', 'modules', 'created_at', 'status'
        ]
        
        self.required_module_fields = [
            'title', 'description', 'sort_order', 'estimated_duration', 'lessons'
        ]
        
        self.required_lesson_fields = [
            'id', 'title', 'content_type', 'estimated_duration', 'learning_objectives',
            'primary_content', 'sort_order', 'is_preview', 'assessment'
        ]
        
        self.required_quiz_fields = [
            'title', 'description', 'instructions', 'max_attempts', 'passing_score',
            'is_randomized', 'show_results', 'questions'
        ]
        
        # Base required fields for all question types
        self.required_question_fields = [
            'question_text', 'question_type', 'points', 'explanation', 'sort_order'
        ]

        # Type-specific required fields
        self.question_type_fields = {
            'true_false': ['correct_answer'],
            'multiple_choice': ['correct_answer', 'options'],
            'fill_in_blank': ['correct_answer'],
            'multiple_select': ['correct_answers', 'options'],
            'matching': ['pairs']
        }
        
        # YITP brand colors for validation
        self.yitp_colors = ['#ff5d15', '#1a2e53', '#0c5460', '#fff8e1', '#f0f8ff']
    
    def validate_structure(self, course_data: Dict) -> None:
        """Validate JSON structure and required fields"""
        logger.info("Validating course structure...")
        
        # Validate course level fields
        for field in self.required_course_fields:
            if field not in course_data:
                self.add_issue('structure', f"Missing required course field: {field}")
            else:
                self.validation_results['structure']['passed'] += 1
        
        # Validate modules
        modules = course_data.get('modules', [])
        if not modules:
            self.add_issue('structure', "No modules found in course")
            return
        
        for i, module in enumerate(modules):
            for field in self.required_module_fields:
                if field not in module:
                    self.add_issue('structure', f"Module {i+1}: Missing required field '{field}'")
                else:
                    self.validation_results['structure']['passed'] += 1
            
            # Validate lessons in module
            lessons = module.get('lessons', [])
            if not lessons:
                self.add_issue('structure', f"Module {i+1}: No lessons found")
                continue
            
            for j, lesson in enumerate(lessons):
                for field in self.required_lesson_fields:
                    if field not in lesson:
                        self.add_issue('structure', f"Module {i+1}, Lesson {j+1}: Missing required field '{field}'")
                    else:
                        self.validation_results['structure']['passed'] += 1
                
                # Validate quiz structure
                assessment = lesson.get('assessment', {})
                quiz = assessment.get('quiz', {})
                
                if quiz:
                    for field in self.required_quiz_fields:
                        if field not in quiz:
                            self.add_issue('structure', f"Module {i+1}, Lesson {j+1}: Missing quiz field '{field}'")
                        else:
                            self.validation_results['structure']['passed'] += 1
                    
                    # Validate questions
                    questions = quiz.get('questions', [])
                    for k, question in enumerate(questions):
                        # Check base required fields
                        for field in self.required_question_fields:
                            if field not in question:
                                self.add_issue('structure', f"Module {i+1}, Lesson {j+1}, Question {k+1}: Missing field '{field}'")
                            else:
                                self.validation_results['structure']['passed'] += 1

                        # Check type-specific required fields
                        question_type = question.get('question_type', '')
                        if question_type in self.question_type_fields:
                            for field in self.question_type_fields[question_type]:
                                if field not in question:
                                    self.add_issue('structure', f"Module {i+1}, Lesson {j+1}, Question {k+1}: Missing {question_type} field '{field}'")
                                else:
                                    self.validation_results['structure']['passed'] += 1
    
    def validate_content_quality(self, course_data: Dict) -> None:
        """Validate content quality and completeness"""
        logger.info("Validating content quality...")
        
        # Check course metadata quality
        title = course_data.get('course_title', '')
        description = course_data.get('course_description', '')
        
        if len(title) < 10:
            self.add_issue('content', "Course title is too short (minimum 10 characters)")
        elif len(title) > 100:
            self.add_issue('content', "Course title is too long (maximum 100 characters)")
        else:
            self.validation_results['content']['passed'] += 1
        
        if len(description) < 50:
            self.add_issue('content', "Course description is too short (minimum 50 characters)")
        elif len(description) > 500:
            self.add_issue('content', "Course description is too long (maximum 500 characters)")
        else:
            self.validation_results['content']['passed'] += 1
        
        # Validate modules and lessons
        modules = course_data.get('modules', [])
        for i, module in enumerate(modules):
            module_title = module.get('title', '')
            module_desc = module.get('description', '')
            
            if len(module_title) < 5:
                self.add_issue('content', f"Module {i+1}: Title too short")
            else:
                self.validation_results['content']['passed'] += 1
            
            if len(module_desc) < 20:
                self.add_issue('content', f"Module {i+1}: Description too short")
            else:
                self.validation_results['content']['passed'] += 1
            
            lessons = module.get('lessons', [])
            for j, lesson in enumerate(lessons):
                lesson_title = lesson.get('title', '')
                primary_content = lesson.get('primary_content', '')
                learning_objectives = lesson.get('learning_objectives', '')
                
                if len(lesson_title) < 5:
                    self.add_issue('content', f"Module {i+1}, Lesson {j+1}: Title too short")
                else:
                    self.validation_results['content']['passed'] += 1
                
                if len(primary_content) < 100:
                    self.add_issue('content', f"Module {i+1}, Lesson {j+1}: Content too short")
                else:
                    self.validation_results['content']['passed'] += 1
                
                if len(learning_objectives) < 20:
                    self.add_issue('content', f"Module {i+1}, Lesson {j+1}: Learning objectives too short")
                else:
                    self.validation_results['content']['passed'] += 1
    
    def validate_quiz_quality(self, course_data: Dict) -> None:
        """Validate quiz structure and question quality"""
        logger.info("Validating quiz quality...")
        
        modules = course_data.get('modules', [])
        for i, module in enumerate(modules):
            lessons = module.get('lessons', [])
            for j, lesson in enumerate(lessons):
                assessment = lesson.get('assessment', {})
                quiz = assessment.get('quiz', {})
                
                if not quiz:
                    self.add_issue('quiz', f"Module {i+1}, Lesson {j+1}: No quiz found")
                    continue
                
                # Validate quiz configuration
                passing_score = quiz.get('passing_score', 0)
                max_attempts = quiz.get('max_attempts', 0)
                
                if passing_score < 50 or passing_score > 100:
                    self.add_issue('quiz', f"Module {i+1}, Lesson {j+1}: Invalid passing score ({passing_score}%)")
                else:
                    self.validation_results['quiz']['passed'] += 1
                
                if max_attempts < 1 or max_attempts > 20:
                    self.add_issue('quiz', f"Module {i+1}, Lesson {j+1}: Invalid max attempts ({max_attempts})")
                else:
                    self.validation_results['quiz']['passed'] += 1
                
                # Validate questions
                questions = quiz.get('questions', [])
                if len(questions) < 3:
                    self.add_issue('quiz', f"Module {i+1}, Lesson {j+1}: Too few questions ({len(questions)})")
                elif len(questions) > 10:
                    self.add_issue('quiz', f"Module {i+1}, Lesson {j+1}: Too many questions ({len(questions)})")
                else:
                    self.validation_results['quiz']['passed'] += 1
                
                # Check question types distribution
                question_type_counts = {}
                valid_question_types = ['true_false', 'multiple_choice', 'fill_in_blank', 'multiple_select', 'matching']

                for question in questions:
                    q_type = question.get('question_type', 'unknown')
                    question_type_counts[q_type] = question_type_counts.get(q_type, 0) + 1

                # Check if we have valid question types
                valid_types_found = sum(question_type_counts.get(qt, 0) for qt in valid_question_types)

                if valid_types_found == 0:
                    self.add_issue('quiz', f"Module {i+1}, Lesson {j+1}: No valid question types found")
                else:
                    self.validation_results['quiz']['passed'] += 1

                # Check for question type diversity (should have at least 2 different types)
                unique_types = len([qt for qt in valid_question_types if question_type_counts.get(qt, 0) > 0])
                if unique_types < 2:
                    self.add_issue('quiz', f"Module {i+1}, Lesson {j+1}: Limited question type diversity ({unique_types} types)")
                else:
                    self.validation_results['quiz']['passed'] += 1
                
                # Validate individual questions
                for k, question in enumerate(questions):
                    self._validate_individual_question(question, i+1, j+1, k+1)

    def _validate_individual_question(self, question: Dict, module_num: int, lesson_num: int, question_num: int) -> None:
        """Validate individual question based on its type"""
        question_text = question.get('question_text', '')
        explanation = question.get('explanation', '')
        question_type = question.get('question_type', '')

        # Basic validation for all question types
        if len(question_text) < 10:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Question text too short")
        else:
            self.validation_results['quiz']['passed'] += 1

        if len(explanation) < 10:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Explanation too short")
        else:
            self.validation_results['quiz']['passed'] += 1

        # Type-specific validation
        if question_type == 'multiple_choice':
            self._validate_multiple_choice_question(question, module_num, lesson_num, question_num)
        elif question_type == 'true_false':
            self._validate_true_false_question(question, module_num, lesson_num, question_num)
        elif question_type == 'fill_in_blank':
            self._validate_fill_in_blank_question(question, module_num, lesson_num, question_num)
        elif question_type == 'multiple_select':
            self._validate_multiple_select_question(question, module_num, lesson_num, question_num)
        elif question_type == 'matching':
            self._validate_matching_question(question, module_num, lesson_num, question_num)
        else:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Unknown question type '{question_type}'")

    def _validate_multiple_choice_question(self, question: Dict, module_num: int, lesson_num: int, question_num: int) -> None:
        """Validate multiple choice question"""
        options = question.get('options', [])
        correct_answer = question.get('correct_answer', '')

        if len(options) < 3:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Too few options ({len(options)})")
        elif len(options) > 6:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Too many options ({len(options)})")
        else:
            self.validation_results['quiz']['passed'] += 1

        if correct_answer not in options:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Correct answer not in options")
        else:
            self.validation_results['quiz']['passed'] += 1

    def _validate_true_false_question(self, question: Dict, module_num: int, lesson_num: int, question_num: int) -> None:
        """Validate true/false question"""
        correct_answer = question.get('correct_answer', '').lower()

        if correct_answer not in ['true', 'false']:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Invalid true/false answer '{correct_answer}'")
        else:
            self.validation_results['quiz']['passed'] += 1

    def _validate_fill_in_blank_question(self, question: Dict, module_num: int, lesson_num: int, question_num: int) -> None:
        """Validate fill-in-the-blank question"""
        correct_answer = question.get('correct_answer', '')
        alternative_answers = question.get('alternative_answers', [])

        if not correct_answer.strip():
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Missing correct answer")
        else:
            self.validation_results['quiz']['passed'] += 1

        if '_' not in question.get('question_text', ''):
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: No blank space (_) found in question")
        else:
            self.validation_results['quiz']['passed'] += 1

    def _validate_multiple_select_question(self, question: Dict, module_num: int, lesson_num: int, question_num: int) -> None:
        """Validate multiple select question"""
        options = question.get('options', [])
        correct_answers = question.get('correct_answers', [])

        if len(options) < 3:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Too few options ({len(options)})")
        else:
            self.validation_results['quiz']['passed'] += 1

        if len(correct_answers) < 1:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: No correct answers specified")
        elif len(correct_answers) >= len(options):
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Too many correct answers")
        else:
            self.validation_results['quiz']['passed'] += 1

        # Check if all correct answers are in options
        invalid_answers = [ans for ans in correct_answers if ans not in options]
        if invalid_answers:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Correct answers not in options: {invalid_answers}")
        else:
            self.validation_results['quiz']['passed'] += 1

    def _validate_matching_question(self, question: Dict, module_num: int, lesson_num: int, question_num: int) -> None:
        """Validate matching question"""
        pairs = question.get('pairs', [])

        if len(pairs) < 2:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Too few matching pairs ({len(pairs)})")
        elif len(pairs) > 6:
            self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Too many matching pairs ({len(pairs)})")
        else:
            self.validation_results['quiz']['passed'] += 1

        # Validate pair structure
        for i, pair in enumerate(pairs):
            if not isinstance(pair, dict) or 'term' not in pair or 'definition' not in pair:
                self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Invalid pair structure at index {i}")
            elif not pair.get('term', '').strip() or not pair.get('definition', '').strip():
                self.add_issue('quiz', f"Module {module_num}, Lesson {lesson_num}, Question {question_num}: Empty term or definition at index {i}")
            else:
                self.validation_results['quiz']['passed'] += 1
    
    def validate_yitp_styling(self, course_data: Dict) -> None:
        """Validate YITP styling and HTML formatting"""
        logger.info("Validating YITP styling...")
        
        modules = course_data.get('modules', [])
        for i, module in enumerate(modules):
            lessons = module.get('lessons', [])
            for j, lesson in enumerate(lessons):
                primary_content = lesson.get('primary_content', '')
                
                if not primary_content:
                    self.add_issue('styling', f"Module {i+1}, Lesson {j+1}: No primary content")
                    continue
                
                # Check for YITP color usage
                color_found = any(color in primary_content for color in self.yitp_colors)
                if not color_found:
                    self.add_issue('styling', f"Module {i+1}, Lesson {j+1}: No YITP brand colors found")
                else:
                    self.validation_results['styling']['passed'] += 1
                
                # Check for required HTML elements
                required_elements = ['<h2', '<div', '<h3', '<h4', '<p>']
                missing_elements = [elem for elem in required_elements if elem not in primary_content]
                
                if missing_elements:
                    self.add_issue('styling', f"Module {i+1}, Lesson {j+1}: Missing HTML elements: {missing_elements}")
                else:
                    self.validation_results['styling']['passed'] += 1
                
                # Check for key takeaway box
                if '💡 Key Takeaway' not in primary_content:
                    self.add_issue('styling', f"Module {i+1}, Lesson {j+1}: Missing Key Takeaway box")
                else:
                    self.validation_results['styling']['passed'] += 1
                
                # Check for activity section
                if '🎯 Activity' not in primary_content:
                    self.add_issue('styling', f"Module {i+1}, Lesson {j+1}: Missing Activity section")
                else:
                    self.validation_results['styling']['passed'] += 1
    
    def add_issue(self, category: str, message: str) -> None:
        """Add validation issue to results"""
        self.validation_results[category]['failed'] += 1
        self.validation_results[category]['issues'].append(message)
    
    def calculate_overall_score(self) -> float:
        """Calculate overall validation score"""
        total_passed = sum(cat['passed'] for cat in self.validation_results.values() if 'passed' in cat)
        total_failed = sum(cat['failed'] for cat in self.validation_results.values() if 'failed' in cat)
        total_checks = total_passed + total_failed
        
        if total_checks == 0:
            return 0.0
        
        score = (total_passed / total_checks) * 100
        return round(score, 2)
    
    def validate_course(self, course_data: Dict) -> Dict:
        """Run complete validation on course data"""
        logger.info("Starting YITP course validation...")
        
        # Reset results
        self.validation_results = {
            'structure': {'passed': 0, 'failed': 0, 'issues': []},
            'content': {'passed': 0, 'failed': 0, 'issues': []},
            'quiz': {'passed': 0, 'failed': 0, 'issues': []},
            'styling': {'passed': 0, 'failed': 0, 'issues': []},
            'overall': {'valid': False, 'score': 0}
        }
        
        # Run validation checks
        self.validate_structure(course_data)
        self.validate_content_quality(course_data)
        self.validate_quiz_quality(course_data)
        self.validate_yitp_styling(course_data)
        
        # Calculate overall score
        score = self.calculate_overall_score()
        self.validation_results['overall']['score'] = score
        self.validation_results['overall']['valid'] = score >= 80.0  # 80% threshold
        
        logger.info(f"Validation completed. Overall score: {score}%")
        
        return self.validation_results
    
    def generate_report(self, results: Dict, output_file: Path = None) -> str:
        """Generate validation report"""
        report_lines = []
        report_lines.append("YITP COURSE VALIDATION REPORT")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Overall summary
        overall = results['overall']
        status = "✅ VALID" if overall['valid'] else "❌ INVALID"
        report_lines.append(f"OVERALL STATUS: {status}")
        report_lines.append(f"OVERALL SCORE: {overall['score']}%")
        report_lines.append("")
        
        # Category breakdown
        for category, data in results.items():
            if category == 'overall':
                continue
            
            report_lines.append(f"{category.upper()} VALIDATION:")
            report_lines.append(f"  Passed: {data['passed']}")
            report_lines.append(f"  Failed: {data['failed']}")
            
            if data['issues']:
                report_lines.append("  Issues:")
                for issue in data['issues']:
                    report_lines.append(f"    - {issue}")
            else:
                report_lines.append("  ✅ No issues found")
            
            report_lines.append("")
        
        # Recommendations
        report_lines.append("RECOMMENDATIONS:")
        if overall['score'] < 80:
            report_lines.append("- Address validation issues before using in production")
            report_lines.append("- Focus on categories with the most failed checks")
        else:
            report_lines.append("- Course meets YITP quality standards")
            report_lines.append("- Ready for import into YITP LMS")
        
        report_text = "\n".join(report_lines)
        
        # Save to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                logger.info(f"Validation report saved to: {output_file}")
            except Exception as e:
                logger.error(f"Error saving report: {str(e)}")
        
        return report_text


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='YITP Course Validator - Quality Assurance Tool')
    parser.add_argument('--input', type=str, required=True,
                       help='Input YITP course JSON file to validate')
    parser.add_argument('--report', type=str,
                       help='Output validation report file (optional)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    input_file = Path(args.input)
    
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return False
    
    try:
        # Load course data
        with open(input_file, 'r', encoding='utf-8') as f:
            course_data = json.load(f)
        
        # Create validator and run validation
        validator = YITPValidator()
        results = validator.validate_course(course_data)
        
        # Generate and display report
        report_file = Path(args.report) if args.report else None
        report = validator.generate_report(results, report_file)
        
        print("\n" + report)
        
        # Return success based on validation results
        return results['overall']['valid']
        
    except Exception as e:
        logger.error(f"Error validating course: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
