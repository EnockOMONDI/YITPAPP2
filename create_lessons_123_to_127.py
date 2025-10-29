#!/usr/bin/env python3
"""
Create Module 2 Lessons 6-10 (IDs 123-127) with quizzes
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
    """Create lessons 6-10 for Module 2"""
    
    # Get Module 2
    try:
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module2 = Module.objects.get(course=course, title__icontains='Personal Initiative')
        print(f"✅ Found Module 2: {module2.title} (ID: {module2.id})")
    except Exception as e:
        print(f"❌ Error finding Module 2: {e}")
        return False
    
    # Define lesson 6 data
    lesson6_data = {
        'title': 'Lesson 6 – Internal Barriers II (1.25 hours)',
        'content': '<div class="iframe-container"><iframe src="/static/module2/lesson_6.html" width="100%" height="800px" frameborder="0"></iframe></div>',
        'objectives': 'Identify advanced internal barriers to personal initiative; Develop strategies to overcome complex mental obstacles; Build advanced self-awareness and resilience',
        'duration': 75,
        'sort_order': 6
    }
    
    lesson6_quiz = [
        {
            "question_text": "Which of the following is an advanced internal barrier to personal initiative?",
            "question_type": "multiple_choice",
            "options": ["Fear of failure", "Perfectionism", "Imposter syndrome", "All of the above"],
            "correct_answer": "All of the above",
            "explanation": "Advanced internal barriers include fear of failure, perfectionism, and imposter syndrome.",
            "points": 1,
            "sort_order": 1
        },
        {
            "question_text": "Overcoming internal barriers requires continuous self-reflection and practice.",
            "question_type": "true_false",
            "correct_answer": "true",
            "explanation": "True. Overcoming internal barriers is an ongoing process that requires consistent self-awareness and practice.",
            "points": 1,
            "sort_order": 2
        },
        {
            "question_text": "Describe three strategies for overcoming perfectionism as an internal barrier.",
            "question_type": "short_answer",
            "correct_answer": "Sample answers: Set realistic standards, embrace iterative improvement, focus on progress over perfection",
            "explanation": "Effective strategies include setting realistic standards, embracing iterative improvement, and focusing on progress rather than perfection.",
            "points": 2,
            "sort_order": 3
        },
        {
            "question_text": "Which mindset shift is most important for overcoming imposter syndrome?",
            "question_type": "multiple_choice",
            "options": ["Avoiding challenges", "Seeking constant validation", "Embracing growth mindset", "Comparing to others"],
            "correct_answer": "Embracing growth mindset",
            "explanation": "Embracing a growth mindset helps overcome imposter syndrome by focusing on learning and development.",
            "points": 1,
            "sort_order": 4
        },
        {
            "question_text": "Explain how self-compassion can help overcome internal barriers to personal initiative.",
            "question_type": "short_answer",
            "correct_answer": "Self-compassion reduces self-criticism, increases resilience, and promotes learning from mistakes",
            "explanation": "Self-compassion helps by reducing harsh self-criticism, building resilience, and creating a safe space for learning from mistakes.",
            "points": 2,
            "sort_order": 5
        }
    ]
    
    # Define lesson 7 data
    lesson7_data = {
        'title': 'Lesson 7 – External Barriers (1.17 hours)',
        'content': '<div class="iframe-container"><iframe src="/static/module2/lesson_7.html" width="100%" height="800px" frameborder="0"></iframe></div>',
        'objectives': 'Recognize external barriers to personal initiative; Learn to navigate organizational and environmental constraints; Develop strategies for overcoming external obstacles',
        'duration': 70,
        'sort_order': 7
    }
    
    lesson7_quiz = [
        {
            "question_text": "External barriers to personal initiative include organizational constraints and resource limitations.",
            "question_type": "true_false",
            "correct_answer": "true",
            "explanation": "True. External barriers include organizational policies, resource constraints, and environmental factors.",
            "points": 1,
            "sort_order": 1
        },
        {
            "question_text": "Which strategy is most effective for navigating organizational barriers?",
            "question_type": "multiple_choice",
            "options": ["Ignoring the barriers", "Building strategic relationships", "Complaining to management", "Working around the system"],
            "correct_answer": "Building strategic relationships",
            "explanation": "Building strategic relationships helps navigate organizational barriers through collaboration and influence.",
            "points": 1,
            "sort_order": 2
        },
        {
            "question_text": "List three types of external barriers that can limit personal initiative.",
            "question_type": "short_answer",
            "correct_answer": "Sample answers: Organizational policies, resource constraints, cultural norms, regulatory requirements",
            "explanation": "External barriers include organizational policies, resource limitations, cultural norms, and regulatory constraints.",
            "points": 2,
            "sort_order": 3
        },
        {
            "question_text": "How can you turn external constraints into opportunities for innovation?",
            "question_type": "short_answer",
            "correct_answer": "By reframing constraints as creative challenges and finding alternative approaches",
            "explanation": "Constraints can drive innovation by forcing creative problem-solving and alternative thinking.",
            "points": 2,
            "sort_order": 4
        },
        {
            "question_text": "Stakeholder mapping is useful for understanding external barriers.",
            "question_type": "true_false",
            "correct_answer": "true",
            "explanation": "True. Stakeholder mapping helps identify key players and potential sources of external barriers or support.",
            "points": 1,
            "sort_order": 5
        }
    ]
    
    # Define lesson 8 data
    lesson8_data = {
        'title': 'Lesson 8 – SMART-PI Goals II (1.08 hours)',
        'content': '<div class="iframe-container"><iframe src="/static/module2/lesson_8.html" width="100%" height="800px" frameborder="0"></iframe></div>',
        'objectives': 'Master advanced SMART-PI goal setting techniques; Apply goal-setting frameworks to complex scenarios; Develop long-term strategic thinking skills',
        'duration': 65,
        'sort_order': 8
    }

    lesson8_quiz = [
        {
            "question_text": "Advanced SMART-PI goals should include stretch targets and contingency plans.",
            "question_type": "true_false",
            "correct_answer": "true",
            "explanation": "True. Advanced goal setting includes stretch targets for growth and contingency plans for adaptability.",
            "points": 1,
            "sort_order": 1
        },
        {
            "question_text": "Which element is most important in advanced SMART-PI goal setting?",
            "question_type": "multiple_choice",
            "options": ["Specificity", "Measurability", "Personal Initiative integration", "Time-bound nature"],
            "correct_answer": "Personal Initiative integration",
            "explanation": "Personal Initiative integration ensures goals promote proactive, self-starting behavior.",
            "points": 1,
            "sort_order": 2
        },
        {
            "question_text": "Describe how to create a goal cascade from strategic to tactical levels.",
            "question_type": "short_answer",
            "correct_answer": "Break down strategic goals into operational objectives, then into specific actions and milestones",
            "explanation": "Goal cascading involves breaking strategic goals into operational objectives and specific actionable steps.",
            "points": 2,
            "sort_order": 3
        },
        {
            "question_text": "What role does feedback play in advanced goal achievement?",
            "question_type": "short_answer",
            "correct_answer": "Feedback enables course correction, learning, and continuous improvement toward goal achievement",
            "explanation": "Feedback is essential for monitoring progress, making adjustments, and ensuring continuous improvement.",
            "points": 2,
            "sort_order": 4
        },
        {
            "question_text": "Long-term strategic thinking is essential for advanced SMART-PI goals.",
            "question_type": "true_false",
            "correct_answer": "true",
            "explanation": "True. Advanced goals require strategic thinking to align short-term actions with long-term vision.",
            "points": 1,
            "sort_order": 5
        }
    ]

    try:
        # Create lesson 6
        print("\n🚀 Creating Lesson 6...")
        lesson6, quiz6 = create_lesson_with_quiz(module2, lesson6_data, lesson6_quiz)

        # Create lesson 7
        print("\n🚀 Creating Lesson 7...")
        lesson7, quiz7 = create_lesson_with_quiz(module2, lesson7_data, lesson7_quiz)

        # Create lesson 8
        print("\n🚀 Creating Lesson 8...")
        lesson8, quiz8 = create_lesson_with_quiz(module2, lesson8_data, lesson8_quiz)

        print(f"\n🎉 Successfully created 3 lessons with quizzes!")
        print(f"Lesson 6 ID: {lesson6.id}, Quiz 6 ID: {quiz6.id}")
        print(f"Lesson 7 ID: {lesson7.id}, Quiz 7 ID: {quiz7.id}")
        print(f"Lesson 8 ID: {lesson8.id}, Quiz 8 ID: {quiz8.id}")

        return True
        
    except Exception as e:
        print(f"❌ Error creating lessons: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating Module 2 Lessons 6-7...")
    success = main()
    if success:
        print("✅ Lessons 6-7 created successfully!")
    else:
        print("❌ Failed to create lessons.")
