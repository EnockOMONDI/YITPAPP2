# 🔗 PayPal Live Webhook Quick Setup Guide

## **IMMEDIATE ACTION REQUIRED**

You need to create a **live webhook** in PayPal Developer Dashboard and update the webhook ID.

---

## **🚀 STEP-BY-STEP WEBHOOK SETUP**

### **Step 1: Access PayPal Developer Dashboard**
1. Go to: https://developer.paypal.com/developer/applications/
2. **Log in** with your PayPal business account
3. **Switch to LIVE environment** (toggle in top-right corner)
4. Select your **YITP live application**

### **Step 2: Create Live Webhook**
1. Click **Webhooks** in the left sidebar
2. Click **Add Webhook** button
3. Enter webhook URL: 
   ```
   https://www.youthimpactglobal.com/payments/paypal/webhook/
   ```
4. Select these events:
   - ✅ `CHECKOUT.ORDER.APPROVED`
   - ✅ `PAYMENT.CAPTURE.COMPLETED` 
   - ✅ `PAYMENT.CAPTURE.DENIED`
   - ✅ `CHECKOUT.ORDER.COMPLETED`
5. Click **Save**

### **Step 3: Copy Webhook ID**
After creating the webhook, you'll see a **Webhook ID** (looks like: `8WH12345678901234`)
**Copy this ID** - you'll need it for the next step.

### **Step 4: Update Configuration Files**

#### **Update .env file:**
```bash
PAYPAL_WEBHOOK_ID=YOUR_COPIED_WEBHOOK_ID_HERE
```

#### **Update render.yaml file:**
```yaml
- key: PAYPAL_WEBHOOK_ID
  value: "YOUR_COPIED_WEBHOOK_ID_HERE"
```

### **Step 5: Deploy to Production**
```bash
git add .env render.yaml
git commit -m "feat: Configure PayPal live webhook ID"
git push origin V5
```

---

## **✅ CURRENT STATUS**

### **✅ COMPLETED:**
- PayPal live credentials updated in .env
- PayPal live credentials updated in render.yaml  
- PAYPAL_MODE set to "live"
- Webhook URL endpoint ready: `/payments/paypal/webhook/`

### **🔄 PENDING:**
- Create live webhook in PayPal Developer Dashboard
- Update PAYPAL_WEBHOOK_ID in both .env and render.yaml
- Deploy updated configuration to production
- Test live payment flow

---

## **🧪 TESTING AFTER SETUP**

### **Test URL:**
```
https://www.youthimpactglobal.com/payments/methods/2/
```
*(This is the $2 USD "Understanding Purpose In Life" course)*

### **What to Verify:**
1. **Payment Flow:** PayPal payment completes successfully
2. **Webhook Processing:** Check logs for webhook events
3. **Course Access:** Student gets immediate access to course
4. **Email Notifications:** Payment confirmation emails sent
5. **Admin Notifications:** Admin receives payment notification

---

## **🔍 WEBHOOK VERIFICATION**

### **Test Webhook URL:**
You can test if your webhook endpoint is accessible:
```bash
curl -X POST https://www.youthimpactglobal.com/payments/paypal/webhook/
```
*Should return a 405 Method Not Allowed (which is correct - it only accepts PayPal webhooks)*

### **Monitor Webhook Events:**
After setup, monitor your application logs for:
```
PayPal webhook received: CHECKOUT.ORDER.APPROVED
PayPal webhook received: PAYMENT.CAPTURE.COMPLETED
Payment confirmed via PayPal webhook: [order_id]
```

---

## **🚨 IMPORTANT NOTES**

### **Security:**
- ✅ Your webhook endpoint has CSRF exemption (required for PayPal)
- ✅ Basic webhook signature verification is implemented
- ✅ HTTPS is required and configured

### **Environment:**
- ✅ Production site URL: `https://www.youthimpactglobal.com`
- ✅ Webhook endpoint: `/payments/paypal/webhook/`
- ✅ PayPal mode: `live` (production)

### **Backup Plan:**
If webhook processing fails, you can manually verify payments in:
- PayPal Business Dashboard
- YITP Admin Panel: `/admin/payments/payment/`

---

## **📞 SUPPORT**

If you encounter issues:
1. Check PayPal Developer Dashboard for webhook delivery status
2. Monitor application logs for error messages
3. Verify webhook ID matches in both configuration files
4. Test with small amount ($2) first

**Your PayPal integration is ready for live production once the webhook is configured!** 🚀
