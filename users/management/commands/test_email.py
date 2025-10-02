"""
Django management command to test email configuration
Usage: python manage.py test_email [email_address]
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from users.email_utils import test_email_configuration, send_html_email
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test email configuration and delivery'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to (default: ADMIN_EMAIL)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging',
        )

    def handle(self, *args, **options):
        if options['verbose']:
            logging.basicConfig(level=logging.INFO)
        
        email_address = options.get('email') or settings.ADMIN_EMAIL
        
        self.stdout.write(
            self.style.SUCCESS(f'🧪 Testing email configuration...')
        )
        
        # Display current email settings
        self.stdout.write(f"📧 Email Backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"🏠 Email Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"🔌 Email Port: {settings.EMAIL_PORT}")
        self.stdout.write(f"🔐 Email TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"👤 Email User: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"📨 Default From: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"🎯 Test Email To: {email_address}")
        
        # Test email configuration
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🚀 Sending test email...")
        
        try:
            test_subject = "YITP Email Configuration Test"
            test_html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #EF7722;">🎉 YITP Email Configuration Test</h2>
                    <p>This is a test email to verify that the YITP email configuration is working correctly.</p>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #FAA533; margin-top: 0;">Configuration Details:</h3>
                        <ul>
                            <li><strong>Email Backend:</strong> {settings.EMAIL_BACKEND}</li>
                            <li><strong>Email Host:</strong> {settings.EMAIL_HOST}</li>
                            <li><strong>Email Port:</strong> {settings.EMAIL_PORT}</li>
                            <li><strong>TLS Enabled:</strong> {settings.EMAIL_USE_TLS}</li>
                            <li><strong>From Email:</strong> {settings.DEFAULT_FROM_EMAIL}</li>
                        </ul>
                    </div>
                    
                    <p style="color: #28a745; font-weight: bold;">
                        ✅ If you receive this email, the configuration is working successfully!
                    </p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    
                    <p style="font-size: 12px; color: #666;">
                        This test email was sent from the YITP Django application.<br>
                        Youth Impact Training Programme - Empowering Youth for Global Impact
                    </p>
                </div>
            </body>
            </html>
            """
            
            test_plain_content = f"""
YITP Email Configuration Test

This is a test email to verify that the YITP email configuration is working correctly.

Configuration Details:
- Email Backend: {settings.EMAIL_BACKEND}
- Email Host: {settings.EMAIL_HOST}
- Email Port: {settings.EMAIL_PORT}
- TLS Enabled: {settings.EMAIL_USE_TLS}
- From Email: {settings.DEFAULT_FROM_EMAIL}

✅ If you receive this email, the configuration is working successfully!

---
This test email was sent from the YITP Django application.
Youth Impact Training Programme - Empowering Youth for Global Impact
            """
            
            result = send_html_email(
                subject=test_subject,
                html_content=test_html_content,
                recipient_list=[email_address],
                plain_text_content=test_plain_content
            )
            
            if result:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Test email sent successfully to {email_address}!')
                )
                self.stdout.write(
                    self.style.SUCCESS('📬 Please check the recipient\'s inbox (and spam folder) for the test email.')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to send test email to {email_address}')
                )
                self.stdout.write(
                    self.style.WARNING('💡 Check the Django logs for detailed error information.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Email test failed with exception: {str(e)}')
            )
            
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🏁 Email test completed.")
        
        # Additional troubleshooting tips
        self.stdout.write("\n📋 Troubleshooting Tips:")
        self.stdout.write("1. Verify Gmail app password is correct")
        self.stdout.write("2. Check that 2-factor authentication is enabled on Gmail")
        self.stdout.write("3. Ensure EMAIL_HOST_PASSWORD environment variable is set")
        self.stdout.write("4. Check recipient's spam/junk folder")
        self.stdout.write("5. Verify sender email is not blacklisted")
