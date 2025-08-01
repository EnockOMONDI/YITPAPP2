"""
Django management command for importing blog posts from Excel files
Usage: python manage.py import_blog_posts <excel_file_path>
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth.models import User
from blogapp.models import Post, Category
from blogapp.resources import PostResource
from blogapp.utils import validate_import_file
import openpyxl
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import blog posts from Excel file'

    def add_arguments(self, parser):
        parser.add_argument(
            'excel_file',
            type=str,
            help='Path to the Excel file containing blog posts'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without actually importing data'
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Skip rows with errors and continue importing'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch (default: 100)'
        )

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        dry_run = options['dry_run']
        skip_errors = options['skip_errors']
        batch_size = options['batch_size']

        # Validate file exists
        if not os.path.exists(excel_file):
            raise CommandError(f'File "{excel_file}" does not exist.')

        # Validate file format
        if not excel_file.lower().endswith(('.xlsx', '.xls')):
            raise CommandError('File must be an Excel file (.xlsx or .xls)')

        self.stdout.write(
            self.style.SUCCESS(f'Starting import from: {excel_file}')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No data will be imported')
            )

        try:
            # Load and validate the Excel file
            workbook = openpyxl.load_workbook(excel_file, read_only=True)
            worksheet = workbook.active

            # Get headers from first row
            headers = [cell.value for cell in worksheet[1]]
            self.stdout.write(f'Found headers: {headers}')

            # Validate required columns
            required_columns = ['title', 'content']
            missing_columns = []
            
            for required_col in required_columns:
                if not any(required_col.lower() in str(header).lower() for header in headers if header):
                    missing_columns.append(required_col)

            if missing_columns:
                raise CommandError(f'Missing required columns: {missing_columns}')

            # Process data rows
            total_rows = worksheet.max_row - 2  # Exclude header and description rows
            processed_count = 0
            success_count = 0
            error_count = 0
            skipped_count = 0

            self.stdout.write(f'Processing {total_rows} rows...')

            # Create progress bar
            progress_interval = max(1, total_rows // 20)  # Update every 5%

            for row_num, row in enumerate(worksheet.iter_rows(min_row=3, values_only=True), 1):
                try:
                    # Create row dictionary
                    row_data = {}
                    for col_num, value in enumerate(row):
                        if col_num < len(headers) and headers[col_num]:
                            row_data[headers[col_num].lower().replace(' ', '_')] = value

                    # Skip empty rows
                    if not row_data.get('title'):
                        skipped_count += 1
                        continue

                    # Process the row
                    if not dry_run:
                        success = self.process_blog_post(row_data, skip_errors)
                        if success:
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        # Dry run - just validate
                        self.validate_blog_post(row_data)
                        success_count += 1

                    processed_count += 1

                    # Show progress
                    if processed_count % progress_interval == 0:
                        percentage = (processed_count / total_rows) * 100
                        self.stdout.write(f'Progress: {percentage:.1f}% ({processed_count}/{total_rows})')

                except Exception as e:
                    error_count += 1
                    if skip_errors:
                        self.stdout.write(
                            self.style.WARNING(f'Row {row_num}: {str(e)} (skipped)')
                        )
                        continue
                    else:
                        raise CommandError(f'Error processing row {row_num}: {str(e)}')

            # Final summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('IMPORT SUMMARY'))
            self.stdout.write('='*50)
            self.stdout.write(f'Total rows processed: {processed_count}')
            self.stdout.write(f'Successfully imported: {success_count}')
            self.stdout.write(f'Errors: {error_count}')
            self.stdout.write(f'Skipped (empty): {skipped_count}')

            if dry_run:
                self.stdout.write(
                    self.style.WARNING('\nDRY RUN COMPLETED - No data was actually imported')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'\nImport completed! {success_count} blog posts imported.')
                )

        except Exception as e:
            raise CommandError(f'Import failed: {str(e)}')

    def process_blog_post(self, row_data, skip_errors=False):
        """Process a single blog post row"""
        try:
            # Get or create category
            category = None
            if row_data.get('category'):
                category, created = Category.objects.get_or_create(
                    title=row_data['category'],
                    defaults={
                        'slug': row_data['category'].lower().replace(' ', '-'),
                        'active': True
                    }
                )
                if created:
                    self.stdout.write(f'Created category: {category.title}')

            # Get user if specified
            user = None
            if row_data.get('user'):
                try:
                    if '@' in str(row_data['user']):
                        user = User.objects.get(email=row_data['user'])
                    else:
                        user = User.objects.get(username=row_data['user'])
                except User.DoesNotExist:
                    if not skip_errors:
                        raise Exception(f"User not found: {row_data['user']}")

            # Create blog post
            post = Post.objects.create(
                title=row_data['title'],
                content=row_data.get('content', ''),
                Author=row_data.get('author', 'YITP Admin'),
                category=category,
                user=user,
                status=row_data.get('status', 'draft').lower(),
                featured=self.parse_boolean(row_data.get('featured', False)),
                trending=self.parse_boolean(row_data.get('trending', False)),
            )

            # Add tags if specified
            if row_data.get('tags'):
                tag_names = [tag.strip() for tag in str(row_data['tags']).split(',')]
                post.tags.add(*tag_names)

            return True

        except Exception as e:
            if skip_errors:
                self.stdout.write(
                    self.style.WARNING(f'Error creating post "{row_data.get("title", "Unknown")}": {str(e)}')
                )
                return False
            else:
                raise

    def validate_blog_post(self, row_data):
        """Validate blog post data without creating it"""
        if not row_data.get('title'):
            raise Exception('Title is required')
        
        if not row_data.get('content'):
            raise Exception('Content is required')
        
        # Validate status
        valid_statuses = ['draft', 'in_review', 'published']
        status = row_data.get('status', 'draft').lower()
        if status not in valid_statuses:
            raise Exception(f'Invalid status: {status}. Must be one of: {valid_statuses}')

    def parse_boolean(self, value):
        """Parse boolean value from Excel"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        
        return bool(value)
