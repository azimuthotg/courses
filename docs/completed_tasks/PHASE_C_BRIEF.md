# Phase C Brief — LINE OA Notification, Audit Trail, Bulk User Import

**Source task:** `TASK_PHASE_C_NOTIFICATIONS.md`
**Project:** Micro-LMS / NPU Library LMS
**Prepared:** 12 May 2026
**Status:** Brief only; implementation not yet started in this brief.

## Objective

Phase C adds operational features that are common in enterprise LMS deployments:

1. LINE OA push notification when a learner passes/completes and receives a certificate.
2. Database audit trail for important learner and staff actions.
3. Staff CSV bulk import for local users.

Implement in the task order because later work depends on earlier fields/helpers:

```text
LINE OA user field/settings
→ AuditLog model/helper
→ Bulk CSV import using line_user_id
```

## Current Baseline Before Phase C

Relevant existing Phase A/B work:

- Staff navigation is in `lms/templates/lms/staff/_sidebar.html`.
- Staff pages extend `lms/templates/lms/staff/base_staff.html`.
- Certificates already have `Certificate.serial_number`.
- Completion/certificate issuance is centralized through `lms/utils.py:mark_completed()`.
- `UserQuizAttempt.attempt_type` distinguishes `pre` and `post`.
- Profile and transcript already exist:
  - `/profile/`
  - `/transcript/`
- Report CSV export already exists:
  - `/staff/courses/<pk>/report/export/`

## Work 1 — LINE OA Push Notification

### Purpose

Notify a learner through LINE OA when a course is completed and the certificate is issued.

### Required Changes

- `requirements.txt`
  - Add `requests>=2.31` if it is not already present.

- `.env.example`
  - Add:
    ```env
    LINE_OA_ENABLED=False
    LINE_OA_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
    ```

- `config/settings.py`
  - Follow current settings pattern using `os.getenv`, not `env.bool`.
  - Add:
    ```python
    LINE_OA_ENABLED = os.getenv('LINE_OA_ENABLED', 'False').lower() in ('true', '1', 'yes')
    LINE_OA_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_OA_CHANNEL_ACCESS_TOKEN', '')
    ```

- `lms/models.py`
  - Add `User.line_user_id`.
  - Requires migration.

- `lms/line_notify.py`
  - New helper module.
  - Use `requests.post()` to LINE push endpoint.
  - Must be fail-closed and return `False` if disabled, missing token, missing user ID, or request fails.
  - Do not interrupt learner flow if LINE fails.

- `lms/utils.py`
  - In `mark_completed()`, use:
    ```python
    certificate, created = Certificate.objects.get_or_create(...)
    if created:
        notify_course_completed(user, course, certificate)
    ```
  - Send only on first certificate creation, not every repeated completion check.

- `lms/forms.py`
  - Add `line_user_id` to `LocalUserCreationForm`.

- `lms/templates/lms/local_user_form.html`
  - Add optional LINE User ID field and help text.

### Risk Notes

- LINE API must never block completion flow.
- Keep `LINE_OA_ENABLED=False` as default.
- Do not store channel token anywhere except env.
- `requests` may already be installed indirectly, but still pin/add it in `requirements.txt`.

## Work 2 — Audit Trail

### Purpose

Store important events in DB for admin review.

### Required Changes

- `lms/models.py`
  - Add `AuditLog` model:
    - `user`
    - `action`
    - `description`
    - `ip_address`
    - `created_at`
  - Requires migration.

- `lms/utils.py`
  - Add `log_audit(user, action, description='', request=None)`.
  - It must silently ignore failures and never interrupt a user flow.
  - Extract client IP from `HTTP_X_FORWARDED_FOR` first, then `REMOTE_ADDR`.

- `lms/views.py`
  - Add audit calls in key places:
    - Login success: `login`
    - Quiz pass/fail: `quiz_pass` / `quiz_fail`
    - Staff course create/edit/delete
    - Staff local user create
  - For completion and certificate-issued events, prefer logging from `mark_completed()` so all completion paths are covered.

- `lms/admin.py`
  - Register `AuditLogAdmin`.
  - Make logs read-only:
    - no add permission
    - no change permission
  - Include filters for `action` and `created_at`.

### Suggested Action Coverage

Recommended action list:

```text
login
logout
course_complete
quiz_pass
quiz_fail
certificate_issued
staff_course_create
staff_course_edit
staff_course_delete
staff_user_create
bulk_user_import
```

### Risk Notes

- Be careful not to create noisy duplicate `course_complete` logs when `mark_completed()` is called repeatedly.
- Use certificate `created` flag to log `certificate_issued` once.
- Login audit should use `self.request`, not an undefined `request`.

## Work 3 — Bulk User Import CSV

### Purpose

Allow staff to create many local users from a CSV upload.

### Required Changes

- `lms/views.py`
  - Add `BulkUserImportView(LoginRequiredMixin, StaffRequiredMixin, View)`.
  - Read uploaded CSV as `utf-8-sig`.
  - Use `csv.DictReader`.
  - Skip duplicate usernames.
  - Hash plaintext passwords with `set_password`.
  - Use `set_unusable_password()` when password is blank.
  - Support optional `line_user_id`.
  - Add success/warning/error messages.
  - Consider logging `bulk_user_import` with created/skipped/error counts.

- `lms/staff_urls.py`
  - Add:
    ```python
    path('users/import/', views.BulkUserImportView.as_view(), name='staff-bulk-user-import')
    ```

- `lms/templates/lms/staff/bulk_user_import.html`
  - New staff page extending `lms/staff/base_staff.html`.
  - Show required CSV format.
  - Include file input and submit button.

- `lms/templates/lms/staff/_sidebar.html`
  - Add link to `staff-bulk-user-import`.

### CSV Format

```csv
username,first_name,last_name,email,department,password,is_staff,line_user_id
staff001,สมชาย,ใจดี,somchai@npu.ac.th,สำนักวิทยบริการ,Pass1234!,False,
staff002,สมหญิง,รักดี,somying@npu.ac.th,สำนักวิทยบริการ,Pass1234!,True,Uxxxxx
```

### Risk Notes

- Validate CSV extension and missing file.
- Do not echo passwords back to UI.
- Avoid creating partial duplicate users on repeated import.
- Keep error display capped, e.g. first 10 errors.

## Expected Migrations

One migration can cover both:

- `User.line_user_id`
- `AuditLog`

Potential name:

```text
lms/migrations/0004_user_line_user_id_auditlog.py
```

Run:

```bash
./venv/bin/python manage.py makemigrations lms
./venv/bin/python manage.py migrate
```

## Verification Plan

### Fast Checks

```bash
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
```

### Django Client Smoke Tests

Recommended smoke routes:

```text
/users/create/                         200 for staff
/staff/users/import/                   200 for staff
/admin/lms/auditlog/                   reachable for admin
```

Recommended behavior checks:

- `LINE_OA_ENABLED=False` and a completion event should not error.
- Completing a course creates a certificate and no duplicate notification call should occur on repeat completion.
- Login or quiz submit creates `AuditLog` rows.
- CSV upload creates local users and skips duplicates.

### Playwright Targeted Suites

Run impacted suites first:

```bash
./venv/bin/python -m pytest tests/test_user_management.py tests/test_staff_content.py tests/test_course_flow.py --browser chromium -q
```

Full suite after targeted green:

```bash
./venv/bin/python -m pytest tests/ --browser chromium -v
```

## Implementation Order

1. Add dependency/env/settings for LINE OA.
2. Add `User.line_user_id` and local user form/template field.
3. Add `lms/line_notify.py`.
4. Update `mark_completed()` for notification on new certificate only.
5. Add `AuditLog` model, migration, helper, admin registration.
6. Add audit calls in views/utils.
7. Add bulk import view, URL, template, sidebar link.
8. Run migrations and checks.
9. Run smoke tests and targeted Playwright tests.

## Open Questions For Phase C Implementation

- Should student self-service LINE binding be added later, or will staff manually enter `line_user_id`?
- Should bulk-imported users default to `is_active=True` if the CSV omits a value? Recommended: yes.
- Should audit logs include object IDs in `description` for easier traceability? Recommended: include course/user identifiers when available.
- Should LINE notify also be sent specifically on post-test pass before certificate issuance, or only on certificate creation? Task says both pass and completion, but current completion path issues certificate after post-test pass. Recommended implementation: one notification on certificate creation to avoid duplicate messages, unless separate messages are explicitly required.
