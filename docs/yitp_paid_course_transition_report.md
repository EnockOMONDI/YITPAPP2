## Executive Summary

Following the decision to reposition the “Youth Impact Training Programme (YITP)” course as a paid learning product, all enrollment and access pathways were reviewed to determine operational impact. The current LMS implementation already distinguishes between free and paid offerings via the `Course.price` attribute, so raising the price above zero automatically routes every enrollment attempt through the paid-course safeguards. No code modifications are required to enforce payment; however, the change triggers specific behaviors that leadership should note.

## Enrollment Gatekeeping

- The unified `EnrollmentService` validates every enrollment or quick-start request (courses/enrollment_service.py:40-101). When `course.price > 0`, learners must have a `Profile.payment_status` of `confirmed`, `partially_paid`, or `sponsorship`. Partial payments that have lapsed are blocked with a tailored message instructing learners to complete the second installment.
- All UX entry points—course detail CTA buttons, quick start routes, and `/progress/enroll/`—call the same service (courses/views.py:428-520; progress/views.py:180-220). As a result, there is no alternative path that bypasses the payment check.
- Trial enrollment remains available only for paid courses. Without payment access, students may start a two-lesson trial, but the same validator prevents users who already have payment access (or who exhausted their trial) from creating duplicates (courses/enrollment_service.py:118-160; courses/trial_views.py:24-111).

## Impact on Currently Enrolled Students

- Lesson and quiz access rely on the existence of an `Enrollment` record rather than the profile’s payment status. `LessonDetailView` fetches the learner’s enrollment (`courses/views.py:545-640`), and `Lesson.is_accessible_for_user` only checks prerequisites and trial boundaries (`courses/models.py:385-426`). Therefore, students who enrolled while the course was free remain unaffected and retain full content access.
- Trial governance (`courses/trial_service.py:93-200`) first looks for active trials, but defaults to granting access to any user who already has an active or completed enrollment. Converting a trial to full access, however, still requires a verified payment status (`courses/trial_views.py:112-147`).
- Enrollment records are `unique_together` on (student, course), so existing entries stay intact unless explicitly deleted (`progress/models.py:204-289`). The shift to paid pricing does not retroactively downgrade or remove these records.

## Business Risks and Mitigations

- **Perception risk for legacy learners.** Their profile dashboards will now display “Payment required” banners even though their enrollment remains valid. Consider programmatically marking grandfathered students as `sponsorship` to align messaging with their actual access status.
- **Support load.** Expect an uptick in payment-verification tickets, particularly around expired partial payments. Ensure support scripts reference the automated expiry messaging emitted by `EnrollmentService`.
- **Revenue leakage prevention.** Because every entry point defers to the unified service, there is minimal risk of unpaid enrollments slipping through. Periodic audits of `Profile.payment_status` against `Enrollment` records can confirm compliance.

## Recommended Next Steps

1. Publish internal and external communications that explain the pricing change, payment workflow, and trial option.
2. Run a QA pass that covers: unpaid learner enrollment (expect rejection), paid learner enrollment (expect success), and existing learner lesson access (should remain uninterrupted).
3. Decide on a policy for legacy learners—either convert their payment status or formalize them as sponsored students—to eliminate confusing “Unpaid” badges on their dashboards.
