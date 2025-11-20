"""
Certificate Generation Service for YITP
Generates PDF certificates for course completion with verification
"""

from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.utils import timezone

import logging
import uuid
import os
from io import BytesIO

# PDF generation imports
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib.colors import Color, black, blue
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from progress.models import Certificate, Enrollment

logger = logging.getLogger(__name__)


class CertificateService:
    """
    Service for generating and managing course completion certificates
    """
    
    @staticmethod
    def generate_certificate(enrollment):
        """
        Generate a PDF certificate for course completion
        
        Args:
            enrollment: Enrollment object for completed course
            
        Returns:
            dict: {
                'success': bool,
                'certificate': Certificate object or None,
                'message': str,
                'file_path': str or None
            }
        """
        try:
            # Validate enrollment completion
            if not enrollment.is_completed:
                return {
                    'success': False,
                    'certificate': None,
                    'message': 'Course not completed yet',
                    'file_path': None
                }
            
            # Check if certificate already exists
            existing_certificate = Certificate.objects.filter(enrollment=enrollment).first()
            if existing_certificate:
                existing_path = ''
                if existing_certificate.certificate_data:
                    existing_path = existing_certificate.certificate_data.get('file_path', '')
                return {
                    'success': True,
                    'certificate': existing_certificate,
                    'message': 'Certificate already exists',
                    'file_path': existing_path
                }
            
            # Generate certificate
            if REPORTLAB_AVAILABLE:
                pdf_result = CertificateService._generate_pdf_certificate(enrollment)
            else:
                # Fallback to HTML certificate
                pdf_result = CertificateService._generate_html_certificate(enrollment)
            
            if pdf_result['success']:
                # Create certificate record
                certificate = Certificate.objects.create(
                    enrollment=enrollment,
                    certificate_id=CertificateService._generate_certificate_id(),
                    verification_code=CertificateService._generate_verification_code(),
                    issued_date=timezone.now(),
                    final_score=enrollment.progress_percentage,
                    certificate_data={'file_path': pdf_result.get('file_path', '')}
                )
                
                logger.info(f"Certificate generated: {certificate.certificate_id} for {enrollment.student.email}")
                
                return {
                    'success': True,
                    'certificate': certificate,
                    'message': 'Certificate generated successfully',
                    'file_path': pdf_result.get('file_path', '')
                }
            else:
                return pdf_result
                
        except Exception as e:
            logger.error(f"Certificate generation failed: {str(e)}")
            return {
                'success': False,
                'certificate': None,
                'message': f'Certificate generation failed: {str(e)}',
                'file_path': None
            }

    @staticmethod
    def _generate_certificate_id():
        """Generate unique certificate ID"""
        return f"YITP-CERT-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    @staticmethod
    def _generate_verification_code():
        """Generate verification code for certificate"""
        return str(uuid.uuid4()).replace('-', '').upper()[:12]

    @staticmethod
    def _generate_pdf_certificate(enrollment):
        """Generate PDF certificate using ReportLab"""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=Color(0.1, 0.2, 0.5)  # YITP blue
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=18,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=Color(1.0, 0.36, 0.08)  # YITP orange
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=12,
                alignment=TA_CENTER
            )
            
            # Certificate content
            story.append(Spacer(1, 50))
            
            # YITP Logo (if available)
            logo_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'images', 'yitp-logo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=100, height=50)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 20))
            
            # Certificate title
            story.append(Paragraph("CERTIFICATE OF COMPLETION", title_style))
            story.append(Spacer(1, 30))
            
            # Subtitle
            story.append(Paragraph("Youth Impact Training Programme", subtitle_style))
            story.append(Spacer(1, 40))
            
            # Main content
            story.append(Paragraph("This is to certify that", body_style))
            story.append(Spacer(1, 20))
            
            # Student name
            name_style = ParagraphStyle(
                'StudentName',
                parent=styles['Heading2'],
                fontSize=20,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=black
            )
            student_name = f"{enrollment.student.first_name} {enrollment.student.last_name}".strip()
            if not student_name:
                student_name = enrollment.student.username
            story.append(Paragraph(f"<b>{student_name}</b>", name_style))
            story.append(Spacer(1, 30))
            
            # Course completion text
            story.append(Paragraph("has successfully completed the course", body_style))
            story.append(Spacer(1, 20))
            
            # Course title
            course_style = ParagraphStyle(
                'CourseTitle',
                parent=styles['Heading3'],
                fontSize=16,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=Color(0.1, 0.2, 0.5)
            )
            story.append(Paragraph(f"<b>{enrollment.course.title}</b>", course_style))
            story.append(Spacer(1, 30))
            
            # Completion details
            completion_date = enrollment.completion_date or timezone.now()
            story.append(Paragraph(f"Completed on: {completion_date.strftime('%B %d, %Y')}", body_style))
            story.append(Paragraph(f"Course Duration: {enrollment.course.estimated_duration} hours", body_style))
            story.append(Paragraph(f"Final Score: {enrollment.progress_percentage:.1f}%", body_style))
            story.append(Spacer(1, 40))
            
            # Signature section
            signature_style = ParagraphStyle(
                'Signature',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph("_________________________", signature_style))
            story.append(Paragraph("YITP Program Director", signature_style))
            story.append(Spacer(1, 20))
            
            # Certificate details
            cert_id = CertificateService._generate_certificate_id()
            verification_code = CertificateService._generate_verification_code()
            
            details_style = ParagraphStyle(
                'Details',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_LEFT,
                textColor=Color(0.5, 0.5, 0.5)
            )
            
            story.append(Paragraph(f"Certificate ID: {cert_id}", details_style))
            story.append(Paragraph(f"Verification Code: {verification_code}", details_style))
            
            # Verification URL
            verification_url = f"{settings.SITE_URL}/certificates/verify/{verification_code}/"
            story.append(Paragraph(f"Verify at: {verification_url}", details_style))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            # Create file
            filename = f"certificate_{enrollment.student.username}_{enrollment.course.slug}.pdf"
            file_content = ContentFile(buffer.getvalue(), name=filename)
            
            return {
                'success': True,
                'file': file_content,
                'message': 'PDF certificate generated successfully'
            }
            
        except Exception as e:
            logger.error(f"PDF certificate generation failed: {str(e)}")
            return {
                'success': False,
                'file': None,
                'message': f'PDF generation failed: {str(e)}'
            }

    @staticmethod
    def _generate_html_certificate(enrollment):
        """Generate HTML certificate as fallback"""
        try:
            # Generate certificate data
            cert_data = {
                'student_name': f"{enrollment.student.first_name} {enrollment.student.last_name}".strip() or enrollment.student.username,
                'course_title': enrollment.course.title,
                'completion_date': enrollment.completion_date or timezone.now(),
                'duration': enrollment.course.estimated_duration,
                'score': enrollment.progress_percentage,
                'certificate_id': CertificateService._generate_certificate_id(),
                'verification_code': CertificateService._generate_verification_code(),
                'issue_date': timezone.now(),
                'verification_url': f"{settings.SITE_URL}/certificates/verify/VERIFICATION_CODE/"
            }
            
            # Render HTML template
            html_content = render_to_string('certificates/certificate_template.html', cert_data)
            
            # Save as HTML file (could be converted to PDF using wkhtmltopdf)
            filename = f"certificate_{enrollment.student.username}_{enrollment.course.slug}.html"
            file_content = ContentFile(html_content.encode('utf-8'), name=filename)
            
            return {
                'success': True,
                'file': file_content,
                'message': 'HTML certificate generated successfully'
            }
            
        except Exception as e:
            logger.error(f"HTML certificate generation failed: {str(e)}")
            return {
                'success': False,
                'file': None,
                'message': f'HTML generation failed: {str(e)}'
            }

    @staticmethod
    def verify_certificate(verification_code):
        """
        Verify certificate authenticity
        
        Args:
            verification_code: Certificate verification code
            
        Returns:
            dict: {
                'valid': bool,
                'certificate': Certificate or None,
                'message': str
            }
        """
        try:
            certificate = Certificate.objects.get(verification_code=verification_code)
            
            return {
                'valid': True,
                'certificate': certificate,
                'message': 'Certificate is valid and authentic'
            }
            
        except Certificate.DoesNotExist:
            return {
                'valid': False,
                'certificate': None,
                'message': 'Invalid verification code'
            }
        except Exception as e:
            logger.error(f"Certificate verification failed: {str(e)}")
            return {
                'valid': False,
                'certificate': None,
                'message': f'Verification failed: {str(e)}'
            }

    @staticmethod
    def get_user_certificates(user):
        """Get all certificates for a user"""
        return Certificate.objects.filter(
            enrollment__student=user
        ).select_related('enrollment__course').order_by('-issued_date')
