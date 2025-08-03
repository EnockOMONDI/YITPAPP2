"""
Magic Link Authentication Utilities for YITP
Secure token-based authentication for instructor welcome emails
"""

import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

def generate_magic_link_token(user, purpose='instructor_welcome', expiry_days=10):
    """
    Generate a secure magic link token for a user

    Args:
        user: User instance
        purpose: Purpose of the token (default: 'instructor_welcome')
        expiry_days: Number of days until token expires (default: 10)

    Returns:
        MagicLinkToken instance
    """
    # Import here to avoid circular imports
    from .models import MagicLinkToken
    # Generate a secure random token
    raw_token = secrets.token_urlsafe(32)
    
    # Create a signed token using Django's signing framework
    signer = TimestampSigner()
    signed_token = signer.sign(f"{user.id}:{raw_token}:{purpose}")
    
    # Create hash for database storage (for security)
    token_hash = hashlib.sha256(signed_token.encode()).hexdigest()
    
    # Calculate expiry date
    expires_at = timezone.now() + timedelta(days=expiry_days)
    
    # Clean up old unused tokens for this user and purpose
    MagicLinkToken.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False
    ).delete()
    
    # Create new token
    magic_token = MagicLinkToken.objects.create(
        user=user,
        token=signed_token,
        token_hash=token_hash,
        expires_at=expires_at,
        purpose=purpose
    )
    
    logger.info(f"Generated magic link token for user {user.username} with purpose {purpose}")
    return magic_token

def generate_magic_link_url(user, purpose='instructor_welcome', expiry_days=10):
    """
    Generate a complete magic link URL for a user
    
    Args:
        user: User instance
        purpose: Purpose of the token
        expiry_days: Number of days until token expires
    
    Returns:
        tuple: (magic_link_url, token_instance)
    """
    # Generate the token
    magic_token = generate_magic_link_token(user, purpose, expiry_days)
    
    # Build the magic link URL
    base_url = getattr(settings, 'SITE_URL', 'https://yitp-lms.onrender.com')
    magic_link_path = reverse('users:magic_login', kwargs={'token': magic_token.token})
    magic_link_url = f"{base_url}{magic_link_path}"
    
    logger.info(f"Generated magic link URL for user {user.username}: {magic_link_url}")
    return magic_link_url, magic_token

def validate_magic_link_token(token_string):
    """
    Validate a magic link token

    Args:
        token_string: The token string from the URL

    Returns:
        tuple: (is_valid, user_or_error_message, token_instance_or_none)
    """
    # Import here to avoid circular imports
    from .models import MagicLinkToken

    try:
        # Find the token in database
        try:
            magic_token = MagicLinkToken.objects.get(token=token_string)
        except MagicLinkToken.DoesNotExist:
            logger.warning(f"Magic link token not found: {token_string[:20]}...")
            return False, "Invalid or expired magic link", None
        
        # Check if token is already used
        if magic_token.is_used:
            logger.warning(f"Magic link token already used: {magic_token.user.username}")
            return False, "This magic link has already been used", magic_token
        
        # Check if token is expired
        if magic_token.is_expired():
            logger.warning(f"Magic link token expired: {magic_token.user.username}")
            return False, "This magic link has expired", magic_token
        
        # Validate the signed token
        signer = TimestampSigner()
        try:
            # Extract the original data from the signed token
            unsigned_data = signer.unsign(token_string, max_age=timedelta(days=10))
            user_id, raw_token, purpose = unsigned_data.split(':')
            
            # Verify the user ID matches
            if int(user_id) != magic_token.user.id:
                logger.error(f"User ID mismatch in magic link token")
                return False, "Invalid magic link", magic_token
            
        except (BadSignature, SignatureExpired, ValueError) as e:
            logger.error(f"Magic link token signature validation failed: {str(e)}")
            return False, "Invalid or expired magic link", magic_token
        
        # All validations passed
        logger.info(f"Magic link token validated successfully for user {magic_token.user.username}")
        return True, magic_token.user, magic_token
        
    except Exception as e:
        logger.error(f"Error validating magic link token: {str(e)}")
        return False, "An error occurred while validating the magic link", None

def authenticate_user_with_magic_link(request, token_string):
    """
    Authenticate and log in a user using a magic link token
    
    Args:
        request: Django request object
        token_string: The magic link token
    
    Returns:
        tuple: (success, message, user_or_none)
    """
    # Validate the token
    is_valid, user_or_error, magic_token = validate_magic_link_token(token_string)
    
    if not is_valid:
        return False, user_or_error, None
    
    user = user_or_error
    
    try:
        # Get client information
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Mark token as used
        magic_token.mark_as_used(ip_address=ip_address, user_agent=user_agent)
        
        # Log the user in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        logger.info(f"User {user.username} successfully authenticated via magic link")
        
        # Send login notification
        try:
            from users.email_utils import send_login_notification
            send_login_notification(user, ip_address, user_agent)
        except Exception as e:
            logger.error(f"Failed to send login notification: {str(e)}")
        
        return True, "Successfully logged in via magic link", user
        
    except Exception as e:
        logger.error(f"Error during magic link authentication: {str(e)}")
        return False, "An error occurred during authentication", None

def cleanup_expired_tokens():
    """
    Clean up expired magic link tokens
    This should be run periodically (e.g., via a cron job or management command)
    """
    # Import here to avoid circular imports
    from .models import MagicLinkToken

    expired_count = MagicLinkToken.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()[0]
    
    logger.info(f"Cleaned up {expired_count} expired magic link tokens")
    return expired_count

def get_user_magic_tokens(user, purpose=None):
    """
    Get all magic link tokens for a user

    Args:
        user: User instance
        purpose: Optional purpose filter

    Returns:
        QuerySet of MagicLinkToken instances
    """
    # Import here to avoid circular imports
    from .models import MagicLinkToken

    queryset = MagicLinkToken.objects.filter(user=user)
    if purpose:
        queryset = queryset.filter(purpose=purpose)
    return queryset.order_by('-created_at')
