#!/usr/bin/env python3
"""
Create Module 2 Lessons 6-10 with quizzes following the exact same structure as lessons 1-5
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
from django.utils import timezone

def create_lessons_6_to_10():
    """Create lessons 6-10 for Module 2 with quizzes"""
    
    # Get Module 2
    try:
        course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        module2 = Module.objects.get(course=course, title__icontains='Personal Initiative')
        print(f"✅ Found Module 2: {module2.title} (ID: {module2.id})")
    except Exception as e:
        print(f"❌ Error finding Module 2: {e}")
        return False
    
    # Define lessons 6-10 based on the JSON structure and slide ranges
    lesson_definitions = [
        {
            'title': 'Lesson 6 – Internal Barriers II (1.25 hours)',
            'slides': '56-71',
            'duration': 75,
            'objectives': 'Identify advanced internal barriers to personal initiative; Develop strategies to overcome complex mental obstacles; Build advanced self-awareness and resilience',
            'sort_order': 6
        },
        {
            'title': 'Lesson 7 – External Barriers (1.17 hours)',
            'slides': '72-82',
            'duration': 70,
            'objectives': 'Recognize external barriers to personal initiative; Learn to navigate organizational and environmental constraints; Develop strategies for overcoming external obstacles',
            'sort_order': 7
        },
        {
            'title': 'Lesson 8 – SMART-PI Goals II (1.08 hours)',
            'slides': '83-91',
            'duration': 65,
            'objectives': 'Master advanced SMART-PI goal setting techniques; Apply goal-setting frameworks to complex scenarios; Develop long-term strategic thinking skills',
            'sort_order': 8
        },
        {
            'title': 'Lesson 9 – Bootstrapping & Resourcefulness (1.33 hours)',
            'slides': '92-108',
            'duration': 80,
            'objectives': 'Develop resourcefulness and bootstrapping skills; Learn to maximize limited resources; Build creative problem-solving capabilities',
            'sort_order': 9
        },
        {
            'title': 'Lesson 10 – Time, Systems & Cadence (1.25 hours)',
            'slides': '109-121',
            'duration': 75,
            'objectives': 'Master time management and system thinking; Develop sustainable work cadences; Build systematic approaches to personal initiative',
            'sort_order': 10
        }
    ]
    
    # Quiz questions for each lesson (following the same format as existing quizzes)
    quiz_questions = {
        6: [  # Lesson 6 - Internal Barriers II
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
        ],
        7: [  # Lesson 7 - External Barriers
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
        ],
        8: [  # Lesson 8 - SMART-PI Goals II
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
        ],
        9: [  # Lesson 9 - Bootstrapping & Resourcefulness
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
        ],
        10: [  # Lesson 10 - Time, Systems & Cadence
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
    }
    
    # Create lessons and quizzes
    created_lessons = []
    created_quizzes = []
    
    for lesson_def in lesson_definitions:
        try:
            # Check if lesson already exists
            existing_lesson = Lesson.objects.filter(
                module=module2,
                title=lesson_def['title']
            ).first()

            if existing_lesson:
                print(f"⚠️  Lesson already exists: {lesson_def['title']} (ID: {existing_lesson.id})")
                continue

            # Create lesson
            lesson = Lesson.objects.create(
                module=module2,
                title=lesson_def['title'],
                content_type='text',
                content=f'<div class="iframe-container"><iframe src="/static/module2/lesson_{lesson_def["sort_order"]}.html" width="100%" height="800px" frameborder="0"></iframe></div>',
                learning_objectives=lesson_def['objectives'],
                estimated_duration=lesson_def['duration'],
                sort_order=lesson_def['sort_order'],
                is_published=True,
                is_mandatory=True
            )
            
            print(f"✅ Created lesson: {lesson.title} (ID: {lesson.id})")
            created_lessons.append(lesson)
            
            # Create quiz for this lesson
            quiz = Quiz.objects.create(
                lesson=lesson,
                title=f"Lesson {lesson_def['sort_order']} Quiz",
                description=f"Test your understanding of {lesson.title}",
                passing_score=70,
                max_attempts=15,
                time_limit=None,
                is_published=True,
                is_randomized=False,
                show_results=True
            )
            
            print(f"✅ Created quiz: {quiz.title} (ID: {quiz.id})")
            created_quizzes.append(quiz)
            
            # Create questions for this quiz
            questions_data = quiz_questions[lesson_def['sort_order']]
            for q_data in questions_data:
                question = Question.objects.create(
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
            
            print(f"✅ Created {len(questions_data)} questions for quiz {quiz.id}")
            
        except Exception as e:
            print(f"❌ Error creating lesson {lesson_def['title']}: {e}")
            return False
    
    print(f"\n🎉 Successfully created {len(created_lessons)} lessons and {len(created_quizzes)} quizzes!")
    return True

if __name__ == "__main__":
    print("🚀 Creating Module 2 Lessons 6-10...")
    success = create_lessons_6_to_10()
    if success:
        print("✅ All lessons and quizzes created successfully!")
    else:
        print("❌ Failed to create lessons and quizzes.")
