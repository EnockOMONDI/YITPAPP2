"""
Comprehensive Unit Tests for Core Error Handling
Tests error handling, logging, and user feedback mechanisms
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest
from unittest.mock import patch, MagicMock

from core.error_handling import (
    ErrorHandler, YITPError, EnrollmentError,
    PaymentError, CertificateError
)

User = get_user_model()


class ErrorHandlerTestCase(TestCase):
    """Test ErrorHandler functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='erroruser',
            email='error@example.com',
            password='testpass123'
        )

    def test_handle_enrollment_error_limit_reached(self):
        """Test enrollment error handling for limit reached"""
        request = self.factory.get('/')
        request.user = self.user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        error = EnrollmentError(
            "Enrollment limit reached",
            error_code='E001'
        )
        
        response = ErrorHandler.handle_enrollment_error(error, request)
        
        # Should handle gracefully
        self.assertIsNotNone(response)

    def test_yitp_error_custom_message(self):
        """Test YITPError with custom user message"""
        error = YITPError(
            message="Internal error message",
            error_code="TEST001",
            user_message="User-friendly message"
        )
        
        self.assertEqual(error.user_message, "User-friendly message")
        self.assertEqual(error.error_code, "TEST001")
