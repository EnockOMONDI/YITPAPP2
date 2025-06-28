# YITP (Youth Impact Global) Django Application - Technical Documentation

## 📋 Table of Contents
1. [Project Overview & Architecture](#project-overview--architecture)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Database Models Documentation](#database-models-documentation)
5. [Views & URL Patterns](#views--url-patterns)
6. [Email System Documentation](#email-system-documentation)
7. [Setup & Installation](#setup--installation)
8. [Deployment](#deployment)

---

## 1. Project Overview & Architecture

### **Application Purpose**
The Youth Impact Training Programme (YITP) is a comprehensive Django web application designed to:
- Manage user registration and authentication with email verification
- Handle sponsorship requests and applications
- Publish blog posts and educational content
- Manage events (both physical and online)
- Facilitate community engagement through comments and interactions

### **Architecture Pattern**
- **Framework**: Django 4.2+ (MVT - Model-View-Template pattern)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Bootstrap-based responsive templates
- **Email System**: SMTP with HTML templates
- **Media Management**: Uploadcare integration
- **Admin Interface**: Django Jet (enhanced admin panel)

---

## 2. Technology Stack

### **Core Framework**
- **Django**: 4.2.20+ (Web framework)
- **Python**: 3.8+ (Programming language)

### **Database**
- **SQLite**: Local development database
- **PostgreSQL**: Production database (Neon cloud)
- **psycopg2-binary**: PostgreSQL adapter

### **Frontend & UI**
- **Bootstrap**: Responsive CSS framework
- **CKEditor**: Rich text editing
- **Django Jet**: Enhanced admin interface
- **Uploadcare**: Media file management

### **Email & Communication**
- **SMTP**: Gmail integration for email delivery
- **HTML Templates**: Responsive email templates

### **Additional Libraries**
- **django-taggit**: Tag management system
- **shortuuid**: Short UUID generation
- **Pillow**: Image processing
- **graphene-django**: GraphQL API support
- **whitenoise**: Static file serving
- **gunicorn**: Production WSGI server

---

## 3. Project Structure

```
YITPAPP/
├── blog/                    # Main Django project directory
│   ├── settings.py         # Project settings and configuration
│   ├── urls.py             # Root URL configuration
│   ├── wsgi.py             # WSGI application entry point
│   └── asgi.py             # ASGI application entry point
├── users/                   # User management app
│   ├── models.py           # User profiles, OTP, sponsorship models
│   ├── views.py            # Authentication and user views
│   ├── urls.py             # User-related URL patterns
│   ├── email_utils.py      # Email notification utilities
│   ├── otp_views.py        # OTP verification system
│   ├── forms.py            # User forms and validation
│   └── admin.py            # Admin interface configuration
├── blogapp/                 # Blog management app
│   ├── models.py           # Post, Category, Comment models
│   ├── views.py            # Blog listing and detail views
│   ├── urls.py             # Blog URL patterns
│   └── admin.py            # Blog admin configuration
├── events/                  # Event management app
│   ├── models.py           # Event, EventCategory, EventComment models
│   ├── views.py            # Event listing and detail views
│   ├── urls.py             # Event URL patterns
│   └── admin.py            # Event admin configuration
├── yitp/                    # Main content app
│   ├── models.py           # Static content models
│   ├── views.py            # Homepage and static page views
│   └── urls.py             # Main content URL patterns
├── templates/               # HTML templates
│   ├── emails/             # Email templates (HTML & text)
│   ├── users/              # User-related templates
│   ├── yitp/               # Main site templates
│   └── base.html           # Base template
├── static/                  # Static files (CSS, JS, images)
├── media/                   # User-uploaded files
├── requirements.txt         # Python dependencies
├── render.yaml             # Render deployment configuration
└── manage.py               # Django management script
```

### **Django Apps Overview**

#### **users** - User Management & Authentication
- User registration with email verification
- OTP-based email verification system
- User profiles with additional information
- Sponsorship request management
- Login/logout functionality

#### **blogapp** - Blog & Content Management
- Blog post creation and management
- Category and tag system
- Comment functionality
- Featured and trending posts
- Search and pagination

#### **events** - Event Management
- Physical and online event management
- Event categories and filtering
- Event comments and engagement
- Featured events system

#### **yitp** - Main Website Content
- Homepage and static pages
- Course/program information
- About us and team pages
- Contact and FAQ pages

---

## 4. Database Models Documentation

### **users.models**

#### **Profile Model**
```python
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    bio = models.TextField(default='Edit your Bio!')
    website = models.CharField(max_length=40)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
```
- **Purpose**: Extends Django User model with additional profile information
- **Relationships**: One-to-One with Django User model
- **Fields**: Profile image, bio, website, phone number

#### **OTPVerification Model**
```python
class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
```
- **Purpose**: Manages email verification OTP codes
- **Relationships**: Foreign Key to User
- **Methods**: `is_expired()`, `is_valid()`
- **Features**: 6-digit codes, 200-minute expiry, single-use validation

#### **SponsorshipRequest Model**
```python
class SponsorshipRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Personal Information
    full_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    nationality = models.CharField(max_length=50)
    # ... additional fields for comprehensive sponsorship application
```
- **Purpose**: Handles sponsorship applications with detailed information
- **Relationships**: Foreign Key to User
- **Features**: Multi-step form, document uploads, status tracking

### **blogapp.models**

#### **Category Model**
```python
class Category(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    active = models.BooleanField(default=True)
```
- **Purpose**: Blog post categorization
- **Features**: SEO-friendly slugs, active/inactive status

#### **Post Model**
```python
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=1000)
    content = RichTextField(max_length=10000)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    tags = TaggableManager()
    status = models.CharField(choices=BLOG_PUBLISH_STATUS, max_length=100)
    featured = models.BooleanField(default=False)
    trending = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    pid = ShortUUIDField(length=10, max_length=25)
```
- **Purpose**: Blog post management with rich content
- **Relationships**: Foreign Key to User and Category
- **Features**: Rich text content, tagging, view tracking, status workflow
- **Methods**: `get_read_time()` - calculates reading time

#### **Comment Model**
```python
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    full_name = models.CharField(max_length=1000)
    email = models.EmailField()
    comment = models.TextField()
    active = models.BooleanField(default=True)
```
- **Purpose**: User comments on blog posts
- **Relationships**: Foreign Key to Post
- **Features**: Moderation system, email collection

### **events.models**

#### **Event Model**
```python
class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateTimeField()
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    location = models.CharField(max_length=200, blank=True, null=True)
    online_url = models.URLField(max_length=500, blank=True, null=True)
    content = RichTextField()
    featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
```
- **Purpose**: Event management for both physical and online events
- **Relationships**: Foreign Key to User and EventCategory
- **Features**: Dual-mode events, rich content, view tracking
- **Methods**: `clean()` - validates event type requirements, `get_location_display()`

---

## 5. Views & URL Patterns

### **Authentication Views (users/views.py)**

#### **register(request)**
- **URL**: `/register/`
- **Purpose**: User registration with email verification
- **Features**: Form validation, OTP generation, profile creation
- **Template**: `signup.html`
- **Authentication**: None required

#### **login(request)**
- **URL**: `/login/`
- **Purpose**: User authentication with login notifications
- **Features**: Email notification on successful login
- **Template**: `login.html`
- **Authentication**: None required

#### **profile(request)**
- **URL**: `/profile/`
- **Purpose**: User profile management
- **Authentication**: Login required (`@login_required`)
- **Template**: `profile.html`

### **OTP Verification Views (users/otp_views.py)**

#### **verify_otp_view(request)**
- **URL**: `/verify-otp/`
- **Purpose**: Email verification via OTP
- **Features**: OTP validation, user activation, welcome email
- **Template**: `users/verify_otp.html`

#### **resend_otp_view(request)**
- **URL**: `/resend-otp/`
- **Purpose**: AJAX OTP resending with cooldown
- **Response**: JSON response
- **Features**: Rate limiting, new OTP generation

### **Blog Views (blogapp/views.py)**

#### **blogList(request)**
- **URL**: `/blogs/`
- **Purpose**: Blog post listing with search and pagination
- **Features**: Search functionality, category filtering, pagination
- **Template**: `yitp/bloglist.html`

#### **blogDetail(request, pid)**
- **URL**: `/blogs/<pid>`
- **Purpose**: Individual blog post display with comments
- **Features**: View counting, comment submission, related posts
- **Template**: `yitp/blogdetail.html`

### **Event Views (events/views.py)**

#### **event_list(request)**
- **URL**: `/events/`
- **Purpose**: Event listing with filtering
- **Features**: Type filtering, search, category filtering, pagination
- **Template**: `events/event_list.html`

#### **event_detail(request, id)**
- **URL**: `/events/<id>/`
- **Purpose**: Individual event display with comments
- **Features**: View counting, comment system, related events
- **Template**: `events/event_detail.html`

### **Main Content Views (yitp/views.py)**

#### **home(request)**
- **URL**: `/`
- **Purpose**: Homepage with dynamic content
- **Template**: `yitp/index.html`

#### **Static Page Views**
- **about(request)**: `/about/` - About us page
- **courses(request)**: `/courses/` - Programs overview
- **team(request)**: `/team/` - Team information
- **contact(request)**: `/contact/` - Contact page with messaging

---

## 6. Email System Documentation

### **Email Configuration (blog/settings.py)**
```python
# SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'dedeexpeditions@gmail.com'
DEFAULT_FROM_EMAIL = 'YOUTH IMPACT GLOBAL <dedeexpeditions@gmail.com>'

# Admin Configuration
ADMIN_EMAIL = 'youthimpactglobal3@gmail.com'

# OTP Configuration
OTP_EXPIRY_MINUTES = 200
OTP_LENGTH = 6
```

### **Email Utilities (users/email_utils.py)**

#### **Core Functions**
- **`generate_otp(length=6)`**: Generates random numeric OTP
- **`send_html_email()`**: Sends HTML emails with plain text fallback
- **`send_otp_email(user, otp_code)`**: OTP verification emails
- **`send_welcome_email(user)`**: Welcome emails for new users
- **`send_login_notification(user, request)`**: Security login alerts
- **`send_sponsorship_confirmation_email()`**: Sponsorship confirmations

### **Email Templates**

#### **Base Template (templates/emails/base_email.html)**
- **Features**: Responsive design, YITP branding, mobile optimization
- **Styling**: Orange gradient header, professional layout
- **Components**: Header, content area, footer with contact info

#### **Email Types**
1. **OTP Verification** (`otp_verification.html/.txt`)
   - 6-digit verification code
   - Expiry information (200 minutes)
   - Security instructions

2. **Welcome Email** (`welcome.html/.txt`)
   - User greeting and platform introduction
   - Next steps and resources
   - Support contact information

3. **Login Notification** (`login_notification.html/.txt`)
   - Login time and IP address
   - Device/browser information
   - Security alert features

4. **Sponsorship Emails** (`sponsorship_*.html/.txt`)
   - Application confirmations
   - Status updates
   - Admin notifications

### **OTP Verification System**

#### **Workflow**
1. User registers with email address
2. System generates 6-digit OTP with 200-minute expiry
3. OTP email sent using HTML template
4. User enters OTP on verification page
5. System validates OTP and activates account
6. Welcome email sent upon successful verification

#### **Security Features**
- Single-use OTP codes
- Time-based expiration
- Previous OTP invalidation on new generation
- Rate limiting on resend requests

---

## 7. Setup & Installation

### **Local Development Setup**

#### **Prerequisites**
- Python 3.8+
- pip (Python package manager)
- Virtual environment tool

#### **Installation Steps**
```bash
# 1. Create project directory
mkdir yitp-project && cd yitp-project

# 2. Create virtual environment
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# 3. Clone repository
git clone <repository-url> .

# 4. Install dependencies
pip install -r requirements.txt

# 5. Database setup
python manage.py makemigrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver
```

#### **Environment Configuration**
The application uses SQLite for local development (configured in `blog/settings.py`).
For production deployment, PostgreSQL configuration is available but commented out.

### **Database Migrations**
```bash
# Generate migrations for all apps
python manage.py makemigrations users
python manage.py makemigrations blogapp
python manage.py makemigrations events

# Apply migrations
python manage.py migrate
```

---

## 8. Deployment

### **Production Configuration (Render)**

#### **Database Configuration**
- **Production**: PostgreSQL (Neon cloud database)
- **Environment Variables**: Configured in `render.yaml`
- **Connection**: SSL-enabled with connection pooling

#### **Email Configuration**
- **SMTP Provider**: Gmail
- **Credentials**: Environment variables in `render.yaml`
- **Security**: App-specific password authentication

#### **Static Files**
- **Handler**: WhiteNoise for static file serving
- **Collection**: Automated during build process
- **CDN**: Uploadcare for media files

#### **Build Process**
1. **Dependency Installation**: `pip install -r requirements.txt`
2. **Static Collection**: `python manage.py collectstatic`
3. **Database Migration**: `python manage.py migrate`
4. **Service Start**: `gunicorn blog.wsgi:application`

### **Environment Variables (render.yaml)**
```yaml
envVars:
  - key: DEBUG
    value: False
  - key: DATABASE_URL
    value: postgresql://...
  - key: EMAIL_HOST_USER
    value: dedeexpeditions@gmail.com
  - key: EMAIL_HOST_PASSWORD
    value: roqu frlt wvof rqxk
  - key: DEFAULT_FROM_EMAIL
    value: "YOUTH IMPACT GLOBAL"
```

---

## 📚 Additional Resources

### **Admin Interface**
- **URL**: `/admin/` (Django admin)
- **Enhanced**: `/jet/` (Django Jet interface)
- **Features**: Model management, user administration, content moderation

### **API Access**
- **GraphQL**: `/graphql/` (GraphiQL interface)
- **Features**: Query interface for advanced integrations

### **Testing**
- **Email System**: `test_email_system.py` - Comprehensive email testing
- **Coverage**: All email functions and OTP workflows

### **Documentation Files**
- **Business Documentation**: `YITP_Business_Documentation.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: `DEPLOYMENT_TROUBLESHOOTING.md`
- **Email System Summary**: `EMAIL_NOTIFICATION_SYSTEM_SUMMARY.md`

---

*This documentation provides a comprehensive technical overview of the YITP Django application. For specific implementation details, refer to the source code and additional documentation files.*
