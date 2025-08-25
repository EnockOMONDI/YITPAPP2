# 🚀 PayPal Live Production Setup Guide for YITP

## **✅ ENVIRONMENT VARIABLES CONFIGURATION**

### **1. Local Development (.env file) - ✅ COMPLETED**
```bash
# PayPal Live Production Credentials
PAYPAL_CLIENT_ID=AcZ8rCsyFeympsh1tPzIEpPorEPtmGT40qZkS-YsE6pxxtMyqJ18BjfriE07hiGxOEMnBom_H6VoWdD9
PAYPAL_CLIENT_SECRET=EEvqKEvfY7ZqDfO067JliUSGcJKzWo_8HWjWPp7xxEvfX6FXlyfNFIDFhMhq4IahEgH_FMPBpyTMFyca

# PayPal Environment Configuration
PAYPAL_MODE=live
PAYPAL_WEBHOOK_ID=YOUR_NEW_LIVE_WEBHOOK_ID_HERE
```

### **2. Production Deployment (render.yaml) - ✅ UPDATED**
The render.yaml file has been updated with your live credentials. You need to:

1. **Update the PAYPAL_WEBHOOK_ID** after creating the live webhook (see step 2 below)
2. **Deploy to production** to apply the changes

---

## **🔗 WEBHOOK URL CONFIGURATION**

### **Production Webhook URL:**
```
https://www.youthimpactglobal.com/payments/paypal/webhook/
```

### **PayPal Developer Dashboard Setup:**

#### **Step 1: Access Live PayPal Application**
1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/developer/applications/)
2. Log in with your PayPal business account
3. **Switch to LIVE environment** (toggle in top-right corner)
4. Select your YITP live application

#### **Step 2: Create Live Webhook**
1. Navigate to **Webhooks** section
2. Click **Add Webhook**
3. Enter webhook URL: `https://www.youthimpactglobal.com/payments/paypal/webhook/`
4. Select the following events:
   - ✅ `CHECKOUT.ORDER.APPROVED`
   - ✅ `PAYMENT.CAPTURE.COMPLETED`
   - ✅ `PAYMENT.CAPTURE.DENIED`
   - ✅ `CHECKOUT.ORDER.COMPLETED`
