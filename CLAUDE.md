# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Micro-LMS** — a small Learning Management System for the library of Nakhon Phanom University. Supports NPU Active Directory login, YouTube-based lessons, Pre/Post-test quizzes, and E-Certificate generation (PDF).

- **Deploy URL:** `https://lib.npu.ac.th/courses/` (IIS reverse proxy subpath)
- **Dev environment:** WSL2 / Linux
- **Production:** Windows Server + IIS + NSSM + Waitress

## Tech Stack

- **Backend:** Django 5.2+, Python 3.11+, Class-Based Views (CBV)
- **Database:** MySQL (`mysqlclient`)
- **Frontend:** HTML + Tailwind CSS via CDN (no build step)
- **Auth:** NPU student API backend + `django-auth-ldap` (NPU Active Directory) + local fallback
- **Static files:** `whitenoise` (2nd middleware position, after SecurityMiddleware)
- **WSGI:** Waitress (entry: `deploy/waitress_serve.py`)
- **Env vars:** `python-dotenv`
- **Forms:** `django-crispy-forms` + `crispy-tailwind`
- **PDF:** `xhtml2pdf` (for E-Certificate)

## Dev Setup (WSL2)

```bash
# System prereqs (required for python-ldap)
sudo apt install libldap2-dev libsasl2-dev

# Python environment
pip install -r requirements.txt

# Database (create MySQL DB first, then)
python manage.py makemigrations lms
python manage.py migrate
python manage.py createsuperuser

# Run dev server
python manage.py runserver
```

## Project Structure

```
config/             # Django project package (settings, urls, wsgi)
lms/                # Single app — all LMS logic
  models.py
  views.py
  urls.py
  forms.py
  admin.py
  utils.py          # _mark_completed() + generate_certificate_pdf()
  migrations/
  templatetags/
    lms_extras.py   # get_item filter (required for dict lookup in templates)
  templates/
    base.html
    registration/login.html
    lms/
      course_list.html, course_detail.html, lesson.html
      quiz.html, quiz_result.html
      certificate_template.html   # xhtml2pdf — NO Tailwind CDN here
static/lms/fonts/   # Sarabun-Regular.ttf (Thai font for PDF)
media/              # Course thumbnails (dev only)
deploy/
  waitress_serve.py
  install_service.bat
  web.config        # IIS reverse proxy rules (port 8002)
```

## Common Commands

```bash
python manage.py runserver
python manage.py makemigrations lms
python manage.py migrate
python manage.py collectstatic --noinput

# Production (Waitress)
python deploy/waitress_serve.py
```

## Deployment Configuration (Critical)

Settings are env-driven. Dev vs prod values:

| Setting | Dev | Prod |
|---|---|---|
| `FORCE_SCRIPT_NAME` | `''` | `'/courses'` |
| `STATIC_URL` | `'/static/'` | `'/courses/static/'` |
| `DEBUG` | `True` | `False` |
| `WAITRESS_PORT` | any | `8002` |

