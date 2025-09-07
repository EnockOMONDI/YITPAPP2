#!/usr/bin/env python3
"""
Create Super Admin Account for YITP Project Owner
Creates Victor's super admin account on both production and development databases
"""

import os
import sys
import django
from datetime import datetime

def setup_django_environment(environment='development'):
    """Setup Django environment for specified database"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    
    if environment == 'production':
        os.environ['DJANGO_ENV'] = 'production'
    else:
        os.environ.pop('DJANGO_ENV', None)  # Remove to ensure development mode
    
    django.setup()

class SuperAdminCreator:
    def __init__(self):
        self.admin_data = {
            'username': 'victor',
            'email': 'info@youthimpactglobal.com',
            'password': 'victorpassword',
            'first_name': 'Victor',
            'last_name': '(YITP Project Owner)',
            'is_superuser': True,
            'is_staff': True,
            'is_active': True
        }
    
    def log(self, message, environment=""):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        env_prefix = f"[{environment.upper()}]" if environment else ""
        print(f"[{timestamp}] {env_prefix} {message}")
    
    def create_superuser_account(self, environment):
        """Create super admin account in specified environment"""
        self.log(f"Creating super admin account in {environment} database...", environment)
        
        try:
            from django.contrib.auth.models import User
            from users.models import Profile
            
            # Check if user already exists
            existing_user = User.objects.filter(username=self.admin_data['username']).first()
            
            if existing_user:
                self.log(f"User '{self.admin_data['username']}' already exists", environment)
                self.log(f"Updating existing user to super admin status...", environment)
                
                # Update existing user
                existing_user.email = self.admin_data['email']
                existing_user.first_name = self.admin_data['first_name']
                existing_user.last_name = self.admin_data['last_name']
                existing_user.is_superuser = self.admin_data['is_superuser']
                existing_user.is_staff = self.admin_data['is_staff']
                existing_user.is_active = self.admin_data['is_active']
                existing_user.set_password(self.admin_data['password'])
                existing_user.save()
                
                user = existing_user
                self.log(f"✅ Updated existing user: {user.username}", environment)
            else:
                # Create new user
                user = User.objects.create_user(
                    username=self.admin_data['username'],
                    email=self.admin_data['email'],
                    password=self.admin_data['password'],
                    first_name=self.admin_data['first_name'],
                    last_name=self.admin_data['last_name']
                )
                
                # Set superuser privileges
                user.is_superuser = self.admin_data['is_superuser']
                user.is_staff = self.admin_data['is_staff']
                user.is_active = self.admin_data['is_active']
                user.save()
                
                self.log(f"✅ Created new super admin: {user.username}", environment)
            
            # Create or update profile
            profile, created = Profile.objects.get_or_create(user=user)
            profile.bio = "YITP Project Owner and Super Administrator"
            profile.location = "Global"
            profile.website = "https://www.youthimpactglobal.com"
            profile.save()
            
            if created:
                self.log(f"✅ Created profile for: {user.username}", environment)
            else:
                self.log(f"✅ Updated profile for: {user.username}", environment)
            
            # Verify superuser status
            self.log(f"📊 User Details:", environment)
            self.log(f"   Username: {user.username}", environment)
            self.log(f"   Email: {user.email}", environment)
            self.log(f"   Full Name: {user.first_name} {user.last_name}", environment)
            self.log(f"   Superuser: {user.is_superuser}", environment)
            self.log(f"   Staff: {user.is_staff}", environment)
            self.log(f"   Active: {user.is_active}", environment)
            self.log(f"   User ID: {user.id}", environment)
            
            return user
            
        except Exception as e:
            self.log(f"❌ Error creating super admin: {str(e)}", environment)
            return None
    
    def test_database_connection(self, environment):
        """Test database connection"""
        self.log(f"Testing {environment} database connection...", environment)
        
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            self.log(f"✅ Database connection successful", environment)
            
            # Get database info
            db_config = connection.settings_dict
            engine = db_config['ENGINE']
            
            if 'postgresql' in engine:
                db_type = "PostgreSQL (Supabase)"
                host = db_config.get('HOST', 'Unknown')
                self.log(f"   Database: {db_type}", environment)
                self.log(f"   Host: {host}", environment)
            elif 'sqlite' in engine:
                db_type = "SQLite"
                db_name = db_config.get('NAME', 'Unknown')
                self.log(f"   Database: {db_type}", environment)
                self.log(f"   File: {db_name}", environment)
            
            return True
            
        except Exception as e:
            self.log(f"❌ Database connection failed: {str(e)}", environment)
            return False
    
    def create_admin_on_both_databases(self):
        """Create super admin on both production and development databases"""
        self.log("🚀 CREATING SUPER ADMIN ON BOTH DATABASES")
        self.log("=" * 80)
        
        environments = ['development', 'production']
        results = {}
        
        for environment in environments:
            try:
                self.log(f"\n📍 PROCESSING {environment.upper()} DATABASE", environment)
                self.log("-" * 60, environment)
                
                # Setup Django environment
                setup_django_environment(environment)
                
                # Test database connection
                if not self.test_database_connection(environment):
                    results[environment] = False
                    continue
                
                # Create super admin account
                user = self.create_superuser_account(environment)
                results[environment] = user is not None
                
                if results[environment]:
                    self.log(f"✅ {environment.upper()} setup completed successfully", environment)
                else:
                    self.log(f"❌ {environment.upper()} setup failed", environment)
                
            except Exception as e:
                self.log(f"❌ Fatal error in {environment}: {str(e)}", environment)
                results[environment] = False
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log("📊 SUPER ADMIN CREATION SUMMARY")
        self.log("=" * 80)
        
        for environment, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            self.log(f"{environment.upper()}: {status}")
        
        if all(results.values()):
            self.log("\n🎉 SUPER ADMIN CREATED SUCCESSFULLY ON BOTH DATABASES!")
            self.log("\n📋 LOGIN CREDENTIALS:")
            self.log(f"   Username: {self.admin_data['username']}")
            self.log(f"   Email: {self.admin_data['email']}")
            self.log(f"   Password: {self.admin_data['password']}")
            self.log("\n🔗 ACCESS URLS:")
            self.log("   Development: http://127.0.0.1:8000/admin/")
            self.log("   Production: https://www.youthimpactglobal.com/admin/")
            self.log("\n🎯 SUPER ADMIN DASHBOARD:")
            self.log("   Development: http://127.0.0.1:8000/users/superuser/profile/")
            self.log("   Production: https://www.youthimpactglobal.com/users/superuser/profile/")
        else:
            failed_envs = [env for env, success in results.items() if not success]
            self.log(f"\n⚠️ PARTIAL SUCCESS - Failed environments: {', '.join(failed_envs)}")
        
        return all(results.values())

def main():
    """Main execution function"""
    creator = SuperAdminCreator()
    success = creator.create_admin_on_both_databases()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
