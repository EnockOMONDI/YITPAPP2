#!/usr/bin/env python3
"""
Create Module 2 Lessons 9-10 with quizzes
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from django.contrib.auth import get_user_model

def create_lesson_with_quiz(module, lesson_data, quiz_data):
    """Create a single lesson with its quiz"""
    
    # Create lesson
    lesson = Lesson(
        module=module,
        title=lesson_data['title'],
        content_type='text',
        content=lesson_data['content'],
        learning_objectives=lesson_data['objectives'],
        estimated_duration=lesson_data['duration'],
        sort_order=lesson_data['sort_order'],
        is_published=True,
        is_mandatory=True
    )
    lesson.save()
    print(f"✅ Created lesson: {lesson.title} (ID: {lesson.id})")
    
    # Create quiz
    quiz = Quiz(
        lesson=lesson,
        title=f"Lesson {lesson_data['sort_order']} Quiz",
        description=f"Test your understanding of {lesson.title}",
        passing_score=70,
        max_attempts=15,
        time_limit=None,
        is_published=True,
        is_randomized=False,
        show_results=True
    )
    quiz.save()
    print(f"✅ Created quiz: {quiz.title} (ID: {quiz.id})")
    
    # Create questions
    for q_data in quiz_data:
        question = Question(
            quiz=quiz,
            question_text=q_data['question_text'],
            question_type=q_data['question_type'],
            points=q_data['points'],
            sort_order=q_data['sort_order'],
            explanation=q_data['explanation']
        )
        
        # Set correct answer and options based on question type
        if q_data['question_type'] == 'multiple_choice':
            question.options = q_data['options']
            question.correct_answer = q_data['correct_answer']
        elif q_data['question_type'] == 'true_false':
            question.correct_answer = q_data['correct_answer']
        elif q_data['question_type'] == 'short_answer':
            question.correct_answer = q_data['correct_answer']
        
        question.save()
    
    print(f"✅ Created {len(quiz_data)} questions for quiz {quiz.id}")
    return lesson, quiz

def main():
    """Create lessons 9-10 for Module 2"""
    
    # Get Module 2
    try:
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module2 = Module.objects.get(course=course, title__icontains='Personal Initiative')
        print(f"✅ Found Module 2: {module2.title} (ID: {module2.id})")
    except Exception as e:
        print(f"❌ Error finding Module 2: {e}")
        return False
    
    # Define lesson 9 data
    lesson9_data = {
        'title': 'Lesson 9 – Bootstrapping & Resourcefulness (1.33 hours)',
        'content': '<div class="iframe-container"><iframe src="/static/module2/lesson_9.html" width="100%" height="800px" frameborder="0"></iframe></div>',
        'objectives': 'Develop resourcefulness and bootstrapping skills; Learn to maximize limited resources; Build creative problem-solving capabilities',
        'duration': 80,
        'sort_order': 9
    }
    
    lesson9_quiz = [
        {
            "question_text": "Bootstrapping means starting with minimal resources and building incrementally.",
            "question_type": "true_false",
            "correct_answer": "true",
            "explanation": "True. Bootstrapping involves starting with limited resources and growing through reinvestment and creativity.",
            "points": 1,
            "sort_order": 1
        },
        {
            "question_text": "Which mindset is most important for effective bootstrapping?",
            "question_type": "multiple_choice",
            "options": ["Scarcity mindset", "Abundance mindset", "Resourcefulness mindset", "Conservative mindset"],
            "correct_answer": "Resourcefulness mindset",
            "explanation": "A resourcefulness mindset focuses on creative solutions and maximizing available resources.",
            "points": 1,
            "sort_order": 2
        },
        {
            "question_text": "List three strategies for maximizing limited resources.",
            "question_type": "short_answer",
            "correct_answer": "Sample answers: Leverage partnerships, repurpose existing assets, focus on high-impact activities",
            "explanation": "Effective strategies include leveraging partnerships, repurposing assets, and prioritizing high-impact activities.",
            "points": 2,
            "sort_order": 3
        },
        {
            "question_text": "How does creative problem-solving support bootstrapping efforts?",
            "question_type": "short_answer",
            "correct_answer": "Creative problem-solving finds innovative solutions that require fewer resources while achieving goals",
            "explanation": "Creative problem-solving helps find innovative, resource-efficient solutions to achieve objectives.",
            "points": 2,
            "sort_order": 4
        },
        {
            "question_text": "Resourcefulness is a learnable skill that improves with practice.",
            "question_type": "true_false",
            "correct_answer": "true",
            "explanation": "True. Resourcefulness can be developed through practice, experience, and deliberate skill building.",
            "points": 1,
            "sort_order": 5
        }
    ]
    
    # Define lesson 10 data
    lesson10_data = {
        'title': 'Lesson 10 – Time, Systems & Cadence (1.25 hours)',
        'content': '<div class="iframe-container"><iframe src="/static/module2/lesson_10.html" width="100%" height="800px" frameborder="0"></iframe></div>',
        'objectives': 'Master time management and system thinking; Develop sustainable work cadences; Build systematic approaches to personal initiative',
        'duration': 75,
        'sort_order': 10
    }
    
    lesson10_quiz = [
        {
            "question_text": "Effective time management requires both planning and systematic execution.",
            "question_type": "true_false",
            "correct_answer": "true",
            "explanation": "True. Time management combines strategic planning with systematic execution and regular review.",
            "points": 1,
            "sort_order": 1
        },
        {
            "question_text": "Which approach is most effective for sustainable productivity?",
            "question_type": "multiple_choice",
            "options": ["Working longer hours", "Multitasking constantly", "Developing consistent cadences", "Eliminating all breaks"],
            "correct_answer": "Developing consistent cadences",
            "explanation": "Consistent cadences create sustainable productivity through rhythm and systematic approaches.",
            "points": 1,
            "sort_order": 2
        },
        {
            "question_text": "Describe three components of an effective personal productivity system.",
            "question_type": "short_answer",
            "correct_answer": "Sample answers: Task capture system, prioritization framework, regular review process",
            "explanation": "Effective systems include task capture, prioritization methods, and regular review processes.",
            "points": 2,
            "sort_order": 3
        },
        {
            "question_text": "How do systems thinking principles apply to personal initiative?",
            "question_type": "short_answer",
            "correct_answer": "Systems thinking helps understand interconnections, feedback loops, and leverage points for maximum impact",
            "explanation": "Systems thinking reveals how actions interconnect and where to focus effort for maximum impact.",
            "points": 2,
            "sort_order": 4
        },
        {
            "question_text": "Regular cadences help maintain momentum and prevent burnout.",
            "question_type": "true_false",
            "correct_answer": "true",
            "explanation": "True. Regular cadences provide structure, maintain momentum, and help prevent burnout through sustainable pacing.",
            "points": 1,
            "sort_order": 5
        }
    ]

    try:
        # Create lesson 9
        print("\n🚀 Creating Lesson 9...")
        lesson9, quiz9 = create_lesson_with_quiz(module2, lesson9_data, lesson9_quiz)
        
        # Create lesson 10
        print("\n🚀 Creating Lesson 10...")
        lesson10, quiz10 = create_lesson_with_quiz(module2, lesson10_data, lesson10_quiz)
        
        print(f"\n🎉 Successfully created 2 lessons with quizzes!")
        print(f"Lesson 9 ID: {lesson9.id}, Quiz 9 ID: {quiz9.id}")
        print(f"Lesson 10 ID: {lesson10.id}, Quiz 10 ID: {quiz10.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating lessons: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating Module 2 Lessons 9-10...")
    success = main()
    if success:
        print("✅ Lessons 9-10 created successfully!")
    else:
        print("❌ Failed to create lessons.")
