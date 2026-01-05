# Navigation Context Audit

Comprehensive survey of the current Youth Impact Training Programme (YITP) application to inform the next-generation navigation/translation rebuild.

## 1. Branding & Layout Baselines

- **Core palette & typography:** `templates/unified/base.html:14-120` defines CSS variables for YITP Orange `#ff5d15`, YITP Dark Blue `#341C67`, gradients, button states, and hero styles that are reused across LMS/profile/public pages.
- **Spacing fixes baked in templates:** many views (e.g., `templates/lms/courses/dashboard.html:6-25`, `templates/registration/unified_profile.html:9-33`) add `.margin-top` compensations for the now-removed navbar. The new system must account for this to avoid redundant offsets.
- **Global assets still loaded:** `assets/css/bootstrap.min.css`, `assets/css/style.css`, and `assets/js/main.js` power both marketing and LMS surfaces. Any new navigation should piggyback on these shared bundles.

## 2. Public & Marketing Surface

### URL coverage (`yitp/urls.py:8-36`)
- Home (`''`), course marketing pages (`web_courses_list`, `coursedetail1-6`), docs (`documentation`), company info (`about`, `team`, `privacy-policy`, `terms-of-service`), FAQ, contact/support, SEO endpoints, translation demos.
- Events and blogs pulled via `events.views.event_list` and `blogapp.urls`.

### Content templates
- `templates/yitp/index.html`, `templates/yitp/about.html`, `templates/yitp/support.html` use hero sections with CTA buttons, testimonial cards, and highlight components. They assume a top navigation occupying ~100px height.
- Footers (`templates/unified/footer.html`) expose Support, Terms, Privacy quick links; any public navbar should complement these.

## 3. Profile & Account Experience

### Unified profile (`templates/registration/unified_profile.html`)
- Extends `yitp/baseprofile.html` and renders tabbed sections: Dashboard, Courses, LMS, Analytics, Billing, Settings, Security. Buttons use `.btn-yitp-primary` gradient.
- Security/privacy widgets: `.security-item`, `.account-item`, `.privacy-item` cards with hover states tied to the brand colors.

### Users URLs (`users/urls.py:13-59`)
- Public marketing pages (`home`, `aboutus`, etc.).
- Instructor center (`instructor_dashboard`, `instructor_courses`, `instructor_messages`, `instructor_analytics`, `instructor_tutorial`).
- Accountant dashboard (`accountant_dashboard`) and content manager area (`content_manager_dashboard`).
- Magic link, OTP verification, timezone helpers, system status, and superuser management endpoints.

### Templates of note
- `templates/users/instructor/dashboard.html` – uses gradient nav ribbon (`templates/instructor/navigation.html`) with quick actions (New Module, Assign Module, New Quiz, Messages, Analytics). Sidebar-like layout must be mirrored in future nav.
- `templates/users/superuser_dashboard.html` – cards for metrics, CSV exports, action buttons.
- `templates/users/accountant_dashboard.html` – finance summary cards, pending payouts list.

## 4. LMS Surfaces

### Courses module (`courses/urls.py:9-24`)
- Visitor-facing course list/detail plus authenticated flows (Dashboard, How It Works, Admin Support, Module2 downloads, Quick Start, Enroll, Module/Lesson detail, My Courses).
- Templates such as `templates/lms/courses/dashboard.html`, `templates/lms/courses/course_detail.html`, and lesson detail templates lean on card grids and progress bars.

### Learning progress (`progress/urls.py:8-29`)
- Student dashboards (`progress:dashboard`, `my_progress`, `achievements`, `leaderboard`, `learning_paths`, `study_sessions`, analytics) plus enroll/unenroll endpoints.
- Template styling similar to courses (cards, charts, progress bars). Many include top margin offsets expecting a fixed navbar.

### Communication suite (`communication/urls.py:8-34`)
- Messaging inbox/sent, compose, message detail/reply.
- Forums, announcements, notifications, plus AJAX endpoints for unread counts.
- Templates (e.g., `templates/lms/communication/dashboard.html`) integrate tabs + badges, ideal for contextual nav sections.

### Assessments (`assessments/urls.py:8-21`)
- Quiz and assignment dashboards, detailed views, take quiz form, submission flows.

### Content & builder (`content/urls.py`, `course_builder/urls.py`)
- Content dashboards, libraries, exercises, search; builder wizard, media library, templates. Instructor roles rely heavily on these.

### Analytics (`analytics/urls.py:12-23`)
- Views for payment methods, user behavior, course revenue plus data APIs. Likely restricted to staff/superusers.

## 5. Payments & Certificates

- `payments/urls.py:13-31` – payment methods, processors (M-Pesa, PayPal, bank), callbacks, status pages.
- `certificates/urls.py:8-13` – verify/download/my certificates; should be accessible to students from both LMS and profile navs.

## 6. Role Inventory

- **Public/anonymous** – marketing pages, blog, events, register/login.
- **Student (default authenticated)** – profile sections, LMS dashboards (courses, progress, assessments, communication, content view), payments/certificates.
- **Instructor** – dashboards (`users:instructor_*`), content management, analytics, messaging.
- **Accountant** – finance dashboard, billing/analytics sections.
- **Content Manager** – share instructor surfaces but with content focus (content management, wizard, course builder).
- **Superuser / Project Owner** – superuser dashboard, CSV exports, live metrics, admin portal, analytics.
- **Developers/administrators** – system status, OTP/magic link testers (likely hidden from general nav but worth noting).

## 7. Styling Observations

- LMS & profile templates use Bootstrap 5 utility classes plus custom `.card`, `.badge`, `.btn-outline-primary` modifications.
- Numerous templates reference `margin-top` hacks referencing the old navbar height; new navigation should provide a consistent spacer (e.g., CSS variable set on `<body>`).
- Instructor ribbon (`templates/instructor/navigation.html`) uses gradient background, quick action pills, and role badges; new design should reuse this concept or integrate into new nav.

## Implications for New Navigation

- Every surface expects a header offset and global notification/message components; new nav must provide these hooks.
- Role-specific endpoints are well defined; nav logic can rely on `request.user` flags (superuser, instructor_profile, etc.) and sections (`request.GET.section` on profile).
- Mobile experience currently relied on sidebar markup (now removed); we need a consolidated responsive system that exposes both public marketing links and authenticated workspace access without reintroducing duplication.

Use this audit to design role-aware navigation that surfaces the correct URL clusters while honoring the established YITP branding tokens.
