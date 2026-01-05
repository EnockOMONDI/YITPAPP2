# YITP Developer Guide

Interview-ready documentation for the Youth Impact Training Platform (YITP) Django monolith. Use this as a single source of truth when you're walking someone through the system or investigating production behaviour.

---

## Project Summary & Goals (Elevator Pitch)
- **Mission**: deliver cohort-based leadership and innovation training for African youth through a blended LMS + marketing site.
- **Objective**: provide a frictionless path from landing page → registration/OTP verification → self-serve payments (M-Pesa, bank transfer, PayPal) → trial/paid enrollment → content delivery, feedback, certificates, and analytics.
- **Approach**: modular Django apps (yitp , LMS, payments, analytics) sharing a Postgres database, with async-like automation implemented via management commands and service layers.

## Architecture & Motivations
- **Monolith with clear domains**: `blog` project + per-domain Django apps keep deployment simple on Render while letting teams work in parallel.
- **Service classes + middleware**: cross-cutting logic (trial access, enrollment, payment orchestration, smart redirects) lives in reusable services/middleware (`courses/enrollment_service.py`, `courses/trial_service.py`, `yitp/middleware.py`).
- **Rich templating**: public marketing pages in `templates/yitp`, LMS dashboards under `templates/lms`, shared nav/components in `templates/includes`.
- **Async-by-command**: scheduled jobs implemented as `management/commands` (analytics generation, verification reminders, payment follow-ups) to avoid Celery operational overhead on Render.
- **Observability-first**: extensive logging (`logs/`, `core/error_handling.py`), admin dashboards, and analytics service to monitor conversions without external APM yet.

## Repository Layout & Application Map

### Root Structure
| Path | Notes |
| --- | --- |
| `blog/` | Django project config (`settings.py`, `urls.py`, `wsgi.py`). |
| `yitp/` | Public site views, middleware, lightweight models. |
| `users/` | Auth, profiles, OTP, magic links, instructor tooling, emails. |
| `courses/`, `progress/`, `assessments/` | Core LMS domain: catalog + progress tracking + assessments. |
| `communication/`, `content/`, `course_builder/` | Engagement, content libraries, instructor builder wizard. |
| `payments/`, `analytics/`, `certificates/` | Commerce stack, insights, certificate generation services. |
| `blogapp/`, `events/` | Editorial content and events microsite. |
| `static/`, `templates/`, `media/`, `logs/` | Frontend assets, Django templates, uploaded media, log output. |
| `docs/` | Deep-dive Markdown guides (security, OTP, translations, etc.). |
| `tests/` | High-level regression suite + smoke-test runners. |
| `render.yaml`, `build.sh` | Render deployment definition & build pipeline. |

### App-by-app Snapshot
| App | Purpose | Key Files |
| --- | --- | --- |
| `yitp` | Marketing home, SEO pages, navigation middleware. | `yitp/views.py`, `yitp/middleware.py`, `templates/yitp/*.html`. |
| `users` | Registration, profiles, OTP, magic links, instructor dashboards, CSV exports. | `users/models.py`, `users/views.py`, `users/instructor_views.py`, `users/mailtrap_service.py`. |
| `courses` | Catalog (categories, courses, modules, lessons), enrollment & trials. | `courses/models.py`, `courses/views.py`, `courses/enrollment_service.py`, `courses/trial_service.py`. |
| `progress` | Enrollment status, lesson progress, achievements, certificates. | `progress/models.py`, `progress/views.py`. |
| `assessments` | Quizzes, assignments, peer/self reviews. | `assessments/models.py`, `assessments/views.py`. |
| `communication` | Messaging, forums, notifications, study groups. | `communication/models.py`, `communication/views.py`. |
| `content` | Content library, reusable lesson resources, exercises. | `content/models.py`, `content/views.py`. |
| `payments` | M-Pesa, bank, PayPal intake; payment service + email notifications. | `payments/models.py`, `payments/payment_service.py`, `payments/email_service.py`, `payments/views.py`. |
| `analytics` | Aggregated payment + revenue insights, dashboards, services. | `analytics/models.py`, `analytics/services.py`, `analytics/views.py`. |
| `course_builder` | Instructor-friendly wizard, templates, media library. | `course_builder/models.py`, `course_builder/views.py`. |
| `certificates` | Verification & download endpoints for generated certificates. | `certificates/certificate_service.py`, `certificates/views.py`. |
| `blogapp` & `events` | Marketing content verticals. | `blogapp/models.py`, `blogapp/views.py`, `events/models.py`. |

