#!/usr/bin/env python
"""
Trial System Data Migration Script for YITP
Handles data cleanup and migration for the new trial system
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from users.models import Profile
from progress.models import Enrollment
from courses.models import Course
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TrialSystemDataMigration:
    """
    Data migration utilities for trial system implementation
    """
    
    def __init__(self):
        self.stats = {
            'profiles_updated': 0,
            'enrollments_updated': 0,
            'errors': 0
        }
    
    @transaction.atomic
    def migrate_existing_profiles(self):
        """
        Ensure all existing profiles have proper trial status defaults
        """
        logger.info("Starting profile migration for trial system...")
        
        try:
            profiles = Profile.objects.all()
            
            for profile in profiles:
                updated = False
                
                # Ensure trial status is set to 'none' for existing users
                if not hasattr(profile, 'trial_status') or profile.trial_status is None:
                    profile.trial_status = 'none'
                    updated = True
                
                # Ensure trial fields have proper defaults
                if not hasattr(profile, 'trial_lessons_accessed') or profile.trial_lessons_accessed is None:
                    profile.trial_lessons_accessed = []
                    updated = True
                
                if not hasattr(profile, 'trial_quizzes_taken') or profile.trial_quizzes_taken is None:
                    profile.trial_quizzes_taken = []
                    updated = True
                
                if updated:
                    profile.save(update_fields=[
                        'trial_status', 'trial_lessons_accessed', 'trial_quizzes_taken'
                    ])
                    self.stats['profiles_updated'] += 1
            
            logger.info(f"Profile migration completed. Updated {self.stats['profiles_updated']} profiles.")
            
        except Exception as e:
            logger.error(f"Error during profile migration: {str(e)}")
            self.stats['errors'] += 1
            raise
    
    @transaction.atomic
    def migrate_existing_enrollments(self):
        """
        Ensure all existing enrollments have proper enrollment type
        """
        logger.info("Starting enrollment migration for trial system...")
        
        try:
            enrollments = Enrollment.objects.all()
            
            for enrollment in enrollments:
                updated = False
                
                # Set enrollment type to 'paid' for existing enrollments
                if not hasattr(enrollment, 'enrollment_type') or enrollment.enrollment_type is None:
                    enrollment.enrollment_type = 'paid'
                    updated = True
                
                # Ensure trial boundaries field exists
                if not hasattr(enrollment, 'trial_boundaries') or enrollment.trial_boundaries is None:
                    enrollment.trial_boundaries = {}
                    updated = True
                
                if updated:
                    enrollment.save(update_fields=['enrollment_type', 'trial_boundaries'])
                    self.stats['enrollments_updated'] += 1
            
            logger.info(f"Enrollment migration completed. Updated {self.stats['enrollments_updated']} enrollments.")
            
        except Exception as e:
            logger.error(f"Error during enrollment migration: {str(e)}")
            self.stats['errors'] += 1
            raise
    
    def validate_trial_system_integrity(self):
        """
        Validate trial system data integrity
        """
        logger.info("Validating trial system data integrity...")
        
        issues = []
        
        # Check for profiles with invalid trial status
        invalid_trial_profiles = Profile.objects.exclude(
            trial_status__in=['none', 'active', 'expired', 'converted']
        )
        if invalid_trial_profiles.exists():
            issues.append(f"Found {invalid_trial_profiles.count()} profiles with invalid trial status")
        
        # Check for trial enrollments without proper boundaries
        trial_enrollments = Enrollment.objects.filter(enrollment_type='trial')
        for enrollment in trial_enrollments:
            if not enrollment.trial_boundaries:
                issues.append(f"Trial enrollment {enrollment.id} missing trial boundaries")
        
        # Check for active trial users without trial course
        active_trial_profiles = Profile.objects.filter(trial_status='active', trial_course__isnull=True)
        if active_trial_profiles.exists():
            issues.append(f"Found {active_trial_profiles.count()} active trial profiles without trial course")
        
        if issues:
            logger.warning("Data integrity issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("No data integrity issues found.")
        
        return issues
    
    def cleanup_orphaned_trial_data(self):
        """
        Clean up orphaned trial data
        """
        logger.info("Cleaning up orphaned trial data...")
        
        try:
            # Reset trial status for users with deleted trial courses
            orphaned_profiles = Profile.objects.filter(
                trial_status__in=['active', 'expired'],
                trial_course__isnull=True
            )
            
            if orphaned_profiles.exists():
                logger.info(f"Resetting {orphaned_profiles.count()} orphaned trial profiles")
                orphaned_profiles.update(
                    trial_status='none',
                    trial_started_at=None,
                    trial_lessons_accessed=[],
                    trial_quizzes_taken=[],
                    trial_conversion_prompted_at=None
                )
            
            # Clean up trial enrollments for non-existent courses
            orphaned_enrollments = Enrollment.objects.filter(
                enrollment_type='trial',
                course__isnull=True
            )
            
            if orphaned_enrollments.exists():
                logger.info(f"Deleting {orphaned_enrollments.count()} orphaned trial enrollments")
                orphaned_enrollments.delete()
            
            logger.info("Orphaned data cleanup completed.")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            self.stats['errors'] += 1
            raise
    
    def generate_migration_report(self):
        """
        Generate migration report
        """
        logger.info("=== TRIAL SYSTEM MIGRATION REPORT ===")
        logger.info(f"Profiles updated: {self.stats['profiles_updated']}")
        logger.info(f"Enrollments updated: {self.stats['enrollments_updated']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        
        # Current system stats
        total_profiles = Profile.objects.count()
        active_trials = Profile.objects.filter(trial_status='active').count()
        trial_enrollments = Enrollment.objects.filter(enrollment_type='trial').count()
        
        logger.info(f"Total profiles: {total_profiles}")
        logger.info(f"Active trials: {active_trials}")
        logger.info(f"Trial enrollments: {trial_enrollments}")
        logger.info("=== END MIGRATION REPORT ===")
    
    def run_full_migration(self):
        """
        Run complete migration process
        """
        logger.info("Starting full trial system data migration...")
        
        try:
            # Step 1: Migrate profiles
            self.migrate_existing_profiles()
            
            # Step 2: Migrate enrollments
            self.migrate_existing_enrollments()
            
            # Step 3: Validate integrity
            issues = self.validate_trial_system_integrity()
            
            # Step 4: Cleanup orphaned data
            self.cleanup_orphaned_trial_data()
            
            # Step 5: Generate report
            self.generate_migration_report()
            
            if self.stats['errors'] == 0:
                logger.info("✅ Trial system migration completed successfully!")
            else:
                logger.warning(f"⚠️ Migration completed with {self.stats['errors']} errors")
            
            return self.stats['errors'] == 0
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            return False


def main():
    """
    Main migration function
    """
    print("YITP Trial System Data Migration")
    print("=" * 40)
    
    migration = TrialSystemDataMigration()
    
    try:
        success = migration.run_full_migration()
        
        if success:
            print("\n✅ Migration completed successfully!")
            return 0
        else:
            print("\n❌ Migration completed with errors!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Migration interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
