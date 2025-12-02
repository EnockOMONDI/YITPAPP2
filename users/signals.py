from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from . models import Profile, InstructorProfile, SponsorshipRequest
from payments.models import Payment
from blogapp.models import Post, Category
import logging

# Set up logger
logger = logging.getLogger(__name__)


def _ensure_aware(dt):
    """Return a timezone-aware datetime (if value is provided)."""
    if dt and timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_default_timezone())
    return dt


@receiver(pre_save, sender=User)
def ensure_user_datetimes_are_aware(sender, instance, **kwargs):
    """Force core auth datetime fields to be timezone aware."""
    instance.last_login = _ensure_aware(instance.last_login)
    instance.date_joined = _ensure_aware(instance.date_joined)


@receiver(pre_save, sender=Payment)
def ensure_payment_datetimes_are_aware(sender, instance, **kwargs):
    """Guard Payment timestamps against naive assignments."""
    instance.created_at = _ensure_aware(instance.created_at)
    instance.confirmed_at = _ensure_aware(instance.confirmed_at)
    instance.expires_at = _ensure_aware(instance.expires_at)

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Create a profile for newly created users only"""
    if created:  # Only create profile for new users
        try:
            # Check if profile already exists
            if not hasattr(instance, 'profile'):
                Profile.objects.create(user=instance)
        except ObjectDoesNotExist:
            Profile.objects.create(user=instance)


@receiver(post_save, sender=InstructorProfile)
def setup_instructor_permissions(sender, instance, created, **kwargs):
    """
    Automatically set up permissions and staff status when InstructorProfile is created or updated.
    This signal ensures instructors get the appropriate permissions based on their role.
    """
    user = instance.user

    # Always ensure instructor users have staff status for admin access
    if instance.instructor_role in ['system_admin', 'course_instructor', 'content_manager', 'accountant', 'teaching_assistant']:
        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=['is_staff'])

    # Set up role-based permissions
    try:
        # Get content types for permission assignment
        from courses.models import Course, Module, Lesson
        from progress.models import Enrollment
        from assessments.models import Quiz, Question

        course_ct = ContentType.objects.get_for_model(Course)
        module_ct = ContentType.objects.get_for_model(Module)
        lesson_ct = ContentType.objects.get_for_model(Lesson)
        enrollment_ct = ContentType.objects.get_for_model(Enrollment)
        quiz_ct = ContentType.objects.get_for_model(Quiz)
        question_ct = ContentType.objects.get_for_model(Question)
        payment_ct = ContentType.objects.get_for_model(Payment)
        sponsorship_ct = ContentType.objects.get_for_model(SponsorshipRequest)
        post_ct = ContentType.objects.get_for_model(Post)
        category_ct = ContentType.objects.get_for_model(Category)

        # Clear existing permissions to avoid duplicates
        user.user_permissions.clear()

        # Define role-specific permission mappings
        role_permissions = {
            'system_admin': {
                'is_superuser': True,
                'permissions': []  # Superusers get all permissions automatically
            },
            'course_instructor': {
                'is_superuser': False,
                'permissions': [
                    # Course visibility
                    (course_ct, ['view']),
                    # Module and lesson management
                    (module_ct, ['view', 'change']),
                    (lesson_ct, ['view', 'add', 'change']),
                    (enrollment_ct, ['view', 'change']),
                    # Assessment management
                    (quiz_ct, ['view', 'add', 'change']),
                    (question_ct, ['view', 'add', 'change']),
                ]
            },
            'teaching_assistant': {
                'is_superuser': False,
                'permissions': [
                    # Limited course access
                    (course_ct, ['view']),
                    (module_ct, ['view', 'change']),
                    (lesson_ct, ['view', 'change']),
                    (enrollment_ct, ['view', 'change']),
                    # Assessment grading
                    (quiz_ct, ['view', 'change']),
                    (question_ct, ['view']),
                ]
            },
            'content_manager': {
                'is_superuser': False,
                'permissions': [
                    # Content creation focus (course creation restricted to super admins)
                    (course_ct, ['view']),
                    (module_ct, ['view', 'add', 'change']),
                    (lesson_ct, ['view', 'add', 'change']),
                    (enrollment_ct, ['view']),
                    # Assessment creation
                    (quiz_ct, ['view', 'add', 'change']),
                    (question_ct, ['view', 'add', 'change']),
                    # Blog management
                    (post_ct, ['view', 'add', 'change']),
                    (category_ct, ['view', 'add', 'change']),
                ]
            },
            'accountant': {
                'is_superuser': False,
                'permissions': [
                    (payment_ct, ['view', 'change']),
                    (sponsorship_ct, ['view', 'change']),
                    (course_ct, ['view']),
                    (enrollment_ct, ['view']),
                ]
            },
            'grader': {
                'is_superuser': False,
                'permissions': [
                    # Grading focus
                    (course_ct, ['view']),
                    (module_ct, ['view']),
                    (lesson_ct, ['view']),
                    (enrollment_ct, ['view', 'change']),
                    # Assessment grading
                    (quiz_ct, ['view', 'change']),
                    (question_ct, ['view']),
                ]
            }
        }

        # Apply role-specific permissions
        role_config = role_permissions.get(instance.instructor_role, role_permissions['course_instructor'])

        # Set superuser status
        if role_config['is_superuser'] and not user.is_superuser:
            user.is_superuser = True
            user.save(update_fields=['is_superuser'])
        elif not role_config['is_superuser'] and user.is_superuser:
            # Only remove superuser if they're not system_admin
            if instance.instructor_role != 'system_admin':
                user.is_superuser = False
                user.save(update_fields=['is_superuser'])

        # Add specific permissions for non-superusers
        if not role_config['is_superuser']:
            permissions_to_add = []

            for content_type, actions in role_config['permissions']:
                for action in actions:
                    try:
                        permission = Permission.objects.get(
                            content_type=content_type,
                            codename=f'{action}_{content_type.model}'
                        )
                        permissions_to_add.append(permission)
                    except Permission.DoesNotExist:
                        # Permission doesn't exist, skip it
                        continue

            # Add all permissions at once
            if permissions_to_add:
                user.user_permissions.add(*permissions_to_add)

        # Auto-verify system admins and mark verification timestamp
        if instance.instructor_role == 'system_admin' and instance.verification_status != 'verified':
            instance.verification_status = 'verified'
            instance.verified_at = timezone.now()
            # Save without triggering the signal again
            InstructorProfile.objects.filter(pk=instance.pk).update(
                verification_status='verified',
                verified_at=timezone.now()
            )

        # Send welcome email notification for newly created instructor profiles
        if created:
            try:
                from .email_utils import send_instructor_welcome_email, log_instructor_account_creation

                # Try to determine who created this instructor account
                created_by_admin = None

                # Check if there's a current request context to get the admin user
                try:
                    from django.contrib.admin.models import LogEntry

                    # Get the most recent log entry for this user creation
                    user_ct = ContentType.objects.get_for_model(User)
                    recent_log = LogEntry.objects.filter(
                        content_type=user_ct,
                        object_id=str(user.pk),
                        action_flag=1  # ADDITION
                    ).order_by('-action_time').first()

                    if recent_log:
                        created_by_admin = recent_log.user
                except Exception:
                    # If we can't determine the admin, that's okay
                    pass

                # Send the welcome email
                email_sent = send_instructor_welcome_email(
                    user=user,
                    instructor_profile=instance,
                    temporary_password=None,  # No temp password for signal-created accounts
                    created_by_admin=created_by_admin
                )

                # Log the account creation for audit purposes
                log_instructor_account_creation(
                    user=user,
                    instructor_profile=instance,
                    created_by_admin=created_by_admin,
                    email_sent=email_sent
                )

                if email_sent:
                    logger.info(f"✅ Welcome email sent to new instructor: {user.email}")
                else:
                    logger.warning(f"⚠️ Failed to send welcome email to new instructor: {user.email}")

            except Exception as email_error:
                logger.error(f"❌ Error sending instructor welcome email to {user.email}: {str(email_error)}")
                # Don't break the save process if email fails

    except Exception as e:
        # Log the error but don't break the save process
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error setting up instructor permissions for {user.username}: {str(e)}")

        # At minimum, ensure staff status is set
        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=['is_staff'])

        # Still try to send welcome email even if permissions failed
        if created:
            try:
                from .email_utils import send_instructor_welcome_email, log_instructor_account_creation

                email_sent = send_instructor_welcome_email(
                    user=user,
                    instructor_profile=instance,
                    temporary_password=None,
                    created_by_admin=None
                )

                log_instructor_account_creation(
                    user=user,
                    instructor_profile=instance,
                    created_by_admin=None,
                    email_sent=email_sent
                )

                if email_sent:
                    logger.info(f"✅ Welcome email sent despite permission setup failure: {user.email}")

            except Exception as email_error:
                logger.error(f"❌ Failed to send welcome email after permission error: {str(email_error)}")