## URL Map (Per App)

| App | Representative Routes | Notes |
| --- | --- | --- |
| `yitp` | `/`, `/about/`, `/team/`, `/welcome/`, `/faqs/`, `/web_courses_list/`, `/translation-demo/`, `/sitemap.xml`, `/robots.txt`. | Landing + SEO + translation demos with middleware that reroutes authenticated users. |
| `users` | `/users/...` (`instructor/`, `content/`, `magic-login/<token>/`, `superuser/export/...`, timezone endpoints). | Unified profile dashboards, exports, magic-link auth, admin tooling. |
| `courses` | `/lms/courses/`, `/lms/courses/<slug>/`, `/enroll/`, `/modules/<id>/`, `/lessons/<id>/`, `/my-courses/`, `/trial/*`. | Class-based views for catalog + lesson detail + trial conversion. |
| `progress` | `/lms/progress/` dashboard, `/course/<id>/progress/`, `/achievements/`, `/api/update-lesson-progress/`. | Student progress UI + AJAX endpoints. |
| `assessments` | `/lms/assessments/quizzes/…`, `/assignments/…`, `/quiz-success/<attempt>/`. | Quiz/assignment flow. |
| `communication` | `/lms/communication/inbox/`, `/forums/`, `/notifications/`, API endpoints for messaging/unread counts. |
| `content` | `/lms/content/library/`, `/resources/`, `/exercises/`, `/search/`. | Content management for instructors. |
| `payments` | `/payments/methods/<course_id>/`, `/process/mpesa|paypal|bank-transfer/`, `/status/<payment_id>/`, `/paypal/*`, `/mpesa/*`. | Payment intake, callbacks, status pages. |
| `analytics` | `/analytics/`, `/payment-methods/`, `/course-revenue/`, `api/*` for trends & reports. |
| `course_builder` | `/course-builder/`, `/wizard/step/<n>/`, `/api/`, `/media/upload/`, `/template/<id>/`. |
| `certificates` | `/certificates/verify/<code>/`, `/download/<code>/`, `/my-certificates/`. |
| `events` | `/events/`, `/events/<id>/`. |
| `blogapp` | `/blogs/`, `/blogs/category/<slug>/`, `/blogs/<pid>`. |

> Tip: Django namespaces match app names (e.g., `reverse('courses:lesson_detail', ...)`) which keeps templates maintainable.

## Templates & Static Assets
- Marketing templates under `templates/yitp/`, LMS layouts under `templates/lms/…`, email templates in `templates/emails/`, and shared nav + modals in `templates/includes/`.
- Static assets live in `static/` with subfolders for marketing images (`static/assets/img/*`), LMS bundles (`static/lmsassets`), vendor JS (`static/js/vendor`), and custom scripts such as `static/js/yitp-translate-basic.js`.
- WhiteNoise serves assets; `build.sh` runs `collectstatic --clear` before deploy to populate `staticfiles/`.
- Rich text editing uses `django_ckeditor_5` and Uploadcare (`UPLOADCARE_*` env vars) for media in course content.

## Models & Data Design Rationale

### People, Identity & Access (`users/models.py`)
- `Profile` extends Django `User` with payment status, installment tracking, geo metadata, and trial fields (`trial_status`, `trial_course`, `has_any_payment_access`). These flags gate enrollments and conversions without extra joins.
- `OTPVerification`, `MagicLinkToken`, and `SponsorshipRequest` capture verification flows and scholarship applications; `ShortUUIDField` + hashed tokens avoid leaking secrets if DB snapshots are shared.
- `InstructorProfile`, `CourseInstructor`, and `Specialization` encode instructor onboarding, permissions, and disciplines so the LMS can display curated dashboards.

