from django.core.management.base import BaseCommand
from courses.models import Course, Lesson

class Command(BaseCommand):
    help = 'Update YITP introductory course content with enhanced prerequisite messaging'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Updating YITP introductory course content...')
        
        try:
            # Find the YITP intro course
            course = Course.objects.get(title__icontains="Introduction to YITP")
            self.stdout.write(f'✅ Found course: {course.title}')
            
            # Find the lesson
            lesson = Lesson.objects.filter(module__course=course).first()
            if not lesson:
                self.stdout.write(self.style.ERROR('❌ No lesson found for the course'))
                return
            
            self.stdout.write(f'✅ Found lesson: {lesson.title}')
            
            # Enhanced lesson content with prerequisite messaging
            enhanced_content = """
            <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
                <!-- Enhanced Header with Prerequisite Notice -->
                <div style="background: linear-gradient(135deg, #341C67 0%, #ff5d15 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                    <h1 style="margin: 0; font-size: 2.5em;">Welcome to YITP! 🎓</h1>
                    <p style="margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9;">Your Learning Journey Begins Here</p>
                </div>

                <!-- Prerequisite Course Notice -->
                <div style="background: linear-gradient(135deg, rgba(255,93,21,0.1), rgba(26,46,83,0.1)); padding: 25px; border-radius: 10px; margin-bottom: 30px; border: 2px solid #ff5d15;">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h2 style="color: #341C67; margin: 0; font-size: 1.8em;">
                            <i style="color: #ff5d15;">⭐</i> PREREQUISITE COURSE <i style="color: #ff5d15;">⭐</i>
                        </h2>
                    </div>
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h3 style="color: #341C67; margin-top: 0;">
                            <i style="color: #ff5d15;">🚀</i> This is an introductory course designed to set you up on the YITP platform
                        </h3>
                        <p style="line-height: 1.6; color: #333; font-size: 1.1em;">
                            <strong style="color: #ff5d15;">Completion of this course is required before accessing other courses.</strong>
                            This mandatory course will introduce you to the YITP platform, learning system, and prepare you for your educational journey.
                        </p>
                        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
                            <span style="background: #ff5d15; color: white; padding: 8px 15px; border-radius: 20px; font-size: 0.9em; font-weight: 600;">
                                <i>⏱️</i> 25 minutes
                            </span>
                            <span style="background: #341C67; color: white; padding: 8px 15px; border-radius: 20px; font-size: 0.9em; font-weight: 600;">
                                <i>🎓</i> Beginner Level
                            </span>
                            <span style="background: #28a745; color: white; padding: 8px 15px; border-radius: 20px; font-size: 0.9em; font-weight: 600;">
                                <i>🎁</i> Free Course
                            </span>
                        </div>
                    </div>
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
                        
                        <h3 style="color: #ff5d15;">💬 Support System</h3>
                        <p style="color: #666; margin-left: 20px;">Access help resources, contact instructors, and connect with fellow learners.</p>
                    </div>
                </div>

                <div style="background: #fff; padding: 25px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #341C67; margin-top: 0;">📋 How YITP Courses Work</h2>
                    
                    <div style="margin: 20px 0;">
                        <h3 style="color: #ff5d15;">📖 Course Structure</h3>
                        <p style="color: #666; margin-left: 20px;">Each course is divided into modules, with each module containing multiple lessons and assessments.</p>
                        
                        <h3 style="color: #ff5d15;">✅ Assessments</h3>
                        <p style="color: #666; margin-left: 20px;">Complete quizzes and assignments to test your understanding. You need 70% to pass each quiz.</p>
                        
                        <h3 style="color: #ff5d15;">🏆 Certificates</h3>
                        <p style="color: #666; margin-left: 20px;">Earn completion certificates when you successfully finish all course requirements.</p>
                        
                        <h3 style="color: #ff5d15;">⏰ Flexible Learning</h3>
                        <p style="color: #666; margin-left: 20px;">Learn at your own pace with 24/7 access to course materials.</p>
                    </div>
                </div>

                <div style="background: #fff; padding: 25px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #341C67; margin-top: 0;">🎓 Getting Support</h2>
                    <p style="line-height: 1.6; color: #333;">
                        We're here to support you every step of the way! Here's how to get help when you need it:
                    </p>
                    
                    <div style="margin: 20px 0;">
                        <h3 style="color: #ff5d15;">📧 Contact Information</h3>
                        <p style="color: #666; margin-left: 20px;">
                            <strong>Email:</strong> youthimpactglobal3@gmail.com<br>
                            <strong>Response Time:</strong> Within 24 hours
                        </p>
                        
                        <h3 style="color: #ff5d15;">❓ Help Resources</h3>
                        <p style="color: #666; margin-left: 20px;">Access our comprehensive help center and frequently asked questions.</p>
                        
                        <h3 style="color: #ff5d15;">👥 Community Support</h3>
                        <p style="color: #666; margin-left: 20px;">Connect with fellow learners and share your learning experience.</p>
                    </div>
                </div>

                <!-- Next Steps Section -->
                <div style="background: linear-gradient(135deg, rgba(255,93,21,0.1), rgba(26,46,83,0.1)); padding: 25px; border-radius: 10px; margin-bottom: 30px; border: 2px solid #341C67;">
                    <h2 style="color: #341C67; margin-top: 0; text-align: center;">🚀 Ready to Begin Your Journey?</h2>
                    <p style="line-height: 1.6; color: #333; text-align: center; font-size: 1.1em;">
                        Complete this introductory course and take the quiz to unlock access to our full range of courses.
                        Your transformational learning experience starts now!
                    </p>
                    <div style="text-align: center; margin-top: 20px;">
                        <p style="color: #ff5d15; font-weight: 600; font-size: 1.1em;">
                            <i>⭐</i> Remember: This course completion is mandatory for accessing other YITP courses <i>⭐</i>
                        </p>
                    </div>
                </div>

                <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <p style="margin: 0; color: #666; font-style: italic;">
                        "Education is the most powerful weapon which you can use to change the world." - Nelson Mandela
                    </p>
                </div>
            </div>
            """
            
            # Update the lesson content
            lesson.content = enhanced_content
            lesson.save()

            # Also update the course description to emphasize prerequisite status
            enhanced_description = """🌟 PREREQUISITE COURSE - START HERE 🌟

Welcome to the Youth Impact Training Programme! This is a MANDATORY introductory course designed to set you up on the YITP platform and prepare you for your transformational learning journey.

⭐ IMPORTANT: Completion of this course is REQUIRED before accessing other courses.

In this course, you will:
• Understand YITP's mission and how we're transforming lives through education
• Learn to navigate our learning platform effectively
• Discover how to track your progress and complete assignments
• Access support resources and contact information
• Prepare for your educational journey with YITP

This prerequisite course takes approximately 25 minutes to complete. Upon successful completion and quiz passing (70% required), the YITP team will review your progress and grant access to our full range of courses within 48 hours.

🚀 Your transformational learning experience starts here!"""

            course.description = enhanced_description
            course.save()

            self.stdout.write(self.style.SUCCESS('✅ Successfully updated lesson content and course description with enhanced prerequisite messaging'))
            self.stdout.write(f'📝 Updated lesson: {lesson.title}')
            self.stdout.write(f'📝 Updated course description: {course.title}')
            
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ YITP introductory course not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error updating course content: {str(e)}'))
