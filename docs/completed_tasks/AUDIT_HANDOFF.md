# Claude Audit Handoff

**Date prepared:** 12 May 2026
**Project:** Micro-LMS / NPU Library LMS
**Primary app:** `lms`
**Deployment target:** `https://lib.npu.ac.th/courses/`

This document is a focused handoff for a Claude audit pass. Broader project notes are in `CLAUDE.md`; full progress history is in `PROGRESS.md`.

## Latest Codex Update - 12 May 2026

### Phase C Brief Prepared

Codex read `TASK_PHASE_C_NOTIFICATIONS.md` and prepared a Phase C implementation brief:

- `PHASE_C_BRIEF.md`

The brief covers:

- LINE OA push notification scope and risks.
- AuditLog model/helper/admin coverage.
- Bulk user import CSV workflow.
- Expected migration shape.
- Suggested implementation order.
- Verification plan and targeted Playwright suites.
- Open questions for implementation.

No Phase C code implementation has been started as part of the brief.

### Phase B Feature Essentials

Codex completed `TASK_PHASE_B_FEATURES.md` tasks 1-6:

1. **Course search and filter**
   - `CourseListView` now supports `?q=` search across active course `title` and `description`.
   - `course_list.html` includes search, submit, and clear controls.
   - Empty search results show a specific "ไม่พบวิชา..." message.

2. **Configurable pass threshold**
   - Added `Course.pass_threshold` with default `70`.
   - `CourseForm` exposes `pass_threshold` for staff editing.
   - `QuizView.post()` now uses `course.pass_threshold` instead of hardcoded 70.
   - Quiz and result templates show the course-specific threshold.

3. **User profile page**
   - Added `UserProfileView`.
   - Added `/profile/` route named `user-profile`.
   - Added `lms/templates/lms/profile.html`.
   - Navbar username now links to profile.
   - Profile shows learner info, progress history, best score, and certificate links.

4. **Certificate serial number**
   - Added `Certificate.serial_number`, unique, generated as `CERT-{BE_YEAR}-{XXXXXX}`.
   - Existing certificates were backfilled during migration.
   - Certificate PDF template now displays serial number in both default and background-overlay layouts.

5. **Staff report export CSV**
   - Added `StaffCourseReportExportView`.
   - Added `/staff/courses/<pk>/report/export/` route named `staff-course-report-export`.
   - Course report page has an `Export CSV` button.
   - CSV includes UTF-8 BOM for Thai Excel compatibility and columns for learner, status, lesson count, post-test score, pass/fail, and certificate presence.

6. **Learner transcript PDF**
   - Added `LearnerTranscriptView`.
   - Added `/transcript/` route named `learner-transcript`.
   - Added `lms/templates/lms/transcript_template.html`.
   - Profile page includes a `ดาวน์โหลด Transcript PDF` button.
   - Transcript PDF shows learner info, enrolled courses, status, best post-test score, and certificate serial number.

Files changed for Phase B:

- `lms/models.py`
- `lms/forms.py`
- `lms/views.py`
- `lms/urls.py`
- `lms/staff_urls.py`
- `lms/admin.py`
- `lms/templates/base.html`
- `lms/templates/lms/course_list.html`
- `lms/templates/lms/quiz.html`
- `lms/templates/lms/quiz_result.html`
- `lms/templates/lms/certificate_template.html`
- `lms/templates/lms/staff/course_report.html`
- `lms/templates/lms/profile.html`
- `lms/templates/lms/transcript_template.html`
- `tests/test_user_management.py`

Migration added and applied:

- `lms/migrations/0003_certificate_serial_number_course_pass_threshold.py`

Migration result:

```text
Applying lms.0003_certificate_serial_number_course_pass_threshold... OK
```

Verification performed:

```text
./venv/bin/python manage.py check
System check identified no issues (0 silenced).

./venv/bin/python manage.py makemigrations --check --dry-run
No changes detected
```

Manual Django client smoke test:

```text
/?q=<course search>                       200 text/html
/profile/                                200 text/html
/transcript/                             200 application/pdf
/staff/courses/<id>/report/export/       200 text/csv; charset=utf-8-sig
/course/<id>/quiz/post/                  200 text/html
certificate serial sample: CERT-2569-7940B2
course pass_threshold sample: 70
```

Threshold behavior check:

```text
temporary course pass_threshold: 101
post-test score: 100.0
is_passed: False
```

Targeted Playwright verification:

```text
./venv/bin/python -m pytest tests/test_course_flow.py tests/test_staff_content.py tests/test_user_management.py --browser chromium -q
Initial result: 88 passed, 4 failed
Failure reason: old user-management tests still expected the removed navbar "เพิ่มผู้ใช้" link after Phase A moved staff navigation to the sidebar.

Updated tests/test_user_management.py to assert the sidebar "จัดการผู้ใช้" link instead.

./venv/bin/python -m pytest tests/test_user_management.py --browser chromium -q
14 passed in 489.28s
```