`settings.py` must always include:
```python
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

**IIS rewrite behavior:** IIS strips the `/courses/` prefix before forwarding to Waitress. Django receives bare paths. `FORCE_SCRIPT_NAME` re-adds `/courses` only for URL generation (`{% url %}`, redirects, `STATIC_URL`).

## Data Models

| Model | Key Fields / Notes |
|---|---|
| `User(AbstractUser)` | `department` (CharField, blank) — synced from AD |
| `Course` | `title`, `description`, `thumbnail(ImageField)`, `require_post_test(Bool)`, `is_active(Bool)` |
| `Lesson` | `course(FK)`, `title`, `youtube_video_id`, `order` — Meta ordering: `['order']` |
| `Quiz` | `course(FK)`, `quiz_type('pre'/'post')` — unique_together: `(course, quiz_type)` |
| `Question` | `quiz(FK)`, `text`, `order` |
| `Answer` | `question(FK)`, `text`, `is_correct(Bool)` |
| `UserProgress` | `user(FK)`, `course(FK)`, `status('in_progress'/'completed')`, `lessons_completed(M2M→Lesson)` — unique_together: `(user, course)` |
| `UserQuizAttempt` | `user(FK)`, `quiz(FK)`, `score_percentage(Float)`, `is_passed(Bool)`, `attempted_at` |
| `Certificate` | `user(FK)`, `course(FK)`, `issued_at` — unique_together: `(user, course)` |

`AUTH_USER_MODEL = 'lms.User'` must be set in settings **before** the first migration. Never change after.

## Authentication

Authentication backend order:
1. `lms.auth_backends.NPUStudentAPIBackend` — student login via NPU API
2. `django_auth_ldap.backend.LDAPBackend` — staff login via AD when `LDAP_ENABLED=True`
3. `django.contrib.auth.backends.ModelBackend` — local admin/test users

Student API config:
```env
NPU_STUDENT_AUTH_ENABLED=True
NPU_STUDENT_AUTH_URL=https://api.npu.ac.th/v2/ldap/auth_and_get_student/
NPU_STUDENT_AUTH_TOKEN=<token>
NPU_STUDENT_AUTH_TIMEOUT=10
```

Student backend behavior:
- POST body uses `userLdap` and `passLdap`
- Backend only calls the API for 12-digit numeric usernames (`NPU_STUDENT_CODE_LENGTH=12`) so staff/local accounts do not generate student API noise
- `student_info.student_code` maps to `User.username`
- `student_name` / `student_surname` map to `first_name` / `last_name`
- `faculty_name / program_name` maps to `department`
- Django password is set unusable; do not store the LDAP/API password locally

Local user creation:
- Admin/staff page: `/users/create/`
- View: `LocalUserCreateView`
- Form: `LocalUserCreationForm`
- Access is restricted to authenticated `is_staff=True` users
- Use this for staff/local accounts while student accounts continue through the NPU API backend
- Browser coverage is in `tests/test_user_management.py`

Staff content frontend:
- URL prefix: `/staff/`
- URL file: `lms/staff_urls.py`
- Staff dashboard: `staff-dashboard`
- Course CRUD, Lesson CRUD, Quiz/Question CRUD, and course report are implemented in `lms/views.py`
- Templates live in `lms/templates/lms/staff/`
- Access is restricted to authenticated `is_staff=True` users via `StaffRequiredMixin`
- Browser coverage is in `tests/test_staff_content.py`

## Business Logic

- **Passing score:** 70% for Post-test
- **Completion trigger** (`lms/utils.py:_mark_completed`):
  - `require_post_test=False`: all lessons in `lessons_completed` M2M → `'completed'`
  - `require_post_test=True`: Post-test `is_passed=True` → `'completed'`
- **Certificate:** `Certificate.objects.get_or_create(user, course)` — called inside `_mark_completed`, idempotent
- **Progress init:** `UserProgress` created via `get_or_create` on first lesson/detail view

## Quiz Scoring (lms/views.py:QuizView.post)

```python
score_pct = correct / total * 100
is_passed = score_pct >= 70
UserQuizAttempt.objects.create(user, quiz, score_percentage, is_passed)
if quiz_type == 'post' and is_passed:
    _mark_completed(user, course, progress)
```

## PDF Certificate

- Library: `xhtml2pdf` (no system binary needed, safe on Windows Server)
- Thai font: `Sarabun-Regular.ttf` in `static/lms/fonts/` — must use `link_callback` to map `STATIC_URL` → `STATIC_ROOT` filesystem path; CDN fonts do NOT work in xhtml2pdf
- Template `certificate_template.html`: inline CSS only (A4 landscape), no Tailwind CDN
- `CertificateDownloadView`: guards with `get_object_or_404(Certificate, user=request.user, course=course)`

## Admin Structure

3-level nesting (Course → Quiz → Questions → Answers) via `show_change_link=True`:
- `CourseAdmin`: inlines = `[LessonInline, QuizInline]`; `QuizInline` has `show_change_link=True`
- `QuestionAdmin`: inlines = `[AnswerInline]`; accessible by clicking into a Quiz

## Template Notes

- `{% load lms_extras %}` required in any template using `|get_item` filter
- `get_item` filter in `lms/templatetags/lms_extras.py` enables `dict|get_item:variable_key` (Django templates can't do `dict[var]` natively)
- LDAP dev fallback: set `AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']` and use `createsuperuser` until AD credentials are available

## Known Gotchas

1. `python-ldap` on Windows Server requires build tools or prebuilt wheel — test this early in deployment
2. `WhiteNoiseMiddleware` must be **2nd** in `MIDDLEWARE` (right after `SecurityMiddleware`)
3. xhtml2pdf cannot use JavaScript or CDN — all CSS must be inline or in a `<style>` block
4. `FORCE_SCRIPT_NAME` and `STATIC_URL` must be set as a matching pair (see table above)
5. Django admin does not support 3-level inline nesting natively — use `show_change_link=True`
6. Add `lms/templatetags/__init__.py` (empty file) or the templatetag won't load

## Development Phases

| Phase | Scope |
|---|---|
| 1 | Project bootstrap: `requirements.txt`, `config/settings.py`, `.env.example`, Django project init |
| 2 | Models + migrations (`lms/models.py`) |
| 3 | Auth: LDAP config, `LMSLoginView`, login template |
| 4 | Core views: `CourseListView`, `CourseDetailView`, `LessonView`, `utils._mark_completed` |
| 5 | Quiz: `QuizSubmitForm`, `QuizView`, scoring logic |
| 6 | Certificate PDF: `generate_certificate_pdf`, `link_callback`, `certificate_template.html` |
| 7 | Admin: all `ModelAdmin` classes with inlines |
| 8 | Templates: all HTML + Tailwind CDN polish |
| 9 | Production: `deploy/waitress_serve.py`, `install_service.bat`, `web.config` |
