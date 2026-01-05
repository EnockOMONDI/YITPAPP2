# YITP Django System Architecture A

> How the Youth Impact Training Programme (YITP) LMS is wired together. Every statement below is backed by the code in this repository.

## Table of Contents
1. [Overview](#overview)
2. [Runtime & Deployment](#runtime--deployment)
3. [Application & Service Inventory](#application--service-inventory)
4. [Cross-Cutting Capabilities](#cross-cutting-capabilities)
5. [Integrations & External Services](#integrations--external-services)
6. [Representative Data Flows](#representative-data-flows)
7. [Operational Considerations](#operational-considerations)

## Overview
- Monolithic Django 3.1.5 project (`blog/settings.py`) that powers the LMS, public marketing pages, payments, analytics, and communication tools.
- Local reusable apps live under the repository root (for example `users`, `courses`, `payments`, `analytics`). The Django project itself is named `blog` and exposes URLs via `blog/urls.py`.
- The system is designed for East African learners (default timezone is `Africa/Nairobi` and the payment stack includes Safaricom M-Pesa and bank transfers).
- Modernized admin is provided by the `unfold` UI plus `import_export`, `django_ckeditor_5`, `taggit`, `graphene_django`, `crispy_forms`, `corsheaders`, and Django REST Framework (all loaded in `INSTALLED_APPS`).

## Runtime & Deployment
### Environment detection
- `blog/settings.py` implements `detect_environment()` to switch between production (Render/Supabase) and development (local SQLite) based on `DJANGO_ENV`, hosting provider env vars, and CLI flags. The result toggles `DEBUG`, `ALLOWED_HOSTS`, and hardened security defaults (HSTS, SSL redirects, secure cookies, CSP headers).

### Databases
- Production: PostgreSQL connection pulled from `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` (see `blog/settings.py` + `render.yaml`). SSL is required when `IS_PRODUCTION` is true.
- Development: file-based SQLite database at `BASE_DIR / db.dev.sqlite3` populated from production snapshots (`blog/settings.py`).

### Static & media assets
- `WhiteNoise` handles static assets inside middleware (`whitenoise.middleware.WhiteNoiseMiddleware`).
- Static directories: `STATICFILES_DIRS` includes `BASE_DIR / 'static'`; collected files land in `staticfiles`. Media uploads resolve to `media/` (`blog/settings.py`).

### Logging & observability
- `LOGGING` in `blog/settings.py` ships structured logs to `logs/yitp.log` plus a dedicated payments log. Handlers are wired to Django core, `payments.*`, course enrollment, and certificate modules.
- Default admin email notifications use `ADMIN_EMAIL` from environment variables.

### Deployment footprint
- Render.com service definition (`render.yaml`) runs `build.sh` and launches `gunicorn blog.wsgi:application` on branch `2026mtesting` with networked PostgreSQL (Supabase). Secrets configured there include Mailtrap, PayPal Live keys, M-Pesa sandbox, TinyMCE API, and site metadata.
- Infrastructure-as-code toggles (for example `render_fallback.yaml` and `build_fallback.sh`) provide rollback paths.

## Application & Service Inventory
| Component | Responsibilities | Key References |
| --- | --- | --- |
| `users` | Registration, OTP verification, profiles, sponsorship workflow, instructor portals, custom dashboards, timezone detection, Mailtrap email hooks, magic-link auth | `users/models.py`, `users/views.py`, `users/otp_views.py`, `users/mailtrap_service.py`, `users/magic_link_views.py` |
| `yitp` | Marketing and landing pages (`home`, `documentation`, `about`, `team`), resume routing logic, FAQ content, welcome page | `yitp/views.py`, templates under `templates/yitp/` |
| `courses` | Course catalogs, categories, modules, lessons, trial access checks, TinyMCE-backed fields, instructor notifications | `courses/models.py`, `courses/trial_service.py`, `courses/views.py` |
| `progress` | Enrollments, lesson progress, quiz attempts, certificates, learning paths, achievements, gating of resume pointers | `progress/models.py`, `progress/views.py` |
| `assessments` | Quizzes, questions, assignments, rubrics, peer review, self assessments, grading policies | `assessments/models.py`, `assessments/views.py` |
| `course_builder` | Course templates, reusable content blocks, question banks, auto-save sessions for instructors | `course_builder/models.py`, `course_builder/views.py` |
| `content` | Content items, interactive exercises, downloadable resources, content libraries | `content/models.py`, `content/views.py` |
| `communication` | Messaging, inbox/sent views, forums, replies, feedback, announcements, notifications, study groups | `communication/models.py`, `communication/views.py` |
| `payments` | Payment methods, M-Pesa STK push, bank transfers, PayPal REST API orders, payment emails, manual verification | `payments/models.py`, `payments/payment_service.py`, `payments/paypal_service.py`, `payments/email_service.py`, `payments/views.py` |
| `certificates` | Public verification, download endpoints, PDF generation (ReportLab), integration with enrollment data | `certificates/views.py`, `certificates/certificate_service.py` |
| `analytics` | Payment analytics aggregates, user behavior, course revenue, staff dashboard & APIs | `analytics/models.py`, `analytics/services.py`, `analytics/views.py` |
| `blogapp` | Blog CMS (posts, categories, comments, static content) with Uploadcare-backed imagery | `blogapp/models.py`, `blogapp/views.py` |
| `events` | Event publishing (physical/online), tagging, validation, comments | `events/models.py`, `events/views.py` |

## Cross-Cutting Capabilities
### Authentication & identity
- Registration (`users/views.py::register`) creates inactive accounts, triggers OTP creation, and sends HTML emails via `users/mailtrap_service.MailtrapEmailService`.
- OTP management lives in `users/otp_views.py` and `users/models.OTPVerification`. OTP codes expire after `OTP_EXPIRY_MINUTES` (200 minutes default) and redundant OTPs are cleaned through management commands (`users/management/commands/send_verification_reminders.py`).
- Profiles (`users/models.Profile`) track payment status, installment progress, location metadata, gamification stats, and trial state. Signals update profile completeness.
- Sponsorship and scholarship requests (`users/models.SponsorshipRequest`) capture financial info, supporting docs, workflow statuses, and admin assignments.
- Magic link login and status pages are implemented in `users/magic_link_views.py` and `users/magic_link_utils.py`.
- Instructor user flows include creation helpers, secure temporary passwords, and audit logging (`users/email_utils.py`).

### Learning content & course delivery
- `courses` defines `Category`, `Course`, `Module`, `Lesson`, and tagging models. CKEditor 5 fields power descriptions and lesson bodies. Auto-review submissions send notifications through `users.email_utils` when instructors create courses.
- Trial access boundaries (e.g., first two lessons) are enforced via `courses/trial_service.TrialAccessService`, which queries enrollments from `progress`.
- The Course Builder app exposes instructor-friendly templates, reusable content blocks, question banks, and session persistence (`course_builder/models.py`).
- The `content` app manages reusable assets (text, video, audio, documents, interactive exercises, checklists) and their linkage to lessons through join tables such as `LessonContent` and `LessonResource`.

### Assessment & progress tracking
- `assessments` contains quizzes with attempt limits, randomized ordering, time limits, assignments with submission formats, peer review instructions, rubrics, self-assessments, grading scales, and template libraries.
- `progress` keeps canonical enrollment state, progress percentages, last accessed lesson pointers, lesson progress rows, quiz attempts (with feedback analytics), certificates, learning paths, and achievements. Enrollment methods automatically compute completion status, learning streaks, eligibility for certificates, and send emails when thresholds are met.
- Certificates are stored as `progress.models.Certificate` rows and surfaced through the `certificates` app. `certificates/certificate_service.py` generates PDFs via ReportLab (when available) or HTML and issues verification IDs. Public verification and downloads live in `certificates/views.py`.

### Communication & collaboration
- Direct messaging, inbox/sent/reply flows, and message read status are handled in `communication/views.py`.
- Discussion forums include forums, topics (with pin/lock flags, view/reply counts), replies (with threading and solution markers), announcements with priority levels, notifications with actionable URLs, and study groups (`communication/models.py`).
- Feedback entities cover lessons, assignments, quizzes, courses, and instructors, enabling instructor/peer/system reviews.

### Commerce & payments
- Payment methods, payment records, and installment relationships are defined in `payments/models.py`. Each payment automatically writes back into a learner profile (`Profile.confirm_payment`, `confirm_partial_payment`, `complete_installment_payment`).
- `payments/payment_service.py` centralizes creation of payment records, M-Pesa STK pushes (consumer key/secret/passkey configured via env vars), PayPal order creation/capture (REST API via `PayPalService`), manual verification, and installment orchestration.
- PayPal integration: `payments/paypal_service.py` exchanges tokens, creates orders, handles capture webhooks, and validates signatures (hooks wired in `payments/views.py` under `/payments/paypal/*`). Live credentials are defined in `render.yaml` and `blog/settings.py`.
- M-Pesa integration: callback URLs (`MPESA_CALLBACK_URL`, etc.) are derived from `SITE_URL` in `blog/settings.py`. Reference validation ensures format correctness and duplicate detection before manual verification.
- Bank transfer metadata (Absa account, paybill, SWIFT, WhatsApp verification number) is codified in `blog/settings.py`.
- Payment emails use `payments/email_service.py` which renders HTML templates and sends via the Mailtrap service wrapper.
- `blog/settings.py` exposes `AVAILABLE_PAYMENT_METHODS` to the front-end for building UI choices.

### Email & notification infrastructure
- Mailtrap HTTP API is the single delivery channel in production (`blog/settings.py` under "EMAIL CONFIGURATION" plus `users/mailtrap_service.py`). The SDK (`mailtrap.MailtrapClient`) is instantiated once and reused.
- Legacy compatibility helpers `send_html_email` and `send_template_email` delegate to the Mailtrap service so existing template code under `templates/emails/` still works.
- OTP, onboarding, instructor, payment, sponsorship, and certificate notifications are all consolidated inside `users/email_utils.py` and `payments/email_service.py`.
- The communication notification system (`communication.models.Notification`) tracks unread state, action URLs, and timestamps for in-app alerts.

### Analytics & reporting
- `analytics/models.py` stores daily payment aggregates, individual user payment behavior, and course-level revenue analytics with installment completion rates.
- `analytics/services.py` computes daily snapshots, revenue trends, payment method success rates, installment analytics, and exposes helper APIs consumed by staff dashboards.
- `analytics/views.py` serves multiple admin-only dashboards and JSON endpoints (revenue trends, payment methods, installments, user behavior, course revenue) which power interactive charts (`templates/analytics/*.html`).

### Public-facing experience
- `yitp/views.py` implements the marketing site, including a "smart resume" redirect that sends logged-in users back to their last lesson or to instructor dashboards depending on profile state.
- `blogapp` and `events` provide blog/article publishing and event management with tags, Uploadcare image handling, validation for online vs physical events, and comment systems.
- GraphQL endpoint (`/graphql/`) is wired through `GraphQLView` (see `blog/urls.py`) to expose schema data for downstream integrations.

## Integrations & External Services
- **Mailtrap**: Transactional email delivery via HTTP API (`MAILTRAP_API_TOKEN`, `DEFAULT_FROM_EMAIL`, SDK wrapper in `users/mailtrap_service.py`).
- **Safaricom M-Pesa**: STK push, callbacks, and query URLs assembled in `blog/settings.py`; API invocation lives in `payments/payment_service.py`.
- **PayPal**: Live REST credentials from environment variables (`render.yaml`) used by `payments/paypal_service.py` for access tokens, order creation, capture, and webhook verification.
- **Uploadcare**: Image fields in `blogapp` and `users` leverage `pyuploadcare` for asset handling.
- **TinyMCE / CKEditor 5**: Rich editor support for course builder, blog posts, and CMS sections via `TINYMCE_API_KEY` and `django_ckeditor_5` fields.
- **Graphene-Django**: GraphQL interface exposed at `/graphql/` for broader integrations.
- **WhiteNoise**: Static asset serving within Django middleware for Render deployments.

## Representative Data Flows
### 1. Onboarding & OTP verification
1. `users/views.register` persists a new inactive `User`, materializes a `Profile`, and invokes `users.email_utils.send_otp_email`.
2. `users/otp_views.generate_and_send_otp` invalidates previous codes, creates an `OTPVerification` row, and hands the message to Mailtrap.
3. Users confirm codes via `users/otp_views.verify_otp_view`, which marks the OTP as verified, activates the account, flips `Profile.email_verified`, and logs the action.
4. Reminder management commands (`send_verification_reminders`, `fix_admin_created_users`, `check_otp_consistency`) keep OTP data clean and reissue codes as needed.

### 2. Payment submission to enrollment activation
1. Learners initiate a payment from `templates/payments/payment_methods.html`, which posts into `payments/views.py` for M-Pesa, PayPal, or bank transfers.
2. `PaymentService.create_payment_record` writes the core record; downstream handlers branch to M-Pesa STK, PayPal order creation, or manual bank workflows.
3. Upon confirmation (`Payment.confirm_payment`), the linked `Profile` updates payment status and optionally installments. Enrollment logic (`progress.Enrollment`) can then mark status active/completed and send relevant course access emails.
4. Payment emails notify both the learner and admins via Mailtrap, and analytics services consume the payment signal during the next daily aggregation.

### 3. Certificate issuance & verification
1. When `progress.Enrollment.get_completion_status` detects 100% completion, it calls `users.email_utils.send_course_completion_email` and enables certificate generation.
2. `progress.Enrollment.generate_certificate` delegates to `certificates/certificate_service.py`, which produces a PDF (ReportLab) or HTML fallback, stores metadata on the `Certificate` row, and returns the file path.
3. Public visitors can verify certificates via `/certificates/verify/<code>/` (`certificates.views.CertificateVerificationView`). Downloads enforce ownership or admin rights and regenerate PDFs on demand if the stored file is missing.

### 4. Daily payment analytics refresh
1. Cron/management command triggers `analytics.services.PaymentAnalyticsService.generate_daily_analytics(date)`.
2. The service summarizes `payments.Payment` records by method, status, revenue, install installments, and user behavior, writes to `PaymentAnalytics`, and updates per-course revenue metadata.
3. Staff dashboards (`analytics.views.AnalyticsDashboardView`) pull these aggregates plus `PaymentMethodAnalyticsView` and API endpoints for visualizations.

## Operational Considerations
- **Configuration**: All sensitive values (secret key, database credentials, Mailtrap, PayPal, M-Pesa, TinyMCE, `ADMIN_EMAIL`, `SITE_URL`) are environment variables loaded through `python-decouple` with fallbacks (`blog/settings.py`).
- **Security**: Production enables HSTS, SSL redirects, secure cookies, clickjacking protection, and custom error pages (`blog/settings.py`). Trial access and magic links enforce strict token lifetimes.
- **Admin UX**: The Unfold admin theme (`unfold.*` apps) reorganizes links for blogs, courses, assessments, progress, and user management, with custom icons defined in `blog/settings.py`.
- **APIs**: Django REST Framework and Graphene-Django are installed, so the project can expose REST and GraphQL endpoints alongside HTML views. `/graphql/` is currently wired with GraphiQL enabled (`blog/urls.py`).
- **Background tasks**: While Celery/Redis are not used, repeat jobs run through Django management commands (e.g., OTP cleanup, analytics export, course PDF export under `courses/management/commands/export_module2_pdfs.py`).
- **Logging & auditing**: Payment, enrollment, instructor onboarding, and OTP flows log to dedicated files under `logs/`; `users/email_utils.log_instructor_account_creation` produces structured audit events.
- **Testing & local data**: Multiple SQLite snapshots (`db.dev.sqlite3`, `db_development.sqlite3`, `db_test.sqlite3`) are included for local experimentation. Automated tests live under `tests/` and `users/tests.py`.

This document reflects the exact behavior of the repository as of the current workspace state. Update it whenever code changes introduce new services, flows, or integrations.

## Project URLs
The primary routes are declared in `blog/urls.py` and the individual app `urls.py` modules. High-level entry points include:

- `admin/` – Django admin (extended via Unfold).
- `ckeditor5/` – Rich text uploader endpoints.
- `graphql/` – GraphQLView with GraphiQL enabled.
- `register/`, `login/`, `logout/` – Custom auth views defined in `users/views.py`.
- `profile/`, `profile/edit/`, `profile/request-data/`, `profile/request-deletion/`, `profile/lms/`, `profile/courses/`, `profile/analytics/`, `profile/billing/` – Unified learner dashboard sections.
- `sponsorship-request/`, `apply-for-sponsorship/` – Sponsorship workflows.
- `verify-otp/`, `resend-otp/`, `otp-status/` – OTP verification and status APIs.
- `status/` – System status page.
- `accounts/login/`, `accounts/logout/` – Django’s fallback auth views.
- `password_reset/`, `password_reset/done/`, `reset/<uidb64>/<token>/`, `reset/done/` – Password reset flow.
- Root includes to app routers:
  - `''` → `yitp.urls` (marketing site and home).
  - `users/` → `users.urls` (dashboards, instructor tools, APIs).
  - `blogs/` → `blogapp.urls`.
  - `events/` → `events.urls`.
  - `lms/courses/`, `lms/progress/`, `lms/assessments/`, `lms/communication/`, `lms/content/` → respective LMS apps.
  - `payments/` → payment initiation, callbacks, PayPal/M-Pesa webhooks.
  - `analytics/` → staff dashboards and JSON endpoints.
  - `course-builder/` → instructor builder flows.
  - `certificates/` → verification/download pages.
- `favicon.ico` – Redirect to the bundled site icon.
- Static/media routes are appended via `static(settings.MEDIA_URL, ...)` for media downloads when `DEBUG` is enabled.
