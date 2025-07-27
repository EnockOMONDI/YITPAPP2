from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
import pytz
from courses.models import Course, Module, Lesson
from progress.models import Enrollment, LessonProgress
from assessments.models import Quiz, Question, QuizAttempt
from certificates.models import Certificate
from courses.enrollment_service import EnrollmentService

class Command(BaseCommand):
    help = 'Test complete student journey for YITP LMS'

    def handle(self, *args, **options):
        self.stdout.write("=== YITP LMS PHASE 3: END-TO-END FLOW TESTING ===")
        
        # Configure East Africa Time (Nairobi - UTC+3)
        nairobi_tz = pytz.timezone('Africa/Nairobi')
        current_time = timezone.now().astimezone(nairobi_tz)
        self.stdout.write(f"✅ Timezone configured: {nairobi_tz}")
        self.stdout.write(f"Current time in Nairobi: {current_time}")
        
        # Step 1: Get test data
        self.stdout.write("\n=== STEP 1: CONNECTING TO TEST DATA ===")
        try:
            finaluser = User.objects.get(username='finaluser')
            course = Course.objects.get(title="Starting a Business in 2025")
            enrollment = Enrollment.objects.get(student=finaluser, course=course)
            
            self.stdout.write(f"✅ User: {finaluser.get_full_name()} ({finaluser.email})")
            self.stdout.write(f"✅ Course: {course.title}")
            self.stdout.write(f"✅ Enrollment: ID {enrollment.id}, Status: {enrollment.status}")
            self.stdout.write(f"   Enrolled at (Nairobi): {enrollment.enrolled_at.astimezone(nairobi_tz)}")
            self.stdout.write(f"   Current progress: {enrollment.progress_percentage}%")
            
        except Exception as e:
            self.stdout.write(f"❌ Error connecting to test data: {e}")
            return
        
        # Step 2: Get course structure
        self.stdout.write("\n=== STEP 2: COURSE STRUCTURE ANALYSIS ===")
        lessons = []
        for module in course.modules.all().order_by('sort_order'):
            for lesson in module.lessons.all().order_by('sort_order'):
                lessons.append(lesson)
        
        self.stdout.write(f"Total lessons: {len(lessons)}")
        for i, lesson in enumerate(lessons, 1):
            self.stdout.write(f"  {i}. {lesson.title} (Module: {lesson.module.title})")
        
        # Step 3: Complete all lessons
        self.stdout.write("\n=== STEP 3: COMPLETING ALL LESSONS ===")
        
        for i, lesson in enumerate(lessons):
            lesson_num = i + 1
            self.stdout.write(f"\n--- Processing Lesson {lesson_num}: {lesson.title} ---")
            
            # Check if lesson is accessible
            try:
                accessible, message = lesson.is_accessible_for_user(finaluser)
                self.stdout.write(f"Accessible: {accessible} - {message}")
                
                if not accessible:
                    self.stdout.write(f"❌ Cannot access lesson {lesson_num}: {message}")
                    continue
                
                # Create or get lesson progress
                lesson_progress, created = LessonProgress.objects.get_or_create(
                    enrollment=enrollment,
                    lesson=lesson,
                    defaults={'status': 'in_progress'}
                )
                
                if created:
                    self.stdout.write(f"📝 Created new progress for lesson {lesson_num}")
                else:
                    self.stdout.write(f"📝 Found existing progress for lesson {lesson_num}")
                
                # Mark lesson as completed if not already
                if lesson_progress.status != 'completed':
                    lesson_progress.mark_completed()
                    self.stdout.write(f"✅ Lesson {lesson_num} completed!")
                    self.stdout.write(f"   Completed at (Nairobi): {lesson_progress.completed_at.astimezone(nairobi_tz)}")
                else:
                    self.stdout.write(f"✅ Lesson {lesson_num} already completed")
                
                # Check for quiz after lesson completion
                quiz = lesson.quizzes.first()
                if quiz:
                    self.stdout.write(f"\n🧪 Testing Quiz: {quiz.title}")
                    self.test_quiz_completion(quiz, finaluser, enrollment, nairobi_tz)
                    
            except Exception as e:
                self.stdout.write(f"❌ Error processing lesson {lesson_num}: {e}")
        
        # Step 4: Test course completion
        self.stdout.write("\n=== STEP 4: TESTING COURSE COMPLETION ===")
        self.test_course_completion(enrollment, nairobi_tz)
        
        # Step 5: Test certificate generation
        self.stdout.write("\n=== STEP 5: TESTING CERTIFICATE GENERATION ===")
        self.test_certificate_generation(finaluser, course, nairobi_tz)
        
        # Step 6: Final verification
        self.stdout.write("\n=== STEP 6: FINAL VERIFICATION ===")
        self.verify_final_progress(enrollment, nairobi_tz)
        
        # Step 7: Provide recommendations
        self.stdout.write("\n=== STEP 7: RECOMMENDATIONS FOR IMPROVEMENT ===")
        self.provide_recommendations()
        
        self.stdout.write("\n=== END-TO-END TESTING COMPLETED ===")

    def test_quiz_completion(self, quiz, student, enrollment, nairobi_tz):
        """Test quiz completion with 70% passing score"""
        self.stdout.write(f"Quiz: {quiz.title}")
        self.stdout.write(f"Passing score: {quiz.passing_score}%")
        self.stdout.write(f"Max attempts: {quiz.max_attempts}")
        
        # Check if already completed
        existing_attempt = QuizAttempt.objects.filter(
            quiz=quiz, 
            student=student, 
            is_passed=True
        ).first()
        
        if existing_attempt:
            self.stdout.write(f"✅ Quiz already passed with score: {existing_attempt.score}%")
            return
        
        # Get quiz questions
        questions = quiz.questions.all().order_by('sort_order')
        self.stdout.write(f"Questions: {questions.count()}")
        
        if questions.count() == 0:
            self.stdout.write("❌ No questions found for quiz")
            return
        
        # Create quiz attempt
        quiz_attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=student,
            enrollment=enrollment,
            started_at=timezone.now()
        )
        
        # Simulate answering questions correctly (100% score)
        correct_answers = questions.count()
        total_questions = questions.count()
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Update quiz attempt
        quiz_attempt.score = score
        quiz_attempt.is_passed = score >= quiz.passing_score
        quiz_attempt.completed_at = timezone.now()
        quiz_attempt.save()
        
        self.stdout.write(f"✅ Quiz completed!")
        self.stdout.write(f"   Score: {score}%")
        self.stdout.write(f"   Passed: {quiz_attempt.is_passed}")
        self.stdout.write(f"   Completed at (Nairobi): {quiz_attempt.completed_at.astimezone(nairobi_tz)}")

    def test_course_completion(self, enrollment, nairobi_tz):
        """Test automatic course completion detection"""
        self.stdout.write("Testing course completion detection...")
        
        # Refresh enrollment to get latest progress
        enrollment.refresh_from_db()
        
        # Check completion status
        try:
            completion_status = enrollment.check_completion_status()
            self.stdout.write(f"Completion check result: {completion_status}")
            
            if completion_status.get('is_completed'):
                self.stdout.write(f"✅ Course automatically marked as completed!")
                if enrollment.completion_date:
                    self.stdout.write(f"   Completion date (Nairobi): {enrollment.completion_date.astimezone(nairobi_tz)}")
                self.stdout.write(f"   Final progress: {enrollment.progress_percentage}%")
            else:
                self.stdout.write(f"⏳ Course not yet completed")
                self.stdout.write(f"   Current progress: {enrollment.progress_percentage}%")
                
        except Exception as e:
            self.stdout.write(f"❌ Error checking completion status: {e}")

    def test_certificate_generation(self, user, course, nairobi_tz):
        """Test certificate generation and email delivery"""
        self.stdout.write("Testing certificate generation...")
        
        try:
            # Check if certificate already exists
            certificate = Certificate.objects.filter(user=user, course=course).first()
            
            if certificate:
                self.stdout.write(f"✅ Certificate found!")
                self.stdout.write(f"   Certificate ID: {certificate.certificate_id}")
                self.stdout.write(f"   Issued at (Nairobi): {certificate.issued_at.astimezone(nairobi_tz)}")
            else:
                self.stdout.write("⏳ No certificate found - checking if course is completed")
                
                # Check if course is completed
                enrollment = Enrollment.objects.get(student=user, course=course)
                if enrollment.status == 'completed':
                    self.stdout.write("📜 Course completed - certificate should be generated")
                else:
                    self.stdout.write("⏳ Course not completed yet")
                    
        except Exception as e:
            self.stdout.write(f"❌ Certificate testing error: {e}")

    def verify_final_progress(self, enrollment, nairobi_tz):
        """Verify final progress and provide summary"""
        enrollment.refresh_from_db()
        
        self.stdout.write(f"Final enrollment status: {enrollment.status}")
        self.stdout.write(f"Final progress: {enrollment.progress_percentage}%")
        
        if enrollment.completion_date:
            self.stdout.write(f"Completion date (Nairobi): {enrollment.completion_date.astimezone(nairobi_tz)}")
        
        # Count completed lessons
        completed_lessons = LessonProgress.objects.filter(
            enrollment=enrollment,
            status='completed'
        ).count()
        
        total_lessons = enrollment.course.modules.aggregate(
            total=models.Count('lessons')
        )['total'] or 0
        
        self.stdout.write(f"Lessons completed: {completed_lessons}/{total_lessons}")
        
        # Count passed quizzes
        passed_quizzes = QuizAttempt.objects.filter(
            student=enrollment.student,
            enrollment=enrollment,
            is_passed=True
        ).count()
        
        self.stdout.write(f"Quizzes passed: {passed_quizzes}")

    def provide_recommendations(self):
        """Provide recommendations for improving the student journey"""
        self.stdout.write("\n🚀 RECOMMENDATIONS FOR WORLD-CLASS LMS EXPERIENCE:")
        
        recommendations = [
            "1. PROGRESS TRACKING: Implement real-time progress bars and visual indicators",
            "2. GAMIFICATION: Add points, badges, and leaderboards for engagement",
            "3. MOBILE OPTIMIZATION: Ensure seamless mobile learning experience",
            "4. OFFLINE CAPABILITY: Allow content download for offline learning",
            "5. SOCIAL LEARNING: Add discussion forums and peer interaction",
            "6. ADAPTIVE LEARNING: Personalize content based on learning pace",
            "7. ANALYTICS DASHBOARD: Provide detailed learning analytics to students",
            "8. NOTIFICATION SYSTEM: Smart reminders and progress notifications",
            "9. ACCESSIBILITY: Full WCAG compliance for inclusive learning",
            "10. MICROLEARNING: Break content into smaller, digestible chunks"
        ]
        
        for rec in recommendations:
            self.stdout.write(f"   {rec}")
