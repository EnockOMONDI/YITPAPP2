from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from django.db import models
import json

from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question
from users.models import InstructorProfile
from .models import CourseTemplate, ContentBlock, QuestionBank, CourseBuilderSession


class InstructorRequiredMixin:
    """Mixin to ensure user is a verified instructor"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access the course builder.")
            return redirect('login')

        try:
            instructor_profile = request.user.instructor_profile
            if not (instructor_profile.is_verified and instructor_profile.is_active):
                messages.error(request, "You need to be a verified instructor to access the course builder.")
                return redirect('profile')
        except:
            messages.error(request, "You need to be a verified instructor to access the course builder.")
            return redirect('profile')

        return super().dispatch(request, *args, **kwargs)


class CourseBuilderDashboardView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
    """
    Main course builder dashboard showing existing courses and templates
    """
    template_name = 'course_builder/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instructor = self.request.user
        instructor_profile = instructor.instructor_profile

        # Get instructor's courses
        if instructor_profile.instructor_role == 'system_admin':
            instructor_courses = Course.objects.all()
        else:
            instructor_courses = Course.objects.filter(instructor=instructor)

        # Get course templates
        course_templates = CourseTemplate.objects.filter(is_active=True)

        # Get active course builder sessions
        active_sessions = CourseBuilderSession.objects.filter(
            instructor=instructor,
            status='active'
        ).order_by('-last_saved')[:5]

        # Course statistics
        total_courses = instructor_courses.count()
        published_courses = instructor_courses.filter(is_published=True).count()
        draft_courses = instructor_courses.filter(is_published=False).count()

        context.update({
            'instructor_profile': instructor_profile,
            'instructor_courses': instructor_courses[:10],  # Recent courses
            'course_templates': course_templates,
            'active_sessions': active_sessions,
            'total_courses': total_courses,
            'published_courses': published_courses,
            'draft_courses': draft_courses,
        })

        return context


class CourseBuilderWizardView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
    """
    5-step course creation wizard
    """
    template_name = 'course_builder/wizard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get step from URL or default to 1
        step = int(self.kwargs.get('step', 1))
        if step < 1 or step > 5:
            step = 1

        # Get or create course builder session
        session_id = self.request.GET.get('session')
        course_session = None

        if session_id:
            try:
                course_session = CourseBuilderSession.objects.get(
                    id=session_id,
                    instructor=self.request.user
                )
            except CourseBuilderSession.DoesNotExist:
                pass

        # Get course templates and categories for step 1
        course_templates = CourseTemplate.objects.filter(is_active=True)
        categories = Category.objects.filter(is_active=True)

        # Get content blocks and question bank for later steps
        content_blocks = ContentBlock.objects.filter(
            models.Q(created_by=self.request.user) | models.Q(is_template=True)
        )
        question_bank = QuestionBank.objects.filter(
            models.Q(created_by=self.request.user) | models.Q(is_public=True)
        )

        context.update({
            'current_step': step,
            'course_session': course_session,
            'course_templates': course_templates,
            'categories': categories,
            'content_blocks': content_blocks,
            'question_bank': question_bank,
            'steps': [
                {'number': 1, 'title': 'Course Basics', 'description': 'Title, description, and category'},
                {'number': 2, 'title': 'Course Structure', 'description': 'Modules and lessons organization'},
                {'number': 3, 'title': 'Content Creation', 'description': 'Add content to lessons'},
                {'number': 4, 'title': 'Assessments', 'description': 'Create quizzes and assignments'},
                {'number': 5, 'title': 'Settings & Publishing', 'description': 'Final settings and publish'},
            ]
        })

        return context


# API Views for AJAX functionality

@method_decorator(csrf_exempt, name='dispatch')
class CourseBuilderAPIView(LoginRequiredMixin, InstructorRequiredMixin, View):
    """
    API endpoint for course builder AJAX operations
    """

    def get(self, request, *args, **kwargs):
        """Handle GET requests for data retrieval"""
        action = request.GET.get('action')

        if action == 'get_lessons':
            return self.get_lessons(request)
        elif action == 'get_lesson_content':
            return self.get_lesson_content(request)
        elif action == 'get_session':
            return self.get_session(request)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'save_session':
            return self.save_session(request)
        elif action == 'create_course':
            return self.create_course(request)
        elif action == 'update_course_structure':
            return self.update_course_structure(request)
        elif action == 'add_content':
            return self.add_content(request)
        elif action == 'save_lesson_content':
            return self.save_lesson_content(request)
        elif action == 'create_quiz':
            return self.create_quiz(request)
        elif action == 'publish_course':
            return self.publish_course(request)
        elif action == 'get_template':
            return self.get_template(request)
        elif action == 'create_template':
            return self.create_template(request)
        elif action == 'get_session':
            return self.get_session(request)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})

    def save_session(self, request):
        """Auto-save course builder session"""
        try:
            session_data = json.loads(request.POST.get('session_data', '{}'))
            current_step = int(request.POST.get('current_step', 1))
            session_id = request.POST.get('session_id')

            if session_id:
                session = get_object_or_404(CourseBuilderSession, id=session_id, instructor=request.user)
            else:
                session = CourseBuilderSession.objects.create(
                    instructor=request.user,
                    session_data=session_data,
                    current_step=current_step
                )

            session.session_data = session_data
            session.current_step = current_step
            session.save()

            return JsonResponse({
                'success': True,
                'session_id': session.id,
                'message': 'Session saved successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def create_course(self, request):
        """Create new course from wizard step 1"""
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            difficulty_level = request.POST.get('difficulty_level', 'beginner')
            estimated_duration = int(request.POST.get('estimated_duration', 10))

            # Create course with in_review status
            course = Course.objects.create(
                title=title,
                slug=slugify(title),
                description=description,
                instructor=request.user,
                category_id=category_id if category_id else None,
                difficulty_level=difficulty_level,
                estimated_duration=estimated_duration,
                status='in_review',
                is_published=False
            )

            # Update session with course
            session_id = request.POST.get('session_id')
            if session_id:
                session = get_object_or_404(CourseBuilderSession, id=session_id, instructor=request.user)
                session.course = course
                session.save()

            return JsonResponse({
                'success': True,
                'course_id': course.id,
                'course_title': course.title,
                'message': 'Course created successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def update_course_structure(self, request):
        """Update course modules and lessons structure"""
        try:
            course_id = request.POST.get('course_id')
            structure_data = json.loads(request.POST.get('structure_data', '[]'))

            course = get_object_or_404(Course, id=course_id, instructor=request.user)

            # Clear existing modules and lessons
            course.modules.all().delete()

            # Create new structure
            for module_data in structure_data:
                module = Module.objects.create(
                    course=course,
                    title=module_data.get('title'),
                    description=module_data.get('description', ''),
                    sort_order=module_data.get('sort_order', 0),
                    estimated_duration=module_data.get('estimated_duration', 60),
                    is_published=False
                )

                # Create lessons for this module
                for lesson_data in module_data.get('lessons', []):
                    Lesson.objects.create(
                        module=module,
                        title=lesson_data.get('title'),
                        content_type=lesson_data.get('content_type', 'text'),
                        sort_order=lesson_data.get('sort_order', 0),
                        estimated_duration=lesson_data.get('estimated_duration', 30),
                        is_published=False
                    )

            return JsonResponse({
                'success': True,
                'message': 'Course structure updated successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def add_content(self, request):
        """Add content to lessons (legacy method)"""
        try:
            lesson_id = request.POST.get('lesson_id')
            content = request.POST.get('content', '')
            video_url = request.POST.get('video_url', '')

            lesson = get_object_or_404(Lesson, id=lesson_id, module__course__instructor=request.user)
            lesson.content = content
            lesson.video_url = video_url
            lesson.save()

            return JsonResponse({
                'success': True,
                'message': 'Content added successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def save_lesson_content(self, request):
        """Enhanced method to save lesson content with multiple content types"""
        try:
            lesson_id = request.POST.get('lesson_id')
            content_type = request.POST.get('content_type', 'text')
            content = request.POST.get('content', '')
            duration = request.POST.get('duration', 30)
            learning_objectives = request.POST.get('learning_objectives', '')

            # Get additional content type specific data
            video_url = request.POST.get('video_url', '')
            document_url = request.POST.get('document_url', '')
            audio_url = request.POST.get('audio_url', '')

            lesson = get_object_or_404(Lesson, id=lesson_id, module__course__instructor=request.user)

            # Update lesson fields
            lesson.content_type = content_type
            lesson.content = content
            lesson.estimated_duration = int(duration)
            lesson.learning_objectives = learning_objectives

            # Update content type specific fields
            if content_type == 'video':
                lesson.video_url = video_url
            elif content_type == 'document':
                lesson.document_url = document_url
            elif content_type == 'audio':
                lesson.audio_url = audio_url

            lesson.save()

            # Return updated lesson data
            lesson_data = {
                'id': lesson.id,
                'title': lesson.title,
                'content_type': lesson.content_type,
                'content': lesson.content,
                'estimated_duration': lesson.estimated_duration,
                'learning_objectives': lesson.learning_objectives,
                'video_url': getattr(lesson, 'video_url', ''),
                'document_url': getattr(lesson, 'document_url', ''),
                'audio_url': getattr(lesson, 'audio_url', ''),
            }

            return JsonResponse({
                'success': True,
                'message': 'Lesson content saved successfully',
                'lesson_data': lesson_data
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def get_lessons(self, request):
        """Get lessons for a course builder session"""
        try:
            session_id = request.GET.get('session_id')
            session = get_object_or_404(CourseBuilderSession, id=session_id, instructor=request.user)

            lessons = []

            if session.course:
                # Get lessons from actual course
                for module in session.course.modules.all():
                    for lesson in module.lessons.all():
                        lessons.append({
                            'id': lesson.id,
                            'title': lesson.title,
                            'module_title': module.title,
                            'content_type': getattr(lesson, 'content_type', 'text'),
                            'estimated_duration': lesson.estimated_duration
                        })
            else:
                # Get lessons from session data
                session_data = session.session_data or {}
                modules_data = session_data.get('modules', [])

                lesson_id = 1
                for module_data in modules_data:
                    module_title = module_data.get('title', 'Untitled Module')
                    for lesson_data in module_data.get('lessons', []):
                        lessons.append({
                            'id': f"temp_{lesson_id}",
                            'title': lesson_data.get('title', 'Untitled Lesson'),
                            'module_title': module_title,
                            'content_type': lesson_data.get('content_type', 'text'),
                            'estimated_duration': lesson_data.get('estimated_duration', 30)
                        })
                        lesson_id += 1

            return JsonResponse({
                'success': True,
                'lessons': lessons
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def get_lesson_content(self, request):
        """Get content for a specific lesson"""
        try:
            lesson_id = request.GET.get('lesson_id')

            if lesson_id.startswith('temp_'):
                # Handle temporary lesson from session data
                return JsonResponse({
                    'success': True,
                    'lesson': {
                        'id': lesson_id,
                        'title': 'Lesson',
                        'content_type': 'text',
                        'content': '',
                        'estimated_duration': 30,
                        'learning_objectives': '',
                        'video_url': '',
                        'document_url': '',
                        'audio_url': '',
                    }
                })

            lesson = get_object_or_404(Lesson, id=lesson_id, module__course__instructor=request.user)

            lesson_data = {
                'id': lesson.id,
                'title': lesson.title,
                'content_type': getattr(lesson, 'content_type', 'text'),
                'content': lesson.content,
                'estimated_duration': lesson.estimated_duration,
                'learning_objectives': lesson.learning_objectives,
                'video_url': getattr(lesson, 'video_url', ''),
                'document_url': getattr(lesson, 'document_url', ''),
                'audio_url': getattr(lesson, 'audio_url', ''),
            }

            return JsonResponse({
                'success': True,
                'lesson': lesson_data
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def create_quiz(self, request):
        """Create quiz for a lesson"""
        try:
            lesson_id = request.POST.get('lesson_id')
            quiz_title = request.POST.get('quiz_title')
            quiz_description = request.POST.get('quiz_description', '')
            questions_data = json.loads(request.POST.get('questions_data', '[]'))

            lesson = get_object_or_404(Lesson, id=lesson_id, module__course__instructor=request.user)

            # Create quiz
            quiz = Quiz.objects.create(
                lesson=lesson,
                title=quiz_title,
                description=quiz_description,
                passing_score=70,
                is_published=False
            )

            # Create questions
            for question_data in questions_data:
                Question.objects.create(
                    quiz=quiz,
                    question_text=question_data.get('question_text'),
                    question_type=question_data.get('question_type', 'multiple_choice'),
                    options=question_data.get('options', []),
                    correct_answer=question_data.get('correct_answer'),
                    explanation=question_data.get('explanation', ''),
                    points=question_data.get('points', 1),
                    sort_order=question_data.get('sort_order', 0)
                )

            return JsonResponse({
                'success': True,
                'quiz_id': quiz.id,
                'message': 'Quiz created successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def publish_course(self, request):
        """Submit course for review (instructors) or publish course (admins)"""
        try:
            course_id = request.POST.get('course_id')
            is_featured = request.POST.get('is_featured') == 'true'
            price = float(request.POST.get('price', 0))
            enrollment_limit = request.POST.get('enrollment_limit')

            course = get_object_or_404(Course, id=course_id, instructor=request.user)

            # Only admins can directly publish courses
            if request.user.is_superuser:
                course.publish_course(request.user, "Published via course builder")
                course.is_featured = is_featured
                course.price = price
                if enrollment_limit:
                    course.enrollment_limit = int(enrollment_limit)
                course.save()
                message = 'Course published successfully!'
            else:
                # Instructors can only submit for review
                course.submit_for_review(request.user)
                course.is_featured = is_featured
                course.price = price
                if enrollment_limit:
                    course.enrollment_limit = int(enrollment_limit)
                course.save()
                message = 'Course submitted for admin review!'

            # Mark session as completed
            session_id = request.POST.get('session_id')
            if session_id:
                try:
                    session = CourseBuilderSession.objects.get(id=session_id, instructor=request.user)
                    session.status = 'completed'
                    session.save()
                except CourseBuilderSession.DoesNotExist:
                    pass

            return JsonResponse({
                'success': True,
                'course_url': reverse('courses:course_detail', kwargs={'slug': course.slug}) if course.is_published else '#',
                'message': message
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def get_template(self, request):
        """Get content template by ID"""
        try:
            template_id = request.POST.get('template_id')
            template = get_object_or_404(ContentBlock, id=template_id)

            # Check if user can access this template
            if not (template.is_template or template.created_by == request.user):
                return JsonResponse({'success': False, 'error': 'Access denied'})

            return JsonResponse({
                'success': True,
                'content': template.content.get('html', '') if isinstance(template.content, dict) else str(template.content),
                'title': template.title,
                'type': template.content_type
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def create_template(self, request):
        """Create new content template"""
        try:
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            content_type = request.POST.get('content_type', 'text')
            content = request.POST.get('content', '')
            tags = request.POST.get('tags', '')
            is_template = request.POST.get('is_template') == 'true'

            # Create content block
            content_block = ContentBlock.objects.create(
                title=title,
                description=description,
                content_type=content_type,
                content={'html': content} if content_type == 'text' else content,
                tags=tags,
                is_template=is_template,
                created_by=request.user
            )

            return JsonResponse({
                'success': True,
                'template_id': content_block.id,
                'message': 'Template created successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def get_session(self, request):
        """Get course builder session data"""
        try:
            session_id = request.POST.get('session_id')
            if not session_id:
                return JsonResponse({'success': False, 'error': 'Session ID required'})

            session = get_object_or_404(CourseBuilderSession, id=session_id, instructor=request.user)

            return JsonResponse({
                'success': True,
                'session_data': session.session_data,
                'current_step': session.current_step,
                'course_id': session.course.id if session.course else None
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class MediaLibraryView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
    """
    Media library for managing course content files
    """
    template_name = 'course_builder/media_library.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get uploaded files for this instructor
        # This would integrate with your file storage system
        context.update({
            'media_files': [],  # Placeholder for media files
            'upload_url': reverse('course_builder:upload_media'),
        })

        return context


@method_decorator(csrf_exempt, name='dispatch')
class MediaUploadView(LoginRequiredMixin, InstructorRequiredMixin, View):
    """
    Handle file uploads for course content
    """

    def post(self, request, *args, **kwargs):
        try:
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return JsonResponse({'success': False, 'error': 'No file provided'})

            # Validate file type and size
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'application/pdf']
            max_size = 50 * 1024 * 1024  # 50MB

            if uploaded_file.content_type not in allowed_types:
                return JsonResponse({'success': False, 'error': 'File type not allowed'})

            if uploaded_file.size > max_size:
                return JsonResponse({'success': False, 'error': 'File too large (max 50MB)'})

            # Save file (this would integrate with your storage system)
            # For now, we'll return a placeholder response

            return JsonResponse({
                'success': True,
                'file_url': '/media/placeholder.jpg',  # Placeholder URL
                'file_name': uploaded_file.name,
                'file_size': uploaded_file.size,
                'file_type': uploaded_file.content_type
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ContentTemplateView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
    """
    Manage content templates and reusable blocks
    """
    template_name = 'course_builder/content_templates.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get content blocks for this instructor
        user_blocks = ContentBlock.objects.filter(created_by=self.request.user)
        template_blocks = ContentBlock.objects.filter(is_template=True)

        context.update({
            'user_blocks': user_blocks,
            'template_blocks': template_blocks,
        })

        return context
