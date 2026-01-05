# YITP Engineering Onboarding 

> Purpose: give new contributors a fast, safe path from laptop setup to production deployments. Keep this document current whenever the project or processes change.

## 1. Starting Points
- **Read the system architecture**: Review `YITP.md` end to end so you understand apps, services, and flows (OTP, payments, analytics, communication).
- **Identify stakeholders**: Confirm primary contacts for engineering, product, finance/payments, and content so you know who to pull in when changes touch their areas.
- **Access checklist**:
  - GitHub repository (read/write). 
  - Render.com service (deploy + logs).
  - Supabase/PostgreSQL database (read replicates + ability to run migrations).
  - Mailtrap production project.
  - PayPal developer & live dashboards.
  - Safaricom M-Pesa sandbox credentials (and the secure channel for exchanging production keys).
  - Uploadcare media account.
  - Slack/Teams channels where incidents and deploys are broadcast.

## 2. Local Environment Setup
1. **Install tooling**
   - Python 3.11+ (project currently runs on 3.11 in dev; production is Django 3.1.5-compatible).
   - Pip/pipenv/virtualenv (team standard: virtualenv + `pip install -r requirements.txt`).
   - Node/Yarn only if you plan to rebuild static assets (WhiteNoise serves the bundled artifacts by default).
   - SQLite utilities (for `db.dev.sqlite3`).
2. **Clone & bootstrap**
   ```bash
   git clone <repo-url>
   cd YITPAPP
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Environment variables**
   - Copy `.env.example` (create one if it doesn’t exist) into `.env` and fill in the following from shared vaults:
     - `SECRET_KEY`, `DJANGO_ENV`, `DEBUG`, `SITE_URL`.
     - Mailtrap sandbox token (`MAILTRAP_API_TOKEN`).
     - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (use dev snapshot or Supabase read replica).
     - `TINYMCE_API_KEY`, `ADMIN_EMAIL`, `DEFAULT_FROM_EMAIL`.
     - Payment credentials (sandbox): `MPESA_*`, `PAYPAL_*`.
   - Django reads env vars via `python-decouple` inside `blog/settings.py`.
4. **Database prep**
   - Default dev DB is `db.dev.sqlite3` (already included). If you need a fresh copy, ask for the latest sanitized dump and replace the file.
   - Run migrations if needed: `python manage.py migrate`.
5. **Static & media**
   - Collect static for local testing: `python manage.py collectstatic --noinput`.
   - Media uploads default to `media/`; ensure the directory exists.
6. **Smoke test**
   ```bash
   python manage.py runserver
   ```
   - Visit `http://127.0.0.1:8000/` for marketing pages.
   - Validate `/admin/`, `/profile/`, `/payments/` pages render (use existing dev accounts or create new ones through the OTP flow).

## 3. Coding Standards & Workflow
- **Branching model**: Feature branches off `main` (or the active release branch such as `2026mtesting`); name them `feature/<ticket>` or `bugfix/<ticket>`.
- **Style & linting**:
  - Follow PEP8/Black-style formatting; keep imports ordered (standard lib, third-party, local).
  - Use docstrings/comments sparingly to explain non-obvious workflows (payments, OTP, analytics).
- **Testing expectations**:
  - Unit tests live under `tests/` plus each app’s `tests.py`.
  - Core suites to run before raising a PR:
    - Registration + OTP: `python manage.py test tests.test_user_registration_journey`.
    - Payments: `python manage.py test tests.test_payment_integration tests.test_paypal_integration tests.test_payment_verification_workflow`.
    - Trial access: `python manage.py test tests.test_trial_system`.
    - Enrollment journeys: `python manage.py test tests.test_course_enrollment_journey`.
  - Use the provided SQLite test DB (`db_test.sqlite3`) or spin up Postgres via Docker if needed for concurrency features.
- **Code review**:
  - Open PRs with a checklist: description, screenshots (UI), tests run, migration notes, security considerations.
  - Assign at least one reviewer familiar with the affected domain (e.g., payments, analytics) plus an ops reviewer for deploy-sensitive changes.