Notes for Claude:

- Full `tests/` suite was not rerun after Phase B; targeted suites covering course flow, staff content, and user management were exercised.
- Course and staff tests were green in the combined targeted run; only obsolete navbar expectations failed and were updated.
- `forms.py` still contains older blue Tailwind constants for generated form widgets from before the theme task. This was not changed in Phase B because the task did not request theme cleanup.

### Phase A UX Overhaul

Codex completed `TASK_PHASE_A_UX_OVERHAUL.md` tasks 1-5:

1. **Staff left sidebar**
   - Added `lms/templates/lms/staff/_sidebar.html`.
   - Added `lms/templates/lms/staff/base_staff.html`.
   - Removed staff-only links from the global navbar in `base.html`.
   - Converted staff templates to extend `lms/staff/base_staff.html` and use `staff_content`.
   - Sidebar links cover Dashboard, course management, local user creation, and Django Admin.

2. **Breadcrumb navigation**
   - Added breadcrumbs to student pages:
     - course detail
     - lesson
     - quiz
     - quiz result
   - Added breadcrumbs to staff pages:
     - dashboard
     - course list
     - course create/edit
     - lesson form
     - quiz edit
     - course report

3. **Previous / next lesson navigation**
   - `LessonView.get()` now computes `prev_lesson`, `next_lesson`, `lesson_number`, and `lesson_total`.
   - `lesson.html` displays lesson count and previous/next controls.
   - Final lesson shows a "กลับหน้าวิชา" action.

4. **Progress bar**
   - `CourseDetailView.get_context_data()` now sends:
     - `lessons_total`
     - `lessons_done`
     - `progress_pct`
   - `LessonView.get()` sends the same progress context.
   - `course_detail.html` and `lesson.html` show progress count and percentage bar.

5. **Quiz answer review**
   - `QuizView.post()` now builds `answer_review`.
   - `quiz_result.html` shows each question, learner answer, correctness, and correct answer for wrong responses.

Files changed for Phase A:

- `lms/views.py`
- `lms/templates/base.html`
- `lms/templates/lms/staff/_sidebar.html`
- `lms/templates/lms/staff/base_staff.html`
- `lms/templates/lms/staff/dashboard.html`
- `lms/templates/lms/staff/course_list.html`
- `lms/templates/lms/staff/course_form.html`
- `lms/templates/lms/staff/course_confirm_delete.html`
- `lms/templates/lms/staff/course_report.html`
- `lms/templates/lms/staff/lesson_form.html`
- `lms/templates/lms/staff/lesson_confirm_delete.html`
- `lms/templates/lms/staff/quiz_edit.html`
- `lms/templates/lms/staff/question_form.html`
- `lms/templates/lms/staff/question_confirm_delete.html`
- `lms/templates/lms/course_detail.html`
- `lms/templates/lms/lesson.html`
- `lms/templates/lms/quiz.html`
- `lms/templates/lms/quiz_result.html`
- `tests/test_course_flow.py`

Verification performed:

```text
./venv/bin/python manage.py check
System check identified no issues (0 silenced).
```

Manual Django client smoke test:

```text
/staff/                         200
/staff/courses/                 200
/staff/courses/<id>/edit/       200
/staff/courses/<id>/quiz/post/  200
/staff/courses/<id>/report/     200
/course/<id>/                   200
/course/<id>/lesson/<id>/       200
/course/<id>/quiz/pre/          200
/course/<id>/quiz/post/         200
POST quiz result includes answer review: True
```

Targeted Playwright verification:

```text
./venv/bin/python -m pytest tests/test_course_flow.py --browser chromium -q
36 passed in 275.88s

./venv/bin/python -m pytest tests/test_staff_content.py --browser chromium -q
42 passed in 1440.28s
```

Notes for Claude Phase 2:

- Full suite was not rerun in this pass; impacted suites passed 78/78 tests.
- `tests/test_course_flow.py` had one selector updated from a broad text locator to a heading locator because breadcrumbs now duplicate the course title on the page.
- Business logic remains unchanged except the requested view context additions and quiz answer review data preparation.

### Shared Quiz and Certificate Update

Codex implemented two requested logic changes:

1. **Shared Pre-test / Post-test question set**
   - Pre-test and Post-test now use one shared question set per course.
   - The canonical quiz record is the course `post` quiz.
   - If legacy `pre` questions exist and the `post` quiz has no questions, migration moves those questions to the `post` quiz.
   - Existing legacy pre attempts are moved onto the canonical quiz and preserved through `UserQuizAttempt.attempt_type`.
   - Student URLs remain unchanged:
     - `/course/<course_pk>/quiz/pre/`
     - `/course/<course_pk>/quiz/post/`
   - Staff URLs remain compatible, but UI now presents one shared "ชุดคำถาม Pre-test / Post-test".
   - Post-test remains the only attempt type that triggers course completion and certificate issuance.

