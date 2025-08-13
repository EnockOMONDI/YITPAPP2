"""
PayPal Payment Service for YITP
Handles PayPal payment creation, execution, and webhook verification
"""

import base64
import json
import logging
import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


class PayPalService:
    """
    PayPal payment processing service using PayPal REST API
    """
    
    @staticmethod
    def get_access_token():
        """
        Get PayPal access token for API authentication
        
        Returns:
            dict: {'success': bool, 'access_token': str, 'message': str}
        """
        try:
            # Prepare authentication
            auth_string = f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = 'grant_type=client_credentials'
            
            response = requests.post(
                settings.PAYPAL_TOKEN_URL,
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return {
                    'success': True,
                    'access_token': token_data['access_token'],
                    'message': 'Access token obtained successfully'
                }
            else:
                logger.error(f"PayPal token request failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'access_token': None,
                    'message': f'Token request failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"PayPal token generation error: {str(e)}")
            return {
                'success': False,
                'access_token': None,
                'message': f'Token generation failed: {str(e)}'
            }
    
    @staticmethod
    def format_usd_amount(usd_amount):
        """
        Format USD amount for PayPal processing

        Args:
            usd_amount (Decimal): Amount in USD

        Returns:
            str: Amount in USD formatted to 2 decimal places
        """
        return f"{float(usd_amount):.2f}"
    
    @staticmethod
    def create_payment_order(payment_obj):
        """
        Create PayPal payment order
        
        Args:
            payment_obj: Payment model instance
            
        Returns:
            dict: {'success': bool, 'order_id': str, 'approval_url': str, 'message': str}
        """
        try:
            # Get access token
            token_response = PayPalService.get_access_token()
            if not token_response['success']:
                return token_response
            
            access_token = token_response['access_token']
            
            # Format USD amount (no conversion needed - prices already in USD)
            usd_amount = PayPalService.format_usd_amount(payment_obj.amount)
            
            # Prepare order data
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": payment_obj.reference_number,
                    "amount": {
                        "currency_code": "USD",
                        "value": usd_amount
                    },
                    "description": f"YITP Course: {payment_obj.course.title}",
                    "custom_id": payment_obj.reference_number,
                    "invoice_id": payment_obj.reference_number
                }],
                "application_context": {
                    "brand_name": settings.PAYPAL_BRAND_NAME,
                    "landing_page": "BILLING",
                    "user_action": "PAY_NOW",
                    "return_url": f"{settings.PAYPAL_RETURN_URL}?payment_id={payment_obj.id}",
                    "cancel_url": f"{settings.PAYPAL_CANCEL_URL}?payment_id={payment_obj.id}"
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'PayPal-Request-Id': payment_obj.reference_number
            }
            
            response = requests.post(
                settings.PAYPAL_PAYMENTS_URL,
                headers=headers,
                json=order_data,
                timeout=30
            )
            
            if response.status_code == 201:
                order_response = response.json()
                
                # Find approval URL
                approval_url = None
                for link in order_response.get('links', []):
                    if link['rel'] == 'approve':
                        approval_url = link['href']
                        break
                
                if approval_url:
                    # Update payment with PayPal order ID
                    payment_obj.paypal_payment_id = order_response['id']
                    payment_obj.save(update_fields=['paypal_payment_id'])
                    
                    logger.info(f"PayPal order created: {order_response['id']} for payment {payment_obj.reference_number}")
                    
                    return {
                        'success': True,
                        'order_id': order_response['id'],
                        'approval_url': approval_url,
                        'message': 'PayPal order created successfully'
                    }
                else:
                    return {
                        'success': False,
                        'order_id': None,
                        'approval_url': None,
                        'message': 'No approval URL found in PayPal response'
                    }
            else:
                logger.error(f"PayPal order creation failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'order_id': None,
                    'approval_url': None,
                    'message': f'Order creation failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"PayPal order creation error: {str(e)}")
            return {
                'success': False,
                'order_id': None,
                'approval_url': None,
                'message': f'Order creation failed: {str(e)}'
            }
    
    @staticmethod
    def capture_payment_order(order_id):
        """
        Capture/execute PayPal payment order
        
        Args:
            order_id (str): PayPal order ID
            
        Returns:
            dict: {'success': bool, 'capture_id': str, 'message': str}
        """
        try:
            # Get access token
            token_response = PayPalService.get_access_token()
            if not token_response['success']:
                return token_response
            
            access_token = token_response['access_token']
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            capture_url = f"{settings.PAYPAL_PAYMENTS_URL}/{order_id}/capture"
            
            response = requests.post(
                capture_url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                capture_response = response.json()
                
                # Extract capture ID
                capture_id = None
                purchase_units = capture_response.get('purchase_units', [])
                if purchase_units:
                    captures = purchase_units[0].get('payments', {}).get('captures', [])
                    if captures:
                        capture_id = captures[0]['id']
                
                logger.info(f"PayPal payment captured: {order_id} -> {capture_id}")
                
                return {
                    'success': True,
                    'capture_id': capture_id,
                    'capture_data': capture_response,
                    'message': 'Payment captured successfully'
                }
            else:
                logger.error(f"PayPal capture failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'capture_id': None,
                    'message': f'Payment capture failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"PayPal capture error: {str(e)}")
            return {
                'success': False,
                'capture_id': None,
                'message': f'Payment capture failed: {str(e)}'
            }
    
    @staticmethod
    def verify_webhook_signature(request_body, headers):
        """
        Verify PayPal webhook signature
        
        Args:
            request_body (bytes): Raw request body
            headers (dict): Request headers
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # PayPal webhook verification would go here
            # For now, return True for sandbox testing
            # In production, implement proper signature verification
            
            if settings.PAYPAL_MODE == 'sandbox':
                return True
            
            # TODO: Implement proper webhook signature verification for production
            return True
            
        except Exception as e:
            logger.error(f"PayPal webhook verification error: {str(e)}")
            return False
