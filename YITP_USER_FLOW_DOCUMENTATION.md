# YITP User Flow Documentation

## Overview
This document provides a comprehensive analysis of the Youth Impact Training Programme (YITP) Django application user flows, covering the complete user journey from registration through course completion and sponsorship processes.

## 1. Authentication Flow

### 1.1 User Registration Process

**Entry Point**: `{% url 'yitp:registration' %}` (templates/yitp/registration.html)

**Step-by-Step Process**:
1. **User Access**: User navigates to registration page via YITP navigation
2. **Form Submission**: User fills registration form (handled by `users.views.register`)
3. **Account Creation**: 
   - User model created with `is_active=False`
   - Profile model auto-created via Django signals (`users.signals.py`)
   - Password validation and email validation performed

4. **OTP Generation & Email**:
   - `users.otp_views.send_otp_for_registration()` called
   - 6-digit OTP generated via `users.email_utils.generate_otp()`
   - OTPVerification model record created with 200-minute expiry
   - OTP email sent using template `templates/emails/otp_verification.html`

5. **Redirect**: User redirected to `/verify-otp/?user_id={user.id}`

**Database Models Involved**:
- `User` (Django auth model)
- `users.models.Profile` (auto-created)
- `users.models.OTPVerification`

**Email Templates**:
- `templates/emails/otp_verification.html` (HTML)
- `templates/emails/otp_verification.txt` (plain text)

### 1.2 OTP Verification Workflow

**Entry Point**: `/verify-otp/` (handled by `users.otp_views.verify_otp_view`)

**Step-by-Step Process**:
1. **OTP Entry**: User enters 6-digit code from email
2. **Verification Logic**:
   - OTP validated against database (not expired, not used)
   - OTP marked as `is_used=True` and `is_verified=True`
   - User account activated (`is_active=True`)

3. **Welcome Email**: `users.email_utils.send_welcome_email()` triggered
4. **Redirect**: User redirected to login page with success message

**Conditional Paths**:
- **Invalid/Expired OTP**: Error message, stay on verification page
- **Resend OTP**: AJAX endpoint `/resend-otp/` generates new OTP

**Email Templates**:
- `templates/emails/welcome.html` (comprehensive welcome email)
- `templates/emails/welcome.txt` (plain text version)

### 1.3 Login/Logout Functionality

**Login Process** (`users.views.login`):
1. **Authentication**: Django's `authenticate()` function
2. **Login Notification**: `users.email_utils.send_login_notification()` 
   - Captures IP address, user agent, timestamp
   - Sends security notification email
3. **Redirect**: User redirected to `yitp:home`

**Logout Process** (`users.views.logout`):
- Session cleared via `auth.logout()`
- Redirect to `registration/logged_out.html`

**Email Templates**:
- `templates/emails/login_notification.html`
- `templates/emails/login_notification.txt`

### 1.4 Password Reset Process

**Note**: Currently uses Django's built-in password reset system (not custom implementation found in codebase analysis).

## 2. User Onboarding & Profile Management

### 2.1 Initial Profile Setup

**Profile Model** (`users.models.Profile`):
```python
- user (OneToOneField to User)
- image (ImageField, default='default.jpg')
- bio (TextField, default='Edit your Bio!')
- phone_number (CharField, optional)
```

**Auto-Creation**: Profile automatically created via Django signals when User is created

### 2.2 Profile Management

**Entry Point**: `/profile/` (handled by `users.views.profile`)

**Features**:
- View/edit profile information
- Upload profile image
- Update bio and contact information
- View sponsorship request history

**Template**: Profile view integrated with sponsorship request functionality

## 3. Sponsorship Request Process

### 3.1 Sponsorship Request Submission

**Entry Point**: `/profile/` (POST request with sponsorship form)

**Step-by-Step Process**:
1. **Form Validation**: `users.forms.SponsorshipRequestForm` validation
   - Program selection (with "Other" option)
   - Amount needed (minimum $1)
   - Financial situation assessment
   - Detailed explanation (minimum 100 characters)
   - Emergency contact information
   - Optional supporting documents

2. **Database Creation**: `users.models.SponsorshipRequest` record created
   - Status: 'pending'
   - Timestamps: created_at, updated_at
   - User association

3. **Email Notifications**:
   - **User Confirmation**: `users.email_utils.send_sponsorship_confirmation_email()`
   - **Admin Notification**: `users.email_utils.send_sponsorship_admin_notification()`

**Database Model** (`users.models.SponsorshipRequest`):
```python
- user (ForeignKey to User)
- program (CharField with choices)
- amount_needed (DecimalField)
- financial_situation (CharField with choices)
- reason (TextField)
- status (CharField: pending/under_review/approved/rejected)
- supporting_document (FileField, optional)
- emergency_contact_* (name, phone, email, relationship)
- admin_notes (TextField, for internal use)
- created_at, updated_at (DateTimeFields)
```