### Course Catalog (`courses/models.py`)
- `Category` → `Course` → `Module` → `Lesson` define curriculum hierarchy with CKEditor fields, difficulty, review workflow, and slug-driven URLs.
- `CourseTag`/`CourseTagging` enable custom filters; `CourseReview` stores qualitative feedback for future social proof.

### Progress & Credentials (`progress/models.py` + `certificates/certificate_service.py`)
- `Enrollment` tracks status, type (paid/trial/sponsored), trial boundaries (JSON), and derived stats. Methods update streaks, certificate eligibility, and trial gating logic.
- `LessonProgress`, `QuizAttempt`, `Certificate`, `LearningPath`, `Achievement`, `StudySession` capture granular user activity for dashboards and automation.
- Certificates live in `progress.models.Certificate`, but generation is encapsulated in `certificates/certificate_service.py` (ReportLab PDF fallback to HTML).

### Assessment, Content & Engagement
- `assessments/models.py` manages quizzes, questions, assignments, peer/self reviews, rubrics, and templates to support varied evaluation styles.
- `content/models.py` defines `ContentItem`, `InteractiveExercise`, `LessonContent`, `ContentLibrary` to create reusable building blocks across lessons.
- `communication/models.py` implements `Forum`, `Topic`, `Reply`, `Message`, `Notification`, and `StudyGroup` to keep track of community interactions.

### Commerce & Analytics
- `payments/models.py` holds `PaymentMethod`, `Payment`, `PaymentCallback`, `PaymentNotification`, capturing metadata (installment sequence, references, payer IDs).
- `analytics/models.py` stores aggregated snapshots (`PaymentAnalytics`, `UserPaymentBehavior`, `CourseRevenueAnalytics`) to avoid expensive ad-hoc queries.

## Views / APIs / Services
- Marketing & user views rely on Django class-based views for reuse (`users/instructor_views.py`, `courses/views.py`, `progress/views.py`).
- Service objects centralize side effects:
  - `courses/enrollment_service.py`: validation + transactional creation + email notifications.
  - `courses/trial_service.py`: boundary calculations, gating logic, conversion helpers.
  - `payments/payment_service.py`: orchestrates M-Pesa STK pushes, PayPal orders, manual bank checks, and persists references.
  - `payments/email_service.py`: uses Mailtrap to notify admins/users with rich HTML.
  - `analytics/services.py`: builds dashboards, revenue trends, installment analytics, and updates denormalized tables.
  - `core/error_handling.py`: custom exceptions + decorators to standardize error responses and logging throughout LMS flows.
- APIs: a mix of JSON endpoints (trial status, messaging, analytics) and template responses. GraphQL endpoint (`/graphql/`) is provisioned (Graphene) but schema wiring still TODO (call this out during interviews as planned work).

## Frontend Structure, Components & Choices
- **Bootstrap 5 + Crispy Forms** for consistent UI; `crispy_bootstrap5` renders forms with minimal template logic.
- **Marketing pages** compose hero/header/CTA slices from `templates/yitp/` with `templates/yitp/navbar.html` shared via middleware-provided context (`UnifiedNavigationMiddleware`).
- **LMS dashboards** live in `templates/lms/...` (courses, progress, assessments, trial, account). Each area uses includes for breadcrumbs, alerts, and cards.
- **Custom JS/CSS** lives in `static/js` & `static/css`, e.g., translation demos and trial progress bars.
- **Email templates** in `templates/emails/` mirror brand guidelines and are re-used by payment + onboarding flows.

## Authentication & Authorization Design
- Base authentication is Django `User`; onboarding enforces OTP verification (`users/otp_views.py`) + profile completion before granting LMS access.
- Instructor onboarding uses magic-link tokens (`users/magic_link_utils.py`) with hashed signatures + expiry windows, role-based gating via `InstructorRequiredMixin`.
- Middleware (`SmartRedirectMiddleware`, `CourseDiscoveryRedirectMiddleware`, `WelcomePageRedirectMiddleware`) ensures authenticated users avoid marketing funnels and go straight to relevant dashboards.
- Authorization primarily uses mixins (`LoginRequiredMixin`, `InstructorRequiredMixin`, custom checks in views) plus per-object checks (`CourseBuilderAPIView` asserts instructor status).
- Profiles encode payment/sponsorship/trial states so views can short-circuit unauthorized actions without extra queries.

