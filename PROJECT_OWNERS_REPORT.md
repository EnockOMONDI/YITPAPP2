# Project Owners Report

Date done: February 13, 2026
Time taken: 2 hours 30 minutes

Summary (simple):
We made a full backup of the live database, then updated new students from January 1, 2026 to February 14, 2026 so they are marked as sponsored students.

What we did:
- Made a full backup of the live database (this is a safety copy before changes).
- Found all students who registered between January 1, 2026 and February 13, 2026.
- Excluded staff and superusers (admins) so they were not affected.
- Marked these students as sponsored and set their payment method to scholarship.
- Updated their existing course enrollments to show they are sponsored.

Results:
- Students updated: 46  
- Staff/admins affected: 0
- Students without profiles: 0
- Enrollments updated to sponsored: 5

Why this matters:
- These students now have full access to paid lessons as sponsored learners.

Notes:
- The backup is stored in the project folder so we can restore if needed.
- This report will be updated after major tasks.


# How To Run This Project
This is a Django project with local development driven by `manage.py`, dependencies from `requirements.txt`, and environment variables loaded through `python-decouple` in `blog/settings.py`.

### 1. Prerequisites
- Python 3.11+ recommended.
- `pip` and virtualenv support.
- Optional: SQLite tools if you want to inspect the bundled dev databases directly.

### 2. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables
- Copy `.env.example` to `.env`.
- At minimum, verify or set:
  - `DJANGO_ENV=development`
  - `SECRET_KEY`
  - `DEBUG`
  - `SITE_URL`
  - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
  - `MAILTRAP_API_TOKEN`
  - `MPESA_*`
  - `PAYPAL_*`
  - `TINYMCE_API_KEY`
  - `UPLOADCARE_PUBLIC_KEY`, `UPLOADCARE_SECRET_KEY`
  - `DEFAULT_FROM_EMAIL`, `ADMIN_EMAIL`

### 5. Prepare the database
- The repository already includes local SQLite snapshots such as `db.dev.sqlite3` and `db_test.sqlite3`.
- `blog/settings.py` switches environment behavior automatically, so confirm your `.env` matches the mode you want to run.
- Apply migrations if needed:
```bash
python manage.py migrate
```

### 6. Collect static files
```bash
python manage.py collectstatic --noinput
```

### 7. Run Django locally
```bash
python manage.py runserver
```

Then open:
- `http://127.0.0.1:8000/` for the public site
- `http://127.0.0.1:8000/admin/` for admin
- `http://127.0.0.1:8000/profile/` for learner dashboards
- `http://127.0.0.1:8000/payments/` for payment flows

### 8. Useful checks
```bash
python manage.py check
python manage.py test
```

Targeted suites called out elsewhere in this repo include:
- `python manage.py test tests.test_user_registration_journey`
- `python manage.py test tests.test_payment_integration tests.test_paypal_integration tests.test_payment_verification_workflow`
- `python manage.py test tests.test_trial_system`
- `python manage.py test tests.test_course_enrollment_journey`

### 9. Production-style run notes
- Render uses `./build.sh` during deploys and starts the app with:
```bash
gunicorn blog.wsgi:application
```
- Production hosting is on Render.com with PostgreSQL on Supabase, so local runs may require swapping production credentials for safe dev values.