2. **Certificate background upload + centered overlay**
   - Added `Course.certificate_background`.
   - Staff course form can upload a per-course certificate background image.
   - Certificate PDF template now renders the uploaded background when present.
   - Learner full name and course title are overlaid in the center of the certificate.
   - If no background is uploaded, the previous default certificate layout is still used.

Files changed in this update:

- `lms/models.py`
- `lms/views.py`
- `lms/forms.py`
- `lms/admin.py`
- `lms/templates/lms/quiz.html`
- `lms/templates/lms/quiz_result.html`
- `lms/templates/lms/certificate_template.html`
- `lms/templates/lms/staff/course_form.html`
- `lms/templates/lms/staff/quiz_edit.html`
- `lms/templates/lms/staff/question_form.html`
- `lms/templates/lms/staff/question_confirm_delete.html`
- `lms/templates/lms/staff/course_report.html`
- `tests/test_staff_content.py`
- `docs/FLOWS.md`
- `docs/flow-student.mmd`
- `docs/flow-staff.mmd`
- `docs/flow-student.png`
- `docs/flow-staff.png`

Migration added and applied:

- `lms/migrations/0002_course_certificate_background_and_more.py`

Migration result:

```text
Applying lms.0002_course_certificate_background_and_more... OK
```

Verification performed:

```text
./venv/bin/python manage.py check
System check identified no issues (0 silenced).

./venv/bin/python -m pytest tests/test_staff_content.py --browser chromium -q
42 passed in 1702.02s
```

Manual Django client verification:

```text
/course/102/lesson/34/       200
/course/102/quiz/pre/        200
/course/102/quiz/post/       200
/staff/courses/102/edit/     200
/staff/courses/102/quiz/post/ 200
```

Shared quiz verification for course 102:

```text
course: openVPN
quiz_id: 46
quiz_type: post
questions: 4
```

Pre/Post behavior check:

```text
pre_status: 200
post_status: 200
attempts: [('post', True, 100.0), ('pre', True, 100.0)]
certificate: True
```

Certificate PDF check:

```text
pdf_ok: True
header: b'%PDF'
```

## Current Implementation Status

The main LMS implementation is complete through these areas:

- Django project setup with env-driven settings.
- Custom `User` model with `department`.
- Student login through NPU student API backend.
- Staff/local fallback login through Django `ModelBackend`.
- Optional staff LDAP backend configuration.
- Course, lesson, quiz, progress, attempt, and certificate models.
- Pre-test and post-test now use one shared question set per course; `UserQuizAttempt.attempt_type` records whether a submission was `pre` or `post`.
- Student-facing course list, course detail, lesson, quiz, result, and certificate download views.
- Certificate PDF generation through `xhtml2pdf`, with optional per-course certificate background image upload and centered learner/course text overlay.
- Django admin configuration for all LMS models.
- Staff content-management frontend under `/staff/`.
- Local user creation page under `/users/create/`.
- Basic production deployment files for Waitress, NSSM, and IIS reverse proxy.

## Important Files For Audit

- `config/settings.py` - security, env loading, auth backend order, proxy/subpath config.
- `config/urls.py` - global routing and auth routes.
- `lms/models.py` - data model constraints and relationships.
- `lms/views.py` - core CBV behavior, staff permissions, quiz flow, certificate access.
- `lms/forms.py` - dynamic quiz form and staff content forms.
- `lms/auth_backends.py` - NPU student API authentication.
- `lms/utils.py` - course completion and certificate PDF generation.
- `lms/admin.py` - admin model management.
- `lms/staff_urls.py` - staff-management routes.
- `lms/templates/` - user and staff UI templates.
- `deploy/web.config` - IIS reverse proxy rules.
- `deploy/waitress_serve.py` - production WSGI entrypoint.
- `tests/` - browser test suite.

## Latest Recorded Test Result

### Phase C Targeted Verification - 12 May 2026

Phase C implementation was completed for LINE OA notification support, audit trail, and bulk user CSV import.

Commands/checks run:

```text
./venv/bin/python manage.py migrate
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python -m pytest tests/test_user_management.py tests/test_login.py
```

Results:

```text
lms.0004_user_line_user_id_auditlog applied OK
System check identified no issues
No changes detected
12 passed in 353.33s
```

Additional Django-client smoke checks passed:

