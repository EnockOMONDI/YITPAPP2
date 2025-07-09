"""
Django Management Command: Generate Analytics
Automated task to generate and update payment analytics data
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from analytics.services import PaymentAnalyticsService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate and update payment analytics data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to generate analytics for (YYYY-MM-DD format)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to generate analytics for (default: 1)',
        )
        parser.add_argument(
            '--update-user-behavior',
            action='store_true',
            help='Update user payment behavior analytics',
        )
        parser.add_argument(
            '--update-course-revenue',
            action='store_true',
            help='Update course revenue analytics',
        )
        parser.add_argument(
            '--backfill',
            type=int,
            help='Backfill analytics for the last N days',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS('📊 Starting analytics generation...')
        )
        
        try:
            generated_count = 0
            
            # Handle backfill option
            if options['backfill']:
                generated_count = self.backfill_analytics(options['backfill'])
            
            # Handle specific date or date range
            elif options['date']:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
                generated_count = self.generate_for_date_range(target_date, options['days'])
            
            # Default: generate for yesterday
            else:
                yesterday = (timezone.now() - timedelta(days=1)).date()
                generated_count = self.generate_for_date_range(yesterday, options['days'])
            
            # Update user behavior analytics if requested
            user_updates = 0
            if options['update_user_behavior']:
                user_updates = self.update_user_behavior_analytics()
            
            # Update course revenue analytics if requested
            course_updates = 0
            if options['update_course_revenue']:
                course_updates = self.update_course_revenue_analytics()
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Analytics generation completed:\n'
                    f'   • Daily analytics generated: {generated_count}\n'
                    f'   • User behavior updates: {user_updates}\n'
                    f'   • Course revenue updates: {course_updates}'
                )
            )
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {str(e)}")
            raise CommandError(f'Analytics generation failed: {str(e)}')

    def backfill_analytics(self, days):
        """Backfill analytics for the last N days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        if self.verbose:
            self.stdout.write(f'Backfilling analytics from {start_date} to {end_date}')
        
        return self.generate_for_date_range(start_date, days)

    def generate_for_date_range(self, start_date, days):
        """Generate analytics for a date range"""
        generated_count = 0
        
        for i in range(days):
            target_date = start_date + timedelta(days=i)
            
            if self.verbose:
                self.stdout.write(f'  Generating analytics for {target_date}')
            
            try:
                analytics = PaymentAnalyticsService.generate_daily_analytics(target_date)
                generated_count += 1
                
                if self.verbose:
                    self.stdout.write(
                        f'    ✓ {analytics.total_payments} payments, '
                        f'KES {analytics.total_revenue}'
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'    ✗ Failed to generate analytics for {target_date}: {str(e)}')
                )
        
        return generated_count

    def update_user_behavior_analytics(self):
        """Update user payment behavior analytics"""
        if self.verbose:
            self.stdout.write('Updating user payment behavior analytics...')
        
        try:
            updated_count = PaymentAnalyticsService.update_user_behavior_analytics()
            
            if self.verbose:
                self.stdout.write(f'  ✓ Updated behavior analytics for {updated_count} users')
            
            return updated_count
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Failed to update user behavior analytics: {str(e)}')
            )
            return 0

    def update_course_revenue_analytics(self):
        """Update course revenue analytics"""
        if self.verbose:
            self.stdout.write('Updating course revenue analytics...')
        
        try:
            updated_count = PaymentAnalyticsService.update_course_revenue_analytics()
            
            if self.verbose:
                self.stdout.write(f'  ✓ Updated revenue analytics for {updated_count} courses')
            
            return updated_count
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Failed to update course revenue analytics: {str(e)}')
            )
            return 0
