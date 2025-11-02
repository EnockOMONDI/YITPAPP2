#!/usr/bin/env python3
"""
Extract all quiz answers from all 5 modules in the YITP course
"""

import os
import django
import json
from collections import defaultdict

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question

def extract_all_quiz_answers():
    """Extract all quiz answers from all modules"""
    
    print("📚 EXTRACTING ALL QUIZ ANSWERS FROM YITP COURSE")
    print("=" * 60)
    
    try:
        # Get the YITP course
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        print(f"✅ Found course: {course.title}")
        
        # Get all modules ordered by sort_order
        modules = Module.objects.filter(course=course).order_by('sort_order')
        print(f"📖 Found {modules.count()} modules")
        
        # Structure to hold all quiz data
        quiz_data = {
            'course_title': course.title,
            'course_description': course.description,
            'modules': [],
            'statistics': {
                'total_modules': 0,
                'total_lessons': 0,
                'total_quizzes': 0,
                'total_questions': 0
            }
        }
        
        total_lessons = 0
        total_quizzes = 0
        total_questions = 0
        
        for module in modules:
            print(f"\n📂 Processing Module {module.sort_order}: {module.title}")
            
            # Get all lessons in this module
            lessons = Lesson.objects.filter(module=module).order_by('sort_order')
            module_lessons = []
            module_quizzes = 0
            module_questions = 0
            
            for lesson in lessons:
                print(f"   📄 Processing Lesson: {lesson.title}")
                
                # Get all quizzes for this lesson
                quizzes = Quiz.objects.filter(lesson=lesson).order_by('id')
                lesson_quizzes = []
                
                for quiz in quizzes:
                    print(f"      🧪 Processing Quiz: {quiz.title}")
                    
                    # Get all questions for this quiz
                    questions = Question.objects.filter(quiz=quiz).order_by('id')
                    quiz_questions = []
                    
                    for i, question in enumerate(questions, 1):
                        question_data = {
                            'question_number': i,
                            'question_text': question.question_text,
                            'question_type': question.question_type,
                            'options': question.options if question.options else [],
                            'correct_answer': question.correct_answer,
                            'explanation': question.explanation if question.explanation else '',
                            'points': question.points
                        }
                        quiz_questions.append(question_data)
                        module_questions += 1
                    
                    if quiz_questions:
                        quiz_data_entry = {
                            'quiz_title': quiz.title,
                            'passing_score': quiz.passing_score,
                            'max_attempts': quiz.max_attempts,
                            'questions': quiz_questions,
                            'question_count': len(quiz_questions)
                        }
                        lesson_quizzes.append(quiz_data_entry)
                        module_quizzes += 1
                        
                        print(f"         ✅ Extracted {len(quiz_questions)} questions")
                
                if lesson_quizzes:
                    lesson_data = {
                        'lesson_title': lesson.title,
                        'lesson_sort_order': lesson.sort_order,
                        'estimated_duration': lesson.estimated_duration,
                        'quizzes': lesson_quizzes,
                        'quiz_count': len(lesson_quizzes)
                    }
                    module_lessons.append(lesson_data)
                    total_lessons += 1
            
            if module_lessons:
                module_data = {
                    'module_title': module.title,
                    'module_sort_order': module.sort_order,
                    'module_description': module.description if module.description else '',
                    'lessons': module_lessons,
                    'lesson_count': len(module_lessons),
                    'quiz_count': module_quizzes,
                    'question_count': module_questions
                }
                quiz_data['modules'].append(module_data)
                total_quizzes += module_quizzes
                total_questions += module_questions
                
                print(f"   📊 Module summary: {len(module_lessons)} lessons, {module_quizzes} quizzes, {module_questions} questions")
        
        # Update statistics
        quiz_data['statistics'] = {
            'total_modules': len(quiz_data['modules']),
            'total_lessons': total_lessons,
            'total_quizzes': total_quizzes,
            'total_questions': total_questions
        }
        
        # Save to JSON file
        output_file = 'yitp_quiz_answers_complete.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(quiz_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"   • Total modules: {quiz_data['statistics']['total_modules']}")
        print(f"   • Total lessons: {quiz_data['statistics']['total_lessons']}")
        print(f"   • Total quizzes: {quiz_data['statistics']['total_quizzes']}")
        print(f"   • Total questions: {quiz_data['statistics']['total_questions']}")
        print(f"   • Output file: {output_file}")
        
        return quiz_data, output_file
        
    except Exception as e:
        print(f"❌ Error extracting quiz answers: {e}")
        return None, None

def display_module_breakdown(quiz_data):
    """Display detailed breakdown by module"""
    
    print(f"\n📋 DETAILED MODULE BREAKDOWN:")
    print("=" * 60)
    
    for module in quiz_data['modules']:
        print(f"\n📂 Module {module['module_sort_order']}: {module['module_title']}")
        print(f"   📄 Lessons: {module['lesson_count']}")
        print(f"   🧪 Quizzes: {module['quiz_count']}")
        print(f"   ❓ Questions: {module['question_count']}")
        
        for lesson in module['lessons']:
            print(f"      📄 {lesson['lesson_title']} ({lesson['quiz_count']} quiz{'es' if lesson['quiz_count'] != 1 else ''})")
            
            for quiz in lesson['quizzes']:
                print(f"         🧪 {quiz['quiz_title']} ({quiz['question_count']} questions)")

def main():
    quiz_data, output_file = extract_all_quiz_answers()
    
    if quiz_data and output_file:
        print(f"\n🎉 Quiz answer extraction completed successfully!")
        print(f"📁 Data saved to: {output_file}")
        
        # Display detailed breakdown
        display_module_breakdown(quiz_data)
        
        print(f"\n🔄 Next step: Run generate_answer_key_pdf.py to create the PDF")
        return True
    else:
        print(f"\n❌ Failed to extract quiz answers")
        return False

if __name__ == "__main__":
    main()
