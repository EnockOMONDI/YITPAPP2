#!/usr/bin/env python
"""
YITP Production Database Course Report Generator
Connects to Supabase PostgreSQL and generates comprehensive course documentation
"""

import os
import sys
import django
import json
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

# Setup Django environment for PRODUCTION
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode
django.setup()

from django.contrib.auth.models import User
from django.db.models import Count, Q, Avg
from django.db import models as django_models
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question, Assignment
from content.models import ContentItem, LessonContent
from progress.models import LessonProgress, QuizAttempt, Enrollment
from users.models import Profile

class ProductionCourseReporter:
    """Generate comprehensive course report from production database"""
    
    def __init__(self):
        self.report_data = {
            'generation_time': datetime.now().isoformat(),
            'database_info': {},
            'summary_stats': {},
            'courses': [],
            'issues': []
        }
        
    def verify_production_connection(self):
        """Verify we're connected to production database"""
        print("🔍 VERIFYING PRODUCTION DATABASE CONNECTION")
        print("=" * 60)
        
        try:
            from django.db import connection
            from django.conf import settings
            
            # Check database settings
            db_config = settings.DATABASES['default']
            print(f"📊 Database Engine: {db_config['ENGINE']}")
            print(f"🏠 Database Host: {db_config['HOST']}")
            print(f"📂 Database Name: {db_config['NAME']}")
            print(f"👤 Database User: {db_config['USER']}")
            
            # Test connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                print(f"✅ PostgreSQL Version: {version}")
                
            # Store database info
            self.report_data['database_info'] = {
                'engine': db_config['ENGINE'],
                'host': db_config['HOST'],
                'name': db_config['NAME'],
                'user': db_config['USER'],
                'version': version,
                'connection_verified': True
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            self.report_data['database_info']['connection_verified'] = False
            self.report_data['database_info']['error'] = str(e)
            return False
    
    def gather_summary_statistics(self):
        """Gather overall database statistics"""
        print("\n📊 GATHERING SUMMARY STATISTICS")
        print("=" * 50)
        
        try:
            stats = {}
            
            # Course statistics
            stats['total_courses'] = Course.objects.count()
            stats['published_courses'] = Course.objects.filter(is_published=True).count()
            stats['free_courses'] = Course.objects.filter(price=0).count()
            stats['paid_courses'] = Course.objects.filter(price__gt=0).count()
            
            # Content statistics
            stats['total_modules'] = Module.objects.count()
            stats['total_lessons'] = Lesson.objects.count()
            stats['total_quizzes'] = Quiz.objects.count()
            stats['total_questions'] = Question.objects.count()
            stats['total_assignments'] = Assignment.objects.count()
            stats['total_content_items'] = ContentItem.objects.count()
            
            # User statistics
            stats['total_users'] = User.objects.count()
            stats['total_enrollments'] = Enrollment.objects.count()
            stats['active_enrollments'] = Enrollment.objects.filter(status='active').count()
            
            # Progress statistics
            stats['total_lesson_progress'] = LessonProgress.objects.count()
            stats['completed_lessons'] = LessonProgress.objects.filter(status='completed').count()
            stats['total_quiz_attempts'] = QuizAttempt.objects.count()
            
            # Categories
            stats['total_categories'] = Category.objects.count()
            
            self.report_data['summary_stats'] = stats
            
            # Print summary
            print(f"📚 Total Courses: {stats['total_courses']}")
            print(f"📖 Published Courses: {stats['published_courses']}")
            print(f"🆓 Free Courses: {stats['free_courses']}")
            print(f"💰 Paid Courses: {stats['paid_courses']}")
            print(f"📑 Total Modules: {stats['total_modules']}")
            print(f"📄 Total Lessons: {stats['total_lessons']}")
            print(f"❓ Total Quizzes: {stats['total_quizzes']}")
            print(f"👥 Total Users: {stats['total_users']}")
            print(f"🎓 Total Enrollments: {stats['total_enrollments']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error gathering statistics: {str(e)}")
            self.report_data['issues'].append(f"Statistics gathering failed: {str(e)}")
            return False
    
    def analyze_course_content(self, course):
        """Analyze detailed content structure for a course"""
        course_data = {
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'description': course.description,
            'price': float(course.price) if course.price else 0.0,
            'currency': 'USD',
            'is_published': course.is_published,
            'is_featured': course.is_featured,
            'status': course.status,
            'created_at': course.created_at.isoformat() if course.created_at else None,
            'updated_at': course.updated_at.isoformat() if course.updated_at else None,
            'estimated_duration': course.estimated_duration,
            'difficulty_level': course.difficulty_level,
            'instructor': {
                'id': course.instructor.id,
                'username': course.instructor.username,
                'email': course.instructor.email,
                'first_name': course.instructor.first_name,
                'last_name': course.instructor.last_name,
            } if course.instructor else None,
            'category': {
                'id': course.category.id,
                'name': course.category.name,
                'description': course.category.description,
            } if course.category else None,
            'enrollment_stats': {},
            'modules': [],
            'content_delivery': {},
            'trial_config': {},
            'issues': []
        }
        
        try:
            # Enrollment statistics
            enrollments = Enrollment.objects.filter(course=course)
            course_data['enrollment_stats'] = {
                'total_enrollments': enrollments.count(),
                'active_enrollments': enrollments.filter(status='active').count(),
                'completed_enrollments': enrollments.filter(status='completed').count(),
                'average_progress': enrollments.aggregate(
                    avg_progress=Avg('progress_percentage')
                )['avg_progress'] or 0
            }
            
            # Modules and lessons
            modules = Module.objects.filter(course=course).order_by('sort_order')
            for module in modules:
                module_data = {
                    'id': module.id,
                    'title': module.title,
                    'description': module.description,
                    'order': module.sort_order,
                    'is_published': module.is_published,
                    'lessons': []
                }
                
                # Lessons in this module
                lessons = Lesson.objects.filter(module=module).order_by('sort_order')
                for lesson in lessons:
                    lesson_data = {
                        'id': lesson.id,
                        'title': lesson.title,
                        'content': lesson.content[:200] + '...' if lesson.content and len(lesson.content) > 200 else lesson.content,
                        'order': lesson.sort_order,
                        'is_published': lesson.is_published,
                        'content_type': lesson.content_type,
                        'estimated_duration': lesson.estimated_duration,
                        'is_mandatory': lesson.is_mandatory,
                        'content_items': [],
                        'quizzes': [],
                        'assignments': []
                    }
                    
                    # Content items for this lesson (through LessonContent)
                    content_items = LessonContent.objects.filter(lesson=lesson)
                    for item in content_items:
                        item_data = {
                            'id': item.id,
                            'title': item.title,
                            'content_type': item.content_type,
                            'file_url': item.file_url,
                            'order': item.order,
                            'is_required': item.is_required
                        }
                        lesson_data['content_items'].append(item_data)
                    
                    # Quizzes for this lesson
                    quizzes = Quiz.objects.filter(lesson=lesson)
                    for quiz in quizzes:
                        quiz_data = {
                            'id': quiz.id,
                            'title': quiz.title,
                            'description': quiz.description,
                            'passing_score': quiz.passing_score,
                            'time_limit': quiz.time_limit,
                            'max_attempts': quiz.max_attempts,
                            'is_required': quiz.is_required,
                            'question_count': Question.objects.filter(quiz=quiz).count()
                        }
                        lesson_data['quizzes'].append(quiz_data)
                    
                    # Assignments for this lesson
                    assignments = Assignment.objects.filter(lesson=lesson)
                    for assignment in assignments:
                        assignment_data = {
                            'id': assignment.id,
                            'title': assignment.title,
                            'description': assignment.description,
                            'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                            'max_score': assignment.max_score,
                            'is_required': assignment.is_required
                        }
                        lesson_data['assignments'].append(assignment_data)
                    
                    module_data['lessons'].append(lesson_data)
                
                course_data['modules'].append(module_data)
            
            # Content delivery analysis
            course_data['content_delivery'] = self.analyze_content_delivery(course)
            
            # Trial configuration
            course_data['trial_config'] = self.analyze_trial_config(course)
            
        except Exception as e:
            error_msg = f"Error analyzing course {course.id}: {str(e)}"
            print(f"⚠️ {error_msg}")
            course_data['issues'].append(error_msg)
            self.report_data['issues'].append(error_msg)
        
        return course_data
    
    def analyze_content_delivery(self, course):
        """Analyze how content is delivered for this course"""
        delivery_info = {
            'static_files': {'method': 'unknown', 'count': 0, 'types': []},
            'videos': {'hosting': 'unknown', 'count': 0, 'urls': []},
            'documents': {'storage': 'unknown', 'count': 0, 'types': []},
            'images': {'storage': 'unknown', 'count': 0, 'formats': []},
            'audio': {'storage': 'unknown', 'count': 0, 'formats': []}
        }
        
        try:
            # Analyze content items across all lessons in the course
            content_items = ContentItem.objects.filter(
                lesson__module__course=course
            )
            
            for item in content_items:
                if item.file_url:
                    if 'uploadcare' in item.file_url:
                        delivery_info['static_files']['method'] = 'Uploadcare CDN'
                    elif 'youtube' in item.file_url or 'vimeo' in item.file_url:
                        delivery_info['videos']['hosting'] = 'External (YouTube/Vimeo)'
                        delivery_info['videos']['count'] += 1
                        delivery_info['videos']['urls'].append(item.file_url)
                    
                    # Categorize by content type
                    if item.content_type in ['video', 'mp4', 'avi', 'mov']:
                        delivery_info['videos']['count'] += 1
                    elif item.content_type in ['pdf', 'doc', 'docx', 'txt']:
                        delivery_info['documents']['count'] += 1
                        if item.content_type not in delivery_info['documents']['types']:
                            delivery_info['documents']['types'].append(item.content_type)
                    elif item.content_type in ['jpg', 'jpeg', 'png', 'gif', 'svg']:
                        delivery_info['images']['count'] += 1
                        if item.content_type not in delivery_info['images']['formats']:
                            delivery_info['images']['formats'].append(item.content_type)
                    elif item.content_type in ['mp3', 'wav', 'ogg']:
                        delivery_info['audio']['count'] += 1
                        if item.content_type not in delivery_info['audio']['formats']:
                            delivery_info['audio']['formats'].append(item.content_type)
            
            delivery_info['static_files']['count'] = content_items.count()
            
        except Exception as e:
            print(f"⚠️ Error analyzing content delivery for course {course.id}: {str(e)}")
        
        return delivery_info
    
    def analyze_trial_config(self, course):
        """Analyze trial access configuration for this course"""
        trial_config = {
            'trial_available': False,
            'trial_lessons_count': 0,
            'trial_lessons': [],
            'preview_lessons_count': 0,
            'preview_lessons': []
        }
        
        try:
            # Check for non-mandatory lessons (typically available in trial)
            preview_lessons = Lesson.objects.filter(
                module__course=course,
                is_mandatory=False
            ).order_by('module__sort_order', 'sort_order')

            trial_config['preview_lessons_count'] = preview_lessons.count()
            trial_config['preview_lessons'] = [
                {
                    'id': lesson.id,
                    'title': lesson.title,
                    'module': lesson.module.title,
                    'order': lesson.sort_order
                }
                for lesson in preview_lessons
            ]
            
            # For free courses, trial might be first 2 lessons
            if course.price == 0:
                first_lessons = Lesson.objects.filter(
                    module__course=course
                ).order_by('module__sort_order', 'sort_order')[:2]
                
                trial_config['trial_available'] = True
                trial_config['trial_lessons_count'] = min(2, first_lessons.count())
                trial_config['trial_lessons'] = [
                    {
                        'id': lesson.id,
                        'title': lesson.title,
                        'module': lesson.module.title,
                        'order': lesson.sort_order
                    }
                    for lesson in first_lessons
                ]
            
        except Exception as e:
            print(f"⚠️ Error analyzing trial config for course {course.id}: {str(e)}")
        
        return trial_config

    def fetch_all_courses(self):
        """Fetch and analyze all courses from production database"""
        print("\n📚 FETCHING ALL COURSES FROM PRODUCTION")
        print("=" * 50)

        try:
            courses = Course.objects.all().order_by('created_at')
            total_courses = courses.count()

            print(f"📖 Found {total_courses} courses in production database")

            for i, course in enumerate(courses, 1):
                print(f"📄 Analyzing course {i}/{total_courses}: {course.title}")
                course_data = self.analyze_course_content(course)
                self.report_data['courses'].append(course_data)

            print(f"✅ Successfully analyzed {len(self.report_data['courses'])} courses")
            return True

        except Exception as e:
            error_msg = f"Error fetching courses: {str(e)}"
            print(f"❌ {error_msg}")
            self.report_data['issues'].append(error_msg)
            return False

    def generate_markdown_report(self):
        """Generate comprehensive Markdown report"""
        print("\n📝 GENERATING MARKDOWN REPORT")
        print("=" * 40)

        try:
            report_lines = []

            # Header
            report_lines.extend([
                "# YITP Production Database Course Report",
                "",
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                f"**Database:** {self.report_data['database_info'].get('host', 'Unknown')}",
                f"**Environment:** Production (Supabase PostgreSQL)",
                "",
                "---",
                ""
            ])

            # Table of Contents
            report_lines.extend([
                "## Table of Contents",
                "",
                "1. [Executive Summary](#executive-summary)",
                "2. [Database Connection Info](#database-connection-info)",
                "3. [Summary Statistics](#summary-statistics)",
                "4. [Course Inventory](#course-inventory)",
                "5. [Detailed Course Analysis](#detailed-course-analysis)",
                "6. [Content Delivery Analysis](#content-delivery-analysis)",
                "7. [Trial Access Configuration](#trial-access-configuration)",
                "8. [Issues and Recommendations](#issues-and-recommendations)",
                "",
                "---",
                ""
            ])

            # Executive Summary
            stats = self.report_data['summary_stats']
            report_lines.extend([
                "## Executive Summary",
                "",
                f"The YITP production database contains **{stats.get('total_courses', 0)} courses** with a total of **{stats.get('total_lessons', 0)} lessons** across **{stats.get('total_modules', 0)} modules**.",
                "",
                f"- **Active Enrollments:** {stats.get('active_enrollments', 0)} out of {stats.get('total_enrollments', 0)} total",
                f"- **Course Types:** {stats.get('free_courses', 0)} free courses, {stats.get('paid_courses', 0)} paid courses",
                f"- **Content:** {stats.get('total_content_items', 0)} content items, {stats.get('total_quizzes', 0)} quizzes, {stats.get('total_assignments', 0)} assignments",
                f"- **User Engagement:** {stats.get('completed_lessons', 0)} completed lessons out of {stats.get('total_lesson_progress', 0)} lesson attempts",
                "",
                "---",
                ""
            ])

            # Database Connection Info
            db_info = self.report_data['database_info']
            report_lines.extend([
                "## Database Connection Info",
                "",
                f"- **Engine:** {db_info.get('engine', 'Unknown')}",
                f"- **Host:** {db_info.get('host', 'Unknown')}",
                f"- **Database:** {db_info.get('name', 'Unknown')}",
                f"- **User:** {db_info.get('user', 'Unknown')}",
                f"- **Version:** {db_info.get('version', 'Unknown')}",
                f"- **Connection Status:** {'✅ Verified' if db_info.get('connection_verified') else '❌ Failed'}",
                "",
                "---",
                ""
            ])

            # Summary Statistics
            report_lines.extend([
                "## Summary Statistics",
                "",
                "| Metric | Count |",
                "|--------|-------|",
                f"| Total Courses | {stats.get('total_courses', 0)} |",
                f"| Published Courses | {stats.get('published_courses', 0)} |",
                f"| Free Courses | {stats.get('free_courses', 0)} |",
                f"| Paid Courses | {stats.get('paid_courses', 0)} |",
                f"| Total Modules | {stats.get('total_modules', 0)} |",
                f"| Total Lessons | {stats.get('total_lessons', 0)} |",
                f"| Total Quizzes | {stats.get('total_quizzes', 0)} |",
                f"| Total Questions | {stats.get('total_questions', 0)} |",
                f"| Total Assignments | {stats.get('total_assignments', 0)} |",
                f"| Total Content Items | {stats.get('total_content_items', 0)} |",
                f"| Total Users | {stats.get('total_users', 0)} |",
                f"| Total Enrollments | {stats.get('total_enrollments', 0)} |",
                f"| Active Enrollments | {stats.get('active_enrollments', 0)} |",
                f"| Completed Lessons | {stats.get('completed_lessons', 0)} |",
                f"| Quiz Attempts | {stats.get('total_quiz_attempts', 0)} |",
                "",
                "---",
                ""
            ])

            # Course Inventory
            report_lines.extend([
                "## Course Inventory",
                "",
                "| Course Title | Slug | Price | Status | Enrollments | Modules | Lessons | Instructor |",
                "|--------------|------|-------|--------|-------------|---------|---------|------------|"
            ])

            for course in self.report_data['courses']:
                instructor_name = "Unknown"
                if course.get('instructor'):
                    instructor_name = f"{course['instructor'].get('first_name', '')} {course['instructor'].get('last_name', '')}".strip()
                    if not instructor_name:
                        instructor_name = course['instructor'].get('username', 'Unknown')

                status = "✅ Published" if course.get('is_published') else "❌ Draft"
                price = f"${course.get('price', 0):.2f}" if course.get('price', 0) > 0 else "Free"
                enrollments = course.get('enrollment_stats', {}).get('total_enrollments', 0)
                modules_count = len(course.get('modules', []))
                lessons_count = sum(len(module.get('lessons', [])) for module in course.get('modules', []))

                report_lines.append(
                    f"| {course.get('title', 'Untitled')} | `{course.get('slug', 'no-slug')}` | {price} | {status} | {enrollments} | {modules_count} | {lessons_count} | {instructor_name} |"
                )

            report_lines.extend(["", "---", ""])

            return report_lines

        except Exception as e:
            error_msg = f"Error generating markdown report: {str(e)}"
            print(f"❌ {error_msg}")
            self.report_data['issues'].append(error_msg)
            return []

    def generate_detailed_course_analysis(self, report_lines):
        """Add detailed analysis for each course"""
        try:
            report_lines.extend([
                "## Detailed Course Analysis",
                "",
                "### Course Structure and Content Breakdown",
                ""
            ])

            for course in self.report_data['courses']:
                # Course header
                report_lines.extend([
                    f"### 📚 {course.get('title', 'Untitled Course')}",
                    "",
                    f"**Course ID:** {course.get('id')}",
                    f"**Slug:** `{course.get('slug', 'no-slug')}`",
                    f"**Price:** ${course.get('price', 0):.2f} USD",
                    f"**Status:** {'✅ Published' if course.get('is_published') else '❌ Draft'}",
                    f"**Featured:** {'⭐ Yes' if course.get('is_featured') else '❌ No'}",
                    f"**Created:** {course.get('created_at', 'Unknown')[:10] if course.get('created_at') else 'Unknown'}",
                    f"**Duration:** {course.get('estimated_duration', 'Not specified')} hours",
                    f"**Difficulty:** {course.get('difficulty_level', 'Not specified')}",
                    ""
                ])

                # Instructor info
                if course.get('instructor'):
                    instructor = course['instructor']
                    instructor_name = f"{instructor.get('first_name', '')} {instructor.get('last_name', '')}".strip()
                    if not instructor_name:
                        instructor_name = instructor.get('username', 'Unknown')

                    report_lines.extend([
                        f"**Instructor:** {instructor_name} ({instructor.get('email', 'No email')})",
                        ""
                    ])

                # Category info
                if course.get('category'):
                    category = course['category']
                    report_lines.extend([
                        f"**Category:** {category.get('name', 'Uncategorized')}",
                        ""
                    ])

                # Description
                if course.get('description'):
                    description = course['description'][:300] + '...' if len(course.get('description', '')) > 300 else course.get('description', '')
                    report_lines.extend([
                        f"**Description:** {description}",
                        ""
                    ])

                # Enrollment statistics
                enrollment_stats = course.get('enrollment_stats', {})
                report_lines.extend([
                    "#### 📊 Enrollment Statistics",
                    "",
                    f"- **Total Enrollments:** {enrollment_stats.get('total_enrollments', 0)}",
                    f"- **Active Enrollments:** {enrollment_stats.get('active_enrollments', 0)}",
                    f"- **Completed Enrollments:** {enrollment_stats.get('completed_enrollments', 0)}",
                    f"- **Average Progress:** {enrollment_stats.get('average_progress', 0):.1f}%",
                    ""
                ])

                # Modules and lessons structure
                modules = course.get('modules', [])
                if modules:
                    report_lines.extend([
                        "#### 📑 Course Structure",
                        "",
                        f"**Total Modules:** {len(modules)}",
                        f"**Total Lessons:** {sum(len(module.get('lessons', [])) for module in modules)}",
                        ""
                    ])

                    for module in modules:
                        lessons = module.get('lessons', [])
                        report_lines.extend([
                            f"**Module {module.get('order', '?')}:** {module.get('title', 'Untitled Module')}",
                            f"- Status: {'✅ Published' if module.get('is_published') else '❌ Draft'}",
                            f"- Lessons: {len(lessons)}",
                            ""
                        ])

                        if lessons:
                            for lesson in lessons:
                                content_items = len(lesson.get('content_items', []))
                                quizzes = len(lesson.get('quizzes', []))
                                assignments = len(lesson.get('assignments', []))

                                lesson_status = "✅" if lesson.get('is_published') else "❌"
                                mandatory_status = "🔒" if lesson.get('is_mandatory') else "🔓"

                                report_lines.append(
                                    f"  - **Lesson {lesson.get('order', '?')}:** {lesson.get('title', 'Untitled')} {lesson_status} {mandatory_status}"
                                )

                                if content_items or quizzes or assignments:
                                    content_summary = []
                                    if content_items:
                                        content_summary.append(f"{content_items} content items")
                                    if quizzes:
                                        content_summary.append(f"{quizzes} quizzes")
                                    if assignments:
                                        content_summary.append(f"{assignments} assignments")

                                    report_lines.append(f"    - Content: {', '.join(content_summary)}")

                            report_lines.append("")

                # Content delivery analysis
                delivery = course.get('content_delivery', {})
                if delivery:
                    report_lines.extend([
                        "#### 🚀 Content Delivery Analysis",
                        "",
                        f"- **Static Files:** {delivery.get('static_files', {}).get('method', 'Unknown')} ({delivery.get('static_files', {}).get('count', 0)} files)",
                        f"- **Videos:** {delivery.get('videos', {}).get('hosting', 'Unknown')} ({delivery.get('videos', {}).get('count', 0)} videos)",
                        f"- **Documents:** {delivery.get('documents', {}).get('count', 0)} files ({', '.join(delivery.get('documents', {}).get('types', []))})",
                        f"- **Images:** {delivery.get('images', {}).get('count', 0)} files ({', '.join(delivery.get('images', {}).get('formats', []))})",
                        f"- **Audio:** {delivery.get('audio', {}).get('count', 0)} files ({', '.join(delivery.get('audio', {}).get('formats', []))})",
                        ""
                    ])

                # Trial configuration
                trial_config = course.get('trial_config', {})
                if trial_config:
                    report_lines.extend([
                        "#### 🎁 Trial Access Configuration",
                        "",
                        f"- **Trial Available:** {'✅ Yes' if trial_config.get('trial_available') else '❌ No'}",
                        f"- **Trial Lessons:** {trial_config.get('trial_lessons_count', 0)}",
                        f"- **Preview Lessons:** {trial_config.get('preview_lessons_count', 0)}",
                        ""
                    ])

                    if trial_config.get('trial_lessons'):
                        report_lines.append("**Trial Lessons:**")
                        for lesson in trial_config['trial_lessons']:
                            report_lines.append(f"  - {lesson.get('title', 'Untitled')} (Module: {lesson.get('module', 'Unknown')})")
                        report_lines.append("")

                # Issues
                if course.get('issues'):
                    report_lines.extend([
                        "#### ⚠️ Issues Found",
                        ""
                    ])
                    for issue in course['issues']:
                        report_lines.append(f"- {issue}")
                    report_lines.append("")

                report_lines.extend(["---", ""])

        except Exception as e:
            error_msg = f"Error generating detailed course analysis: {str(e)}"
            print(f"❌ {error_msg}")
            self.report_data['issues'].append(error_msg)

    def generate_content_delivery_summary(self, report_lines):
        """Generate overall content delivery analysis"""
        try:
            report_lines.extend([
                "## Content Delivery Analysis",
                "",
                "### Overall Content Distribution",
                ""
            ])

            # Aggregate content delivery stats
            total_static_files = 0
            total_videos = 0
            total_documents = 0
            total_images = 0
            total_audio = 0
            delivery_methods = set()
            video_hosting = set()

            for course in self.report_data['courses']:
                delivery = course.get('content_delivery', {})

                total_static_files += delivery.get('static_files', {}).get('count', 0)
                total_videos += delivery.get('videos', {}).get('count', 0)
                total_documents += delivery.get('documents', {}).get('count', 0)
                total_images += delivery.get('images', {}).get('count', 0)
                total_audio += delivery.get('audio', {}).get('count', 0)

                if delivery.get('static_files', {}).get('method'):
                    delivery_methods.add(delivery['static_files']['method'])
                if delivery.get('videos', {}).get('hosting'):
                    video_hosting.add(delivery['videos']['hosting'])

            report_lines.extend([
                "| Content Type | Total Count | Delivery Method |",
                "|--------------|-------------|-----------------|",
                f"| Static Files | {total_static_files} | {', '.join(delivery_methods) if delivery_methods else 'Unknown'} |",
                f"| Videos | {total_videos} | {', '.join(video_hosting) if video_hosting else 'Unknown'} |",
                f"| Documents | {total_documents} | File storage |",
                f"| Images | {total_images} | File storage |",
                f"| Audio | {total_audio} | File storage |",
                "",
                "### Content Delivery Recommendations",
                "",
                "- **Static Files:** Using Uploadcare CDN for optimal performance",
                "- **Videos:** External hosting (YouTube/Vimeo) for bandwidth efficiency",
                "- **Documents:** Direct file serving with proper caching headers",
                "- **Images:** CDN delivery with responsive image optimization",
                "- **Audio:** Streaming-optimized delivery for better user experience",
                "",
                "---",
                ""
            ])

        except Exception as e:
            error_msg = f"Error generating content delivery summary: {str(e)}"
            print(f"❌ {error_msg}")
            self.report_data['issues'].append(error_msg)

    def generate_trial_access_summary(self, report_lines):
        """Generate trial access configuration summary"""
        try:
            report_lines.extend([
                "## Trial Access Configuration",
                "",
                "### Trial Access Overview",
                ""
            ])

            # Aggregate trial stats
            courses_with_trial = 0
            total_trial_lessons = 0
            total_preview_lessons = 0

            for course in self.report_data['courses']:
                trial_config = course.get('trial_config', {})
                if trial_config.get('trial_available'):
                    courses_with_trial += 1
                total_trial_lessons += trial_config.get('trial_lessons_count', 0)
                total_preview_lessons += trial_config.get('preview_lessons_count', 0)

            report_lines.extend([
                f"- **Courses with Trial Access:** {courses_with_trial} out of {len(self.report_data['courses'])}",
                f"- **Total Trial Lessons:** {total_trial_lessons}",
                f"- **Total Preview Lessons:** {total_preview_lessons}",
                "",
                "### Trial Configuration by Course",
                "",
                "| Course | Trial Available | Trial Lessons | Preview Lessons |",
                "|--------|-----------------|---------------|-----------------|"
            ])

            for course in self.report_data['courses']:
                trial_config = course.get('trial_config', {})
                trial_available = "✅ Yes" if trial_config.get('trial_available') else "❌ No"
                trial_lessons = trial_config.get('trial_lessons_count', 0)
                preview_lessons = trial_config.get('preview_lessons_count', 0)

                report_lines.append(
                    f"| {course.get('title', 'Untitled')[:30]}... | {trial_available} | {trial_lessons} | {preview_lessons} |"
                )

            report_lines.extend([
                "",
                "### Trial Access Implementation Notes",
                "",
                "- **Free Courses:** First 2 lessons available as trial",
                "- **Paid Courses:** Preview lessons marked with `is_preview=True`",
                "- **Trial Duration:** Configurable per user (default: 7 days)",
                "- **Access Control:** Implemented in lesson view logic",
                "",
                "---",
                ""
            ])

        except Exception as e:
            error_msg = f"Error generating trial access summary: {str(e)}"
            print(f"❌ {error_msg}")
            self.report_data['issues'].append(error_msg)

    def generate_issues_and_recommendations(self, report_lines):
        """Generate issues found and recommendations"""
        try:
            report_lines.extend([
                "## Issues and Recommendations",
                ""
            ])

            if self.report_data['issues']:
                report_lines.extend([
                    "### ⚠️ Issues Found",
                    ""
                ])

                for i, issue in enumerate(self.report_data['issues'], 1):
                    report_lines.append(f"{i}. {issue}")

                report_lines.append("")
            else:
                report_lines.extend([
                    "### ✅ No Critical Issues Found",
                    "",
                    "The production database appears to be in good condition with no critical issues detected.",
                    ""
                ])

            # General recommendations
            report_lines.extend([
                "### 📋 Recommendations",
                "",
                "#### Content Management",
                "- Ensure all courses have proper descriptions and metadata",
                "- Standardize content delivery methods across all courses",
                "- Implement consistent naming conventions for lessons and modules",
                "",
                "#### Performance Optimization",
                "- Use CDN for all static content delivery",
                "- Optimize video content for streaming",
                "- Implement proper caching strategies",
                "",
                "#### User Experience",
                "- Ensure trial access is properly configured for all courses",
                "- Implement progress tracking and analytics",
                "- Add course completion certificates",
                "",
                "#### Data Integrity",
                "- Regular database backups and integrity checks",
                "- Monitor enrollment and progress data consistency",
                "- Implement proper error handling and logging",
                "",
                "---",
                "",
                f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                f"**Total Courses Analyzed:** {len(self.report_data['courses'])}",
                f"**Database Status:** {'✅ Connected' if self.report_data['database_info'].get('connection_verified') else '❌ Connection Issues'}",
                ""
            ])

        except Exception as e:
            error_msg = f"Error generating issues and recommendations: {str(e)}"
            print(f"❌ {error_msg}")
            self.report_data['issues'].append(error_msg)

    def save_report(self, report_lines):
        """Save the complete report to markdown file"""
        try:
            filename = "production_courses_report.md"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))

            print(f"✅ Report saved to: {filename}")
            print(f"📄 Report contains {len(report_lines)} lines")
            return filename

        except Exception as e:
            error_msg = f"Error saving report: {str(e)}"
            print(f"❌ {error_msg}")
            self.report_data['issues'].append(error_msg)
            return None

    def run_complete_analysis(self):
        """Run the complete production database analysis"""
        print("🚀 STARTING YITP PRODUCTION DATABASE ANALYSIS")
        print("=" * 80)

        # Step 1: Verify production connection
        if not self.verify_production_connection():
            print("❌ Cannot proceed without production database connection")
            return False

        # Step 2: Gather summary statistics
        if not self.gather_summary_statistics():
            print("⚠️ Continuing with limited statistics")

        # Step 3: Fetch all courses
        if not self.fetch_all_courses():
            print("❌ Failed to fetch course data")
            return False

        # Step 4: Generate markdown report
        print("\n📝 GENERATING COMPREHENSIVE MARKDOWN REPORT")
        print("=" * 50)

        report_lines = self.generate_markdown_report()
        if not report_lines:
            print("❌ Failed to generate basic report structure")
            return False

        # Add detailed sections
        self.generate_detailed_course_analysis(report_lines)
        self.generate_content_delivery_summary(report_lines)
        self.generate_trial_access_summary(report_lines)
        self.generate_issues_and_recommendations(report_lines)

        # Step 5: Save report
        filename = self.save_report(report_lines)
        if not filename:
            print("❌ Failed to save report")
            return False

        # Final summary
        print("\n🎉 PRODUCTION DATABASE ANALYSIS COMPLETED!")
        print("=" * 60)
        print(f"📁 Report File: {filename}")
        print(f"📊 Courses Analyzed: {len(self.report_data['courses'])}")
        print(f"📄 Total Lessons: {sum(len(course.get('modules', [])) for course in self.report_data['courses'])}")
        print(f"⚠️ Issues Found: {len(self.report_data['issues'])}")
        print()
        print("🔗 NEXT STEPS:")
        print("   • Review the generated report for insights")
        print("   • Address any issues identified")
        print("   • Use data for course optimization")
        print("   • Share with stakeholders as needed")

        return True

def main():
    """Main function to run the production database analysis"""
    try:
        reporter = ProductionCourseReporter()
        success = reporter.run_complete_analysis()

        if success:
            print("\n✅ Analysis completed successfully!")
            return True
        else:
            print("\n❌ Analysis failed!")
            return False

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
