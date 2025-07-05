# YITP Course Enrollment and Payment System Test Suite

## Overview

This comprehensive test suite validates the YITP course enrollment and payment system, ensuring robust functionality across all user workflows from course discovery through completion and certification.

## Test Structure

### 📁 Test Files

- **`test_course_enrollment_journey.py`** - Main enrollment workflow tests (1,400+ lines)
- **`test_payment_integration.py`** - Payment processing integration tests
- **`run_enrollment_tests.py`** - Test runner with coverage reporting
- **`README.md`** - This documentation file

### 🧪 Test Categories

#### 1. Unit Tests
- **EnrollmentService** - Business logic validation
- **PaymentService** - M-Pesa and bank transfer processing
- **CertificateService** - PDF generation and verification
- **Email Notifications** - Confirmation and admin alerts

#### 2. Integration Tests
- **Complete User Journeys** - End-to-end workflows
- **Free Course Enrollment** - No payment required
- **Paid Course Enrollment** - Payment verification
- **Cross-Module Integration** - Service interactions

#### 3. Error Handling Tests
- **Invalid Input Validation** - Malformed data handling
- **Network Failure Recovery** - API timeout scenarios
- **Database Constraint Violations** - Duplicate prevention
- **Email Delivery Failures** - Graceful degradation

#### 4. Security Tests
- **Authentication Requirements** - Access control
- **Input Sanitization** - XSS/SQL injection prevention
- **Cross-User Protection** - Authorization validation
- **Payment Security** - Transaction validation

#### 5. Performance Tests
- **Bulk Operations** - Multiple enrollments
- **Query Efficiency** - Database optimization
- **Response Times** - Performance benchmarks

## Test Coverage

### ✅ Enrollment Workflow
- Course eligibility validation
- Payment status verification
- Enrollment record creation
- Progress tracking initialization
- Email notification delivery
- Admin notification system

### ✅ Payment Processing
- M-Pesa STK Push integration
- Bank transfer verification
- Payment status tracking
- Callback processing
- Timeout handling
- Security validation

### ✅ Certificate Generation
- PDF certificate creation
- Verification code generation
- Certificate delivery
- Verification system

### ✅ Email System
- Enrollment confirmations
- Payment confirmations
- Admin notifications
- Certificate delivery
- Failure handling

## Running Tests

### Quick Start
```bash
# Run all tests
python tests/run_enrollment_tests.py

# Run with coverage
python tests/run_enrollment_tests.py --coverage

# Run specific test pattern
python tests/run_enrollment_tests.py --pattern payment

# Generate HTML coverage report
python tests/run_enrollment_tests.py --coverage --html-report
```

### Django Test Commands
```bash
# Run enrollment tests only
python manage.py test tests.test_course_enrollment_journey

# Run payment tests only
python manage.py test tests.test_payment_integration

# Run with verbosity
python manage.py test tests.test_course_enrollment_journey --verbosity=2

# Keep test database
python manage.py test tests.test_course_enrollment_journey --keepdb
```

### Test Environment Setup
```bash
# Install test dependencies
pip install coverage

# Setup test database
python manage.py migrate

# Run dependency check
python tests/run_enrollment_tests.py --check-deps
```

## Test Data

### 🎓 Test Courses
- **Free Course**: "Introduction to Digital Literacy" (KES 0)
- **Paid Course**: "Advanced Web Development" (KES 15,000)
- **Expensive Course**: "Data Science Bootcamp" (KES 75,000)

### 👥 Test Users
- **Regular User**: Basic user with no payment
- **Paid User**: User with confirmed payment status
- **Admin User**: Administrative privileges

### 💳 Payment Methods
- **M-Pesa**: Mobile money integration
- **Bank Transfer**: Manual verification
- **Credit Card**: Coming soon (UI only)

## Mock Services

### M-Pesa API Mocking
```python
@patch('payments.payment_service.requests.post')
def test_mpesa_success(self, mock_post):
    mock_post.return_value.json.return_value = {
        'ResponseCode': '0',
        'MerchantRequestID': 'test-123',
        'CheckoutRequestID': 'test-456'
    }
```

### Email Backend Mocking
```python
# Email testing with Django's test email backend
from django.core import mail
mail.outbox = []  # Clear before test
# ... perform action that sends email
self.assertEqual(len(mail.outbox), 1)
```

## Test Results Interpretation

### Success Indicators
- ✅ All tests pass
- ✅ Coverage > 90%
- ✅ No security vulnerabilities
- ✅ Performance within limits

### Common Issues
- ❌ Missing dependencies (install required packages)
- ❌ Database migration needed (run `python manage.py migrate`)
- ❌ Email configuration (check SMTP settings)
- ❌ M-Pesa credentials (verify API keys)

## Continuous Integration

### GitHub Actions Example
```yaml
name: YITP Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python tests/run_enrollment_tests.py --coverage
```

## Test Maintenance

### Adding New Tests
1. Follow existing test patterns
2. Use descriptive test names
3. Include both success and failure scenarios
4. Add appropriate mocking for external services
5. Update this documentation

### Test Data Management
- Use `setUp()` and `tearDown()` methods
- Create minimal test data
- Clean up after tests
- Use transactions for isolation

### Performance Considerations
- Use `--keepdb` for faster test runs
- Mock external API calls
- Minimize database queries
- Use appropriate test database settings

## Troubleshooting

### Common Test Failures

#### Import Errors
```bash
# Missing app in INSTALLED_APPS
ModuleNotFoundError: No module named 'payments'
```
**Solution**: Add missing apps to `INSTALLED_APPS` or install dependencies

#### Database Errors
```bash
# Migration needed
django.db.utils.ProgrammingError: relation "payments_payment" does not exist
```
**Solution**: Run `python manage.py migrate`

#### Email Errors
```bash
# SMTP configuration
ConnectionRefusedError: [Errno 61] Connection refused
```
**Solution**: Use test email backend in settings

#### M-Pesa API Errors
```bash
# Missing credentials
KeyError: 'MPESA_CONSUMER_KEY'
```
**Solution**: Add M-Pesa credentials to settings

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use Django debug toolbar
INSTALLED_APPS += ['debug_toolbar']
```

## Contributing

### Test Guidelines
1. Write tests for all new features
2. Maintain high test coverage (>90%)
3. Include edge cases and error scenarios
4. Use meaningful test names and docstrings
5. Follow existing code patterns

### Code Review Checklist
- [ ] Tests cover new functionality
- [ ] Tests include error handling
- [ ] Mock external dependencies
- [ ] Performance impact considered
- [ ] Documentation updated

## Support

For test-related issues:
1. Check this documentation
2. Review test output and logs
3. Verify environment setup
4. Contact development team

---

**Last Updated**: January 5, 2025  
**Test Suite Version**: 1.0  
**Django Version**: 4.2+  
**Python Version**: 3.9+
