"""
Custom email backend for YITP that handles SSL certificate issues
"""
import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class YITPEmailBackend(EmailBackend):
    """
    Custom email backend that handles SSL certificate verification issues
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure local_hostname is set
        if not hasattr(self, 'local_hostname') or self.local_hostname is None:
            self.local_hostname = None

    def open(self):
        """
        Ensure we have a connection to the email server. Return whether or not a
        new connection was required (True or False).
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False

        # If local_hostname is not specified, socket.getfqdn() gets used.
        # For performance, we use the cached FQDN for local_hostname.
        connection_params = {'local_hostname': self.local_hostname}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        if self.use_ssl:
            connection_params['keyfile'] = self.ssl_keyfile
            connection_params['certfile'] = self.ssl_certfile
            
        try:
            self.connection = self.connection_class(self.host, self.port, **connection_params)
            
            # TLS/STARTTLS are mutually exclusive, so only attempt TLS over
            # a non-secure connection.
            if not self.use_ssl and self.use_tls:
                # Create unverified SSL context for development/testing
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                self.connection.starttls(context=context)
                
            if self.username and self.password:
                self.connection.login(self.username, self.password)
                
            logger.info("✅ Successfully connected to email server")
            return True
            
        except (smtplib.SMTPException, OSError) as e:
            if not self.fail_silently:
                logger.error(f"❌ Email connection failed: {str(e)}")
                raise
            logger.warning(f"⚠️ Email connection failed silently: {str(e)}")
            return False
