# Handoff: Phase A / B / C — Development Complete

**Date:** 2026-05-13  
**Status:** ✅ All three phases implemented, verified, and tested  
**Test result:** 128 passed, 0 failed (full Playwright suite on Chromium)

---

## สิ่งที่เสร็จสมบูรณ์แล้ว

### Phase A — UX Overhaul

| Feature | ไฟล์ที่เปลี่ยน |
|---------|--------------|
| Staff Sidebar (`_sidebar.html` + `base_staff.html`) | `lms/templates/lms/staff/` |
| Breadcrumb ทุกหน้า student + staff | templates |
| Prev / Next lesson buttons | `lesson.html`, `views.py:LessonView` |
| Progress bar % | `course_detail.html`, `lesson.html`, `views.py` |
| Quiz answer review หลัง submit | `quiz_result.html`, `views.py:QuizView.post()` |
| UI theme redesign: Blue → Teal + Amber | templates ทั้งหมด, `forms.py` |

### Phase B — Feature Essentials

| Feature | URL / ไฟล์ |
|---------|-----------|
| Course search (`?q=`) | `GET /`, `CourseListView`, `course_list.html` |
| Configurable pass threshold | `Course.pass_threshold` field, migration 0003 |
| User Profile page | `GET /profile/`, `UserProfileView`, `profile.html` |
| Certificate serial number | `Certificate.serial_number` (CERT-{BE}-{hex}), migration 0003 |
| Report export CSV | `GET /staff/courses/<id>/report/export/`, StreamingHttpResponse |
| Learner Transcript PDF | `GET /transcript/`, `LearnerTranscriptView`, `transcript_template.html` |

### Phase C — Notifications & Compliance

| Feature | URL / ไฟล์ |
|---------|-----------|
| LINE OA push notification | `lms/line_notify.py`, `User.line_user_id`, migration 0004 |
| Audit Log | `AuditLog` model, `log_audit()` helper, migration 0004 |
| Bulk User Import (CSV) | `POST /staff/users/import/`, `BulkUserImportView`, `bulk_user_import.html` |

---

## โมเดลที่เพิ่มใหม่

| Model / Field | Migration |
|--------------|-----------|
| `Course.pass_threshold` (PositiveIntegerField, default=70) | 0003 |
| `Course.certificate_background` (ImageField, blank) | 0002 |
| `Certificate.serial_number` (CharField, unique, blank) | 0003 |
| `User.line_user_id` (CharField, max_length=50, blank) | 0004 |
| `AuditLog` (user FK, action, target, ip, timestamp) | 0004 |

---

## Audit Actions ที่ใช้งานอยู่

```python
# wired ใน views.py และ utils.py
'login'             # LMSLoginView.form_valid()
'logout'            # LMSLogoutView.post()
'staff_user_create' # LocalUserCreateView.form_valid()
'staff_course_create', 'staff_course_edit', 'staff_course_delete'
'course_complete'   # _mark_completed() ใน utils.py
'certificate_issued'# _mark_completed() เมื่อออก certificate
'bulk_user_import'  # BulkUserImportView.post()
```

---

## URL Map (สำหรับ dev: `http://127.0.0.1:8001`)

### Student URLs (`lms/urls.py`)
```
/                       — Course list (+ search ?q=)
/course/<id>/           — Course detail + progress
/course/<id>/lesson/<id>/ — Lesson + prev/next
/course/<id>/quiz/<pre|post>/ — Quiz
/course/<id>/quiz/<pre|post>/pre/ — Pre-quiz gate
/certificate/<id>/      — Certificate download (PDF)
/profile/               — User profile + quiz history
/transcript/            — Learner transcript (PDF)
/login/, /logout/       — Auth
/users/create/          — Local user create (staff only)
```