- `/staff/users/import/` loads for staff and imports CSV users.
- Bulk import stores `line_user_id`, hashes password, skips duplicate username, and writes `bulk_user_import` audit log.
- `mark_completed()` creates certificate, writes `course_complete` and `certificate_issued`, and does not error when `LINE_OA_ENABLED=False`.
- Post-test fail/pass writes `quiz_fail` / `quiz_pass`; passing post-test still completes the course and creates a certificate.
- Staff course create/edit/delete writes audit logs and preserves existing redirect behavior.

Files changed/added for Phase C:

- `requirements.txt` - added `requests>=2.31`.
- `.env.example` - added `LINE_OA_ENABLED` and `LINE_OA_CHANNEL_ACCESS_TOKEN`.
- `config/settings.py` - added LINE OA settings through existing `os.getenv` pattern.
- `lms/models.py` - added `User.line_user_id` and new `AuditLog` model.
- `lms/migrations/0004_user_line_user_id_auditlog.py` - migration for LINE user ID and audit logs.
- `lms/line_notify.py` - LINE Messaging API push helper.
- `lms/utils.py` - added `log_audit()` and completion notification/audit behavior.
- `lms/views.py` - added audit calls and `BulkUserImportView`.
- `lms/forms.py` - added `line_user_id` to `LocalUserCreationForm`.
- `lms/admin.py` - added `AuditLogAdmin` and `line_user_id` in user admin.
- `lms/staff_urls.py` - added `staff/users/import/`.
- `lms/templates/lms/local_user_form.html` - added LINE User ID field.
- `lms/templates/lms/staff/_sidebar.html` - added CSV import staff menu link.
- `lms/templates/lms/staff/bulk_user_import.html` - new CSV import UI.

Note: full `tests/` suite was not rerun for Phase C; targeted Playwright and smoke tests were run against the changed areas.

---

Recorded in `PROGRESS.md` from 11 May 2026:

```text
python -m pytest tests/ --browser chromium -v
102 passed, 0 failed
```

Coverage groups recorded:

- Login / logout.
- Course list and detail.
- Lesson view.
- Post-test quiz flow.
- Course completion.
- Certificate download.
- Local user management.
- Staff content management.

Note: this handoff did not rerun the test suite on 12 May 2026; it records the latest documented result from the previous work session.

## Suggested Claude Audit Checklist

1. Review `config/settings.py` for production safety:
   - `DEBUG=False` behavior.
   - `ALLOWED_HOSTS`.
   - `SECRET_KEY` source.
   - cookie/session security for HTTPS.
   - `FORCE_SCRIPT_NAME=/courses` behavior.
   - `USE_X_FORWARDED_HOST` and `SECURE_PROXY_SSL_HEADER`.

2. Review authentication:
   - backend order in `AUTHENTICATION_BACKENDS`.
   - NPU student API error handling and timeouts.
   - confirmation that student API passwords are never stored.
   - staff/local fallback behavior.
   - LDAP settings and disabled/enabled behavior.

3. Review authorization:
   - staff pages restricted to `is_staff=True`.
   - local user creation restricted to staff.
   - certificate download restricted to certificate owner.
   - course and quiz access rules for inactive courses.

4. Review quiz and completion logic:
   - shared question set behavior for both `pre` and `post`.
   - `UserQuizAttempt.attempt_type` separation for reporting and completion.
   - score calculation and divide-by-zero behavior.
   - 70 percent passing rule.
   - idempotent certificate creation.
   - behavior when course requirements or lessons change after progress exists.

5. Review staff content CRUD:
   - validation for lesson ordering.
   - quiz auto-create behavior.
   - question and answer validation.
   - delete behavior and cascades.
   - report calculations.

6. Review certificate PDF:
   - optional `Course.certificate_background` rendering.
   - centered overlay of learner name and course title.
   - Thai font resolution through staticfiles.
   - filesystem path handling on Windows Server.
   - PDF error handling.
   - response headers and access control.

7. Review deployment files:
   - IIS rewrite behavior for `/courses/`.
   - Waitress port and static/media handling.
   - `collectstatic` expectations.
   - Windows service startup path and environment.

8. Review tests:
   - whether Playwright tests depend on existing database state.
   - whether tests clean up created records.
   - whether CI or repeatable local setup is documented enough.

## Known Gaps / Follow-Up Items

- Staff LDAP login still needs real NPU AD credentials and a live login test.
- Production dry run still needs to be performed on the Windows/IIS target.
- `web.config` requires IIS URL Rewrite server variable allowance for `HTTP_X_FORWARDED_PROTO=https`.
- Latest test result is documented from 11 May 2026; rerun tests before final production release.
- Secrets and tokens must remain in `.env` only and must not be committed.

## Existing Documentation

- `CLAUDE.md` - architecture, commands, conventions, gotchas.
- `PROGRESS.md` - detailed implementation progress and recorded test results.
- `gemini-code-1778470863932.md` - earlier high-level project specification.
