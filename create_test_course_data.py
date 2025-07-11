#!/usr/bin/env python
"""
Create comprehensive test data for Enhanced YITP LMS Learning Flow validation
This script creates a complete test course with lessons, quizzes, and user data
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question
from progress.models import Enrollment
from users.models import Profile


def create_test_course_data():
    """Create comprehensive test data for Enhanced Learning Flow validation"""
    
    print("🚀 Creating Enhanced YITP LMS Test Course Data")
    print("=" * 60)
    
    # Step 1: Create or get test category
    print("📂 Creating course category...")
    category, created = Category.objects.get_or_create(
        name="Digital Skills",
        defaults={
            'description': "Essential digital skills for the modern world",
            'is_active': True
        }
    )
    if created:
        print(f"✅ Created category: {category.name}")
    else:
        print(f"✅ Using existing category: {category.name}")
    
    # Step 2: Create test course
    print("\n📚 Creating test course...")

    # Get or create instructor (admin user)
    instructor, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@yitp.test',
            'first_name': 'YITP',
            'last_name': 'Admin',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    if created:
        instructor.set_password('admin123')
        instructor.save()
        print(f"✅ Created instructor: {instructor.username}")

    course, created = Course.objects.get_or_create(
        slug="intro-digital-skills-test",
        defaults={
            'title': "Introduction to Digital Skills",
            'description': """
            <h3>Welcome to Digital Skills Fundamentals</h3>
            <p>This comprehensive course will introduce you to essential digital skills needed in today's world.
            You'll learn about digital tools, computer basics, and internet safety.</p>

            <h4>What You'll Learn:</h4>
            <ul>
                <li>Essential digital tools and their applications</li>
                <li>Basic computer skills and navigation</li>
                <li>Internet safety and security fundamentals</li>
                <li>Best practices for digital communication</li>
            </ul>

            <h4>Course Features:</h4>
            <ul>
                <li>Interactive lessons with practical examples</li>
                <li>Knowledge assessment quizzes</li>
                <li>Progress tracking and achievements</li>
                <li>Certificate upon completion</li>
            </ul>

            <p><strong>Duration:</strong> 3 lessons • <strong>Level:</strong> Beginner • <strong>Price:</strong> FREE</p>
            """,
            'learning_objectives': "Master essential digital tools, develop computer navigation skills, understand internet safety principles, and apply digital communication best practices",
            'prerequisites': "Basic computer access and internet connection",
            'price': 0.00,  # Free course for testing
            'estimated_duration': 3,  # 3 hours total
            'category': category,
            'instructor': instructor,
            'is_published': True,
            'is_featured': True,
            'difficulty_level': 'beginner',
            'enrollment_limit': 1000
        }
    )
    if created:
        print(f"✅ Created course: {course.title}")
    else:
        print(f"✅ Using existing course: {course.title}")
    
    # Step 3: Create test module
    print("\n📖 Creating course module...")
    module, created = Module.objects.get_or_create(
        course=course,
        title="Digital Skills Fundamentals",
        defaults={
            'description': "Core digital skills every person should know",
            'sort_order': 1,
            'is_published': True,
            'estimated_duration': 180  # 180 minutes = 3 hours
        }
    )
    if created:
        print(f"✅ Created module: {module.title}")
    else:
        print(f"✅ Using existing module: {module.title}")
    
    # Step 4: Create test lessons
    print("\n📝 Creating test lessons...")
    
    # Lesson 1: With Quiz (to test quiz integration)
    lesson1, created = Lesson.objects.get_or_create(
        module=module,
        title="Getting Started with Digital Tools",
        defaults={
            'content_type': 'text',
            'content': """
            <h2>Welcome to Digital Tools</h2>
            
            <p>In this lesson, you'll discover the essential digital tools that can transform how you work, 
            communicate, and access information. Digital literacy is no longer optional—it's essential 
            for success in today's world.</p>
            
            <h3>What Are Digital Tools?</h3>
            <p>Digital tools are software applications, platforms, and technologies that help us:</p>
            <ul>
                <li><strong>Communicate:</strong> Email, messaging apps, video calls</li>
                <li><strong>Create:</strong> Document editors, design software, presentation tools</li>
                <li><strong>Organize:</strong> Calendar apps, task managers, cloud storage</li>
                <li><strong>Learn:</strong> Online courses, educational platforms, research tools</li>
                <li><strong>Collaborate:</strong> Shared documents, project management tools</li>
            </ul>
            
            <h3>Essential Digital Tools Categories</h3>
            
            <h4>1. Communication Tools</h4>
            <ul>
                <li><strong>Email:</strong> Gmail, Outlook, Yahoo Mail</li>
                <li><strong>Messaging:</strong> WhatsApp, Telegram, Slack</li>
                <li><strong>Video Conferencing:</strong> Zoom, Google Meet, Microsoft Teams</li>
            </ul>
            
            <h4>2. Productivity Tools</h4>
            <ul>
                <li><strong>Document Creation:</strong> Microsoft Word, Google Docs</li>
                <li><strong>Spreadsheets:</strong> Excel, Google Sheets</li>
                <li><strong>Presentations:</strong> PowerPoint, Google Slides</li>
            </ul>
            
            <h4>3. Storage and Organization</h4>
            <ul>
                <li><strong>Cloud Storage:</strong> Google Drive, Dropbox, OneDrive</li>
                <li><strong>Note Taking:</strong> Evernote, OneNote, Notion</li>
                <li><strong>Task Management:</strong> Todoist, Trello, Asana</li>
            </ul>
            
            <h3>Getting Started Tips</h3>
            <ol>
                <li><strong>Start Simple:</strong> Begin with basic tools like email and document editors</li>
                <li><strong>Practice Regularly:</strong> Use tools daily to build familiarity</li>
                <li><strong>Explore Features:</strong> Most tools have helpful tutorials and guides</li>
                <li><strong>Stay Updated:</strong> Digital tools evolve—keep learning new features</li>
            </ol>
            
            <div class="alert alert-info">
                <h4>💡 Pro Tip</h4>
                <p>Don't try to learn everything at once. Master one tool at a time, then gradually 
                expand your digital toolkit as your confidence grows.</p>
            </div>
            
            <h3>Next Steps</h3>
            <p>After completing this lesson and the assessment quiz, you'll move on to learning
            basic computer skills that will help you navigate these digital tools more effectively.</p>
            """,
            'sort_order': 1,
            'is_published': True,
            'estimated_duration': 45,
            'learning_objectives': "Understand digital tools categories, identify essential communication and productivity tools, learn best practices for digital tool adoption"
        }
    )
    if created:
        print(f"✅ Created lesson 1: {lesson1.title}")
    else:
        print(f"✅ Using existing lesson 1: {lesson1.title}")
    
    # Lesson 2: Without Quiz (for comparison)
    lesson2, created = Lesson.objects.get_or_create(
        module=module,
        title="Basic Computer Skills",
        defaults={
            'content_type': 'text',
            'content': """
            <h2>Essential Computer Skills</h2>
            
            <p>Building on your knowledge of digital tools, this lesson covers the fundamental 
            computer skills you need to navigate technology confidently and efficiently.</p>
            
            <h3>Computer Basics</h3>
            
            <h4>Understanding Your Computer</h4>
            <ul>
                <li><strong>Hardware:</strong> Physical components (monitor, keyboard, mouse, CPU)</li>
                <li><strong>Software:</strong> Programs and applications that run on your computer</li>
                <li><strong>Operating System:</strong> Windows, macOS, or Linux—your computer's main software</li>
            </ul>
            
            <h4>Essential Navigation Skills</h4>
            <ol>
                <li><strong>Desktop Management:</strong> Organizing icons, creating folders</li>
                <li><strong>File Management:</strong> Creating, saving, moving, and deleting files</li>
                <li><strong>Window Management:</strong> Opening, closing, minimizing, and resizing windows</li>
                <li><strong>Menu Navigation:</strong> Using right-click menus and application menus</li>
            </ol>
            
            <h3>Keyboard Shortcuts</h3>
            <p>Learn these time-saving shortcuts:</p>
            <ul>
                <li><strong>Ctrl+C / Cmd+C:</strong> Copy</li>
                <li><strong>Ctrl+V / Cmd+V:</strong> Paste</li>
                <li><strong>Ctrl+Z / Cmd+Z:</strong> Undo</li>
                <li><strong>Ctrl+S / Cmd+S:</strong> Save</li>
                <li><strong>Alt+Tab / Cmd+Tab:</strong> Switch between applications</li>
            </ul>
            
            <h3>Internet Browsing Skills</h3>
            
            <h4>Web Browser Basics</h4>
            <ul>
                <li><strong>Address Bar:</strong> Where you type website URLs</li>
                <li><strong>Bookmarks:</strong> Save frequently visited websites</li>
                <li><strong>Tabs:</strong> Open multiple websites simultaneously</li>
                <li><strong>History:</strong> View previously visited websites</li>
            </ul>
            
            <h4>Search Techniques</h4>
            <ul>
                <li><strong>Use specific keywords:</strong> Be precise in your search terms</li>
                <li><strong>Use quotes:</strong> "exact phrase" for specific phrases</li>
                <li><strong>Use filters:</strong> Date, file type, and other search filters</li>
            </ul>
            
            <h3>Email Management</h3>
            
            <h4>Email Best Practices</h4>
            <ol>
                <li><strong>Clear Subject Lines:</strong> Summarize your email's purpose</li>
                <li><strong>Professional Tone:</strong> Use appropriate language and formatting</li>
                <li><strong>Organize with Folders:</strong> Create folders for different topics</li>
                <li><strong>Regular Cleanup:</strong> Delete unnecessary emails and empty trash</li>
            </ol>
            
            <div class="alert alert-success">
                <h4>✅ Practice Exercise</h4>
                <p>Try creating a new folder on your desktop, saving a document to it, 
                and then moving the folder to a different location. This exercise combines 
                several essential computer skills!</p>
            </div>
            
            <h3>Troubleshooting Basics</h3>
            <ul>
                <li><strong>Restart First:</strong> Many issues resolve with a simple restart</li>
                <li><strong>Check Connections:</strong> Ensure cables and internet are connected</li>
                <li><strong>Update Software:</strong> Keep your programs and OS updated</li>
                <li><strong>Ask for Help:</strong> Don't hesitate to seek assistance when needed</li>
            </ul>
            """,
            'sort_order': 2,
            'is_published': True,
            'estimated_duration': 40,
            'learning_objectives': "Master computer navigation, develop file management skills, learn keyboard shortcuts, understand email best practices"
        }
    )
    if created:
        print(f"✅ Created lesson 2: {lesson2.title}")
    else:
        print(f"✅ Using existing lesson 2: {lesson2.title}")
    
    # Lesson 3: Final lesson to test progression
    lesson3, created = Lesson.objects.get_or_create(
        module=module,
        title="Internet Safety Fundamentals",
        defaults={
            'content_type': 'text',
            'content': """
            <h2>Staying Safe Online</h2>
            
            <p>Internet safety is crucial in our digital world. This lesson will teach you 
            how to protect yourself, your data, and your privacy while enjoying the benefits 
            of online connectivity.</p>
            
            <h3>Understanding Online Threats</h3>
            
            <h4>Common Cyber Threats</h4>
            <ul>
                <li><strong>Phishing:</strong> Fake emails or websites trying to steal your information</li>
                <li><strong>Malware:</strong> Malicious software that can damage your computer</li>
                <li><strong>Identity Theft:</strong> Criminals using your personal information</li>
                <li><strong>Scams:</strong> Fraudulent schemes to steal money or information</li>
            </ul>
            
            <h3>Password Security</h3>
            
            <h4>Creating Strong Passwords</h4>
            <ul>
                <li><strong>Length:</strong> Use at least 12 characters</li>
                <li><strong>Complexity:</strong> Mix uppercase, lowercase, numbers, and symbols</li>
                <li><strong>Uniqueness:</strong> Use different passwords for different accounts</li>
                <li><strong>Avoid Personal Info:</strong> Don't use birthdays, names, or common words</li>
            </ul>
            
            <h4>Password Management</h4>
            <ul>
                <li><strong>Password Managers:</strong> Use tools like LastPass, 1Password, or Bitwarden</li>
                <li><strong>Two-Factor Authentication:</strong> Add an extra layer of security</li>
                <li><strong>Regular Updates:</strong> Change passwords if accounts are compromised</li>
            </ul>
            
            <h3>Safe Browsing Practices</h3>
            
            <h4>Identifying Secure Websites</h4>
            <ul>
                <li><strong>HTTPS:</strong> Look for the lock icon and "https://" in the address bar</li>
                <li><strong>Legitimate URLs:</strong> Check for correct spelling and domain names</li>
                <li><strong>Trust Indicators:</strong> Look for security certificates and trust seals</li>
            </ul>
            
            <h4>Avoiding Suspicious Content</h4>
            <ul>
                <li><strong>Don't Click Unknown Links:</strong> Hover to preview URLs before clicking</li>
                <li><strong>Verify Downloads:</strong> Only download from trusted sources</li>
                <li><strong>Be Skeptical:</strong> If something seems too good to be true, it probably is</li>
            </ul>
            
            <h3>Social Media Safety</h3>
            
            <h4>Privacy Settings</h4>
            <ol>
                <li><strong>Review Privacy Settings:</strong> Regularly check and update your privacy preferences</li>
                <li><strong>Limit Personal Information:</strong> Don't share sensitive details publicly</li>
                <li><strong>Think Before Posting:</strong> Consider the long-term impact of your posts</li>
                <li><strong>Verify Friend Requests:</strong> Only connect with people you know</li>
            </ol>
            
            <h3>Email Security</h3>
            
            <h4>Recognizing Phishing Emails</h4>
            <ul>
                <li><strong>Suspicious Senders:</strong> Unknown or misspelled email addresses</li>
                <li><strong>Urgent Language:</strong> Pressure to act immediately</li>
                <li><strong>Generic Greetings:</strong> "Dear Customer" instead of your name</li>
                <li><strong>Suspicious Links:</strong> Hover to check where links actually lead</li>
            </ul>
            
            <div class="alert alert-warning">
                <h4>⚠️ Important Reminder</h4>
                <p>Legitimate companies will never ask for passwords, credit card numbers, 
                or other sensitive information via email. When in doubt, contact the company 
                directly through their official website or phone number.</p>
            </div>
            
            <h3>Protecting Your Devices</h3>
            
            <h4>Essential Security Measures</h4>
            <ul>
                <li><strong>Antivirus Software:</strong> Install and regularly update antivirus protection</li>
                <li><strong>Software Updates:</strong> Keep your operating system and programs updated</li>
                <li><strong>Firewall:</strong> Enable your computer's firewall protection</li>
                <li><strong>Regular Backups:</strong> Back up important files to cloud storage or external drives</li>
            </ul>
            
            <h3>What to Do If Something Goes Wrong</h3>
            <ol>
                <li><strong>Stay Calm:</strong> Don't panic—most issues can be resolved</li>
                <li><strong>Disconnect:</strong> If you suspect malware, disconnect from the internet</li>
                <li><strong>Change Passwords:</strong> Update passwords for potentially compromised accounts</li>
                <li><strong>Scan for Malware:</strong> Run a full antivirus scan</li>
                <li><strong>Report Issues:</strong> Contact your bank, email provider, or relevant authorities</li>
                <li><strong>Learn from Experience:</strong> Use incidents as learning opportunities</li>
            </ol>
            
            <div class="alert alert-success">
                <h4>🎉 Congratulations!</h4>
                <p>You've completed the Introduction to Digital Skills course! You now have 
                the foundation to safely and effectively use digital tools in your personal 
                and professional life.</p>
            </div>
            """,
            'sort_order': 3,
            'is_published': True,
            'estimated_duration': 50,
            'learning_objectives': "Identify online threats, create secure passwords, practice safe browsing, protect personal information, respond to security incidents"
        }
    )
    if created:
        print(f"✅ Created lesson 3: {lesson3.title}")
    else:
        print(f"✅ Using existing lesson 3: {lesson3.title}")
    
    # Step 5: Create quiz for Lesson 1
    print("\n🧪 Creating assessment quiz...")
    quiz, created = Quiz.objects.get_or_create(
        lesson=lesson1,
        defaults={
            'title': "Digital Tools Assessment",
            'description': """
            Test your understanding of digital tools and their applications.
            You need to score at least 70% to pass this assessment and unlock the next lesson.

            This quiz covers:
            • Types of digital tools
            • Communication platforms
            • Productivity applications
            • Best practices for digital tool usage
            """,
            'instructions': "Read each question carefully and select the best answer. You need 70% to pass.",
            'passing_score': 70,
            'max_attempts': 3,
            'time_limit': 15,  # 15 minutes
            'is_published': True,
            'show_results': True,
            'is_randomized': False
        }
    )
    if created:
        print(f"✅ Created quiz: {quiz.title}")
    else:
        print(f"✅ Using existing quiz: {quiz.title}")

    # Step 6: Create quiz questions
    print("\n❓ Creating quiz questions...")

    questions_data = [
        {
            'question_text': "Which of the following is the PRIMARY purpose of digital communication tools?",
            'question_type': 'multiple_choice',
            'correct_answer': "To facilitate communication between people across different locations",
            'choices': [
                "To facilitate communication between people across different locations",
                "To replace all traditional forms of communication",
                "To make communication more expensive",
                "To limit access to information"
            ],
            'explanation': "Digital communication tools are designed to help people communicate effectively regardless of their physical location.",
            'points': 20,
            'order': 1
        },
        {
            'question_text': "What is the main advantage of using cloud storage services like Google Drive or Dropbox?",
            'question_type': 'multiple_choice',
            'correct_answer': "Files can be accessed from any device with internet connection",
            'choices': [
                "Files can be accessed from any device with internet connection",
                "Files are automatically deleted after 30 days",
                "Cloud storage is always free",
                "Files cannot be shared with others"
            ],
            'explanation': "Cloud storage allows you to access your files from any device with an internet connection, providing flexibility and convenience.",
            'points': 20,
            'order': 2
        },
        {
            'question_text': "Which category of digital tools would include Microsoft Word, Google Docs, and PowerPoint?",
            'question_type': 'multiple_choice',
            'correct_answer': "Productivity Tools",
            'choices': [
                "Communication Tools",
                "Productivity Tools",
                "Entertainment Tools",
                "Security Tools"
            ],
            'explanation': "Microsoft Word, Google Docs, and PowerPoint are productivity tools designed to help create documents and presentations.",
            'points': 20,
            'order': 3
        },
        {
            'question_text': "According to the lesson, what is the BEST approach when starting to learn digital tools?",
            'question_type': 'multiple_choice',
            'correct_answer': "Start simple with basic tools and practice regularly",
            'choices': [
                "Learn all tools at once to save time",
                "Start simple with basic tools and practice regularly",
                "Only use the most advanced tools available",
                "Avoid using digital tools until you're an expert"
            ],
            'explanation': "The lesson recommends starting with basic tools and practicing regularly to build familiarity and confidence.",
            'points': 20,
            'order': 4
        },
        {
            'question_text': "Which of the following is an example of a video conferencing tool mentioned in the lesson?",
            'question_type': 'multiple_choice',
            'correct_answer': "Zoom",
            'choices': [
                "WhatsApp",
                "Google Docs",
                "Zoom",
                "Dropbox"
            ],
            'explanation': "Zoom is specifically mentioned as a video conferencing tool, along with Google Meet and Microsoft Teams.",
            'points': 20,
            'order': 5
        }
    ]

    for q_data in questions_data:
        question, created = Question.objects.get_or_create(
            quiz=quiz,
            question_text=q_data['question_text'],
            defaults={
                'question_type': q_data['question_type'],
                'correct_answer': q_data['correct_answer'],
                'options': q_data['choices'],
                'explanation': q_data['explanation'],
                'points': q_data['points'],
                'sort_order': q_data['order']
            }
        )
        if created:
            print(f"✅ Created question {q_data['order']}: {q_data['question_text'][:50]}...")
        else:
            print(f"✅ Using existing question {q_data['order']}")

    # Step 7: Create test user
    print("\n👤 Creating test user...")
    test_user, created = User.objects.get_or_create(
        username='testlearner',
        defaults={
            'email': 'testlearner@yitp.test',
            'first_name': 'Test',
            'last_name': 'Learner',
            'is_active': True
        }
    )
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print(f"✅ Created test user: {test_user.username}")
        print(f"   📧 Email: {test_user.email}")
        print(f"   🔑 Password: testpass123")
    else:
        print(f"✅ Using existing test user: {test_user.username}")

    # Ensure profile exists
    profile, created = Profile.objects.get_or_create(
        user=test_user,
        defaults={
            'phone_number': '+254712345678',
            'date_of_birth': '1990-01-01',
            'bio': 'Test learner account for validating Enhanced YITP LMS Learning Flow',
            'total_points': 0,
            'current_streak': 0,
            'longest_streak': 0
        }
    )
    if created:
        print(f"✅ Created profile for test user")
    else:
        print(f"✅ Using existing profile for test user")

    # Step 8: Enroll test user in course
    print("\n📝 Enrolling test user in course...")
    enrollment, created = Enrollment.objects.get_or_create(
        student=test_user,
        course=course,
        defaults={
            'status': 'active',
            'enrollment_date': timezone.now()
        }
    )
    if created:
        print(f"✅ Enrolled {test_user.username} in {course.title}")
    else:
        print(f"✅ {test_user.username} already enrolled in {course.title}")

    return course, lesson1, lesson2, lesson3, quiz, test_user


def print_test_instructions():
    """Print comprehensive testing instructions"""
    print("\n" + "=" * 60)
    print("🧪 ENHANCED YITP LMS LEARNING FLOW - TEST INSTRUCTIONS")
    print("=" * 60)

    print("\n🎯 TEST OBJECTIVES:")
    print("Validate all 4 phases of the Enhanced Learning Flow implementation:")
    print("1. ✅ Quiz Integration & Mandatory Completion")
    print("2. 🎮 Gamification System (Points, Achievements, Streaks)")
    print("3. 💬 Communication Features (Lesson Chat Widget)")
    print("4. 🎨 Enhanced UI/UX (Quiz Success Page, Notifications)")

    print("\n🔐 TEST USER CREDENTIALS:")
    print("Username: testlearner")
    print("Password: testpass123")
    print("Email: testlearner@yitp.test")

    print("\n📚 TEST COURSE DETAILS:")
    print("Course: Introduction to Digital Skills")
    print("Price: FREE (no payment required)")
    print("Lessons: 3 lessons with sequential progression")
    print("Quiz: Lesson 1 has mandatory quiz (70% passing score)")

    print("\n🧪 TESTING WORKFLOW:")
    print("1. 🌐 Access: http://127.0.0.1:8001/")
    print("2. 🔑 Login with test user credentials")
    print("3. 📚 Navigate to course: 'Introduction to Digital Skills'")
    print("4. 📝 Enroll in the free course")
    print("5. 📖 Start Lesson 1: 'Getting Started with Digital Tools'")
    print("6. 🧪 Try to complete lesson WITHOUT taking quiz (should be blocked)")
    print("7. 📝 Take the 'Digital Tools Assessment' quiz")
    print("8. 🎉 Experience quiz success page with gamification")
    print("9. ➡️  Continue to Lesson 2 (should now be unlocked)")
    print("10. 💬 Test chat widget on lesson pages")
    print("11. 🏆 Check achievements and leaderboard")

    print("\n✅ EXPECTED BEHAVIORS:")
    print("• Lesson completion blocked until quiz is passed")
    print("• Quiz requires 70% score (3/5 questions correct)")
    print("• Points awarded for lesson completion (10 points)")
    print("• Achievement notifications for first lesson completion")
    print("• Sequential lesson progression (Lesson 2 unlocked after Lesson 1)")
    print("• Chat widget available on all lesson pages")
    print("• Quiz success page with celebration animations")
    print("• Updated user stats and leaderboard position")

    print("\n🐛 TROUBLESHOOTING:")
    print("• If quiz doesn't appear: Check lesson 1 has associated quiz")
    print("• If progression blocked: Ensure quiz is passed with 70%+ score")
    print("• If no points awarded: Check gamification service integration")
    print("• If chat not working: Verify communication app URLs are configured")

    print("\n🎉 SUCCESS CRITERIA:")
    print("All 4 phases working correctly with smooth user experience")
    print("from course enrollment through lesson completion and achievement!")


if __name__ == '__main__':
    course, lesson1, lesson2, lesson3, quiz, test_user = create_test_course_data()
    print_test_instructions()
    print("\n🎉 Enhanced YITP LMS Test Environment Ready!")
    print("🚀 Start testing at: http://127.0.0.1:8001/")
