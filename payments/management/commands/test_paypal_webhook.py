"""
Management command to test PayPal webhook endpoint configuration
"""

import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test PayPal webhook endpoint configuration and accessibility'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default=None,
            help='Custom webhook URL to test (defaults to configured PAYPAL_WEBHOOK_URL)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Testing PayPal Webhook Configuration...\n')
        )

        # Get webhook URL
        webhook_url = options.get('url') or getattr(settings, 'PAYPAL_WEBHOOK_URL', None)
        
        if not webhook_url:
            self.stdout.write(
                self.style.ERROR('❌ No webhook URL configured. Please set PAYPAL_WEBHOOK_URL in settings.')
            )
            return

        self.stdout.write(f'📍 Testing webhook URL: {webhook_url}')
        
        # Test basic connectivity
        self.test_webhook_connectivity(webhook_url, options['verbose'])
        
        # Display configuration summary
        self.display_configuration_summary()

    def test_webhook_connectivity(self, webhook_url, verbose=False):
        """Test if webhook endpoint is accessible"""
        
        try:
            # Test with a simple GET request (should return 405 Method Not Allowed)
            response = requests.get(webhook_url, timeout=10)
            
            if response.status_code == 405:
                self.stdout.write(
                    self.style.SUCCESS('✅ Webhook endpoint is accessible (405 Method Not Allowed expected for GET)')
                )
            elif response.status_code == 200:
                self.stdout.write(
                    self.style.WARNING('⚠️ Webhook endpoint returned 200 for GET (unexpected but accessible)')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Webhook endpoint returned {response.status_code}')
                )
                
            if verbose:
                self.stdout.write(f'Response headers: {dict(response.headers)}')
                
        except requests.exceptions.ConnectionError:
            self.stdout.write(
                self.style.ERROR('❌ Cannot connect to webhook endpoint - check URL and server status')
            )
        except requests.exceptions.Timeout:
            self.stdout.write(
                self.style.ERROR('❌ Webhook endpoint timeout - server may be slow or unresponsive')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing webhook: {str(e)}')
            )

    def display_configuration_summary(self):
        """Display current PayPal webhook configuration"""
        
        self.stdout.write('\n📋 Current PayPal Configuration:')
        self.stdout.write('-' * 50)
        
        config_items = [
            ('Site URL', getattr(settings, 'SITE_URL', 'Not configured')),
            ('PayPal Mode', getattr(settings, 'PAYPAL_MODE', 'Not configured')),
            ('PayPal Client ID', getattr(settings, 'PAYPAL_CLIENT_ID', 'Not configured')[:20] + '...' if getattr(settings, 'PAYPAL_CLIENT_ID', None) else 'Not configured'),
            ('PayPal Webhook URL', getattr(settings, 'PAYPAL_WEBHOOK_URL', 'Not configured')),
            ('PayPal Webhook ID', getattr(settings, 'PAYPAL_WEBHOOK_ID', 'Not configured')),
        ]
        
        for key, value in config_items:
            status_icon = '✅' if value != 'Not configured' else '❌'
            self.stdout.write(f'{status_icon} {key}: {value}')
        
        self.stdout.write('\n🔗 PayPal Developer Dashboard:')
        self.stdout.write('   https://developer.paypal.com/developer/applications/')
        
        self.stdout.write('\n📚 Configuration Guide:')
        self.stdout.write('   docs/PAYPAL_WEBHOOK_CONFIGURATION.md')
        
        self.stdout.write('\n✨ Test completed!')