## Data Flow & Lifecycle
1. **Discovery**: user lands on marketing pages (`yitp/views.py`), is redirected intelligently if already authenticated.
2. **Registration & Verification**: `users/views.register` + OTP (`users/otp_views`) and optional sponsorship request create `Profile` records.
3. **Trial or Payment**: `courses/trial_views.start_trial` vs `payments/views.payment_methods` call `EnrollmentService` or `PaymentService`. Payment emails + admin alerts fire via Mailtrap.
4. **Enrollment to Learning**: `Enrollment` records drive lesson access checks (`TrialAccessService.can_access_lesson`), progress updates, and unlocking of assessments/communication features.
5. **Engagement**: messaging/forums (`communication/views`), content libraries (`content/views`), and analytics dashboards keep users informed.
6. **Completion**: `LessonCompleteView`, `QuizAttempt` updates, and `CertificateService.generate_certificate` issue credentials, while `PaymentAnalyticsService` rolls results into revenue dashboards.
7. **Observation & Iteration**: Admin exports (`users/views.export_*`), analytics endpoints, and docs support operations teams.

## External Integrations & Third-Party APIs
- **M-Pesa (Safaricom Daraja API)**: STK push initiated in `PaymentService.process_mpesa_payment`, callback URLs under `/payments/mpesa/*`.
- **PayPal REST SDK**: `payments/paypal_service.py` (imported by `PaymentService`) handles order creation & webhook validation (`/payments/paypal/*`).
- **Mailtrap**: transactional email via `users/mailtrap_service.py`; all notification utilities call into this client.
- **Uploadcare**: media storage for CKEditor content (`UPLOADCARE_*` envs in `blog/settings.py`).
- **CKEditor 5**: configured toolbars for course, lesson, and basic content (`CKEDITOR_5_CONFIGS`).
- **Django Unfold**: modern admin theme, plus `import_export` for CSV handling.
- **Graphene**: GraphQL endpoint stub ready for future mobile/API consumers.

## Background Jobs & Async Tasks
- Scheduled via cron/Render shell tasks that run Django management commands:
  - `users/management/commands/send_verification_reminders.py`: OTP reminder system with `--dry-run` and targeting options.
  - `payments/management/commands/process_installment_due.py`, `send_renewal_reminders.py`, `check_payment_expiry.py`: installment lifecycle + expiring access.
  - `analytics/management/commands/generate_analytics.py`: daily snapshots, optional backfill, user behavior & course revenue updates.
  - `assessments/management/commands/fix_quiz_progress.py`: repair historical data integrity.
  - `courses/management/commands/create_intro_course.py` & `test_student_journey.py`: seed + regression (used in staging before opening enrollment).
  - `users/management/commands/create_test_instructor.py`, `test_instructor_workflow.py`: reproducible onboarding tests.
- No Celery/Redis yet—intentionally avoided to keep Render deployment simple; commands can be hooked into Render cron jobs or GitHub Actions.

## Database Schema & Safe Inspections
- **Primary DB**: Postgres (Supabase) for prod; SQLite left only for legacy dev but `.env` + `render.yaml` point everything at Postgres.
- **Key tables**:
  - `courses_course`, `courses_module`, `courses_lesson` – catalog hierarchy.
  - `progress_enrollment`, `progress_lessonprogress`, `progress_certificate`.
  - `assessments_quiz`, `assessments_assignment`, `assessments_assignmentsubmission`.
  - `payments_payment`, `analytics_paymentanalytics`, `analytics_userpaymentbehavior`.
  - `communication_message`, `communication_notification`.
- **Read-only inspection tips**:
  - Use `python manage.py dbshell` with explicit `SELECT ... LIMIT 20` queries (never `UPDATE/DELETE` in production shells).
  - Example safe query (copy/paste inside dbshell):
    ```sql
    SELECT status, COUNT(*) FROM payments_payment GROUP BY status ORDER BY status;
    ```
  - Django shell snippet for aggregated checks:
    ```bash
    python manage.py shell -c "from django.db.models import Count; from progress.models import Enrollment; print(Enrollment.objects.values('status').annotate(total=Count('id')))"
    ```
  - For certificate verification stats:
    ```bash
    python manage.py shell -c "from progress.models import Certificate; print(Certificate.objects.order_by('-issued_date')[:5])"
    ```

