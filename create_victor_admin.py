#!/usr/bin/env python3
"""
Simple script to create Victor's super admin account
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Profile

def create_victor_admin():
    """Create Victor's super admin account"""
    print("🚀 Creating Victor's Super Admin Account...")
    
    # Admin data
    username = 'victor'
    email = 'info@youthimpactglobal.com'
    password = 'victorpassword'
    first_name = 'Victor'
    last_name = '(YITP Project Owner)'
    
    try:
        # Check if user exists
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_superuser': True,
                'is_staff': True,
                'is_active': True
            }
        )
        
        if not created:
            print(f"✅ User '{username}' already exists - updating...")
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
        else:
            print(f"✅ Created new user: {username}")
        
        # Set password
        user.set_password(password)
        user.save()
        
        # Create/update profile
        profile, profile_created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'bio': 'YITP Project Owner and Super Administrator',
                'location': 'Global',
                'website': 'https://www.youthimpactglobal.com'
            }
        )
        
        if profile_created:
            print(f"✅ Created profile for: {username}")
        else:
            print(f"✅ Profile already exists for: {username}")
        
        print("\n📊 User Details:")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.first_name} {user.last_name}")
        print(f"   Superuser: {user.is_superuser}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Active: {user.is_active}")
        print(f"   User ID: {user.id}")
        
        print("\n🎉 SUCCESS! Victor's super admin account is ready!")
        print("\n📋 LOGIN CREDENTIALS:")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        
        print("\n🔗 ACCESS URLS:")
        print("   Development: http://127.0.0.1:8000/admin/")
        print("   Production: https://www.youthimpactglobal.com/admin/")
        print("\n🎯 SUPER ADMIN DASHBOARD:")
        print("   Development: http://127.0.0.1:8000/users/superuser/profile/")
        print("   Production: https://www.youthimpactglobal.com/users/superuser/profile/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating super admin: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_victor_admin()
    sys.exit(0 if success else 1)
