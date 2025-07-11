"""
Advanced Content Management System for YITP LMS
Handles file uploads, bulk imports, and media processing
"""

import os
import mimetypes
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
import json


class ContentManagementView(TemplateView):
    """
    Advanced content management interface for instructors
    """
    template_name = 'instructor/content_management.html'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # Check if user is an instructor
        try:
            instructor_profile = request.user.instructor_profile
            if not (instructor_profile.is_verified and instructor_profile.is_active):
                messages.error(request, "You need to be a verified instructor to access content management.")
                return redirect('profile')
        except:
            messages.error(request, "You need to be a verified instructor to access content management.")
            return redirect('profile')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get instructor's uploaded files
        instructor = self.request.user
        
        # Get recent uploads (you would implement a proper file tracking system)
        context['recent_uploads'] = []
        
        # Get supported file types
        context['supported_formats'] = {
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
            'presentations': ['.ppt', '.pptx', '.odp'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.svg'],
            'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a'],
            'archives': ['.zip', '.rar', '.7z', '.tar.gz']
        }
        
        return context


@csrf_exempt
@login_required
def upload_file_ajax(request):
    """
    Handle AJAX file uploads with drag-and-drop support
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Check instructor permissions
    try:
        instructor_profile = request.user.instructor_profile
        if not (instructor_profile.is_verified and instructor_profile.is_active):
            return JsonResponse({'error': 'Insufficient permissions'}, status=403)
    except:
        return JsonResponse({'error': 'Instructor profile required'}, status=403)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    uploaded_file = request.FILES['file']
    
    # Validate file size (max 100MB)
    max_size = 100 * 1024 * 1024  # 100MB
    if uploaded_file.size > max_size:
        return JsonResponse({'error': 'File too large. Maximum size is 100MB.'}, status=400)
    
    # Validate file type
    allowed_extensions = [
        '.pdf', '.doc', '.docx', '.txt', '.rtf',  # Documents
        '.ppt', '.pptx', '.odp',  # Presentations
        '.jpg', '.jpeg', '.png', '.gif', '.svg',  # Images
        '.mp4', '.avi', '.mov', '.wmv', '.flv',  # Videos
        '.mp3', '.wav', '.ogg', '.m4a',  # Audio
        '.zip', '.rar', '.7z', '.tar.gz'  # Archives
    ]
    
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    if file_extension not in allowed_extensions:
        return JsonResponse({'error': f'File type {file_extension} not supported'}, status=400)
    
    try:
        # Create instructor-specific directory
        instructor_dir = f'instructor_content/{request.user.id}/'
        file_path = f'{instructor_dir}{uploaded_file.name}'
        
        # Save file
        saved_path = default_storage.save(file_path, uploaded_file)
        file_url = default_storage.url(saved_path)
        
        # Get file info
        file_info = {
            'name': uploaded_file.name,
            'size': uploaded_file.size,
            'type': uploaded_file.content_type,
            'extension': file_extension,
            'url': file_url,
            'path': saved_path
        }
        
        # TODO: Save file metadata to database
        # You would create a FileUpload model to track uploads
        
        return JsonResponse({
            'success': True,
            'file': file_info,
            'message': f'File "{uploaded_file.name}" uploaded successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Upload failed: {str(e)}'}, status=500)


@login_required
def bulk_import_content(request):
    """
    Handle bulk content import from various file formats
    """
    if request.method != 'POST':
        return redirect('users:content_management')
    
    # Check instructor permissions
    try:
        instructor_profile = request.user.instructor_profile
        if not (instructor_profile.is_verified and instructor_profile.is_active):
            messages.error(request, "Insufficient permissions for bulk import.")
            return redirect('users:content_management')
    except:
        messages.error(request, "Instructor profile required for bulk import.")
        return redirect('users:content_management')
    
    if 'import_file' not in request.FILES:
        messages.error(request, "No file selected for import.")
        return redirect('users:content_management')
    
    import_file = request.FILES['import_file']
    course_id = request.POST.get('course_id')
    
    if not course_id:
        messages.error(request, "Please select a course for import.")
        return redirect('users:content_management')
    
    try:
        from courses.models import Course
        course = Course.objects.get(id=course_id, instructor=request.user)
    except Course.DoesNotExist:
        messages.error(request, "Course not found or access denied.")
        return redirect('users:content_management')
    
    file_extension = os.path.splitext(import_file.name)[1].lower()
    
    try:
        if file_extension in ['.doc', '.docx']:
            result = import_word_document(import_file, course)
        elif file_extension == '.pdf':
            result = import_pdf_document(import_file, course)
        elif file_extension in ['.ppt', '.pptx']:
            result = import_presentation(import_file, course)
        else:
            messages.error(request, f"Import not supported for {file_extension} files.")
            return redirect('users:content_management')
        
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])
            
    except Exception as e:
        messages.error(request, f"Import failed: {str(e)}")
    
    return redirect('users:content_management')


def import_word_document(file, course):
    """
    Import content from Word document
    """
    try:
        # This is a placeholder - you would implement actual Word parsing
        # using libraries like python-docx
        
        # For now, create a basic lesson
        from courses.models import Module, Lesson
        
        # Get or create a module for imported content
        module, created = Module.objects.get_or_create(
            course=course,
            title="Imported Content",
            defaults={
                'description': 'Content imported from Word document',
                'sort_order': course.modules.count() + 1
            }
        )
        
        # Create lesson
        lesson = Lesson.objects.create(
            module=module,
            title=f"Lesson from {file.name}",
            content=f"<p>Content imported from {file.name}</p><p>This is a placeholder. Actual Word parsing would extract the real content.</p>",
            sort_order=module.lessons.count() + 1,
            is_published=False  # Keep as draft initially
        )
        
        return {
            'success': True,
            'message': f'Successfully imported content from {file.name} into course "{course.title}"'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to import Word document: {str(e)}'
        }


def import_pdf_document(file, course):
    """
    Import content from PDF document
    """
    try:
        # This is a placeholder - you would implement actual PDF parsing
        # using libraries like PyPDF2 or pdfplumber
        
        from courses.models import Module, Lesson
        
        # Get or create a module for imported content
        module, created = Module.objects.get_or_create(
            course=course,
            title="Imported Content",
            defaults={
                'description': 'Content imported from PDF document',
                'sort_order': course.modules.count() + 1
            }
        )
        
        # Create lesson
        lesson = Lesson.objects.create(
            module=module,
            title=f"Lesson from {file.name}",
            content=f"<p>Content imported from {file.name}</p><p>This is a placeholder. Actual PDF parsing would extract the real content.</p>",
            sort_order=module.lessons.count() + 1,
            is_published=False
        )
        
        return {
            'success': True,
            'message': f'Successfully imported content from {file.name} into course "{course.title}"'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to import PDF document: {str(e)}'
        }


def import_presentation(file, course):
    """
    Import content from PowerPoint presentation
    """
    try:
        # This is a placeholder - you would implement actual PowerPoint parsing
        # using libraries like python-pptx
        
        from courses.models import Module, Lesson
        
        # Get or create a module for imported content
        module, created = Module.objects.get_or_create(
            course=course,
            title="Imported Content",
            defaults={
                'description': 'Content imported from PowerPoint presentation',
                'sort_order': course.modules.count() + 1
            }
        )
        
        # Create lesson
        lesson = Lesson.objects.create(
            module=module,
            title=f"Lesson from {file.name}",
            content=f"<p>Content imported from {file.name}</p><p>This is a placeholder. Actual PowerPoint parsing would extract slides as lesson content.</p>",
            sort_order=module.lessons.count() + 1,
            is_published=False
        )
        
        return {
            'success': True,
            'message': f'Successfully imported content from {file.name} into course "{course.title}"'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to import presentation: {str(e)}'
        }


@login_required
def media_library(request):
    """
    Display instructor's media library
    """
    try:
        instructor_profile = request.user.instructor_profile
        if not (instructor_profile.is_verified and instructor_profile.is_active):
            messages.error(request, "Insufficient permissions for media library.")
            return redirect('profile')
    except:
        messages.error(request, "Instructor profile required for media library.")
        return redirect('profile')

    # TODO: Implement actual media library with database tracking
    context = {
        'media_files': [],  # Would be populated from database
        'storage_used': 0,  # Calculate actual storage used
        'storage_limit': 1024 * 1024 * 1024,  # 1GB limit
    }

    return render(request, 'instructor/media_library.html', context)
