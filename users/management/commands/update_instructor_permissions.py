"""
Management command to update instructor permissions for admin access
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import InstructorProfile


class Command(BaseCommand):
    help = 'Update instructor permissions for admin access'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Updating instructor permissions...'))
        
        # Get all instructor profiles
        instructor_profiles = InstructorProfile.objects.filter(is_active=True)
        
        for profile in instructor_profiles:
            user = profile.user
            self.stdout.write(f'   Updating permissions for {user.get_full_name()} ({profile.get_instructor_role_display()})')
            
            # Make user staff
            user.is_staff = True
            
            try:
                # Get content types
                course_ct = ContentType.objects.get(app_label='courses', model='course')
                module_ct = ContentType.objects.get(app_label='courses', model='module')
                lesson_ct = ContentType.objects.get(app_label='courses', model='lesson')
                quiz_ct = ContentType.objects.get(app_label='assessments', model='quiz')
                question_ct = ContentType.objects.get(app_label='assessments', model='question')
                message_ct = ContentType.objects.get(app_label='communication', model='message')
                
                # Define permissions based on role
                if profile.instructor_role == 'system_admin':
                    # System admins get superuser status
                    user.is_superuser = True
                    self.stdout.write(f'     ✅ Granted superuser status')
                else:
                    # Other instructors get specific permissions
                    permissions_to_add = []
                    
                    # Course permissions
                    try:
                        permissions_to_add.extend([
                            Permission.objects.get(content_type=course_ct, codename='view_course'),
                            Permission.objects.get(content_type=course_ct, codename='add_course'),
                            Permission.objects.get(content_type=course_ct, codename='change_course'),
                        ])
                    except Permission.DoesNotExist:
                        self.stdout.write(f'     ⚠️  Course permissions not found')
                    
                    # Module and lesson permissions
                    try:
                        permissions_to_add.extend([
                            Permission.objects.get(content_type=module_ct, codename='view_module'),
                            Permission.objects.get(content_type=module_ct, codename='add_module'),
                            Permission.objects.get(content_type=module_ct, codename='change_module'),
                            Permission.objects.get(content_type=lesson_ct, codename='view_lesson'),
                            Permission.objects.get(content_type=lesson_ct, codename='add_lesson'),
                            Permission.objects.get(content_type=lesson_ct, codename='change_lesson'),
                        ])
                    except Permission.DoesNotExist:
                        self.stdout.write(f'     ⚠️  Module/Lesson permissions not found')
                    
                    # Assessment permissions
                    if profile.can_manage_assessments:
                        try:
                            permissions_to_add.extend([
                                Permission.objects.get(content_type=quiz_ct, codename='view_quiz'),
                                Permission.objects.get(content_type=quiz_ct, codename='add_quiz'),
                                Permission.objects.get(content_type=quiz_ct, codename='change_quiz'),
                                Permission.objects.get(content_type=question_ct, codename='view_question'),
                                Permission.objects.get(content_type=question_ct, codename='add_question'),
                                Permission.objects.get(content_type=question_ct, codename='change_question'),
                            ])
                        except Permission.DoesNotExist:
                            self.stdout.write(f'     ⚠️  Assessment permissions not found')
                    
                    # Message permissions
                    try:
                        permissions_to_add.extend([
                            Permission.objects.get(content_type=message_ct, codename='view_message'),
                            Permission.objects.get(content_type=message_ct, codename='change_message'),
                        ])
                    except Permission.DoesNotExist:
                        self.stdout.write(f'     ⚠️  Message permissions not found')
                    
                    # Add permissions to user
                    if permissions_to_add:
                        user.user_permissions.add(*permissions_to_add)
                        self.stdout.write(f'     ✅ Added {len(permissions_to_add)} permissions')
                    else:
                        self.stdout.write(f'     ⚠️  No permissions to add')
                
                user.save()
                
            except Exception as e:
                self.stdout.write(f'     ❌ Error updating permissions: {e}')
        
        self.stdout.write(self.style.SUCCESS('✅ Instructor permissions updated successfully!'))
        
        # Show summary
        self.stdout.write('\n📊 PERMISSION SUMMARY:')
        for profile in instructor_profiles:
            user = profile.user
            perm_count = user.user_permissions.count()
            is_super = user.is_superuser
            is_staff = user.is_staff
            
            self.stdout.write(f'   {user.get_full_name()}: Staff={is_staff}, Super={is_super}, Permissions={perm_count}')
