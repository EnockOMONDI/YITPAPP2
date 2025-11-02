#!/usr/bin/env python3
"""
Configure super admin user (info@youthimpactglobal.com) with complete course access and certificates
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from progress.models import QuizAttempt, LessonProgress, Enrollment, Certificate

class SuperAdminSetup:
    def __init__(self):
        self.admin_email = 'info@youthimpactglobal.com'
        self.admin_user = None
        self.course = None
        self.enrollment = None
        self.setup_results = {
            'user_created': False,
            'user_configured': False,
            'enrollment_created': False,
            'lessons_completed': 0,
            'quizzes_passed': 0,
            'certificate_generated': False,
            'errors': []
        }
    
    def setup_super_admin_user(self):
        """Create or configure super admin user"""
        
        print(f"👤 SETTING UP SUPER ADMIN USER")
        print("=" * 50)
        
        try:
            # Try to get existing user
            self.admin_user = User.objects.get(email=self.admin_email)
            print(f"✅ Found existing user: {self.admin_user.username}")
            
        except User.DoesNotExist:
            # Create new user
            print(f"🆕 Creating new user: {self.admin_email}")
            
            username = self.admin_email.split('@')[0]  # 'info'
            
            self.admin_user = User.objects.create_user(
                username=username,
                email=self.admin_email,
                password='YITPAdmin2024!',  # Strong password
                first_name='YITP',
                last_name='Administrator'
            )
            
            self.setup_results['user_created'] = True
            print(f"✅ Created user: {self.admin_user.username}")
        
        # Configure admin privileges
        if not self.admin_user.is_superuser or not self.admin_user.is_staff:
            self.admin_user.is_superuser = True
            self.admin_user.is_staff = True
            self.admin_user.is_active = True
            self.admin_user.save()
            
            print(f"✅ Configured admin privileges")
            self.setup_results['user_configured'] = True
        else:
            print(f"✅ User already has admin privileges")
        
        print(f"📊 User Status:")
        print(f"   • Username: {self.admin_user.username}")
        print(f"   • Email: {self.admin_user.email}")
        print(f"   • Superuser: {self.admin_user.is_superuser}")
        print(f"   • Staff: {self.admin_user.is_staff}")
        print(f"   • Active: {self.admin_user.is_active}")
        
        return True
    
    def setup_course_enrollment(self):
        """Create or verify course enrollment"""
        
        print(f"\n📚 SETTING UP COURSE ENROLLMENT")
        print("=" * 50)
        
        try:
            self.course = Course.objects.get(slug='youth-impact-training-programme-yitp')
            print(f"✅ Found course: {self.course.title}")
        except Course.DoesNotExist:
            print(f"❌ Course not found")
            self.setup_results['errors'].append("Course not found")
            return False
        
        # Check for existing enrollment
        try:
            self.enrollment = Enrollment.objects.get(
                student=self.admin_user,
                course=self.course
            )
            print(f"✅ Found existing enrollment")

        except Enrollment.DoesNotExist:
            # Create new enrollment
            print(f"🆕 Creating course enrollment")

            self.enrollment = Enrollment.objects.create(
                student=self.admin_user,
                course=self.course,
                enrollment_date=timezone.now(),
                status='completed',  # Mark as completed
                enrollment_type='paid'
            )
            
            self.setup_results['enrollment_created'] = True
            print(f"✅ Created course enrollment")
        
        # Ensure enrollment is properly configured
        if self.enrollment.status != 'completed':
            self.enrollment.status = 'completed'
            self.enrollment.save()
            print(f"✅ Updated enrollment status to completed")

        print(f"📊 Enrollment Status:")
        print(f"   • Course: {self.enrollment.course.title}")
        print(f"   • Status: {self.enrollment.status}")
        print(f"   • Type: {self.enrollment.enrollment_type}")
        print(f"   • Enrollment Date: {self.enrollment.enrollment_date}")
        
        return True
    
    def complete_all_lessons(self):
        """Mark all lessons as completed with 100% progress"""
        
        print(f"\n📖 COMPLETING ALL LESSONS")
        print("=" * 50)
        
        modules = Module.objects.filter(course=self.course).order_by('sort_order')
        total_lessons = 0
        completed_lessons = 0
        
        for module in modules:
            print(f"\n📚 Processing Module {module.sort_order}: {module.title}")
            
            lessons = Lesson.objects.filter(module=module).order_by('sort_order')
            
            for lesson in lessons:
                total_lessons += 1
                
                # Check for existing progress
                lesson_progress, created = LessonProgress.objects.get_or_create(
                    enrollment=self.enrollment,
                    lesson=lesson,
                    defaults={
                        'status': 'completed',
                        'started_at': timezone.now() - timedelta(hours=1),
                        'completed_at': timezone.now(),
                        'time_spent': 3600,  # 1 hour in seconds
                        'attempts': 1,
                        'score': Decimal('100.00')
                    }
                )

                if lesson_progress.status != 'completed':
                    lesson_progress.status = 'completed'
                    lesson_progress.completed_at = timezone.now()
                    lesson_progress.score = Decimal('100.00')
                    lesson_progress.save()
                
                completed_lessons += 1
                status = "🆕" if created else "✅"
                print(f"   {status} {lesson.title}")
        
        self.setup_results['lessons_completed'] = completed_lessons
        
        print(f"\n📊 Lesson Completion Summary:")
        print(f"   • Total lessons: {total_lessons}")
        print(f"   • Completed lessons: {completed_lessons}")
        print(f"   • Completion rate: 100%")
        
        return True
    
    def pass_all_quizzes(self):
        """Create passing quiz attempts for all quizzes"""
        
        print(f"\n🧪 PASSING ALL QUIZZES")
        print("=" * 50)
        
        modules = Module.objects.filter(course=self.course).order_by('sort_order')
        total_quizzes = 0
        passed_quizzes = 0
        
        for module in modules:
            print(f"\n📚 Processing Module {module.sort_order}: {module.title}")
            
            lessons = Lesson.objects.filter(module=module).order_by('sort_order')
            
            for lesson in lessons:
                quizzes = Quiz.objects.filter(lesson=lesson)
                
                for quiz in quizzes:
                    total_quizzes += 1
                    
                    # Check for existing passing attempt
                    existing_attempt = QuizAttempt.objects.filter(
                        student=self.admin_user,
                        enrollment=self.enrollment,
                        quiz=quiz,
                        is_passed=True
                    ).first()
                    
                    if not existing_attempt:
                        # Generate perfect answers for all questions
                        questions = Question.objects.filter(quiz=quiz)
                        perfect_answers = {}
                        
                        for question in questions:
                            if question.question_type == 'multiple_choice':
                                perfect_answers[str(question.id)] = question.correct_answer
                            elif question.question_type == 'true_false':
                                perfect_answers[str(question.id)] = question.correct_answer
                            else:
                                # For any other question types, use correct answer
                                perfect_answers[str(question.id)] = question.correct_answer
                        
                        # Create perfect quiz attempt
                        quiz_attempt = QuizAttempt.objects.create(
                            student=self.enrollment.student,
                            enrollment=self.enrollment,
                            quiz=quiz,
                            attempt_number=1,
                            score=Decimal('100.00'),
                            answers=perfect_answers,
                            is_passed=True,
                            started_at=timezone.now() - timedelta(minutes=10),
                            completed_at=timezone.now()
                        )
                        
                        passed_quizzes += 1
                        print(f"   🆕 {lesson.title} - {quiz.title}: 100% PASS")
                    else:
                        passed_quizzes += 1
                        print(f"   ✅ {lesson.title} - {quiz.title}: Already passed")
        
        self.setup_results['quizzes_passed'] = passed_quizzes
        
        print(f"\n📊 Quiz Completion Summary:")
        print(f"   • Total quizzes: {total_quizzes}")
        print(f"   • Passed quizzes: {passed_quizzes}")
        print(f"   • Pass rate: 100%")
        
        return True
    
    def generate_certificate(self):
        """Generate course completion certificate"""
        
        print(f"\n🏆 GENERATING COURSE COMPLETION CERTIFICATE")
        print("=" * 50)
        
        # Check for existing certificate
        existing_certificate = Certificate.objects.filter(
            enrollment=self.enrollment
        ).first()

        if existing_certificate:
            print(f"✅ Certificate already exists")
            print(f"   • Certificate ID: {existing_certificate.certificate_id}")
            print(f"   • Issue Date: {existing_certificate.issued_date}")
            self.setup_results['certificate_generated'] = True
            return True

        # Generate new certificate
        try:
            certificate = Certificate.objects.create(
                enrollment=self.enrollment,
                certificate_type='completion',
                issued_date=timezone.now(),
                final_score=Decimal('100.00'),
                certificate_data={
                    'student_name': f"{self.admin_user.first_name} {self.admin_user.last_name}",
                    'course_title': self.course.title,
                    'completion_date': timezone.now().isoformat(),
                    'grade': 'A+',
                    'total_score': '100%'
                }
            )
            
            print(f"✅ Certificate generated successfully")
            print(f"   • Certificate ID: {certificate.certificate_id}")
            print(f"   • Issue Date: {certificate.issued_date}")
            print(f"   • Student: {certificate.enrollment.student.get_full_name()}")
            print(f"   • Course: {certificate.enrollment.course.title}")
            
            self.setup_results['certificate_generated'] = True
            return True
            
        except Exception as e:
            error_msg = f"Error generating certificate: {e}"
            print(f"❌ {error_msg}")
            self.setup_results['errors'].append(error_msg)
            return False

    def verify_setup(self):
        """Verify all setup requirements are met"""

        print(f"\n🔍 VERIFYING SETUP COMPLETION")
        print("=" * 50)

        verification_results = {
            'user_exists': False,
            'user_is_admin': False,
            'enrollment_exists': False,
            'enrollment_paid': False,
            'all_lessons_completed': False,
            'all_quizzes_passed': False,
            'certificate_issued': False,
            'dashboard_accessible': False
        }

        # Verify user
        try:
            user = User.objects.get(email=self.admin_email)
            verification_results['user_exists'] = True
            verification_results['user_is_admin'] = user.is_superuser and user.is_staff
            print(f"✅ User exists: {user.username}")
            print(f"✅ Admin privileges: {verification_results['user_is_admin']}")
        except User.DoesNotExist:
            print(f"❌ User not found")

        # Verify enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=self.admin_user,
                course=self.course
            )
            verification_results['enrollment_exists'] = True
            verification_results['enrollment_paid'] = enrollment.status == 'completed'
            print(f"✅ Enrollment exists: {enrollment.course.title}")
            print(f"✅ Status completed: {verification_results['enrollment_paid']}")
        except Enrollment.DoesNotExist:
            print(f"❌ Enrollment not found")

        # Verify lesson completion
        total_lessons = Lesson.objects.filter(module__course=self.course).count()
        completed_lessons = LessonProgress.objects.filter(
            enrollment=self.enrollment,
            lesson__module__course=self.course,
            status='completed'
        ).count()

        verification_results['all_lessons_completed'] = completed_lessons == total_lessons
        print(f"✅ Lessons completed: {completed_lessons}/{total_lessons}")

        # Verify quiz completion
        total_quizzes = Quiz.objects.filter(lesson__module__course=self.course).count()
        passed_quizzes = QuizAttempt.objects.filter(
            enrollment=self.enrollment,
            quiz__lesson__module__course=self.course,
            is_passed=True
        ).count()

        verification_results['all_quizzes_passed'] = passed_quizzes == total_quizzes
        print(f"✅ Quizzes passed: {passed_quizzes}/{total_quizzes}")

        # Verify certificate
        try:
            certificate = Certificate.objects.get(
                enrollment=self.enrollment
            )
            verification_results['certificate_issued'] = True
            print(f"✅ Certificate issued: {certificate.certificate_id}")
        except Certificate.DoesNotExist:
            print(f"❌ Certificate not found")

        # Overall verification
        all_verified = all(verification_results.values())

        print(f"\n📊 VERIFICATION SUMMARY:")
        for key, value in verification_results.items():
            status = "✅" if value else "❌"
            print(f"   {status} {key.replace('_', ' ').title()}: {value}")

        if all_verified:
            print(f"\n🎯 VERIFICATION RESULT: ✅ COMPLETE SUCCESS!")
            print(f"   • All requirements met")
            print(f"   • Super admin fully configured")
            print(f"   • Course access granted")
            print(f"   • Certificate available")
        else:
            print(f"\n🎯 VERIFICATION RESULT: ⚠️  PARTIAL SUCCESS")
            print(f"   • Some requirements not met")
            print(f"   • Review failed items above")

        return all_verified, verification_results

    def generate_setup_report(self, verification_results):
        """Generate comprehensive setup report"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"super_admin_setup_report_{timestamp}.md"

        report_content = f"""# Super Admin Setup Report

## Summary
- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Admin Email:** {self.admin_email}
- **Course:** {self.course.title if self.course else 'N/A'}

## Setup Results

### User Configuration
- **User Created:** {self.setup_results['user_created']}
- **User Configured:** {self.setup_results['user_configured']}
- **Username:** {self.admin_user.username if self.admin_user else 'N/A'}
- **Superuser:** {self.admin_user.is_superuser if self.admin_user else False}
- **Staff:** {self.admin_user.is_staff if self.admin_user else False}

### Course Access
- **Enrollment Created:** {self.setup_results['enrollment_created']}
- **Status:** {self.enrollment.status if self.enrollment else 'N/A'}
- **Lessons Completed:** {self.setup_results['lessons_completed']}
- **Quizzes Passed:** {self.setup_results['quizzes_passed']}
- **Certificate Generated:** {self.setup_results['certificate_generated']}

## Verification Results

"""

        for key, value in verification_results.items():
            status = "✅ PASS" if value else "❌ FAIL"
            report_content += f"- **{key.replace('_', ' ').title()}:** {status}\n"

        if self.setup_results['errors']:
            report_content += f"""

## Errors Encountered

"""
            for error in self.setup_results['errors']:
                report_content += f"- {error}\n"

        report_content += f"""

## Next Steps

1. **Login Test:** User can log in at `/admin/` or `/users/student/`
2. **Dashboard Access:** Verify certificate is visible on student dashboard
3. **Course Navigation:** Test access to all modules and lessons
4. **Certificate Download:** Verify certificate PDF can be downloaded

## Access Information

- **Login URL:** `/admin/` (admin interface) or `/users/student/` (student dashboard)
- **Username:** {self.admin_user.username if self.admin_user else 'N/A'}
- **Email:** {self.admin_email}
- **Password:** YITPAdmin2024! (change after first login)

---
*Report generated by setup_super_admin_complete_access.py*
"""

        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"📄 Setup report saved: {report_filename}")
            return report_filename

        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return None

