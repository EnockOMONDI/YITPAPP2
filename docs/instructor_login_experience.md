# YITP Instructor Login Playbook

> Modernized onboarding for the Youth Impact Training Programme (YITP) instructor portal. Share this with every trainer so their first login is smooth and brand-aligned.

---

## 1. YITP Brand Snapshot

- **Gradient DNA:** `#341C67 → #ff5d15`
- **Primary Fonts:** Inter / system sans-serif
- **Tone:** Confident, supportive, youth-forward

Use that gradient + tone in any screenshots or onboarding decks you send to new instructors.

---

## 2. Pre‑Login Checklist

| Item | Why it matters |
| --- | --- |
| ✅ Instructor profile created in Django admin | Grants staff access + role-based permissions |
| ✅ Verification email sent (contains username + temporary password) | Ensures secure first login |
| ✅ Instructor has bookmarked `https://app.youthimpactglobal.com/users/instructor/` (or local URL) | Reduces “where do I go?” tickets |
| ✅ MFA decision | If your programme enforces MFA, share steps before Day 1 |

> **Tip:** keep a Trello/ClickUp card template with these checkboxes so ops can confirm each instructor is fully provisioned.

---

## 3. Logging In (Desktop)

1. **Navigate** to your deployment URL (example below):
   - Local dev: `http://127.0.0.1:8000/login/`
   - Production: `https://app.youthimpactglobal.com/login/`
2. **Enter credentials** from the Welcome email.
3. **Press “Sign In”.** If credentials are correct, you land on the instructor dashboard
   (`/users/instructor/`).
4. **Set a new password** when prompted.
5. **Bookmark** `/users/instructor/` – this is your primary workspace.

> ⚠️ **Troubleshooting:** If you see “account inactive,” ask ops to verify the InstructorProfile and check that `is_active` + `verification_status = verified`.

---

## 4. Logging In (Mobile)

- The login form is fully responsive. Open the same URL in Safari/Chrome.
- Use a password manager to avoid retyping errors on mobile keyboards.
- After login, add the site to your home screen (iOS: “Add to Home Screen”, Android: “Add shortcut”).

---

## 5. First-Look: Instructor Dashboard Highlights

Once authenticated, the gradient hero welcomes the instructor with stats + shortcuts.

| Card | Location | What instructors do |
| --- | --- | --- |
| **Module Hero** | Top | View unread messages, jump to analytics |
| **Assigned Modules grid** | Mid | Open a module to edit lessons/quizzes |
| **Quizzes & Assessments** | Lower | Create quizzes and add questions/answers |
| **Messages** | Quick actions | Open inbox at `/users/instructor/messages/` |

Encourage instructors to click through each tab in their first week so they understand the YITP toolkit.

---

## 6. Recommended Onboarding Script

1. **Send Welcome Pack** (PDF or Notion) with:
   - Login URL
   - Temporary password
   - This Playbook PDF
2. **Schedule a 20‑min walkthrough** (Zoom/Meet). Cover:
   - Dashboard hero
   - Module manager
   - Messaging hub
3. **Assign a sandbox module** so they can safely create lessons/quizzes.
4. **Collect feedback after Day 3**: “What felt unclear?” – feed this doc accordingly.

---

## 7. Support & Escalations

- **Password resets:** `/accounts/password/reset/`
- **Dashboard bugs:** send URL + screenshot to `support@youthimpactglobal.com`
- **Role upgrades:** ping the Super Admin or fill a request in the ops channel

> 🔁 Update this document whenever the instructor dashboard UI changes. Version/date stamp your updates at the top for transparency.

---

_Last updated: Aug 17, 2024_