### 3.2 Admin Review Workflow

**Admin Interface**: Django admin panel for SponsorshipRequest model

**Status Update Process**:
1. **Admin Action**: Status changed in admin panel
2. **Email Trigger**: `users.email_utils.send_sponsorship_status_update_email()`
3. **User Notification**: Email sent based on new status

**Status Flow**:
- `pending` → `under_review` → `approved`/`rejected`

**Email Templates**:
- `templates/emails/sponsorship_confirmation.html`
- `templates/emails/sponsorship_admin_notification.html`
- `templates/emails/sponsorship_status_update.html`

### 3.3 User Dashboard Updates

**Profile Page Integration**:
- Display all user's sponsorship requests
- Show current status of each request
- Order by creation date (most recent first)

## 4. Course Enrollment & Learning Management

### 4.1 Course Discovery and Browsing

**Entry Points**:
- `/lms/courses/` - Course listing (`courses.views.CourseListView`)
- `/lms/courses/dashboard/` - Student dashboard (`courses.views.DashboardView`)

**Course Listing Features**:
- Filter by category (`courses.models.Category`)
- Filter by difficulty level (beginner/intermediate/advanced)
- Search functionality
- Pagination (12 courses per page)

**Course Model** (`courses.models.Course`):
```python
- title, slug, description
- learning_objectives, prerequisites
- difficulty_level, estimated_duration
- instructor (ForeignKey to User)
- category (ForeignKey to Category)
- is_published, is_featured
- enrollment_limit, price
- thumbnail (ImageField)
```

### 4.2 Course Enrollment Process

**Entry Point**: `/lms/courses/<slug>/enroll/` (POST request)

**Step-by-Step Process**:
1. **Authentication Check**: `LoginRequiredMixin` ensures user is logged in
2. **Course Validation**: Verify course exists and is published
3. **Enrollment Creation**: `progress.models.Enrollment` record created
   - Status: 'active'
   - Progress percentage: 0.00
   - Enrollment date: current timestamp

4. **Duplicate Check**: Prevents multiple enrollments in same course
5. **Redirect**: Back to course detail page with success message

**Database Model** (`progress.models.Enrollment`):
```python
- student (ForeignKey to User)
- course (ForeignKey to Course)
- enrollment_date (DateTimeField)
- completion_date (DateTimeField, nullable)
- status (CharField: active/completed/dropped/suspended)
- progress_percentage (DecimalField)
- last_accessed (DateTimeField)
- certificate_issued (BooleanField)
```

### 4.3 Course Structure Navigation

**Hierarchical Structure**:
1. **Course** → **Modules** → **Lessons**
2. **Module Model** (`courses.models.Module`):
   - Course organization units
   - Sort order for sequential learning
   - Unlock criteria (JSON field)

3. **Lesson Model** (`courses.models.Lesson`):
   - Individual learning units
   - Content types: text, video, presentation, exercise, quiz, assignment
   - Estimated duration, learning objectives

**URL Patterns**:
- `/lms/courses/<slug>/` - Course detail
- `/lms/courses/<slug>/modules/<id>/` - Module detail
- `/lms/courses/<slug>/lessons/<id>/` - Lesson detail

### 4.4 Progress Tracking

**Progress Models** (`progress.models`):

1. **LessonProgress**:
   - Tracks individual lesson completion
   - Status: not_started/in_progress/completed
   - Time spent, attempts, score
   - Methods: `mark_started()`, `mark_completed()`, `add_time_spent()`

2. **StudySession**:
   - Tracks individual study sessions
   - Duration tracking, activities performed
   - Links to specific lessons and courses

**Progress Calculation**:
- Enrollment progress updated automatically when lessons completed
- Formula: (completed_lessons / total_lessons) * 100

### 4.5 Assessment System

**Quiz System** (`assessments.models.Quiz`):

**Quiz Taking Process**:
1. **Access**: `/lms/assessments/quizzes/<id>/take/`
2. **Attempt Creation**: `progress.models.QuizAttempt` record
3. **Answer Processing**: JSON field stores user answers
4. **Score Calculation**: Automatic scoring based on correct answers
5. **Results**: Pass/fail determination based on passing score

**Assignment System** (`assessments.models.Assignment`):

**Assignment Submission Process**:
1. **Access**: `/lms/assessments/assignments/<id>/submit/`
2. **Submission**: `progress.models.AssignmentSubmission` record
3. **File Upload**: Support for various file types
4. **Grading**: Manual grading by instructors
5. **Feedback**: Text feedback and score assignment

**Self-Assessment Tools** (`assessments.models.SelfAssessment`):
- Personal initiative, innovation, goal setting assessments
- JSON-based question and scoring system
- Student self-evaluation tools

### 4.6 Achievement System