### Staff URLs (`lms/staff_urls.py`, prefix `/staff/`)
```
/staff/                         — Dashboard
/staff/courses/                 — Course list
/staff/courses/create/          — Create course
/staff/courses/<id>/edit/       — Edit course
/staff/courses/<id>/delete/     — Delete course
/staff/courses/<id>/lessons/create/ — Create lesson
/staff/courses/<id>/lessons/<id>/edit/ — Edit lesson
/staff/courses/<id>/lessons/<id>/delete/ — Delete lesson
/staff/courses/<id>/quiz/       — Quiz editor
/staff/courses/<id>/quiz/questions/create/ — Add question
/staff/courses/<id>/quiz/questions/<id>/edit/ — Edit question
/staff/courses/<id>/quiz/questions/<id>/delete/ — Delete question
/staff/courses/<id>/report/     — Course report
/staff/courses/<id>/report/export/ — CSV export
/staff/users/import/            — Bulk user import (CSV)
```

---

## ENV vars ที่ใช้งาน

```env
# LINE OA Push (Phase C)
LINE_OA_ENABLED=False          # set True ใน prod เมื่อพร้อม
LINE_OA_CHANNEL_ACCESS_TOKEN=  # จาก LINE Developers console

# NPU Student API
NPU_STUDENT_AUTH_ENABLED=True
NPU_STUDENT_AUTH_URL=https://api.npu.ac.th/v2/ldap/auth_and_get_student/
NPU_STUDENT_AUTH_TOKEN=<token>
NPU_STUDENT_AUTH_TIMEOUT=10
```

---

## Test Coverage (128 tests, 0 failed)

| ไฟล์ | จำนวน tests | ครอบคลุม |
|------|------------|---------|
| `test_login.py` | 8 | login, logout, redirect |
| `test_course_flow.py` | 38 | full student flow, quiz, certificate |
| `test_staff_content.py` | 34 | staff CRUD: course, lesson, quiz, report |
| `test_user_management.py` | 14 | local user create, access control |
| `test_new_features.py` | 26 | search, profile, transcript, bulk import, auth |
| **รวม** | **128** | **0 failed** |

---

## สิ่งที่ยังไม่ได้ทำ / แนะนำ Phase ถัดไป

### P0 — ควรทำก่อน deploy production
- [ ] ทดสอบ LINE OA จริง (ตั้ง `LINE_OA_ENABLED=True` + token จริง)
- [ ] ทดสอบ LDAP บน Windows Server production (python-ldap wheel)
- [ ] ตรวจสอบ `FORCE_SCRIPT_NAME=/courses` + `STATIC_URL=/courses/static/` ใน prod `.env`
- [ ] Run `python manage.py migrate` บน production DB (migrations 0002–0004)

### P1 — Feature ถัดไปที่แนะนำ
- [ ] **Quiz answer review เปิด/ปิด** — staff เลือกได้ว่าจะให้นักศึกษาดูเฉลยไหม
- [ ] **Course prerequisites** — ต้องผ่านวิชา A ก่อนถึงเรียนวิชา B ได้
- [ ] **Question shuffling** — สลับลำดับข้อและตัวเลือกในแต่ละครั้ง
- [ ] **Quiz time limit** — จำกัดเวลาทำข้อสอบ
- [ ] **Department-level access control** — จำกัดวิชาตามคณะ/หน่วยงาน
- [ ] **Enrollment approval** — staff อนุมัติการลงทะเบียนก่อน

### P2 — Analytics & Scale
- [ ] Staff dashboard: กราฟ enrollment trend, pass rate per course
- [ ] Export audit log to CSV
- [ ] File attachment (ไม่ใช่แค่ YouTube link)

---

## หมายเหตุ Dev

- **forms.py widget classes**: ใช้ teal ทั้งหมด (`TEXT_INPUT_CLASS`, `CHECK_INPUT_CLASS`) — ถ้าเพิ่ม field ใหม่ให้ใช้ `apply_tailwind_widgets()` ใน `__init__`
- **transcript_template.html / certificate_template.html**: inline CSS only — ห้ามใช้ Tailwind CDN เพราะ xhtml2pdf ไม่รองรับ JavaScript
- **LINE OA**: ใช้ push individual (ต้องมี `line_user_id`) ไม่ใช่ broadcast — staff กรอก `line_user_id` ใน user form หรือ import CSV
- **AuditLog**: `log_audit()` ใช้ silent pattern (try/except) — failure ไม่ทำให้ request พัง
- **`codex_test` user**: เป็น `is_staff=True` — ใช้ `student_page` fixture (user `663150410020`) สำหรับ test ที่ต้องการ non-staff perspective
