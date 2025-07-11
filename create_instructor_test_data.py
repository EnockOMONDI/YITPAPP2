#!/usr/bin/env python
"""
Create test instructor data for YITP LMS Enhanced Instructor Role System
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/djsean/Desktop/APPS2024/YITP2025/YITPAPP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import InstructorProfile, Specialization, CourseInstructor
from courses.models import Course, Category
from assessments.models import Quiz, Question
from communication.models import Message
from django.utils import timezone
from datetime import timedelta


def create_instructor_test_data():
    """Create comprehensive test data for instructor role system"""
    
    print("🚀 Creating Enhanced Instructor Role System Test Data...")
    print("=" * 60)
    
    # Step 1: Create Specializations
    print("\n📚 Creating Instructor Specializations...")
    specializations_data = [
        {
            'name': 'Digital Marketing',
            'slug': 'digital-marketing',
            'description': 'Social media, SEO, content marketing, and online advertising',
            'icon': 'fas fa-bullhorn',
            'color': '#ff5d15'
        },
        {
            'name': 'Entrepreneurship',
            'slug': 'entrepreneurship',
            'description': 'Business planning, startup development, and innovation',
            'icon': 'fas fa-lightbulb',
            'color': '#1a2e53'
        },
        {
            'name': 'Financial Literacy',
            'slug': 'financial-literacy',
            'description': 'Personal finance, budgeting, and investment basics',
            'icon': 'fas fa-chart-line',
            'color': '#28a745'
        },
        {
            'name': 'Leadership Development',
            'slug': 'leadership-development',
            'description': 'Team management, communication, and leadership skills',
            'icon': 'fas fa-users',
            'color': '#17a2b8'
        },
        {
            'name': 'Technology Skills',
            'slug': 'technology-skills',
            'description': 'Computer literacy, software training, and digital tools',
            'icon': 'fas fa-laptop',
            'color': '#6f42c1'
        }
    ]
    
    created_specializations = []
    for spec_data in specializations_data:
        specialization, created = Specialization.objects.get_or_create(
            slug=spec_data['slug'],
            defaults=spec_data
        )
        created_specializations.append(specialization)
        status = "✅ Created" if created else "📝 Updated"
        print(f"   {status}: {specialization.name}")
    
    # Step 2: Create Test Instructors
    print("\n👨‍🏫 Creating Test Instructors...")
    instructors_data = [
        {
            'username': 'instructor_admin',
            'email': 'admin@yitp.com',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'role': 'system_admin',
            'specializations': ['digital-marketing', 'entrepreneurship'],
            'bio': 'Experienced educator and system administrator with 10+ years in digital education.',
            'qualifications': 'MBA in Business Administration, Certified Digital Marketing Professional',
            'years_experience': 10
        },
        {
            'username': 'instructor_marketing',
            'email': 'marketing@yitp.com',
            'first_name': 'Michael',
            'last_name': 'Chen',
            'role': 'course_instructor',
            'specializations': ['digital-marketing', 'technology-skills'],
            'bio': 'Digital marketing expert specializing in social media and content strategy.',
            'qualifications': 'MS in Digital Marketing, Google Ads Certified, Facebook Blueprint Certified',
            'years_experience': 7
        },
        {
            'username': 'instructor_business',
            'email': 'business@yitp.com',
            'first_name': 'Emily',
            'last_name': 'Rodriguez',
            'role': 'course_instructor',
            'specializations': ['entrepreneurship', 'financial-literacy'],
            'bio': 'Entrepreneur and business consultant helping young people start their own ventures.',
            'qualifications': 'MBA in Entrepreneurship, CPA, Small Business Development Center Advisor',
            'years_experience': 12
        },
        {
            'username': 'instructor_leadership',
            'email': 'leadership@yitp.com',
            'first_name': 'David',
            'last_name': 'Thompson',
            'role': 'course_instructor',
            'specializations': ['leadership-development'],
            'bio': 'Leadership coach and organizational development specialist.',
            'qualifications': 'PhD in Organizational Psychology, Certified Executive Coach',
            'years_experience': 15
        },
        {
            'username': 'teaching_assistant',
            'email': 'ta@yitp.com',
            'first_name': 'Jessica',
            'last_name': 'Williams',
            'role': 'teaching_assistant',
            'specializations': ['technology-skills'],
            'bio': 'Graduate student and teaching assistant specializing in technology education.',
            'qualifications': 'MS in Education Technology (in progress), CompTIA A+ Certified',
            'years_experience': 2
        }
    ]
    
    created_instructors = []
    for instructor_data in instructors_data:
        # Create or get user
        user, user_created = User.objects.get_or_create(
            username=instructor_data['username'],
            defaults={
                'email': instructor_data['email'],
                'first_name': instructor_data['first_name'],
                'last_name': instructor_data['last_name'],
                'is_staff': True,
                'is_active': True
            }
        )
        
        if user_created:
            user.set_password('instructor123')  # Default password for testing
            user.save()
        
        # Create or get instructor profile
        instructor_profile, profile_created = InstructorProfile.objects.get_or_create(
            user=user,
            defaults={
                'instructor_role': instructor_data['role'],
                'bio': instructor_data['bio'],
                'qualifications': instructor_data['qualifications'],
                'years_experience': instructor_data['years_experience'],
                'verification_status': 'verified',
                'verified_at': timezone.now(),
                'is_active': True,
                'can_create_courses': True,
                'can_manage_assessments': True,
                'can_view_analytics': True
            }
        )
        
        # Add specializations
        for spec_slug in instructor_data['specializations']:
            try:
                specialization = Specialization.objects.get(slug=spec_slug)
                instructor_profile.specializations.add(specialization)
            except Specialization.DoesNotExist:
                print(f"   ⚠️  Specialization '{spec_slug}' not found")
        
        created_instructors.append((user, instructor_profile))
        status = "✅ Created" if profile_created else "📝 Updated"
        print(f"   {status}: {user.get_full_name()} ({instructor_profile.get_instructor_role_display()})")
    
    # Step 3: Create Test Messages
    print("\n💬 Creating Test Messages...")
    
    # Get a student user (create if doesn't exist)
    student_user, _ = User.objects.get_or_create(
        username='test_student',
        defaults={
            'email': 'student@yitp.com',
            'first_name': 'Alex',
            'last_name': 'Student',
            'is_active': True
        }
    )
    
    messages_data = [
        {
            'sender': student_user,
            'recipient': created_instructors[1][0],  # Marketing instructor
            'subject': 'Question about Digital Marketing Lesson 1',
            'content': 'Hi Mr. Chen, I have a question about the social media strategy lesson. Could you explain more about content calendars and how to create an effective posting schedule? Thank you!'
        },
        {
            'sender': student_user,
            'recipient': created_instructors[2][0],  # Business instructor
            'subject': 'Help with Business Plan Assignment',
            'content': 'Dear Ms. Rodriguez, I\'m working on my business plan assignment and I\'m struggling with the financial projections section. Could we schedule a time to discuss this? I want to make sure I understand the concepts correctly.'
        },
        {
            'sender': student_user,
            'recipient': created_instructors[1][0],  # Marketing instructor
            'subject': 'Quiz Question Clarification',
            'content': 'Hello, I just completed the Digital Marketing Quiz but I\'m not sure about question 5 regarding SEO keywords. Could you provide some additional explanation about long-tail vs short-tail keywords?'
        }
    ]
    
    for msg_data in messages_data:
        message, created = Message.objects.get_or_create(
            sender=msg_data['sender'],
            recipient=msg_data['recipient'],
            subject=msg_data['subject'],
            defaults={
                'content': msg_data['content'],
                'sent_at': timezone.now() - timedelta(hours=2)
            }
        )
        status = "✅ Created" if created else "📝 Exists"
        print(f"   {status}: {message.subject}")
    
    # Step 4: Update existing courses with instructor assignments
    print("\n📖 Updating Course Instructor Assignments...")

    # Get all available courses
    available_courses = Course.objects.all()
    print(f"   Found {available_courses.count()} courses to assign instructors to")

    for course in available_courses:
        print(f"   Processing course: {course.title}")

        # Assign marketing instructor as primary instructor for first course
        if "Digital" in course.title or "Introduction" in course.title:
            marketing_instructor = created_instructors[1][0]  # instructor_marketing
            course.instructor = marketing_instructor
            course.save()

            # Create course instructor assignment
            course_assignment, created = CourseInstructor.objects.get_or_create(
                course=course,
                instructor=marketing_instructor,
                defaults={
                    'assignment_role': 'primary_instructor',
                    'can_edit_content': True,
                    'can_manage_enrollments': True,
                    'can_grade_assessments': True,
                    'can_view_analytics': True,
                    'can_communicate_students': True,
                    'can_publish_course': True,
                    'assigned_by': created_instructors[0][0],  # System admin
                    'is_active': True
                }
            )

            status = "✅ Created" if created else "📝 Updated"
            print(f"     {status}: {marketing_instructor.get_full_name()} assigned as primary instructor")

            # Add teaching assistant
            ta_user = created_instructors[4][0]  # teaching_assistant
            ta_assignment, created = CourseInstructor.objects.get_or_create(
                course=course,
                instructor=ta_user,
                defaults={
                    'assignment_role': 'teaching_assistant',
                    'can_edit_content': False,
                    'can_manage_enrollments': False,
                    'can_grade_assessments': True,
                    'can_view_analytics': True,
                    'can_communicate_students': True,
                    'can_publish_course': False,
                    'assigned_by': created_instructors[0][0],  # System admin
                    'is_active': True
                }
            )

            status = "✅ Created" if created else "📝 Updated"
            print(f"     {status}: {ta_user.get_full_name()} assigned as TA")

        # Assign business instructor to entrepreneurship course
        elif "Entrepreneurship" in course.title or "Business" in course.title:
            business_instructor = created_instructors[2][0]  # instructor_business
            course.instructor = business_instructor
            course.save()

            # Create course instructor assignment
            course_assignment, created = CourseInstructor.objects.get_or_create(
                course=course,
                instructor=business_instructor,
                defaults={
                    'assignment_role': 'primary_instructor',
                    'can_edit_content': True,
                    'can_manage_enrollments': True,
                    'can_grade_assessments': True,
                    'can_view_analytics': True,
                    'can_communicate_students': True,
                    'can_publish_course': True,
                    'assigned_by': created_instructors[0][0],  # System admin
                    'is_active': True
                }
            )

            status = "✅ Created" if created else "📝 Updated"
            print(f"     {status}: {business_instructor.get_full_name()} assigned as primary instructor")

        else:
            # Assign to marketing instructor as default
            marketing_instructor = created_instructors[1][0]
            course.instructor = marketing_instructor
            course.save()
            print(f"     📝 Assigned {marketing_instructor.get_full_name()} as default instructor")
    
    # Step 5: Summary
    print("\n" + "=" * 60)
    print("✅ INSTRUCTOR ROLE SYSTEM TEST DATA CREATION COMPLETE!")
    print("=" * 60)
    print(f"📚 Created {len(created_specializations)} specializations")
    print(f"👨‍🏫 Created {len(created_instructors)} instructor profiles")
    print(f"💬 Created {len(messages_data)} test messages")
    print("\n🔐 Test Login Credentials:")
    print("   System Admin: instructor_admin / instructor123")
    print("   Marketing Instructor: instructor_marketing / instructor123")
    print("   Business Instructor: instructor_business / instructor123")
    print("   Leadership Instructor: instructor_leadership / instructor123")
    print("   Teaching Assistant: teaching_assistant / instructor123")
    print("\n🌐 Access URLs:")
    print("   Instructor Dashboard: /users/instructor/")
    print("   Django Admin: /admin/")
    print("   Course Management: /users/instructor/courses/")
    print("   Analytics: /users/instructor/analytics/")
    print("   Messages: /users/instructor/messages/")
    print("\n🎯 Next Steps:")
    print("   1. Login with any instructor account")
    print("   2. Test role-based admin filtering")
    print("   3. Create courses with CKEditor")
    print("   4. Test quiz builder interface")
    print("   5. Review analytics dashboard")
    print("   6. Test message system")


if __name__ == '__main__':
    create_instructor_test_data()
