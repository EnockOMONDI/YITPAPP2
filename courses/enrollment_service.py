"""
Unified Course Enrollment Service for YITP
Consolidates enrollment logic from duplicate views into a single, reusable service
"""

from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
import logging

from .models import Course
from progress.models import Enrollment
from users.email_utils import send_enrollment_confirmation_email, send_enrollment_admin_notification

logger = logging.getLogger(__name__)


class EnrollmentService:
    """
    Unified service for handling course enrollments with comprehensive validation
    """
    
    @staticmethod
    def validate_enrollment_eligibility(user, course):
        """
        Validate if user is eligible for enrollment
        
        Returns:
            dict: {'is_valid': bool, 'error_message': str or None}
        """
        # Check if course is published
        if not course.is_published:
            return {
                'is_valid': False,
                'error_message': f'Course "{course.title}" is not currently available for enrollment.'
            }
        
        # Check enrollment limits
        if course.enrollment_limit:
            current_enrollments = Enrollment.objects.filter(
                course=course, 
                status='active'
            ).count()
            
            if current_enrollments >= course.enrollment_limit:
                return {
                    'is_valid': False,
                    'error_message': (
                        f'Sorry, "{course.title}" has reached its enrollment limit of '
                        f'{course.enrollment_limit} students. Please check back later or '
                        f'contact support for waitlist options.'
                    )
                }

        # Check payment verification for paid courses
        if course.price > 0:
            try:
                profile = user.profile
            except:
                # Create profile if it doesn't exist
                from users.models import Profile
                profile = Profile.objects.create(user=user)

            if not profile.has_confirmed_payment:
                return {
                    'is_valid': False,
                    'error_message': (
                        f'Payment verification required for "{course.title}". '
                        f'This course costs KES {course.price:,.2f}. Please complete your payment '
                        f'and wait for confirmation before enrolling. '
                        f'Contact support at +254722646958 for payment verification.'
                    )
                }

        # Check if already enrolled
        existing_enrollment = Enrollment.objects.filter(
            student=user,
            course=course
        ).first()
        
        if existing_enrollment:
            return {
                'is_valid': False,
                'error_message': f'You are already enrolled in "{course.title}".',
                'existing_enrollment': existing_enrollment
            }

        return {'is_valid': True}

    @staticmethod
    @transaction.atomic
    def process_enrollment(user, course):
        """
        Process the actual enrollment with database transaction
        
        Returns:
            dict: {
                'success': bool,
                'enrollment': Enrollment or None,
                'message': str,
                'created': bool
            }
        """
        try:
            enrollment, created = Enrollment.objects.get_or_create(
                student=user,
                course=course,
                defaults={
                    'status': 'active',
                    'progress_percentage': 0.00
                }
            )

            if created:
                logger.info(f"New enrollment created: {user.email} -> {course.title}")
                return {
                    'success': True,
                    'enrollment': enrollment,
                    'message': f'Successfully enrolled in "{course.title}"',
                    'created': True
                }
            else:
                logger.info(f"Existing enrollment found: {user.email} -> {course.title}")
                return {
                    'success': False,
                    'enrollment': enrollment,
                    'message': f'You are already enrolled in "{course.title}"',
                    'created': False
                }
                
        except Exception as e:
            logger.error(f"Enrollment processing failed for {user.email} -> {course.title}: {str(e)}")
            raise ValidationError(f"Failed to process enrollment: {str(e)}")

    @staticmethod
    def send_enrollment_notifications(user, course, enrollment):
        """
        Send enrollment confirmation emails with comprehensive error handling
        
        Returns:
            dict: {'user_email_sent': bool, 'admin_email_sent': bool, 'errors': list}
        """
        results = {
            'user_email_sent': False,
            'admin_email_sent': False,
            'errors': []
        }

        # Send user confirmation email
        try:
            send_enrollment_confirmation_email(user, course, enrollment)
            results['user_email_sent'] = True
            logger.info(f"Enrollment confirmation email sent to {user.email}")
        except Exception as e:
            error_msg = f"Failed to send enrollment confirmation email to {user.email}: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)

        # Send admin notification email
        try:
            send_enrollment_admin_notification(user, course, enrollment)
            results['admin_email_sent'] = True
            logger.info(f"Enrollment admin notification sent for {user.email} -> {course.title}")
        except Exception as e:
            error_msg = f"Failed to send enrollment admin notification: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)

        return results

    @classmethod
    def enroll_user_in_course(cls, user, course):
        """
        Complete enrollment process with validation, processing, and notifications
        
        Returns:
            dict: {
                'success': bool,
                'enrollment': Enrollment or None,
                'message': str,
                'email_results': dict,
                'created': bool
            }
        """
        # Step 1: Validate eligibility
        validation_result = cls.validate_enrollment_eligibility(user, course)
        if not validation_result['is_valid']:
            return {
                'success': False,
                'enrollment': validation_result.get('existing_enrollment'),
                'message': validation_result['error_message'],
                'email_results': None,
                'created': False
            }

        # Step 2: Process enrollment
        try:
            enrollment_result = cls.process_enrollment(user, course)
            
            # Step 3: Send notifications if enrollment was successful
            email_results = None
            if enrollment_result['success'] and enrollment_result['created']:
                email_results = cls.send_enrollment_notifications(
                    user, course, enrollment_result['enrollment']
                )

            return {
                'success': enrollment_result['success'],
                'enrollment': enrollment_result['enrollment'],
                'message': enrollment_result['message'],
                'email_results': email_results,
                'created': enrollment_result['created']
            }
            
        except ValidationError as e:
            logger.error(f"Enrollment validation error: {str(e)}")
            return {
                'success': False,
                'enrollment': None,
                'message': str(e),
                'email_results': None,
                'created': False
            }
        except Exception as e:
            logger.error(f"Unexpected enrollment error: {str(e)}")
            return {
                'success': False,
                'enrollment': None,
                'message': f"An unexpected error occurred during enrollment. Please try again or contact support.",
                'email_results': None,
                'created': False
            }

    @staticmethod
    def get_course_by_slug_or_id(course_identifier):
        """
        Get course by slug or ID to handle both URL patterns
        
        Args:
            course_identifier: Either course slug (str) or course ID (int)
            
        Returns:
            Course object or raises Http404
        """
        if isinstance(course_identifier, str):
            # Handle slug-based lookup
            return get_object_or_404(Course, slug=course_identifier, is_published=True)
        else:
            # Handle ID-based lookup
            return get_object_or_404(Course, id=course_identifier, is_published=True)
