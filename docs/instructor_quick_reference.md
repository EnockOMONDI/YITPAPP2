# YITP Instructor Creation - Quick Reference Guide

## 🚀 Quick Start: Create an Instructor Account

### Step-by-Step Process

1. **Login to Admin** → `/admin/` (Modern YITP-branded interface)
2. **Go to Users** → Sidebar: "User Management" → "Users"
3. **Add User** → Click "Add User" button (+ icon)
4. **Basic Info** → Username, Password, Email, Name
5. **Instructor Profile** → Scroll to "Instructor Profile" section
6. **Select Role** → Choose appropriate instructor role
7. **Fill Details** → Bio, qualifications, experience
8. **Save** → System automatically handles permissions!

## 🎭 Instructor Roles at a Glance

| Role | Admin Access | Auto-Verify | Key Permissions |
|------|-------------|-------------|-----------------|
| 🔴 **System Admin** | ✅ Full | ✅ Yes | Everything (Superuser) |
| 🟠 **Course Instructor** | ✅ Yes | ❌ Manual | Create/manage courses & assessments |
| 🟢 **Teaching Assistant** | ❌ Limited | ❌ Manual | Support courses, grade assessments |
| 🔵 **Content Creator** | ✅ Yes | ❌ Manual | Create content, limited course access |
| ⚫ **Grader** | ❌ Limited | ❌ Manual | Grade assessments only |

## 🎨 Visual Indicators

### Role Badges
- 🔴 System Administrator
- 🟠 Course Instructor (YITP Orange)
- 🟢 Teaching Assistant
- 🔵 Content Creator
- ⚫ Grader

### Verification Status
- ✅ Verified (Green)
- ⏳ Pending (Yellow)
- ❌ Rejected (Red)

## ⚡ What Happens Automatically

When you create an instructor profile, the system automatically:

✅ **Assigns appropriate permissions** based on role
✅ **Grants staff status** for admin access (where applicable)
✅ **Sets superuser status** for system administrators
✅ **Auto-verifies** system administrators
✅ **Auto-verifies** any profile created by superusers
✅ **Sends welcome email** with login credentials and instructions
✅ **Logs account creation** for audit purposes

## 🔧 Common Tasks

### Verify an Instructor
1. Go to "Instructor Profiles" in admin
2. Find the instructor
3. Change "Verification status" to "Verified"
4. Save

### Bulk Verify Multiple Instructors
1. Go to "Instructor Profiles"
2. Select instructors to verify
3. Choose "Verify selected instructors" action
4. Click "Go"

### Change Instructor Role
1. Edit the instructor profile
2. Change "Instructor role"
3. Save (permissions update automatically)

### Deactivate Instructor
1. Edit instructor profile
2. Uncheck "Is active"
3. Save

## 🚨 Troubleshooting

### Instructor Can't Access Admin
- Check: Is "is_staff" = True?
- Check: Does their role allow admin access?
- Solution: Save the instructor profile again

### Permissions Not Working
- Solution: Go to instructor profile and click "Save"
- This re-triggers the permission assignment

### Need to Reset All Permissions
```bash
python manage.py update_instructor_permissions
```

## 📋 Checklist for New Instructors

- [ ] User account created with proper email
- [ ] Instructor profile created with appropriate role
- [ ] Professional information filled out
- [ ] Verification status set (auto for superuser-created)
- [ ] **Welcome email sent successfully** (check admin messages)
- [ ] **Instructor received email** with login credentials
- [ ] Test login and admin access
- [ ] Confirm permissions work correctly
- [ ] **Instructor completed first login** and changed password

## 🔒 Security Notes

- Only create **System Admin** accounts when absolutely necessary
- **Course Instructors** and **Content Creators** get full admin access
- **Teaching Assistants** and **Graders** have limited access
- All instructor accounts automatically get **staff status**
- **Auto-verification** only happens for superuser-created profiles
- **Passwords don't expire** - instructors can use them indefinitely
- **Password reset** available at `/password_reset/` for forgotten passwords

## 💡 Pro Tips

1. **Use descriptive usernames** (e.g., `john.smith.instructor`)
2. **Fill out all profile fields** for better organization
3. **Use specializations** to categorize instructors
4. **Set office hours** for student communication
5. **Add LinkedIn/website** for professional networking
6. **Inform instructors** that passwords don't expire but can be changed anytime
7. **Share password reset URL** (`/password_reset/`) for forgotten passwords

---

*Need help? Check the full documentation in `instructor_workflow_automation.md`*