- **Migrations**:
  - Name migrations descriptively; when touching large tables, add `db_index` or `RunSQL` considerations so ops can evaluate downtime.
  - Document data migrations in PRs and in release notes.

## 4. Deployment Process
1. **Pre-deploy checks**
   - Ensure `main`/release branch is green in CI and tests pass locally.
   - Update `YITP.md` or other docs if architecture or flows changed.
   - Coordinate with finance/content teams when modifying payments, pricing, or email templates.
2. **Render workflow**
   - Build command: `./build.sh` (compiles assets, runs checks).
   - Start command: `gunicorn blog.wsgi:application` (see `render.yaml`).
   - For manual deploys: push to the tracked branch (`2026mtesting`) and watch the Render dashboard for logs. Save the deploy URL for reference.
   - If using `render_fallback.yaml`, ensure the fallback branch is up to date and tested.
3. **Migrations & data ops**
   - Apply migrations automatically via Render deploy hooks or manually `python manage.py migrate` on the instance.
   - For destructive/backfill operations, schedule downtime or maintenance windows; run from a management shell with logs enabled.
4. **Smoke tests post-deploy**
   - Hit `/status/` endpoint.
   - Complete a payment flow in sandbox mode (M-Pesa + PayPal) or use a no-charge course.
   - Verify OTP sign-up, login, profile editing, analytics dashboard.
   - Tail logs (`logs/yitp.log`, `logs/payments.log`) for new errors.
5. **Rollback**
   - If Render build fails, redeploy previous snapshot from dashboard.
   - For database issues, restore from the latest Supabase backup or reapply migration reversals (`python manage.py migrate app <previous_migration>`).
   - Document incidents in the shared runbook/Slack channel.

## 5. Operational Responsibilities
- **Monitoring**
  - Payments: review `payments.log` and PayPal/M-Pesa dashboards daily. Alert finance if repeated failures occur.
  - OTP backlog: run `users/management/commands/check_otp_consistency.py` weekly to catch stale records.
  - Analytics cron: ensure scheduled commands update `PaymentAnalytics` (look for gaps in dashboard charts).
- **Secrets & rotations**
  - Keep `.env` copies local only; production secrets live in Render environment settings and secure vaults.
  - Rotate Mailtrap, PayPal, and M-Pesa keys quarterly or after personnel changes. Update `render.yaml` and notify affected apps.
- **Access reviews**
  - Quarterly review of who has access to Supabase, Render, Mailtrap, PayPal, Uploadcare.
- **Incident response**
  - Document steps for handling PayPal webhook failures, M-Pesa callback timeouts, certificate generation errors, etc.
  - Set expectations: acknowledge within 15 minutes during business hours, involve finance/content owners as needed.

## 6. Domain Knowledge Deep Dives
- **Payments**: Walk through `payments/payment_service.py`, `payments/paypal_service.py`, and templates under `templates/payments/`. Understand reference validation, STK push, and PayPal webhooks before modifying.
- **OTP & identity**: Read `users/otp_views.py`, management commands, and `users/models.Profile` payment state transitions.
- **Analytics**: Review `analytics/services.py` for how daily aggregates are computed, and how dashboards (`analytics/views.py`) fetch data.
- **Certificates**: Understand the flow from `progress.Enrollment.generate_certificate` to `certificates/certificate_service.py` to public verification.

## 7. Suggested Onboarding Timeline
| Day | Focus |
| --- | --- |
| 1 | Environment setup, `YITP.md` review, architecture walkthrough with mentor. |
| 2 | Deep dive into authentication (registration, OTP, magic links) and payments. Run relevant tests locally. |
| 3 | Shadow a deployment to staging/production, learn Render workflows, inspect logs. |
| 4 | Take a bite-sized ticket (UI fix, analytics query), go through PR + review cycle. |
| 5 | Pair on a more substantial feature touching payments or progress to build domain confidence. |
| Week 2 | Own a full change: dev → tests → deploy, including release notes and post-deploy verification. |

## 8. Maintaining This Doc
- Update immediately after changing deployment steps, access requirements, or adding new apps/integrations.
- Run an onboarding retro with each new hire and capture gaps or confusing steps here.
- -Version-control this file so it evolves alongside the project.
