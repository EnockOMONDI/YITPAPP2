# YITP User & Profile Types Overview

This guide summarizes the primary user personas supported in the Youth Impact Training Programme platform and the responsibilities, access levels, and tooling each profile receives.

## 1. Learners (Default Profile)
- **Who they are:** Youth participants enrolled in programmes, mentorship labs, or mastery sprints.
- **Primary surfaces:** Unified learner dashboard (`/profile/`), LMS course experiences, sponsorship request forms, billing & data privacy controls.
- **Key capabilities:**
  - Enroll in courses, track lesson progress, unlock achievements and certificates.
  - Manage sponsorship applications, view billing history, request data exports or account deletion.
  - Access personalized recommendations and resume exactly where they left off in a lesson.

## 2. Course Instructors & Teaching Teams
- **Who they are:** Verified facilitators who create and deliver curriculum content.
- **Roles covered:** System Administrator, Course Instructor, Teaching Assistant, Grader.
- **Primary surfaces:** Instructor dashboard suite (`/users/instructor/...`), content studio, analytics, messaging.
- **Key capabilities:**
  - Build and publish modules/lessons, author assessments, manage cohorts.
  - Review real-time analytics, lesson performance, quiz submissions, and student messages.
  - System administrators additionally access superuser dashboards, live metrics, and Django admin.

## 3. Content Managers (renamed from Content Creators)
- **Who they are:** Non-teaching content operators who focus on curriculum quality, publishing workflows, blog stories, and media assets.
- **Primary surfaces:** New Content Manager Dashboard (`/users/content-manager/dashboard/`), Content Studio, blog management (via Django admin), module management, analytics.
- **Key capabilities:**
  - Track course/module/lesson publishing status, review draft pipelines, and monitor recent content updates alongside editorial blog queues.
  - Coordinate with instructors, manage assets via the content studio, publish blog posts/categories, and keep the catalogue consistent with YITP brand standards.
  - Receive condensed KPIs (published vs draft content) without the full teaching toolkit.

## 4. Accountants / Finance Desk
- **Who they are:** Finance or operations staff responsible for payments, sponsorship fulfilment, and audit readiness.
- **Primary surfaces:** New Accountant Dashboard (`/users/accountant/dashboard/`), learner billing tabs, export endpoints.
- **Key capabilities:**
  - Monitor confirmed revenue, pending verifications, installment pipelines, and sponsorship statuses at a glance.
  - Drill into recent transactions, process pending payments, and coordinate with learners awaiting approval.
  - Access finance-specific exports and compliance notes without exposure to course authoring tools.

## 5. Superusers & Platform Admins
- **Who they are:** Core platform maintainers with total system access.
- **Primary surfaces:** Superuser dashboard (`/users/superuser/profile/`), Django admin, live metrics, debug tooling.
- **Key capabilities:**
  - Globally manage users, instructors, permissions, enrolments, payments, and infrastructure health.
  - Receive elevated alerts (instructor logins, system health), approve courses, and run exports.

### Notes on Access Control
- Every instructor-type profile (including content managers and accountants) is represented by `users.models.InstructorProfile` with a role value. Verification + active status gates their dashboards.
- Role→dashboard routing happens at login and via the smart `_get_resume_destination` utility so specialized users never drop into learner-only views unintentionally.
- Django signals provision the correct permissions per role (course authoring, finance data, etc.) and promote users to staff when necessary.

This structure keeps the learner experience streamlined while unlocking specialized workspaces for internal teams without duplicating accounts. As new roles emerge (e.g., partnerships, mentors), they can plug into the same InstructorProfile framework with targeted dashboards and permissions.