**Learning Paths** (`progress.models.LearningPath`):
- Personalized course sequences
- Many-to-many relationship with courses
- Progress tracking across multiple courses

**Certificates**:
- `certificate_issued` field in Enrollment model
- Triggered upon course completion

## 5. Communication Features

### 5.1 Messaging System

**Private Messages** (`communication.models.Message`):

**Message Flow**:
1. **Compose**: `/lms/communication/compose/`
2. **Send**: Creates Message record with sender/recipient
3. **Inbox**: `/lms/communication/inbox/` - view received messages
4. **Read Tracking**: `mark_as_read()` method updates timestamps

**Features**:
- Thread support (parent_message field)
- Archive functionality
- Read/unread status tracking

### 5.2 Forum System

**Forum Structure** (`communication.models`):
- **Topic**: Discussion topics
- **Reply**: Responses to topics
- **Category-based organization**

**Forum Flow**:
1. **Topic Creation**: Users create discussion topics
2. **Replies**: Other users respond to topics
3. **Activity Tracking**: Last activity timestamps
4. **Moderation**: Admin oversight capabilities

### 5.3 Notification System

**Notification Types** (`communication.models.Notification`):
- Course enrollment, assignment due, quiz available
- Grade posted, forum reply, message received
- Achievement earned, announcements

**Notification Flow**:
1. **Trigger**: System events generate notifications
2. **Delivery**: In-app notification creation
3. **Read Tracking**: User interaction tracking
4. **Action URLs**: Direct links to relevant content

### 5.4 Announcements

**Announcement System** (`communication.models.Announcement`):
- **Priority-based display**
- **Publication scheduling**
- **Expiration dates**
- **Target audience selection**

## 6. Content Management

### 6.1 Content Structure

**Content Types** (`content.models.ContentItem`):
- Text, video, audio, presentation, document
- Interactive content, images, infographics
- File uploads and external URL support

**Content Organization**:
- **Libraries** (`content.models.ContentLibrary`): Organized collections
- **Lesson Integration** (`content.models.LessonContent`): Link content to lessons
- **Resource Management** (`content.models.Resource`): Downloadable resources

### 6.2 Interactive Exercises

**Exercise System** (`content.models.InteractiveExercise`):
- **Types**: Drag-and-drop, matching, simulation, case study
- **Grading**: Optional scoring system
- **Time Limits**: Configurable time constraints
- **JSON Data**: Flexible exercise structure

## 7. Email Workflow Integration

### 7.1 Email System Architecture

**Email Utility Functions** (`users.email_utils.py`):
- `send_html_email()`: Base HTML email function
- Template-based email generation
- Plain text fallbacks
- Error handling and logging

### 7.2 Email Triggers Throughout User Journey

**Registration Flow**:
1. OTP verification email (immediate)
2. Welcome email (after verification)

**Authentication Flow**:
1. Login notification email (each login)
2. Password reset emails (Django built-in)

**Sponsorship Flow**:
1. Confirmation email (immediate submission)
2. Admin notification email (immediate)
3. Status update emails (admin actions)

**Learning Flow**:
1. Enrollment confirmations
2. Assignment due reminders
3. Grade notifications
4. Achievement notifications

### 7.3 SMTP Configuration

**Settings** (`blog.settings.py`):
- Gmail SMTP configuration
- Credentials: dedeexpeditions@gmail.com
- App password authentication
- Production deployment via render.yaml

## 8. Administrative Workflows

### 8.1 User Management

**Admin Capabilities**:
- User account management
- Profile oversight
- Enrollment tracking
- Progress monitoring

### 8.2 Sponsorship Management

**Admin Process**:
1. **Review**: Access sponsorship requests in admin panel
2. **Evaluation**: Review supporting documents and details
3. **Decision**: Update status (approve/reject)
4. **Communication**: Add admin notes
5. **Notification**: Automatic email to applicant

### 8.3 Content Management

**Admin Functions**:
- Course creation and management
- Content upload and organization
- Assessment creation
- User progress oversight

### 8.4 Bulk Operations

**Available Operations**:
- User imports/exports
- Enrollment management
- Grade assignments
- Communication broadcasts

## Technical Implementation Summary

**Key URL Patterns**:
- Authentication: `/register/`, `/login/`, `/verify-otp/`
- Profile: `/profile/`
- LMS: `/lms/courses/`, `/lms/progress/`, `/lms/assessments/`
- Communication: `/lms/communication/`
- Content: `/lms/content/`

**Database Integration**:
- 15+ models across 6 Django apps
- Complex relationships between users, courses, and progress
- JSON fields for flexible data storage
- Automatic timestamp tracking

**Email System**:
- 8 distinct email templates
- HTML and plain text versions
- Comprehensive notification system
- Production-ready SMTP configuration

This documentation provides the complete technical foundation for understanding and extending the YITP user experience across all major workflows.
