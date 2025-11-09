"""
Mailtrap Email Service for YITP Application
Replaces Gmail SMTP with Mailtrap Transactional API
"""
import os
import logging
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

try:
    from mailtrap import MailtrapClient, Mail, Address
    MAILTRAP_AVAILABLE = True
except ImportError:
    MAILTRAP_AVAILABLE = False
    logger.warning("Mailtrap SDK not installed. Install with: pip install mailtrap")

class MailtrapEmailService:
    """
    Mailtrap email service that replaces Gmail SMTP functionality
    Maintains compatibility with existing email utility functions
    """
    
    def __init__(self):
        """Initialize Mailtrap client with API token"""
        self.api_token = getattr(settings, 'MAILTRAP_API_TOKEN', None)
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@youthimpactglobal.com')
        self.client = None
        
        if not self.api_token:
            logger.error("MAILTRAP_API_TOKEN not found in settings")
            return
            
        if not MAILTRAP_AVAILABLE:
            logger.error("Mailtrap SDK not available")
            return
            
        try:
            self.client = MailtrapClient(token=self.api_token)
            logger.info("✅ Mailtrap client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Mailtrap client: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Mailtrap service is available"""
        return self.client is not None and MAILTRAP_AVAILABLE
    
    def send_email(
        self,
        subject: str,
        html_content: str,
        recipient_list: List[str],
        from_email: Optional[str] = None,
        plain_text_content: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send email via Mailtrap API
        
        Args:
            subject: Email subject
            html_content: HTML email content
            recipient_list: List of recipient email addresses
            from_email: Sender email (optional, uses default)
            plain_text_content: Plain text version (optional, auto-generated from HTML)
            reply_to: Reply-to email address (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.is_available():
            logger.error("Mailtrap service not available")
            return False
            
        if not recipient_list:
            logger.error("No recipients provided")
            return False
            
        try:
            # Use provided from_email or default
            sender_email = from_email or self.from_email

            # Generate plain text if not provided
            if not plain_text_content:
                plain_text_content = strip_tags(html_content)

            # Parse from_email to extract name and email address (following working system pattern)
            if '<' in sender_email and '>' in sender_email:
                from_name = sender_email.split('<')[0].strip()
                from_email_addr = sender_email.split('<')[1].split('>')[0].strip()
            else:
                from_name = "Youth Impact Global"
                from_email_addr = sender_email.strip()

            # Create mail object using proper SDK pattern
            mail = Mail(
                sender=Address(email=from_email_addr, name=from_name),
                to=[Address(email=email.strip()) for email in recipient_list],
                subject=subject,
                html=html_content,
            )

            # Add plain text content if provided
            if plain_text_content:
                mail.text = plain_text_content

            # Send email via Mailtrap HTTP API
            logger.info(f"Sending email via Mailtrap API: subject='{subject}', recipients={recipient_list}")
            response = self.client.send(mail)

            logger.info(f"✅ Email sent successfully via Mailtrap API: {response}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email via Mailtrap API: {str(e)}")
            return False
    
    def send_template_email(
        self,
        template_name: str,
        context: Dict[str, Any],
        subject: str,
        recipient_list: List[str],
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send email using Django template
        
        Args:
            template_name: Template name (without .html extension)
            context: Template context variables
            subject: Email subject
            recipient_list: List of recipient email addresses
            from_email: Sender email (optional)
            reply_to: Reply-to email address (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Render HTML template
            html_template = f"emails/{template_name}.html"
            html_content = render_to_string(html_template, context)
            
            # Try to render plain text template
            plain_text_content = None
            try:
                text_template = f"emails/{template_name}.txt"
                plain_text_content = render_to_string(text_template, context)
            except Exception:
                # Plain text template doesn't exist, will auto-generate
                pass
            
            return self.send_email(
                subject=subject,
                html_content=html_content,
                recipient_list=recipient_list,
                from_email=from_email,
                plain_text_content=plain_text_content,
                reply_to=reply_to
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send template email: {str(e)}")
            return False

# Global instance
mailtrap_service = MailtrapEmailService()

def send_html_email(
    subject: str,
    html_content: str,
    recipient_list: List[str],
    from_email: Optional[str] = None,
    plain_text_content: Optional[str] = None
) -> bool:
    """
    Compatibility function that matches the signature of the original send_html_email
    This allows existing code to work without changes
    """
    return mailtrap_service.send_email(
        subject=subject,
        html_content=html_content,
        recipient_list=recipient_list,
        from_email=from_email,
        plain_text_content=plain_text_content
    )

def send_template_email(
    template_name: str,
    context: Dict[str, Any],
    subject: str,
    recipient_list: List[str],
    from_email: Optional[str] = None
) -> bool:
    """
    Compatibility function for template-based emails
    """
    return mailtrap_service.send_template_email(
        template_name=template_name,
        context=context,
        subject=subject,
        recipient_list=recipient_list,
        from_email=from_email
    )