## Deployment & Environment Configuration
- **Render** deployment (see `render.yaml`): builds branch `2026c`, runs `./build.sh`, starts `gunicorn blog.wsgi:application`.
- **`build.sh`**: installs deps, verifies critical imports, shows git status, collects static files, runs migrations, pings DB.
- **Smart env detection** (`blog/settings.py`): `detect_environment()` inspects `DJANGO_ENV`, Render vars, CLI args to set `IS_PRODUCTION`.
- **Settings highlights**:
  - Security toggles (HSTS, SSL redirect, secure cookies) only on in prod.
  - Static & media directories configured for both dev + prod; WhiteNoise handles asset serving.
  - Database config pulls from env even in dev (intentionally mimics prod to avoid drift).
  - `TINYMCE_API_KEY`, `UPLOADCARE_*`, `MAILTRAP_API_TOKEN`, payment credentials all externalized.
- **Environment files**: `.env.example` documents required keys; never commit actual `.env`. `render.yaml` currently contains secrets—treat file as sensitive and rotate keys if it ever leaves secure storage.

## Observability: Logging, Metrics, Error Tracking
- **Logging**: module-level loggers across apps write to `logs/yitp.log`, `logs/payments.log` (see repository). `core/error_handling.py` wraps views/services with consistent logging + user messaging.
- **System Status**: `users/views.system_status` renders uptime, queue backlogs, env markers for quick sanity checks.
- **Analytics dashboards**: `/analytics/` pulls metrics via `PaymentAnalyticsService.get_dashboard_summary()` for near-real-time KPIs (payments/day, revenue, installment completion).
- **Docs**: `docs/error_handling_implementation.md`, `docs/security_enhancements.md`, `docs/system_status_page_implementation.md` capture runbooks for ops.
- **Metrics gaps**: no external APM (Sentry/New Relic) yet; rely on built-in logs + analytics tables. Call this out as a future enhancement.

## Security & Secrets Handling
- OTP verification, magic-link hashing, and profile flags prevent unverified access.
- Course/trial gating uses server-side checks (`TrialAccessService.can_access_lesson`, `EnrollmentService.validate_*`) to foil deep-link bypass attempts.
- Payment inputs are validated for format/duplication before hitting APIs; bank/PayPal transaction IDs deduplicated in `payments/views.py`.
- Middleware enforces secure redirects and blocks anonymous access to `/lms/*`.
- Secrets strategy: `.env` (local), Render env vars (prod). Avoid storing plaintext secrets in repo—`render.yaml` should be sanitized before sharing; treat this as a key talking point plus action item (see Improvements).

## Testing Strategy
- **Automated tests** (`tests/`):
  - `test_course_enrollment_journey.py`, `test_trial_system.py` – integration tests around enrollment/trials.
  - `test_payment_integration.py`, `test_paypal_integration.py`, `test_payment_verification_workflow.py` – cover PaymentService + email notifications.
  - `test_user_registration_journey.py` – registration + OTP + sponsorship flows (with log output archived).
  - `run_enrollment_tests.py`, `simple_test_runner.py` – wrappers for CI or ad-hoc audits.
- **Management-command tests**: commands under `users/management/commands/test_*` exercise instructor onboarding, translation, email configs without touching production state.
- **Manual smoke tests**: `courses/management/commands/test_student_journey.py` walks through typical path; run before large releases.
- **Coverage**: `coverage` dependency available; not wired into build yet—use `coverage run manage.py test` locally as needed.

## Strengths, Trade-offs & Suggested Improvements

**Strengths**
- Modular Django apps with clear separation (marketing vs LMS vs commerce).
- Service-layer abstractions reduce duplication (enrollment, payments, analytics).
- Trial gating + sponsorship + installment handling baked into user profiles.
- Extensive documentation (`docs/`) and logging ease onboarding + ops.
- Payments + analytics integrated tightly, enabling data-informed coaching.

