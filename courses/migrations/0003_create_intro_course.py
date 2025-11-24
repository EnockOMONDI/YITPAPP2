# Generated migration for YITP Introductory Course

from django.db import migrations
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone


def create_intro_course(apps, schema_editor):
    """Create the YITP introductory course with all components"""
    
    # Get model classes
    User = apps.get_model('auth', 'User')
    InstructorProfile = apps.get_model('users', 'InstructorProfile')
    Category = apps.get_model('courses', 'Category')
    Course = apps.get_model('courses', 'Course')
    Module = apps.get_model('courses', 'Module')
    Lesson = apps.get_model('courses', 'Lesson')
    Quiz = apps.get_model('assessments', 'Quiz')
    Question = apps.get_model('assessments', 'Question')
    
    # Create instructor user
    instructor, created = User.objects.get_or_create(
        username='yitpteam',
        defaults={
            'email': 'enockomondike@gmail.com',
            'first_name': 'YITP',
            'last_name': 'Team',
            'is_staff': True,
            'is_active': True
        }
    )
    
    if created:
        if hasattr(instructor, 'set_password'):
            instructor.set_password('sLXSxmMg3tVeV64')
        else:
            instructor.password = make_password('sLXSxmMg3tVeV64')
        instructor.save()
    
    # Create instructor profile
    instructor_profile, created = InstructorProfile.objects.get_or_create(
        user=instructor,
        defaults={
            'instructor_role': 'course_instructor',
            'verification_status': 'verified',
            'bio': 'Official YITP Team instructor account for creating introductory and system courses.'
        }
    )
    
    # Create category
    category, created = Category.objects.get_or_create(
        name='Platform Training',
        defaults={
            'description': 'Courses focused on learning how to use the YITP platform effectively',
            'slug': 'platform-training'
        }
    )
    
    # Create course
    course, created = Course.objects.get_or_create(
        title="Introduction to YITP: Your Learning Journey Begins",
        defaults={
            'description': """Welcome to the Youth Impact Training Programme! This comprehensive introductory course is designed to help you get started on your learning journey with YITP.

In this course, you will:
• Understand YITP's mission and how we're transforming lives through education
• Learn to navigate our learning platform effectively
• Discover how to track your progress and complete assignments
• Access support resources and contact information

This is a mandatory first course for all new students and takes approximately 25 minutes to complete. Upon successful completion, you'll be ready to explore our full range of courses and begin your transformational learning experience.""",
            'instructor': instructor,
            'category': category,
            'price': 0.00,  # Free course
            'estimated_duration': 1,
            'difficulty_level': 'beginner',
            'status': 'published',
            'is_featured': True,
            'learning_objectives': """By the end of this course, you will be able to:

1. Explain YITP's mission and core values
2. Navigate the YITP learning platform confidently
3. Track your learning progress effectively
4. Complete assignments and assessments
5. Access support resources when needed
6. Understand the structure of YITP courses""",
            'prerequisites': 'None - This is the starting point for all YITP students'
        }
    )
    
    # Create module
    module, created = Module.objects.get_or_create(
        course=course,
        title='Getting Started with YITP',
        defaults={
            'description': 'Introduction to the Youth Impact Training Programme platform and learning system',
            'sort_order': 1,
            'estimated_duration': 25,
            'is_published': True
        }
    )
    
    # Lesson content with YITP branding
    lesson_content = """
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #341C67 0%, #ff5d15 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 2.5em;">Welcome to YITP! 🎓</h1>
            <p style="margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9;">Your Learning Journey Begins Here</p>
        </div>

        <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 25px; border-left: 5px solid #ff5d15;">
            <h2 style="color: #341C67; margin-top: 0;">🌟 What is YITP?</h2>
            <p style="line-height: 1.6; color: #333;">
                The <strong>Youth Impact Training Programme (YITP)</strong> is a transformational educational initiative designed to empower young people with the skills, knowledge, and confidence they need to create positive change in their communities and beyond.
            </p>
            <p style="line-height: 1.6; color: #333;">
                Our mission is simple yet powerful: <em>"Transforming lives through accessible, high-quality education that builds leaders for tomorrow."</em>
            </p>
        </div>

        <div style="background: #fff; padding: 25px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #341C67; margin-top: 0;">🎯 Our Core Values</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                <div style="padding: 15px; background: #fff5f0; border-radius: 6px; border: 1px solid #ff5d15;">
                    <h3 style="color: #ff5d15; margin-top: 0;">💡 Innovation</h3>
                    <p style="margin-bottom: 0; color: #666;">Embracing new ideas and creative solutions to drive positive change.</p>
                </div>
                <div style="padding: 15px; background: #f0f4ff; border-radius: 6px; border: 1px solid #341C67;">
                    <h3 style="color: #341C67; margin-top: 0;">🤝 Collaboration</h3>
                    <p style="margin-bottom: 0; color: #666;">Working together to achieve greater impact than we could alone.</p>
                </div>
                <div style="padding: 15px; background: #f0fff0; border-radius: 6px; border: 1px solid #28a745;">
                    <h3 style="color: #28a745; margin-top: 0;">🌱 Growth</h3>
                    <p style="margin-bottom: 0; color: #666;">Continuous learning and development for personal and professional excellence.</p>
                </div>
            </div>
        </div>

        <div style="background: #fff; padding: 25px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #341C67; margin-top: 0;">🧭 Navigating Your YITP Learning Platform</h2>
            <p style="line-height: 1.6; color: #333;">
                Our learning platform is designed to be intuitive and user-friendly. Here's how to make the most of your learning experience:
            </p>
            
            <div style="margin: 20px 0;">
                <h3 style="color: #ff5d15;">📊 Dashboard</h3>
                <p style="color: #666; margin-left: 20px;">Your central hub showing course progress, upcoming assignments, and achievements.</p>
                
                <h3 style="color: #ff5d15;">📚 Course Catalog</h3>
                <p style="color: #666; margin-left: 20px;">Browse and enroll in courses that match your interests and career goals.</p>
                
                <h3 style="color: #ff5d15;">📈 Progress Tracking</h3>
                <p style="color: #666; margin-left: 20px;">Monitor your learning journey with detailed progress reports and completion certificates.</p>
                
                <h3 style="color: #ff5d15;">💬 Support Center</h3>
                <p style="color: #666; margin-left: 20px;">Get help when you need it through our comprehensive support resources.</p>
            </div>
        </div>

        <div style="background: #fff5f0; padding: 25px; border-radius: 8px; margin-bottom: 25px; border: 2px solid #ff5d15;">
            <h2 style="color: #341C67; margin-top: 0;">📋 How to Complete Assignments & Track Progress</h2>
            <ol style="line-height: 1.8; color: #333;">
                <li><strong>Read Each Lesson Carefully:</strong> Take your time to understand the content before moving forward.</li>
                <li><strong>Complete Knowledge Checks:</strong> Each lesson includes quizzes to test your understanding (70% passing score required).</li>
                <li><strong>Track Your Progress:</strong> Use the progress bar to see how much of the course you've completed.</li>
                <li><strong>Earn Your Certificate:</strong> Successfully complete all lessons and assessments to receive your completion certificate.</li>
                <li><strong>Apply Your Learning:</strong> Use the knowledge and skills you've gained in real-world situations.</li>
            </ol>
        </div>

        <div style="background: #f0f4ff; padding: 25px; border-radius: 8px; margin-bottom: 25px; border: 2px solid #341C67;">
            <h2 style="color: #341C67; margin-top: 0;">🆘 Support Resources & Contact Information</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <div>
                    <h3 style="color: #ff5d15;">📧 Email Support</h3>
                    <p style="color: #666;">For technical issues or course questions:<br>
                    <strong>youthimpactglobal3@gmail.com</strong></p>
                </div>
                <div>
                    <h3 style="color: #ff5d15;">📚 Help Center</h3>
                    <p style="color: #666;">Access our comprehensive FAQ and tutorial library through the platform's Help section.</p>
                </div>
                <div>
                    <h3 style="color: #ff5d15;">⏰ Response Time</h3>
                    <p style="color: #666;">We typically respond to support requests within 24 hours during business days.</p>
                </div>
                <div>
                    <h3 style="color: #ff5d15;">🌐 Community</h3>
                    <p style="color: #666;">Connect with fellow learners through our discussion forums and study groups.</p>
                </div>
            </div>
        </div>

        <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 25px; border-radius: 8px; text-align: center;">
            <h2 style="margin-top: 0;">🚀 Ready to Begin Your Journey?</h2>
            <p style="font-size: 1.1em; margin-bottom: 20px;">
                Congratulations! You now have everything you need to succeed on the YITP platform. 
                Remember, every expert was once a beginner, and every journey starts with a single step.
            </p>
            <p style="font-size: 1.2em; font-weight: bold; margin-bottom: 0;">
                Let's transform your potential into impact! 💪
            </p>
        </div>
    </div>
    """
    
    # Create lesson
    lesson, created = Lesson.objects.get_or_create(
        module=module,
        title='Welcome to Youth Impact Training Programme',
        defaults={
            'content': lesson_content,
            'content_type': 'text',
            'sort_order': 1,
            'estimated_duration': 15,
            'is_published': True,
            'is_mandatory': True
        }
    )

    # Create quiz
    quiz, created = Quiz.objects.get_or_create(
        lesson=lesson,
        title='YITP Platform Knowledge Check',
        defaults={
            'description': 'Test your understanding of the YITP platform and learning system. You need 70% to pass.',
            'instructions': 'Read each question carefully and select the best answer. You have 3 attempts to pass with 70% or higher.',
            'passing_score': 70,
            'max_attempts': 3,
            'time_limit': 10,
            'is_published': True,
            'show_results': True
        }
    )

    # Quiz questions data
    questions_data = [
        {
            'question_text': 'What is the main mission of YITP (Youth Impact Training Programme)?',
            'question_type': 'multiple_choice',
            'points': 10,
            'options': [
                'To provide entertainment for young people',
                'Transforming lives through accessible, high-quality education that builds leaders for tomorrow',
                'To sell online courses for profit',
                'To replace traditional education systems'
            ],
            'correct_answer': 'Transforming lives through accessible, high-quality education that builds leaders for tomorrow'
        },
        {
            'question_text': 'What percentage score do you need to pass a YITP quiz?',
            'question_type': 'multiple_choice',
            'points': 10,
            'options': ['50%', '60%', '70%', '80%'],
            'correct_answer': '70%'
        },
        {
            'question_text': 'Which of the following are core values of YITP?',
            'question_type': 'multiple_choice',
            'points': 15,
            'options': ['Innovation', 'Collaboration', 'Growth', 'Competition'],
            'correct_answer': 'Innovation'
        },
        {
            'question_text': 'What is the primary email address for YITP support?',
            'question_type': 'multiple_choice',
            'points': 10,
            'options': [
                'support@yitp.com',
                'youthimpactglobal3@gmail.com',
                'help@youthimpact.org',
                'info@yitp.edu'
            ],
            'correct_answer': 'youthimpactglobal3@gmail.com'
        },
        {
            'question_text': 'How long does it typically take for YITP support to respond to requests?',
            'question_type': 'multiple_choice',
            'points': 10,
            'options': [
                'Within 1 hour',
                'Within 24 hours during business days',
                'Within 1 week',
                'Support is not available'
            ],
            'correct_answer': 'Within 24 hours during business days'
        },
        {
            'question_text': 'True or False: This introductory course is mandatory for all new YITP students.',
            'question_type': 'true_false',
            'points': 10,
            'options': ['True', 'False'],
            'correct_answer': 'True'
        },
        {
            'question_text': 'What should you do if you need help while taking a course?',
            'question_type': 'multiple_choice',
            'points': 15,
            'options': [
                'Give up and quit the course',
                'Skip the difficult parts',
                'Contact support at youthimpactglobal3@gmail.com or use the Help Center',
                'Guess the answers randomly'
            ],
            'correct_answer': 'Contact support at youthimpactglobal3@gmail.com or use the Help Center'
        },
        {
            'question_text': 'What happens when you successfully complete all lessons and assessments in a YITP course?',
            'question_type': 'multiple_choice',
            'points': 20,
            'options': [
                'Nothing happens',
                'You receive a completion certificate',
                'You are automatically enrolled in the next course',
                'You have to pay additional fees'
            ],
            'correct_answer': 'You receive a completion certificate'
        }
    ]

    # Create questions
    for i, q_data in enumerate(questions_data, 1):
        Question.objects.get_or_create(
            quiz=quiz,
            question_text=q_data['question_text'],
            defaults={
                'question_type': q_data['question_type'],
                'points': q_data['points'],
                'sort_order': i,
                'options': q_data['options'],
                'correct_answer': q_data['correct_answer']
            }
        )


def reverse_intro_course(apps, schema_editor):
    """Remove the introductory course and related data"""
    Course = apps.get_model('courses', 'Course')
    User = apps.get_model('auth', 'User')
    
    # Delete course (cascades to modules, lessons, quizzes, questions)
    Course.objects.filter(title__icontains="Introduction to YITP").delete()
    
    # Optionally delete the instructor user (commented out for safety)
    # User.objects.filter(username='yitpteam').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_alter_lesson_content'),
        ('users', '0001_initial'),
        ('assessments', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_intro_course, reverse_intro_course),
    ]
