"""
Comprehensive Unit Tests for Certificate Service
Tests PDF generation, verification codes, and certificate management
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock
import uuid

from certificates.certificate_service import CertificateService
from progress.models import Certificate, Enrollment
from courses.models import Course, Module, Lesson, Category

User = get_user_model()


class CertificateServiceTestCase(TestCase):
    """Test CertificateService functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='certuser',
            email='cert@example.com',
            password='testpass123'
        )
        
        category = Category.objects.create(name='Cert Cat', slug='cert-cat')
        self.course = Course.objects.create(
            title='Certificate Course',
            slug='cert-course',
            description='Description',
            price=Decimal('5000.00'),
            category=category,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            student=self.user,
            course=self.course,
            status='active',
            progress_percentage=100,
            is_completed=True,
            completed_at=timezone.now()
        )

    def test_generate_certificate_success(self):
        """Test successful certificate generation"""
        with patch('certificates.certificate_service.REPORTLAB_AVAILABLE', True):
            with patch.object(CertificateService, '_generate_pdf_certificate') as mock_pdf:
                mock_pdf.return_value = {
                    'success': True,
                    'file_path': '/path/to/cert.pdf'
                }
                
                result = CertificateService.generate_certificate(self.enrollment)
                
                self.assertTrue(result['success'])
                self.assertIsNotNone(result['certificate'])
                self.assertIsInstance(result['certificate'], Certificate)

    def test_generate_certificate_not_completed(self):
        """Test certificate generation for incomplete course"""
        self.enrollment.is_completed = False
        self.enrollment.save()
        
        result = CertificateService.generate_certificate(self.enrollment)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'Course not completed yet')

    def test_generate_certificate_already_exists(self):
        """Test certificate generation when already exists"""
        existing_cert = Certificate.objects.create(
            enrollment=self.enrollment,
            certificate_id='CERT123',
            verification_code='VERIFY123',
            issued_date=timezone.now(),
            final_score=95.0
        )
        
        result = CertificateService.generate_certificate(self.enrollment)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['certificate'].id, existing_cert.id)
        self.assertEqual(result['message'], 'Certificate already exists')

    def test_generate_certificate_id_unique(self):
        """Test that certificate IDs are unique"""
        cert_ids = set()
        for _ in range(10):
            cert_id = CertificateService._generate_certificate_id()
            self.assertNotIn(cert_id, cert_ids)
            cert_ids.add(cert_id)

    def test_generate_verification_code_unique(self):
        """Test that verification codes are unique"""
        codes = set()
        for _ in range(10):
            code = CertificateService._generate_verification_code()
            self.assertNotIn(code, codes)
            codes.add(code)

    def test_verify_certificate_valid(self):
        """Test certificate verification with valid code"""
        cert = Certificate.objects.create(
            enrollment=self.enrollment,
            certificate_id='CERT123',
            verification_code='VERIFY123',
            issued_date=timezone.now(),
            final_score=95.0
        )
        
        result = CertificateService.verify_certificate('VERIFY123')
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['certificate'].id, cert.id)

    def test_verify_certificate_invalid(self):
        """Test certificate verification with invalid code"""
        result = CertificateService.verify_certificate('INVALID')
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['message'], 'Certificate not found')

    @patch('certificates.certificate_service.REPORTLAB_AVAILABLE', False)
    def test_fallback_to_html_certificate(self):
        """Test fallback to HTML when PDF not available"""
        with patch.object(CertificateService, '_generate_html_certificate') as mock_html:
            mock_html.return_value = {
                'success': True,
                'file_path': '/path/to/cert.html'
            }
            
            result = CertificateService.generate_certificate(self.enrollment)
            
            mock_html.assert_called_once()
