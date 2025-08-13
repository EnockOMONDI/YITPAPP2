# PayPal Webhook Configuration Guide for YITP

## 🔗 **Webhook URL Configuration**

### **Production Webhook URL**
```
https://www.youthimpactglobal.com/payments/paypal/webhook/
```

### **Webhook ID**
```
83J77159BP9970500
```

## 📋 **PayPal Developer Dashboard Setup**

### **Step 1: Access PayPal Developer Dashboard**
1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/developer/applications/)
2. Log in with your PayPal business account
3. Select your YITP application

### **Step 2: Configure Webhook**
1. Navigate to **Webhooks** section
2. Click **Add Webhook**
3. Enter webhook URL: `https://www.youthimpactglobal.com/payments/paypal/webhook/`
4. Select the following events:

#### **Required Events:**
- ✅ `CHECKOUT.ORDER.APPROVED` - Order approved by customer
- ✅ `PAYMENT.CAPTURE.COMPLETED` - Payment successfully captured
- ✅ `PAYMENT.CAPTURE.DENIED` - Payment capture failed

#### **Recommended Additional Events:**
- ✅ `CHECKOUT.ORDER.COMPLETED` - Order processing completed
- ✅ `PAYMENT.CAPTURE.PENDING` - Payment capture pending
- ✅ `PAYMENT.CAPTURE.REFUNDED` - Payment refunded
- ✅ `CHECKOUT.ORDER.CANCELLED` - Order cancelled by customer

### **Step 3: Save and Test**
1. Click **Save** to create the webhook
2. Note the **Webhook ID** (should be: `83J77159BP9970500`)
3. Use PayPal's webhook simulator to test

## 🔧 **Technical Implementation**

### **Webhook Handler Location**
- **File**: `payments/views.py`
- **Function**: `paypal_webhook(request)`
- **URL Pattern**: `/payments/paypal/webhook/`

### **Event Processing Logic**
```python
@csrf_exempt
@require_POST
def paypal_webhook(request):
    """Handle PayPal webhook notifications"""
    
    # Verify webhook signature
    if not PayPalService.verify_webhook_signature(request.body, request.headers):
        return JsonResponse({'status': 'error'}, status=400)
    
    webhook_data = json.loads(request.body)
    event_type = webhook_data.get('event_type')
    
    if event_type == 'CHECKOUT.ORDER.APPROVED':
        # Capture payment automatically
        order_id = webhook_data['resource']['id']
        PayPalService.capture_payment_order(order_id)
        
    elif event_type == 'PAYMENT.CAPTURE.COMPLETED':
        # Confirm payment and activate course access
        PaymentService.confirm_payment(payment_reference)
```

### **Security Features**
- ✅ **Signature Verification**: All webhooks verified using PayPal's signature
- ✅ **CSRF Exempt**: Webhook endpoint properly configured for external calls
- ✅ **Error Handling**: Comprehensive error logging and response handling
- ✅ **Idempotency**: Duplicate webhook handling prevention

## 📊 **Webhook Event Handling**

### **CHECKOUT.ORDER.APPROVED**
- **Trigger**: Customer approves payment on PayPal
- **Action**: Automatically capture the payment
- **Result**: Payment moves to completion process

### **PAYMENT.CAPTURE.COMPLETED**
- **Trigger**: Payment successfully captured by PayPal
- **Action**: Confirm payment in YITP system
- **Result**: Course access activated, enrollment confirmed

### **PAYMENT.CAPTURE.DENIED**
- **Trigger**: Payment capture failed
- **Action**: Mark payment as failed
- **Result**: User notified, can retry payment

## 🔍 **Testing & Debugging**

### **Webhook Testing**
1. Use PayPal's webhook simulator in Developer Dashboard
2. Send test events to verify endpoint response
3. Check Django logs for webhook processing

### **Debug Information**
- **Logs Location**: Django application logs
- **Debug Function**: Available in PayPal service
- **Status Monitoring**: Admin interface payment status

### **Common Issues & Solutions**

#### **Webhook Not Receiving Events**
- ✅ Verify URL is accessible: `https://www.youthimpactglobal.com/payments/paypal/webhook/`
- ✅ Check PayPal Developer Dashboard webhook configuration
- ✅ Ensure webhook ID matches: `83J77159BP9970500`

#### **Signature Verification Failing**
- ✅ Verify webhook ID in environment variables
- ✅ Check PayPal mode (sandbox vs live)
- ✅ Ensure proper request headers

#### **Payment Not Confirming**
- ✅ Check webhook event processing logs
- ✅ Verify payment reference matching
- ✅ Ensure database connectivity

## 🌐 **Domain Configuration**

### **Primary Domain**
- **Production**: `https://www.youthimpactglobal.com`
- **Webhook Endpoint**: `/payments/paypal/webhook/`
- **Full URL**: `https://www.youthimpactglobal.com/payments/paypal/webhook/`

### **Environment Variables**
```bash
SITE_URL=https://www.youthimpactglobal.com
PAYPAL_WEBHOOK_ID=83J77159BP9970500
PAYPAL_MODE=sandbox
```

## 📈 **Monitoring & Analytics**

### **Webhook Success Metrics**
- **Response Time**: < 5 seconds
- **Success Rate**: > 99%
- **Error Rate**: < 1%

### **Payment Processing Metrics**
- **Auto-Confirmation Rate**: > 95%
- **Manual Intervention**: < 5%
- **Failed Webhooks**: < 1%

---

**Last Updated**: January 2025  
**Version**: 1.0  
**Platform**: YITP Learning Management System  
**Support**: Contact YITP Technical Team