def main():
    print("👤 SETTING UP SUPER ADMIN WITH COMPLETE COURSE ACCESS")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 Admin Email: info@youthimpactglobal.com")
    print(f"🎯 Goal: Complete course access with certificate")

    setup = SuperAdminSetup()

    # Step 1: Setup user
    if not setup.setup_super_admin_user():
        print(f"❌ Failed to setup user")
        return

    # Step 2: Setup enrollment
    if not setup.setup_course_enrollment():
        print(f"❌ Failed to setup enrollment")
        return

    # Step 3: Complete all lessons
    if not setup.complete_all_lessons():
        print(f"❌ Failed to complete lessons")
        return

    # Step 4: Pass all quizzes
    if not setup.pass_all_quizzes():
        print(f"❌ Failed to pass quizzes")
        return

    # Step 5: Generate certificate
    if not setup.generate_certificate():
        print(f"❌ Failed to generate certificate")
        return

    # Step 6: Verify setup
    all_verified, verification_results = setup.verify_setup()

    # Step 7: Generate report
    report_file = setup.generate_setup_report(verification_results)

    # Final summary
    print(f"\n🎉 SUPER ADMIN SETUP COMPLETED!")
    print("=" * 60)

    if all_verified:
        print(f"✅ COMPLETE SUCCESS!")
        print(f"   • User configured with admin privileges")
        print(f"   • Course enrollment completed")
        print(f"   • All lessons and quizzes completed")
        print(f"   • Certificate generated and issued")
        print(f"   • Dashboard access ready")
    else:
        print(f"⚠️  PARTIAL SUCCESS")
        print(f"   • Some setup steps had issues")
        print(f"   • Review verification results above")

    if report_file:
        print(f"\n📄 Detailed report: {report_file}")

    print(f"\n🔄 Next Steps:")
    print(f"1. 🔐 Test login at /admin/ or /users/student/")
    print(f"2. 📊 Verify dashboard shows certificate")
    print(f"3. 📚 Test course navigation and access")
    print(f"4. 🏆 Download and verify certificate PDF")

    print(f"\n🔑 Login Credentials:")
    print(f"   • Email: info@youthimpactglobal.com")
    print(f"   • Username: info")
    print(f"   • Password: YITPAdmin2024!")

if __name__ == "__main__":
    main()
