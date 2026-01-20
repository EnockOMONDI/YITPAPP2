# Registration Update Report - 2026-01-20

## What we changed
- Added a new dropdown on the sign-up form asking “How did you hear about us?” with options like Google, ChatGPT, social channels, and “Other”.
- Made this question required for new sign-ups and kept the rest of the registration steps the same.
- Saved the chosen answer on each user’s profile with a safe default of “Other” so existing users are not affected.
- Created a database update to store this answer going forward.

## Tests we ran
- Command: `python manage.py test tests.test_user_registration_journey`
- Outcome: 28 tests ran; 22 passed, 5 failed, 1 error.

## What passed (high level)
- New question shows up, must be answered, and saves to the user profile.
- Normal sign-up flow still works and reaches the OTP step.
- Duplicate username/email checks still block bad submissions.
- OTP emails send, and valid OTPs activate accounts and redirect correctly.
- Profile gets created during sign-up and shows the right phone value.

## What failed (high level)
- Complete journey check: the combined “all steps” check flagged the sign-up step as not fully successful (likely tied to one of the other failures below).
- Invalid user ID for OTP: when testing an OTP with a fake user, the system tried to redirect to a route name it could not find.
- Missing user ID for OTP: the system did not handle a missing user ID as expected.
- Email send failure during sign-up: the test expected the user to stay created/activated when email sending fails, but the outcome did not match.
- Expired OTP: the test expected the user to stay inactive with a clear message, but the check failed.
- Invalid OTP: similar to expired OTP; expected inactive user plus an error message, but the check failed.

## Notes
- The failures above were already present in the broader registration/OTP flow and are unrelated to the new “How did you hear about us?” change. They need follow-up fixes in the OTP error-handling paths.
- We plan to add this question to the user dashboard so existing users can update their answer later. No impact on current users until that UI is added.
