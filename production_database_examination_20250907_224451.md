# YITP Production Database Examination Report

**Generated:** 2025-09-07 22:44:51

---

🔍 YITP PRODUCTION DATABASE EXAMINATION
================================================================================
Started: 2025-09-07 22:44:36
🔍 TESTING PRODUCTION DATABASE CONNECTION
============================================================
✅ Database Connection: SUCCESS
   Database Version: PostgreSQL 17.4 on aarch64-unknown-linux-gnu, compiled by gcc (GCC) 13.2.0, 64-bit
   Database Host: aws-0-eu-west-1.pooler.supabase.com
   Database Name: postgres
   Database User: postgres.ovywuanlidncuecjlyve

📚 EXAMINING EXISTING COURSES
============================================================
Total Courses Found: 2

📖 Course 1: Introduction to YITP: Your Learning Journey Begins
   Slug: introduction-to-yitp-your-learning-journey-begins
   Status: published | Published: True
   Price: $0.00
   Instructor: yitpteam
   Modules: 1 | Lessons: 1
     📁 Module 1: Getting Started with YITP (1 lessons)
       📄 Lesson 1: Welcome to Youth Impact Training Programme (1 quizzes)

📖 Course 6: Youth Impact Training Programme (YITP)
   Slug: youth-impact-training-programme-yitp
   Status: published | Published: True
   Price: $39.00
   Instructor: yitpteam
   Modules: 1 | Lessons: 8
     📁 Module 1: Understanding Purpose in Life (UPL 101) (8 lessons)
       📄 Lesson 1: Lesson 1: Introduction to Life’s Purpose (1 quizzes)
       📄 Lesson 2: Lesson 2: Foundations of Purpose (1 quizzes)
       📄 Lesson 3: Lesson 3: Purpose and Service (0 quizzes)
       ... and 5 more lessons

🎯 EXAMINING MAIN YITP COURSE
============================================================
✅ Main YITP Course Found: Youth Impact Training Programme (YITP)
   Course ID: 6
   Slug: youth-impact-training-programme-yitp
   Status: published
   Published: True
   Price: $39.00

📁 Current Modules (1):
   Module 1: Understanding Purpose in Life (UPL 101)
     Description: An 8-lesson, 2-week part-time module guiding learners to define, live, and share a life purpose thro...
     Lessons: 8 | Quizzes: 2
     Duration: 600 minutes
     Published: True
       📄 Lesson 1: Lesson 1: Introduction to Life’s Purpose
         Type: text | Duration: 60 min
         🧩 Quiz: Lesson 1 Checkpoint (5 questions)
       📄 Lesson 2: Lesson 2: Foundations of Purpose
         Type: text | Duration: 90 min
         🧩 Quiz: Lesson 2 Checkpoint (5 questions)
       📄 Lesson 3: Lesson 3: Purpose and Service
         Type: text | Duration: 60 min
       📄 Lesson 4: Lesson 4: Overcoming Obstacles to Purpose
         Type: text | Duration: 60 min
       📄 Lesson 5: Lesson 5: Tools to Define Your Purpose
         Type: text | Duration: 90 min
       📄 Lesson 6: Lesson 6: Purpose in Action
         Type: text | Duration: 90 min
       📄 Lesson 7: Lesson 7: Sharing & Sustaining Your Purpose
         Type: text | Duration: 90 min
       📄 Lesson 8: Lesson 8: Reflection & Forward Planning
         Type: text | Duration: 60 min

📂 EXAMINING CATEGORIES
============================================================
Total Categories: 3
   📂 Personal Development: 1 courses
   📂 Platform Training: 1 courses
   📂 Virtual Training: 0 courses

👨‍🏫 EXAMINING INSTRUCTORS
============================================================
❌ Error examining instructors: Cannot resolve keyword 'instructor_courses' into field. Choices are: achievements, approved_sponsorships, assignment_submissions, course_assignments, course_reviews, course_sessions, courses_reviewed, courses_taught, created_announcements, created_assessments, created_content, created_content_blocks, created_course_templates, created_forums, created_libraries, created_questions, created_resources, created_study_groups, created_templates, created_topics, date_joined, email, enrollments, event, first_name, forum_replies, given_feedback, graded_assignments, groups, id, instructor_assignments_made, instructor_profile, is_active, is_staff, is_superuser, last_login, last_name, learning_paths, logentry, magic_tokens, notifications, otpverification, password, payment_behavior, payments, post, profile, quiz_attempts, received_feedback, received_messages, reviewed_sponsorship_requests, self_assessment_responses, sent_messages, sponsorship_requests, study_groups, study_sessions, studygroupmembership, user_permissions, username, verified_instructors, verified_payments

💡 UPL 101 INTEGRATION RECOMMENDATIONS
============================================================
✅ Main YITP Course Found: Youth Impact Training Programme (YITP)
   Current Modules: 1

⚠️ EXISTING MODULES DETECTED:
   - Module 1: Understanding Purpose in Life (UPL 101) (8 lessons)

🔧 INTEGRATION STRATEGY:
1. BACKUP existing modules before integration
2. OPTION A: Replace existing modules with UPL 101
3. OPTION B: Insert UPL 101 as Module 1, shift others
4. OPTION C: Add UPL 101 as additional module

📋 UPL 101 INTEGRATION PLAN:
1. Create Module: 'Understanding Purpose in Life (UPL 101)'
2. Add 8 lessons (Sessions 1-8)
3. Create 40 quiz questions (5 per session)
4. Set proper sequencing and prerequisites
5. Update course price to $39 USD
6. Verify all functionality
