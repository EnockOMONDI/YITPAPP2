#!/usr/bin/env python
"""
Django management command to create a test instructor user account
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from users.models import Profile, InstructorProfile
import secrets
import string


class Command(BaseCommand):
    help = 'Create a test instructor user account with proper permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='rayerin924@jxbav.com',
            help='Email address for the instructor account'
        )
        parser.add_argument(
            '--username',
            type=str,
            default='instructor_rayerin',
            help='Username for the instructor account'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=None,
            help='Password for the instructor account (auto-generated if not provided)'
        )
        parser.add_argument(
            '--role',
            type=str,
            default='course_instructor',
            choices=['system_admin', 'course_instructor', 'teaching_assistant', 'content_creator', 'grader'],
            help='Instructor role'
        )

    def handle(self, *args, **options):
        email = options['email']
        username = options['username']
        password = options['password']
        role = options['role']

        # Generate secure password if not provided
        if not password:
            # Generate a secure but memorable password
            password = self.generate_secure_password()

        self.stdout.write(self.style.SUCCESS('🎓 Creating Test Instructor Account'))
        self.stdout.write('=' * 50)

        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'❌ User with username "{username}" already exists!')
                )
                return

            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'❌ User with email "{email}" already exists!')
                )
                return

            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name='Ray',
                last_name='Erin',
                is_staff=True,
                is_active=True
            )

            self.stdout.write(
                self.style.SUCCESS(f'✅ Created user: {username}')
            )

            # Create or update the basic profile
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'phone_number': '+254700000000',
                    'bio': 'Test instructor account for YITP LMS testing and development',
                    'email_verified': True,
                    'profile_completion_percentage': 85.00,
                    'total_points': 0,
                    'current_streak': 0,
                    'longest_streak': 0
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS('✅ Created basic profile')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ Updated existing profile')
                )

            # Create instructor profile
            instructor_profile, created = InstructorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'instructor_role': role,
                    'bio': 'Experienced educator specializing in youth development and digital literacy. '
                           'Passionate about creating engaging learning experiences that empower young minds.',
                    'qualifications': 'M.Ed. in Educational Technology, B.A. in Youth Development, '
                                    'Certified Digital Learning Specialist',
                    'years_experience': 8,
                    'verification_status': 'verified',
                    'verified_at': timezone.now(),
                    'is_active': True,
                    'can_create_courses': True,
                    'can_manage_assessments': True,
                    'can_view_analytics': True
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created instructor profile with role: {role}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ Updated existing instructor profile')
                )

            # Set up permissions based on role
            self.setup_permissions(user, role)

            # Verify admin access
            self.verify_admin_access(user)

            # Display account details
            self.display_account_details(user, password, instructor_profile)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating instructor account: {str(e)}')
            )
            raise

    def generate_secure_password(self):
        """Generate a secure but memorable password"""
        # Use a combination of words and numbers for memorability
        adjectives = ['Smart', 'Quick', 'Bright', 'Swift', 'Clear']
        nouns = ['Teacher', 'Guide', 'Mentor', 'Coach', 'Leader']
        
        adjective = secrets.choice(adjectives)
        noun = secrets.choice(nouns)
        number = secrets.randbelow(100)
        
        # Add some special characters for security
        special_chars = '!@#$'
        special = secrets.choice(special_chars)
        
        return f"{adjective}{noun}{number:02d}{special}"

    def setup_permissions(self, user, role):
        """Set up permissions based on instructor role"""
        self.stdout.write('🔐 Setting up permissions...')
        
        try:
            # Get content types for different models
            content_types = {
                'course': ContentType.objects.get(app_label='courses', model='course'),
                'module': ContentType.objects.get(app_label='courses', model='module'),
                'lesson': ContentType.objects.get(app_label='courses', model='lesson'),
                'quiz': ContentType.objects.get(app_label='assessments', model='quiz'),
                'question': ContentType.objects.get(app_label='assessments', model='question'),
                'enrollment': ContentType.objects.get(app_label='courses', model='enrollment'),
            }

            permissions_to_add = []

            if role == 'system_admin':
                # System admins get superuser status
                user.is_superuser = True
                user.save()
                self.stdout.write('   ✅ Granted superuser status')
            else:
                # Add specific permissions for other instructor roles
                permission_sets = {
                    'course_instructor': [
                        ('courses', 'course', ['view', 'add', 'change']),
                        ('courses', 'module', ['view', 'add', 'change']),
                        ('courses', 'lesson', ['view', 'add', 'change']),
                        ('courses', 'enrollment', ['view', 'change']),
                        ('assessments', 'quiz', ['view', 'add', 'change']),
                        ('assessments', 'question', ['view', 'add', 'change']),
                    ],
                    'content_creator': [
                        ('courses', 'course', ['view', 'add', 'change']),
                        ('courses', 'module', ['view', 'add', 'change']),
                        ('courses', 'lesson', ['view', 'add', 'change']),
                        ('assessments', 'quiz', ['view', 'add', 'change']),
                        ('assessments', 'question', ['view', 'add', 'change']),
                    ],
                    'teaching_assistant': [
                        ('courses', 'course', ['view']),
                        ('courses', 'module', ['view']),
                        ('courses', 'lesson', ['view']),
                        ('courses', 'enrollment', ['view', 'change']),
                        ('assessments', 'quiz', ['view']),
                        ('assessments', 'question', ['view']),
                    ],
                    'grader': [
                        ('courses', 'course', ['view']),
                        ('assessments', 'quiz', ['view', 'change']),
                        ('assessments', 'question', ['view']),
                    ]
                }

                role_permissions = permission_sets.get(role, permission_sets['course_instructor'])
                
                for app_label, model, actions in role_permissions:
                    for action in actions:
                        try:
                            ct = ContentType.objects.get(app_label=app_label, model=model)
                            perm = Permission.objects.get(content_type=ct, codename=f'{action}_{model}')
                            permissions_to_add.append(perm)
                        except (ContentType.DoesNotExist, Permission.DoesNotExist):
                            self.stdout.write(f'   ⚠️  Permission {action}_{model} not found')

                if permissions_to_add:
                    user.user_permissions.add(*permissions_to_add)
                    self.stdout.write(f'   ✅ Added {len(permissions_to_add)} permissions')

        except Exception as e:
            self.stdout.write(f'   ❌ Error setting up permissions: {e}')

    def verify_admin_access(self, user):
        """Verify that the user can access Django admin"""
        self.stdout.write('🔍 Verifying admin access...')
        
        if user.is_staff:
            self.stdout.write('   ✅ User has staff status - can access Django admin')
        else:
            self.stdout.write('   ❌ User does not have staff status')
            
        if user.is_superuser:
            self.stdout.write('   ✅ User has superuser status - full admin access')
        elif user.user_permissions.exists():
            self.stdout.write(f'   ✅ User has {user.user_permissions.count()} specific permissions')
        else:
            self.stdout.write('   ⚠️  User has no specific permissions')

    def display_account_details(self, user, password, instructor_profile):
        """Display the created account details"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('🎉 TEST INSTRUCTOR ACCOUNT CREATED SUCCESSFULLY!'))
        self.stdout.write('=' * 50)
        
        self.stdout.write(f'👤 Username: {user.username}')
        self.stdout.write(f'📧 Email: {user.email}')
        self.stdout.write(f'🔑 Password: {password}')
        self.stdout.write(f'👨‍🏫 Role: {instructor_profile.get_instructor_role_display()}')
        self.stdout.write(f'✅ Verification Status: {instructor_profile.get_verification_status_display()}')
        
        self.stdout.write('\n📋 PERMISSIONS SUMMARY:')
        permissions = instructor_profile.get_permissions_summary()
        for key, value in permissions.items():
            status = '✅' if value else '❌'
            self.stdout.write(f'   {status} {key.replace("_", " ").title()}: {value}')
        
        self.stdout.write('\n🌐 ACCESS INFORMATION:')
        self.stdout.write('   • Main Application: http://localhost:8000/')
        self.stdout.write('   • Django Admin: http://localhost:8000/admin/')
        self.stdout.write('   • Documentation: http://localhost:8000/documentation/')
        
        self.stdout.write('\n📝 NEXT STEPS:')
        self.stdout.write('   1. Test login to main application')
        self.stdout.write('   2. Test login to Django admin interface')
        self.stdout.write('   3. Verify course creation permissions')
        self.stdout.write('   4. Test assessment management features')
        
        self.stdout.write('\n' + '=' * 50)