**Trade-offs / Improvements**
1. **Secret management**: sanitize `render.yaml`, move secrets to Render Dashboard or external vault, rotate compromised keys.
2. **Background processing**: management commands are simple but manual; consider Celery/cron YAML when workload grows or tasks need retries.
3. **GraphQL/API strategy**: Graphene dependency is unused—either wire schema for mobile clients or drop to reduce surface area.
4. **Testing depth**: add unit tests around TrialAccessService, PaymentService (mocking M-Pesa/PayPal), and middleware to improve confidence.
5. **Settings consistency**: `blog/settings.py` mentions Django 3.1.5 although repo runs Django 5.x—clean up comments and ensure local dev optionally uses SQLite to avoid relying on prod DB.
6. **Observability**: add structured logging config and optional Sentry integration for runtime alerting.

## Interview Talking Points & FAQ

### Talking Points
1. **Why this architecture**: highlight decision to keep a monolith with modular apps for speed and ease of deployment on Render, yet still enforce domain boundaries via services.
2. **Trial-to-paid funnel**: describe `TrialAccessService` + `EnrollmentService` synergy and how payment status flags on `Profile` drive UI + access control.
3. **Payment resilience**: explain how `PaymentService`, validation helpers, and Mailtrap alerts replace manual WhatsApp verification, reducing human toil.
4. **Instructor onboarding**: mention magic links + audit logging (`users/email_utils.py`) ensuring secure invite flows.
5. **Analytics + operations**: show how `PaymentAnalyticsService` + management commands let non-engineers track KPIs without querying production DB.

### FAQ
| Question | Answer |
| --- | --- |
| **How do trial users get prevented from deep-linking to later lessons?** | `TrialAccessService.can_access_lesson` calculates lesson order per course and compares against stored trial boundaries in `Enrollment.trial_boundaries`; views call it before rendering content, and AJAX endpoints respond with upgrade prompts. |
| **What happens when a user pays but enrollment hasn’t propagated?** | Payment callbacks update `Profile.payment_status`; `EnrollmentService.validate_enrollment_eligibility` checks `has_any_payment_access` before allowing re-enrollment, and admin notifications (`PaymentEmailService`) flag pending verifications. |
| **How are instructors onboarded safely?** | Admin triggers `users.email_utils.create_instructor_with_temporary_password`, sending a Mailtrap-backed welcome email with a magic-link token hashed in DB; `InstructorRequiredMixin` locks down dashboards until verification completes. |
| **How do we investigate production issues without risking data?** | Use read-only shell/queries (see Database section) plus `users/views.system_status` and analytics dashboards; logs in `logs/` capture contextual metadata for payments/enrollments. |
| **What’s the plan for async scaling?** | Current cron-friendly commands cover daily jobs; roadmap includes evaluating Celery/Redis once concurrency, retries, or scheduled reminders exceed Render cron capabilities. |

## Appendix – Useful Commands & Scripts

| Command | Purpose |
| --- | --- |
| `python manage.py send_verification_reminders --dry-run` | Preview OTP reminder emails without touching users. |
| `python manage.py process_installment_due --dry-run --check-overdue` | Inspect upcoming/overdue installments and notifications. |
| `python manage.py generate_analytics --backfill 7 --update-user-behavior --update-course-revenue --verbose` | Recompute analytics for the last week. |
| `python manage.py fix_quiz_progress` | Repair missing lesson-progress entries for passed quizzes. |
| `python manage.py test tests.test_payment_integration` | Run targeted payment regression tests (fast smoke). |
| `python manage.py shell -c "from django.db.models import Count; from payments.models import Payment; print(Payment.objects.values('payment_method','status').annotate(total=Count('id')))"` | Read-only snapshot of payment pipeline health. |
| `python manage.py export_users_csv` *(via `/users/superuser/export/users/`)* | Admin-only CSV export endpoint, handy for audits (read-only). |

> For production investigations, prefer the management commands above or CSV exports. If deeper DB access is required, use `python manage.py dbshell` with `SELECT` queries only and document everything in the ops log.

---

**Use this document before interviews** to rehearse the story: start with the mission, walk through the architecture, highlight trials/payments/analytics as differentiators, and close with honest trade-offs plus roadmap items. The combination of modular Django apps, strong documentation, and pragmatic automation is the core narrative.
