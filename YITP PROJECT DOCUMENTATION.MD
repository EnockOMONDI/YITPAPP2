# YITP Project Documentation

> Documentation for the Youth Impact Training Programme (YITP) platform. Secrets and live credentials are intentionally excluded.

## Table of Contents
1. [Overview](#overview)
2. [Runtime & Deployment](#runtime--deployment)
3. [Application & Service Inventory](#application--service-inventory)
4. [Cross-Cutting Capabilities](#cross-cutting-capabilities)
5. [Integrations & External Services](#integrations--external-services)
6. [Representative Data Flows](#representative-data-flows)
7. [Operational Considerations](#operational-considerations)
8. [Sample Environment](#sample-environment)

## Overview
- Monolithic Django project that powers the public marketing site, LMS, payments, analytics, instructor tooling, and communication features.
- The Django project package is `blog`; domain apps live at the repository root, including `users`, `courses`, `progress`, `assessments`, `payments`, `analytics`, `communication`, `content`, `certificates`, `blogapp`, `events`, `yitp`, and `course_builder`.
- The platform is tuned for East African delivery: default timezone is `Africa/Nairobi`, M-Pesa is supported, and payment/course flows assume a learner-facing LMS plus internal operational dashboards.
- The admin layer is enhanced with `unfold`, alongside `django_ckeditor_5`, `import_export`, `taggit`, `graphene_django`, `crispy_forms`, `corsheaders`, and Django REST Framework.

## Runtime & Deployment
### Environment detection
- `blog/settings.py` uses `detect_environment()` to determine production vs development from `DJANGO_ENV`, hosting env vars, CLI context, and `DEBUG`.
- Environment selection controls `DEBUG`, `ALLOWED_HOSTS`, cookie security, SSL redirect, HSTS, and custom error page behavior.

### Databases
- Production uses PostgreSQL via `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`.
- The configured connection enforces SSL and a connection timeout.
- The current settings file also uses PostgreSQL in development/local mode when those env vars are present.

### Static and media
- Static files are served through WhiteNoise middleware.
- `STATICFILES_DIRS` points at `static/`; collected assets go to `staticfiles/`.
- Uploaded media lands in `media/`.

### Application startup
- Entry point for management commands is `manage.py`.
- Runtime server entry point is `blog.wsgi:application`.
- ASGI support also exists via `blog/asgi.py`, although the Render start command uses Gunicorn with WSGI.

### Deployment footprint
- Render deployment is defined in `render.yaml`.
- Build flow runs `build.sh`, installs dependencies, runs Django checks, collects static assets, and applies migrations.
- A fallback path exists via `render_fallback.yaml` and `build_fallback.sh`.

### Logging and observability
- `blog/settings.py` defines structured logging with file-based handlers under `logs/`.
- Payment, enrollment, certificate, and general Django logging are configured separately.
- `users/views.py` also exposes system-status-style diagnostics and deployment metadata views for admin use.

## Application & Service Inventory
| Component | Responsibilities | Key References |
| --- | --- | --- |
| `users` | Registration, login, OTP verification, profile management, sponsorship workflows, instructor dashboards, magic link auth, timezone handling, email utilities | `users/models.py`, `users/views.py`, `users/otp_views.py`, `users/auth_views.py`, `users/magic_link_views.py`, `users/email_utils.py` |
| `yitp` | Public marketing site, landing pages, support pages, smart redirect middleware, welcome flow | `yitp/views.py`, `yitp/middleware.py`, `yitp/urls.py` |
| `blogapp` | Blog posts, categories, comments, static content, admin import/export | `blogapp/models.py`, `blogapp/views.py`, `blogapp/resources.py` |
| `events` | Event publishing, event categories, comments, seeding command | `events/models.py`, `events/views.py` |
| `courses` | Course catalog, modules, lessons, course detail pages, enrollments, trial access, course exports | `courses/models.py`, `courses/views.py`, `courses/enrollment_service.py`, `courses/trial_service.py` |
| `progress` | Enrollment state, lesson progress, quiz attempts, certificates, achievements, study sessions, learning paths | `progress/models.py`, `progress/views.py`, `progress/services.py` |
| `assessments` | Quizzes, questions, assignments, rubrics, self-assessment, peer review, grading logic | `assessments/models.py`, `assessments/views.py`, `assessments/services.py` |
| `communication` | Inbox, messaging, forums, topics, replies, announcements, notifications, study groups | `communication/models.py`, `communication/views.py` |
| `content` | Reusable content items, resources, exercises, content libraries, lesson-linked resources | `content/models.py`, `content/views.py` |
| `payments` | Payment records, M-Pesa, PayPal, bank transfer processing, callbacks, payment emails, installment workflows | `payments/models.py`, `payments/views.py`, `payments/payment_service.py`, `payments/paypal_service.py`, `payments/email_service.py` |
| `certificates` | Certificate verification, download, certificate detail pages, PDF generation integration | `certificates/views.py`, `certificates/certificate_service.py` |
| `analytics` | Payment analytics, user payment behavior, course revenue analytics, dashboard APIs | `analytics/models.py`, `analytics/views.py`, `analytics/services.py` |
| `course_builder` | Instructor-facing course builder, templates, reusable content blocks, question bank, autosave sessions | `course_builder/models.py`, `course_builder/views.py` |

## Cross-Cutting Capabilities
### Authentication and identity
- Registration and login logic is custom and lives mainly in `users/views.py`.
- OTP verification is implemented in `users/otp_views.py` using `users.models.OTPVerification`.
- `users.models.Profile` is the central extension model for Django `User` and stores payment state, profile completion, location, verification state, gamification state, and trial state.
- Magic link login is handled through `users/magic_link_utils.py` and `users/magic_link_views.py`.
- Instructor roles and permissions are driven by `users.models.InstructorProfile` plus `users/signals.py`.

### Middleware and redirect behavior
- `yitp/middleware.py` contains:
- `SmartRedirectMiddleware` for resume-style navigation after login.
- `CourseDiscoveryRedirectMiddleware` for course-related routing behavior.
- `WelcomePageRedirectMiddleware` for onboarding/welcome control.
- `UnifiedNavigationMiddleware` for template-level navigation context.

### Signals
- `users/signals.py` auto-creates profiles for new users, makes datetimes timezone-aware, and assigns instructor permissions/staff access.
- `yitp/signals.py` sets a session flag on successful login so middleware can redirect users intelligently.

### Learning delivery
- `courses` defines the main learning hierarchy: category -> course -> module -> lesson.
- `progress` stores canonical learner state for enrollments and completed work.
- `assessments` stores quizzes and assignments but depends on `progress` for attempt and completion state.
- `content` acts as a reusable library for learning assets and lesson-linked resources.

### Commerce and access control
- Payment flows are split across form-handling views, a central `PaymentService`, and provider-specific helper services.
- Payment confirmation can unlock or maintain learner access via profile state and enrollment logic.
- Trial access logic is isolated in `courses/trial_service.py`.

### Certificates
- Certificate eligibility is derived from enrollment completion state.
- Certificate generation is handled by `certificates/certificate_service.py` using ReportLab when available, with fallback behavior when not.
- Public verification is exposed by verification code through the `certificates` app.

### Analytics
- `analytics` computes daily payment summaries and longer-term behavior metrics.
- The system stores both aggregate snapshots and per-user/per-course analytics records.

## Integrations & External Services
- **Render**: deployment target using `render.yaml`.
- **PostgreSQL**: primary database in hosted environments.
- **Mailtrap**: transactional email delivery through HTTP API wrappers in `users/mailtrap_service.py`.
- **Safaricom M-Pesa**: STK push and callback flow configured in settings and executed in `payments/payment_service.py`.
- **PayPal**: order creation, return/cancel handling, capture processing, and webhook handling via `payments/paypal_service.py` and `payments/views.py`.
- **Uploadcare**: asset upload/storage integration referenced in settings and image-backed models.
- **CKEditor 5**: rich content editor for lessons and content management.
- **Graphene-Django**: GraphQL endpoint exposed at `/graphql/`.
- **WhiteNoise**: static file serving in deployed environments.

## Representative Data Flows
### 1. Registration and OTP verification
1. User submits registration form handled in `users/views.py`.
2. A Django `User` plus linked `Profile` is created.
3. OTP generation and dispatch occur through `users/otp_views.py` and email utilities.
4. Verification endpoint confirms the code, activates the user, and marks the profile as email-verified.

### 2. Enrollment and course participation
1. Learner browses courses through `courses/views.py`.
2. Enrollment is created either directly or as part of a confirmed payment flow.
3. Lesson access and progression are tracked in `progress.models.LessonProgress`.
4. Quiz access and outcomes update `QuizAttempt`, lesson completion, and enrollment progress percentages.

### 3. Payment processing
1. Learner selects a payment option from the payments UI.
2. `payments/views.py` validates the request and calls `PaymentService`.
3. Provider-specific logic runs for M-Pesa, PayPal, or bank transfer.
4. On successful confirmation, payment records are updated and downstream access/payment status can be unlocked or extended.

### 4. Certificate issuance
1. Enrollment reaches completion state in `progress`.
2. Certificate generation is delegated to `CertificateService`.
3. A verification code and certificate metadata are stored.
4. Public verification and authenticated access happen through `certificates/views.py`.

### 5. Analytics refresh
1. Management command `generate_analytics` triggers analytics services.
2. Payment data is aggregated into daily analytics tables.
3. User behavior and course revenue analytics can be updated in the same run.
4. Dashboard/API views expose these records to staff-facing templates and JSON consumers.

## Operational Considerations
- Sensitive configuration should only be supplied through environment variables.
- The repository currently contains deployment files that reference real-looking values; those should be treated as compromised if they are active anywhere and rotated outside the codebase.
- Recurring operational work is implemented through Django management commands rather than Celery or another queue.
- Important commands exist for OTP cleanup, payment expiry, installment processing, reminder emails, analytics generation, quiz progress repair, content export, and seed data creation.
- The codebase is tightly coupled across apps. `users`, `progress`, `courses`, `assessments`, and `payments` import from each other heavily, so changes should be tested end-to-end rather than in isolation.
- The admin interface is customized with Unfold and role-driven permissions, so role testing matters during handover.

## Sample Environment
The following is a redacted example only. It is not the live environment.

```env
DJANGO_ENV=production
DEBUG=False
SECRET_KEY=change_me
ALLOWED_HOSTS=example.com,www.example.com

DB_NAME=app_db
DB_USER=app_user
DB_PASSWORD=app_password
DB_HOST=db.example.com
DB_PORT=5432

SITE_URL=https://example.com
ADMIN_EMAIL=admin@example.com
DEFAULT_FROM_EMAIL=noreply@example.com

MAILTRAP_API_TOKEN=mailtrap_api_token

MPESA_CONSUMER_KEY=mpesa_consumer_key
MPESA_CONSUMER_SECRET=mpesa_consumer_secret
MPESA_SHORTCODE=mpesa_shortcode
MPESA_PASSKEY=mpesa_passkey
MPESA_ENVIRONMENT=sandbox

PAYPAL_CLIENT_ID=paypal_client_id
PAYPAL_CLIENT_SECRET=paypal_client_secret
PAYPAL_MODE=sandbox
PAYPAL_WEBHOOK_ID=paypal_webhook_id

TINYMCE_API_KEY=tinymce_api_key
UPLOADCARE_PUBLIC_KEY=uploadcare_public_key
UPLOADCARE_SECRET_KEY=uploadcare_secret_key
```

## Project URLs
- `admin/` - Django admin.
- `ckeditor5/` - editor upload endpoints.
- `graphql/` - GraphQL endpoint with GraphiQL enabled in current wiring.
- `register/`, `login/`, `logout/` - custom authentication endpoints.
- `profile/` and related section routes - unified user profile/dashboard.
- `users/` - instructor tools, dashboards, magic link endpoints, timezone endpoints, superuser tooling.
- `blogs/` - blog pages.
- `events/` - event pages.
- `lms/courses/`, `lms/progress/`, `lms/assessments/`, `lms/communication/`, `lms/content/` - LMS subsystems.
- `payments/` - payment methods, processing, callbacks, webhooks.
- `analytics/` - analytics dashboards and APIs.
- `course-builder/` - instructor course builder.
- `certificates/` - certificate verification, detail, and download pages.

This document is based on the current repository state and should be refreshed whenever architecture, integrations, or operational jobs change.