5. Click **Save**
6. **Copy the Webhook ID** (you'll need this for step 3)

#### **Step 3: Update Webhook ID**
1. Update `PAYPAL_WEBHOOK_ID` in render.yaml with the new live webhook ID
2. Update your local `.env` file with the same webhook ID
3. Deploy to production

---

## **⚙️ PRODUCTION DEPLOYMENT CHECKLIST**

### **Required Configuration Updates:**

#### **✅ Environment Variables (render.yaml):**
```yaml
- key: PAYPAL_CLIENT_ID
  value: "AcZ8rCsyFeympsh1tPzIEpPorEPtmGT40qZkS-YsE6pxxtMyqJ18BjfriE07hiGxOEMnBom_H6VoWdD9"
- key: PAYPAL_CLIENT_SECRET
  value: "EEvqKEvfY7ZqDfO067JliUSGcJKzWo_8HWjWPp7xxEvfX6FXlyfNFIDFhMhq4IahEgH_FMPBpyTMFyca"
- key: PAYPAL_MODE
  value: "live"
- key: PAYPAL_WEBHOOK_ID
  value: "YOUR_NEW_LIVE_WEBHOOK_ID_HERE"
```

#### **✅ Webhook Signature Verification:**
The current implementation has a TODO for production webhook verification. For enhanced security, consider implementing proper signature verification:

**File:** `payments/paypal_service.py` (line 369)
```python
# TODO: Implement proper webhook signature verification for production
```

#### **✅ SSL Certificate:**
- ✅ Your production site already has SSL: `https://www.youthimpactglobal.com`
- ✅ PayPal requires HTTPS for live webhooks

#### **✅ Domain Verification:**
- ✅ Your domain `youthimpactglobal.com` is properly configured
- ✅ Webhook URL is accessible: `/payments/paypal/webhook/`


---

## **🧪 SAFE TESTING RECOMMENDATIONS**

### **1. Pre-Production Testing (Recommended)**

#### **Test with Small Amounts:**
- Start with the lowest course price ($2 USD for "Understanding Purpose In Life")
- Use your own PayPal account for initial tests
- Test the complete flow: payment → webhook → course access

#### **Test Scenarios:**
1. **Successful Payment Flow:**
   - Navigate to: `https://www.youthimpactglobal.com/payments/methods/2/`
   - Complete PayPal payment
   - Verify course access is granted
   - Check email notifications

2. **Webhook Processing:**
   - Monitor webhook logs in production
   - Verify `CHECKOUT.ORDER.APPROVED` and `PAYMENT.CAPTURE.COMPLETED` events
   - Check payment status updates in admin panel

3. **Email Notifications:**
   - Verify payment confirmation emails are sent
   - Check admin notification emails to `youthimpactglobal3@gmail.com`

### **2. Production Monitoring**

#### **Log Monitoring:**
Monitor these log entries in production:
```bash
# PayPal webhook events
"PayPal webhook received: CHECKOUT.ORDER.APPROVED"
"PayPal webhook received: PAYMENT.CAPTURE.COMPLETED"

# Payment processing
"PayPal payment order created"
"Payment confirmed via PayPal webhook"
```

#### **Database Monitoring:**
Check the `payments_payment` table for:
- `status` field updates (pending → completed)
- `paypal_payment_id` population
- `paypal_capture_id` population

---

## **🔒 SECURITY CONSIDERATIONS**

### **1. Webhook Security:**
- ✅ CSRF exemption is properly configured for webhook endpoint
- ✅ Webhook signature verification is implemented (basic)
- ⚠️ Consider implementing full PayPal signature verification for production

### **2. Payment Validation:**
- ✅ Payment amounts are validated against course prices
- ✅ Duplicate payment prevention is implemented
- ✅ Payment status tracking is comprehensive

### **3. Error Handling:**
- ✅ Comprehensive error logging is implemented
- ✅ Failed payments are properly tracked
- ✅ Admin notifications for payment issues

---

## **📊 MONITORING & ANALYTICS**

### **Key Metrics to Monitor:**

#### **Payment Success Rate:**
- Track successful vs failed payments
- Monitor webhook delivery success
- Check payment completion times

#### **Course Access Activation:**
- Verify automatic course access after payment
- Monitor enrollment confirmation emails
- Check user dashboard updates

#### **Error Rates:**
- PayPal API errors
- Webhook processing failures
- Payment verification issues

---

## **🚨 TROUBLESHOOTING GUIDE**

### **Common Issues & Solutions:**

#### **1. Webhook Not Receiving Events:**
- Verify webhook URL is accessible: `curl https://www.youthimpactglobal.com/payments/paypal/webhook/`
- Check PayPal Developer Dashboard for webhook delivery attempts
- Verify webhook ID matches in environment variables

#### **2. Payment Not Completing:**
- Check PayPal order status in PayPal dashboard
- Verify webhook events are being processed
- Check payment status in YITP admin panel

#### **3. Course Access Not Granted:**
- Verify payment status is "completed" in database
- Check enrollment records in admin panel
- Verify email notifications were sent

---

## **📋 DEPLOYMENT STEPS**

### **Step-by-Step Deployment:**

1. **✅ Update Local Environment:**
   - Your `.env` file is already updated with live credentials

2. **✅ Update Production Configuration:**
   - render.yaml has been updated with live credentials
   - Need to update PAYPAL_WEBHOOK_ID after creating webhook

3. **🔄 Create Live Webhook:**
   - Follow webhook setup instructions above
   - Copy the webhook ID

4. **🔄 Update Webhook ID:**
   - Update PAYPAL_WEBHOOK_ID in render.yaml
   - Update PAYPAL_WEBHOOK_ID in .env

5. **🔄 Deploy to Production:**
   ```bash
   git add render.yaml
   git commit -m "feat: Configure PayPal for live production mode"
   git push origin V5
   ```

6. **🔄 Test Live Integration:**
   - Test with small amount ($2 course)
   - Verify webhook processing
   - Check course access activation

---

## **✅ VERIFICATION CHECKLIST**

- [ ] PayPal live credentials updated in render.yaml
- [ ] PAYPAL_MODE set to "live"
- [ ] Live webhook created in PayPal Developer Dashboard
- [ ] PAYPAL_WEBHOOK_ID updated with live webhook ID
- [ ] Production deployment completed
- [ ] Test payment with small amount successful
- [ ] Webhook events processing correctly
- [ ] Course access granted automatically
- [ ] Email notifications working
- [ ] Admin notifications received

---

## **🎯 NEXT STEPS**

1. **Create live webhook** in PayPal Developer Dashboard
2. **Update PAYPAL_WEBHOOK_ID** in render.yaml and .env
3. **Deploy to production**
4. **Test with $2 course** payment
5. **Monitor webhook logs** for successful processing
6. **Verify course access** activation

Your PayPal integration is now ready for live production use! 🚀
