# PayPal Testing Checklist for YITP Platform

## 🧪 **Pre-Testing Setup**

### ✅ **PayPal Developer Account Setup**
- [ ] Create PayPal Developer account at https://developer.paypal.com
- [ ] Create sandbox application "YITP Learning Platform"
- [ ] Get sandbox Client ID and Client Secret
- [ ] Create webhook with URL: `https://www.youthimpactglobal.com/payments/paypal/webhook/`
- [ ] Subscribe to events: `CHECKOUT.ORDER.APPROVED`, `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`
- [ ] Copy webhook ID and update in production environment

### ✅ **Sandbox Test Accounts**
- [ ] Create sandbox buyer account with $1000 balance
- [ ] Create sandbox seller/business account
- [ ] Note down test account credentials

### ✅ **YITP Configuration Verification**
- [ ] Verify PayPal credentials are set in production environment
- [ ] Confirm `PAYPAL_MODE=sandbox` for testing
- [ ] Update `PAYPAL_WEBHOOK_ID` with new webhook ID
- [ ] Verify course "Understanding Purpose In life" is published ($2 USD)

## 🧪 **Test Scenarios**

### **Test 1: Full Payment Flow ($2 USD)**
**URL**: `https://www.youthimpactglobal.com/payments/methods/2/`

#### **Steps:**
1. [ ] Navigate to payment methods page
2. [ ] Verify PayPal button shows "$2 USD with PayPal"
3. [ ] Click PayPal payment button
4. [ ] Verify redirect to `sandbox.paypal.com`
5. [ ] Login with sandbox buyer account
6. [ ] Complete $2 USD payment approval
7. [ ] Verify redirect back to YITP platform
8. [ ] Check course enrollment is activated
9. [ ] Verify access to course content

#### **Expected Results:**
- [ ] ✅ Immediate course access activation
- [ ] ✅ User receives payment success email with invoice
- [ ] ✅ Admin receives payment notification at youthimpactglobal3@gmail.com
- [ ] ✅ Payment status shows "confirmed" in admin panel
- [ ] ✅ Course appears in user's enrolled courses

### **Test 2: Installment Payment Flow ($1 USD × 2)**
**URL**: `https://www.youthimpactglobal.com/payments/methods/2/`

#### **First Installment:**
1. [ ] Select "2 Installments" payment option
2. [ ] Verify PayPal button shows "$1 USD with PayPal (First Installment)"
3. [ ] Complete first installment payment
4. [ ] Verify 30-day course access activated
5. [ ] Check installment tracking in user profile

#### **Second Installment:**
6. [ ] Wait for installment reminder email (or test manually)
7. [ ] Complete second installment payment
8. [ ] Verify full course access activated
9. [ ] Check payment completion status

#### **Expected Results:**
- [ ] ✅ First payment: 30-day access with expiration tracking
- [ ] ✅ Second payment: Full lifetime access
- [ ] ✅ Installment reminder emails sent
- [ ] ✅ Payment history shows both installments

### **Test 3: Payment Failure Scenarios**

#### **Cancelled Payment:**
1. [ ] Start PayPal payment process
2. [ ] Cancel payment on PayPal page
3. [ ] Verify return to YITP with error message
4. [ ] Check failure notification emails sent

#### **Insufficient Funds:**
1. [ ] Use sandbox account with $0 balance
2. [ ] Attempt payment
3. [ ] Verify proper error handling
4. [ ] Check admin failure notifications

#### **Expected Results:**
- [ ] ✅ User receives failure notification email
- [ ] ✅ Admin receives failure alert email
- [ ] ✅ Payment status remains "pending" or "failed"
- [ ] ✅ User can retry payment

### **Test 4: Email Notification System**

#### **User Emails (to test user account):**
- [ ] Payment initiated confirmation
- [ ] Payment success with invoice details
- [ ] Payment failure with retry instructions
- [ ] Course enrollment confirmation

#### **Admin Emails (to youthimpactglobal3@gmail.com):**
- [ ] Successful payment notification
- [ ] Failed payment alert
- [ ] Installment payment tracking

#### **Email Content Verification:**
- [ ] YITP branding colors (#ff5d15 orange, #1a2e53 dark blue)
- [ ] Correct payment amounts and course details
- [ ] Working links to course and dashboard
- [ ] Professional formatting and layout

### **Test 5: Webhook Integration**

#### **Webhook Testing:**
1. [ ] Use PayPal webhook simulator in Developer Dashboard
2. [ ] Send test `CHECKOUT.ORDER.APPROVED` event
3. [ ] Send test `PAYMENT.CAPTURE.COMPLETED` event
4. [ ] Verify webhook endpoint responds correctly
5. [ ] Check Django logs for webhook processing

#### **Expected Results:**
- [ ] ✅ Webhook signature verification passes
- [ ] ✅ Payment status updated automatically
- [ ] ✅ Course enrollment triggered by webhook
- [ ] ✅ Email notifications sent via webhook

## 🔧 **Technical Verification**

### **Database Checks:**
- [ ] Payment records created with correct amounts
- [ ] PayPal transaction IDs stored properly
- [ ] Course enrollments activated
- [ ] User profiles updated with payment status

### **Admin Panel Verification:**
- [ ] Payments visible in Django admin
- [ ] Course enrollments show correct status
- [ ] User profiles reflect payment history
- [ ] Email logs show successful delivery

### **Security Verification:**
- [ ] Webhook signature verification working
- [ ] PayPal API credentials secure
- [ ] HTTPS connections for all PayPal interactions
- [ ] No sensitive data exposed in logs

## 🚨 **Troubleshooting Guide**

### **Common Issues:**

#### **PayPal Redirect Fails:**
- Check PayPal credentials are correct
- Verify sandbox mode is enabled
- Check PayPal order creation logs

#### **Webhook Not Triggered:**
- Verify webhook URL is accessible
- Check webhook ID matches PayPal dashboard
- Review webhook signature verification

#### **Emails Not Delivered:**
- Check Gmail SMTP configuration
- Verify email templates exist
- Review email service logs

#### **Course Access Not Activated:**
- Check enrollment service integration
- Verify payment confirmation logic
- Review webhook processing logs

## ✅ **Testing Completion Criteria**

### **All Tests Must Pass:**
- [ ] Full payment flow works end-to-end
- [ ] Installment payments function correctly
- [ ] Email notifications deliver properly
- [ ] Webhook integration processes payments automatically
- [ ] Admin receives all required notifications
- [ ] Course access activates immediately
- [ ] Payment failure scenarios handled gracefully

### **Performance Criteria:**
- [ ] Payment processing < 30 seconds
- [ ] Course access activation < 5 seconds after webhook
- [ ] Email delivery < 2 minutes
- [ ] No payment processing errors

## 🎯 **Sign-off**

**Tested By:** ________________  
**Date:** ________________  
**Environment:** Production/Sandbox  
**All Tests Passed:** ✅ / ❌  

**Notes:**
_________________________________
_________________________________
_________________________________

---

**🚀 Ready for Production:** Once all tests pass, the automated PayPal payment system is ready for live use!
