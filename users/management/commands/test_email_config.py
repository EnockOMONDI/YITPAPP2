"""
Django management command to test email configuration
Usage: python manage.py test_email_config [--send-test-email email@example.com]
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from users.email_utils import test_email_configuration, send_html_email
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test email configuration and optionally send a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--send-test-email',
            type=str,
            help='Send a test email to the specified address'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        test_email = options.get('send_test_email')

        self.stdout.write(
            self.style.SUCCESS('🔍 YITP Email Configuration Test')
        )
        self.stdout.write('=' * 50)

        # Test email configuration
        config_result = test_email_configuration()
        
        if config_result['success']:
            self.stdout.write(
                self.style.SUCCESS('✅ Email configuration test PASSED')
            )
            if verbose:
                self.stdout.write('Configuration details:')
                for key, value in config_result['config'].items():
                    self.stdout.write(f'  {key}: {value}')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Email configuration test FAILED')
            )
            self.stdout.write(f'Error: {config_result["message"]}')
            if verbose and config_result.get('config'):
                self.stdout.write('Configuration details:')
                for key, value in config_result['config'].items():
                    self.stdout.write(f'  {key}: {value}')

        # Send test email if requested
        if test_email:
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(f'📧 Sending test email to {test_email}...')
            
            subject = 'YITP Email Configuration Test'
            html_content = '''
            <html>
            <body>
                <h2 style="color: #FAA533;">🎓 YITP Email Test</h2>
                <p>This is a test email from the Youth Impact Training Programme system.</p>
                <p><strong>Email configuration is working correctly!</strong></p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This email was sent from the YITP production system to verify email functionality.
                </p>
            </body>
            </html>
            '''
            
            try:
                success = send_html_email(
                    subject=subject,
                    html_content=html_content,
                    recipient_list=[test_email]
                )
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Test email sent successfully to {test_email}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Failed to send test email to {test_email}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Exception sending test email: {str(e)}')
                )

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 SUMMARY')
        self.stdout.write('=' * 50)
        
        if config_result['success']:
            self.stdout.write(
                self.style.SUCCESS('✅ Email system is properly configured')
            )
            if test_email:
                self.stdout.write('✅ Test email functionality verified')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Email system needs attention')
            )
            self.stdout.write('🔧 Recommended actions:')
            self.stdout.write('   1. Check EMAIL_HOST setting (should be smtp.gmail.com)')
            self.stdout.write('   2. Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD')
            self.stdout.write('   3. Ensure Gmail app password is correct')
            self.stdout.write('   4. Check network connectivity to Gmail SMTP')

        self.stdout.write('\n🌐 Production URLs:')
        self.stdout.write('   • Admin: https://www.youthimpactglobal.com/admin/')
        self.stdout.write('   • Test command: python manage.py test_email_config --send-test-email your@email.com')
        self.stdout.write('=' * 50)
