# Micro-LMS — Progress Report

**วันที่อัพเดต:** 11 พฤษภาคม 2569
**ระบบ:** NPU Library LMS — `https://lib.npu.ac.th/courses/`
**Dev Server:** `http://localhost:8001/` (รันอยู่)
**Database:** MySQL @ 202.29.55.213 / `arc_courses`

---

## สถานะรวม

| Phase | รายการ | สถานะ |
|---|---|---|
| 1 | Project Bootstrap | ✅ เสร็จ |
| 2 | Models & Migrations | ✅ เสร็จ |
| 3 | Auth (Student API + LDAP config) | ✅ นักศึกษาพร้อมใช้ / LDAP staff รอ credentials |
| 4 | Core Views | ✅ เสร็จ |
| 5 | Quiz System | ✅ เสร็จ |
| 6 | Certificate PDF | ✅ เสร็จ |
| 7 | Django Admin | ✅ เสร็จ |
| 8 | Templates (HTML) | ✅ เสร็จ |
| 9 | Production Config | ✅ ไฟล์พื้นฐานเสร็จ |
| 10 | Staff Content Frontend | ✅ เสร็จ |

---

## Phase ที่เสร็จแล้ว

### Phase 1 — Project Bootstrap ✅

- `requirements.txt` — ครบทุก package
- `venv` — Python 3.12 + packages ติดตั้งครบ
- Django 6.0.5 project scaffold สร้างแล้ว (`config/` + `lms/`)
- `config/settings.py` — env-driven ด้วย python-dotenv
  - `AUTH_USER_MODEL = 'lms.User'`
- `FORCE_SCRIPT_NAME` / `STATIC_URL` เปลี่ยนตาม env (dev vs prod)
- `WhiteNoiseMiddleware` ตำแหน่ง 2 ใน MIDDLEWARE
- `FILE_UPLOAD_PERMISSIONS = None` เพื่อเลี่ยงปัญหา chmod บน WSL/Windows mount ตอน `collectstatic`
- LDAP เปิดใช้งานผ่าน `LDAP_ENABLED=True` ใน `.env`
  - `CRISPY_TEMPLATE_PACK = 'tailwind'`
- `.env` — ตั้งค่า MySQL และ dev config แล้ว
- `.env.example` — template สำหรับ production
- `.gitignore` — ครอบคลุม venv, .env, media, staticfiles

### Phase 2 — Models & Migrations ✅

ไฟล์: `lms/models.py`, `lms/migrations/0001_initial.py`

| Model | สถานะ |
|---|---|
| `User(AbstractUser)` | ✅ มี `department` field |
| `Course` | ✅ ครบทุก field |
| `Lesson` | ✅ มี `youtube_video_id`, `order` |
| `Quiz` | ✅ unique_together (course, quiz_type) |
| `Question` | ✅ |
| `Answer` | ✅ มี `is_correct` |
| `UserProgress` | ✅ มี `lessons_completed` M2M |
| `UserQuizAttempt` | ✅ |
| `Certificate` | ✅ unique_together (user, course) |

- `python manage.py migrate` — **รันสำเร็จ** ทุก table สร้างแล้วใน DB
- สร้าง superuser `admin` / `admin1234` แล้ว

### Phase 3 — Auth ✅ (นักศึกษาพร้อมใช้ / staff LDAP รอ credentials)

- `LMSLoginView`, `LMSLogoutView` ใน `lms/views.py`
- หน้า `registration/login.html` — ใช้งานได้แล้ว
- `lms/auth_backends.py` — `NPUStudentAPIBackend` สำหรับนักศึกษา
  - POST ไปที่ `https://api.npu.ac.th/v2/ldap/auth_and_get_student/`
  - ส่ง body: `userLdap`, `passLdap`
  - token อ่านจาก `.env` key `NPU_STUDENT_AUTH_TOKEN`
  - สร้าง/อัปเดต `User` จาก `student_info`
  - ตั้ง password ใน Django เป็น unusable เพื่อไม่เก็บรหัสผ่าน LDAP/API
  - map `department` เป็น `faculty_name / program_name`
- ทดสอบ student auth จริงผ่าน API สำเร็จ ✅
  - user: `663150410020`
  - ได้ชื่อ-นามสกุลและคณะ/สาขากลับมา
  - `is_staff=False`, `password_usable=False`
- ใส่ `NPU_STUDENT_AUTH_TOKEN` ใน `.env` แล้ว ✅
- ทดสอบ student login ผ่าน browser หน้า `/login/` สำเร็จ ✅
- Staff/local admin login ยังผ่าน `ModelBackend` ✅
- หน้าเพิ่มผู้ใช้ local สำหรับ admin/staff เสร็จแล้ว ✅
  - URL: `/users/create/`
  - เฉพาะ `is_staff=True`
  - สร้างบัญชี local staff/user ได้
  - ทดสอบผ่าน Django test client, browser จริง และ Playwright suite แล้ว
- **LDAP สำหรับเจ้าหน้าที่ผ่าน AD ยังไม่ได้ทดสอบจริง** — เปิดใช้งานได้โดยตั้ง `LDAP_ENABLED=True` + credentials ใน `.env`

### Phase 4 — Core Views ✅

ไฟล์: `lms/views.py`, `lms/utils.py`

- `CourseListView` — แสดงหลักสูตร + progress badge
- `CourseDetailView` — รายละเอียด + lessons + quiz links + certificate
- `LessonView` — บันทึก `lessons_completed` M2M + ตรวจ completion
- `mark_completed()` ใน `utils.py` — idempotent, auto-create Certificate

### Phase 5 — Quiz System ✅

ไฟล์: `lms/forms.py`, `lms/views.py`

- `QuizSubmitForm` — dynamic RadioSelect per Question
- `QuizView` — score calculation, `is_passed = score >= 70`
- `UserQuizAttempt` สร้างทุกครั้งที่ทำ (เก็บประวัติทุก attempt)
- Post-test pass → trigger `mark_completed()`

### Phase 6 — Certificate PDF ✅

ไฟล์: `lms/utils.py`, `lms/templates/lms/certificate_template.html`

- `generate_certificate_pdf()` ใช้ xhtml2pdf
- `link_callback()` ใช้ staticfiles finder ก่อน แล้ว fallback ไป `STATIC_ROOT` (สำหรับ Thai font)
- Template: A4 landscape, inline CSS, ชื่อ-หลักสูตร-วันที่-ลายเซ็น
- `Sarabun-Regular.ttf` วางแล้วที่ `static/lms/fonts/`

### Phase 7 — Django Admin ✅

ไฟล์: `lms/admin.py`

- `UserAdmin` — extends `BaseUserAdmin`, เพิ่ม `department` field
- `CourseAdmin` — inlines: `LessonInline`, `QuizInline`
- `LessonInline` — TabularInline, fields: order, title, youtube_video_id
- `QuizInline` — TabularInline, `show_change_link=True`
- `QuizAdmin` — list/filter/search และ question count
- `QuestionAdmin` — inlines: `AnswerInline`, filter by course/type
- `AnswerInline` — TabularInline, fields: text, is_correct
- `AnswerAdmin` — list/filter/search สำหรับตรวจตัวเลือก
- `UserProgressAdmin` — list_display + filter + filter_horizontal
- `UserQuizAttemptAdmin` — list_display + filter
- `CertificateAdmin` — list_display + filter

### Phase 8 — Templates ✅

ไฟล์ทั้งหมดใน `lms/templates/`

| Template | สถานะ |
|---|---|
| `base.html` | ✅ Tailwind CDN + Sarabun font + navbar + footer |
| `registration/login.html` | ✅ gradient background + form |
| `lms/course_list.html` | ✅ grid cards + progress badge |
| `lms/course_detail.html` | ✅ lesson list + quiz panel + certificate button |
| `lms/lesson.html` | ✅ YouTube embed + sidebar nav |
| `lms/quiz.html` | ✅ dynamic RadioSelect questions |
| `lms/quiz_result.html` | ✅ score display + pass/fail + next action |
| `lms/certificate_template.html` | ✅ xhtml2pdf template (no CDN) |
| `lms/local_user_form.html` | ✅ หน้า admin/staff เพิ่มผู้ใช้ local |
| `lms/staff/*.html` | ✅ staff frontend 10 templates |

- `lms/templatetags/lms_extras.py` — `get_item` filter สำหรับ dict lookup

**ผลทดสอบ:**
- หน้า Login โหลดได้ ✅
- Login ด้วย admin/admin1234 ผ่าน ✅
- Redirect ไปหน้า course list ✅
- Logout ผ่าน navbar ใช้ POST + CSRF แล้ว ✅
- Full flow ผ่านด้วย Django test client ✅
  - test user: `codex_test` / `CodexTest1234!`
  - course: `[TEST] Codex Full Flow Course` (`course_id=1`)
  - lesson completed → post-test submit → score 100% → progress completed → certificate created
  - certificate PDF generated แล้ว header เป็น `%PDF`
  - certificate download endpoint คืน `200 application/pdf`

---

### Phase 9 — Production Config ✅

ไฟล์:
- `deploy/waitress_serve.py` — entry point สำหรับ NSSM service
- `deploy/install_service.bat` — ติดตั้ง Windows service
- `deploy/web.config` — IIS reverse proxy rules สำหรับ `/courses/` → `127.0.0.1:8002`

**หมายเหตุ:** `web.config` ตั้ง `HTTP_X_FORWARDED_PROTO=https`; IIS URL Rewrite ต้อง allow server variable นี้ในระดับ server ก่อนใช้งานจริง

**Production .env ที่ต้องตั้งค่า:**
```
FORCE_SCRIPT_NAME=/courses
STATIC_URL=/courses/static/
DEBUG=False
LDAP_ENABLED=True
NPU_STUDENT_AUTH_ENABLED=True
NPU_STUDENT_AUTH_URL=https://api.npu.ac.th/v2/ldap/auth_and_get_student/
NPU_STUDENT_AUTH_TOKEN=<token>
NPU_STUDENT_AUTH_TIMEOUT=10
WAITRESS_PORT=8002
```

### Phase 10 — Staff Content Frontend ✅

ไฟล์:
- `lms/staff_urls.py` — URL prefix `/staff/` รวม 13 routes
- `lms/forms.py` — `CourseForm`, `LessonForm`, `QuestionWithAnswersForm`
- `lms/views.py` — staff views รวม 13 views
- `lms/templates/lms/staff/` — 10 templates
- `tests/test_staff_content.py` — 21 tests

ความสามารถ:
- Dashboard สถิติหลักสูตร
- Course CRUD
- Lesson CRUD พร้อม validate `course + order`
- Quiz auto-create สำหรับ pre/post test
- Question + 4 answers CRUD
- Course report พร้อม enrollment/completion/certificate/pass-rate/avg-score
- จำกัดสิทธิ์เฉพาะ `is_staff=True`
- Navbar เพิ่มเมนู `จัดการเนื้อหา` เฉพาะ staff

---

## งานค้างเพิ่มเติม

| รายการ | รายละเอียด |
|---|---|
| collectstatic | รันล่าสุดผ่านแล้ว: `0 copied, 131 unmodified` |
| LDAP เจ้าหน้าที่ทดสอบ | ตั้ง `LDAP_ENABLED=True` + credentials NPU AD แล้วทดสอบ staff login จริง |
| ~~NPU student token~~ | ✅ ใส่ใน `.env` แล้ว; ไม่ commit token ลง repo |
| ~~ทดสอบ full flow~~ | ✅ ผ่านแล้วทั้ง Django test client และ Playwright browser test |
| ~~Playwright test suite~~ | ✅ เสร็จแล้ว — รันล่าสุด 102 passed, 0 failed |

---

## โครงสร้างไฟล์ปัจจุบัน

```
/mnt/c/projects/courses/
├── .env                    ✅ (MySQL credentials ตั้งแล้ว)
├── .env.example            ✅
├── .gitignore              ✅
├── manage.py               ✅
├── requirements.txt        ✅
├── CLAUDE.md               ✅
├── PROGRESS.md             ← ไฟล์นี้
├── config/
│   ├── settings.py         ✅ (env-driven)
│   ├── urls.py             ✅
│   └── wsgi.py             ✅
├── lms/
│   ├── models.py           ✅ (9 models, migrated)
│   ├── views.py            ✅ (all CBVs)
│   ├── urls.py             ✅
│   ├── staff_urls.py       ✅
│   ├── forms.py            ✅ (QuizSubmitForm)
│   ├── auth_backends.py    ✅ (NPUStudentAPIBackend)
│   ├── utils.py            ✅ (mark_completed, PDF)
│   ├── admin.py            ✅
│   ├── migrations/
│   │   └── 0001_initial.py ✅
│   ├── templatetags/
│   │   └── lms_extras.py   ✅ (get_item filter)
│   └── templates/
│       ├── base.html       ✅
│       ├── registration/
│       │   └── login.html  ✅
│       └── lms/
│           ├── course_list.html        ✅
│           ├── course_detail.html      ✅
│           ├── lesson.html             ✅
│           ├── quiz.html               ✅
│           ├── quiz_result.html        ✅
│           ├── local_user_form.html    ✅
│           ├── certificate_template.html ✅
│           └── staff/                  ✅ (10 templates)
├── static/lms/fonts/
│   └── Sarabun-Regular.ttf ✅
├── media/                  ✅ (dir created)
├── logs/                   ✅ (dir created)
├── deploy/
│   ├── waitress_serve.py   ✅
│   ├── install_service.bat ✅
│   └── web.config          ✅
└── tests/                  ✅ (Playwright browser tests)
    ├── conftest.py         ✅ (fixtures: page, logged_in_page)
    ├── test_settings.py    ✅ (BASE_URL, credentials, IDs)
    ├── test_login.py       ✅ (5 tests)
    ├── test_course_flow.py ✅ (18 tests)
    ├── test_user_management.py ✅ (7 tests)
    ├── test_staff_content.py ✅ (21 tests)
    └── pytest.ini          ✅
```

---

## สรุปสำหรับ Codex

**อัพเดต:** 11 พฤษภาคม 2569

**สิ่งที่ทำแล้วทั้งหมด:**
- Phase 1–9 ครบ (bootstrap, models, auth, views, quiz, PDF, admin, templates, deploy config)
- Student authentication ผ่าน NPU API พัฒนาและทดสอบจริงแล้ว
- หน้า admin/staff เพิ่มผู้ใช้ local เสร็จและทดสอบผ่าน browser แล้ว
- Staff content management frontend เสร็จแล้ว
- Playwright browser test suite **102 passed, 0 failed**
- Push ขึ้น GitHub: `https://github.com/azimuthotg/courses.git` (branch: `main`)

### ผลการทดสอบ Playwright (browser จริง — Chromium)

```
รันด้วย: python -m pytest tests/ --browser chromium -v
ผลล่าสุด: 102 passed in 2288.42s
```

| กลุ่ม | Tests | ผล |
|---|---|---|
| Login / Logout | 5 | ✅ pass |
| Course List | 2 | ✅ pass |
| Course Detail | 3 | ✅ pass |
| Lesson View | 3 | ✅ pass |
| Post Quiz | 5 | ✅ pass |
| Course Completion | 2 | ✅ pass |
| Certificate Download | 3 | ✅ pass |
| User Management | 7 | ✅ pass |
| Staff Content Management | 21 | ✅ pass |
| **รวม** | **51 tests × 2 = 102** | **✅ 102 passed, 0 failed** |

### ข้อสังเกตสำคัญจากการทดสอบ

1. **Logout ใน navbar แก้แล้ว** — ใช้ `<form method="post">` + `{% csrf_token %}` ตาม behavior ของ Django รุ่นใหม่
2. **Quiz tests แก้แล้ว** — selector ส่งคำตอบใช้ role/name `ส่งคำตอบ` เพื่อไม่ชนกับปุ่ม logout ที่เป็น submit button ใน navbar
3. **Certificate download** — response เป็น `Content-Disposition: attachment` ต้องใช้ `expect_download()` ของ Playwright ไม่ใช่ `page.goto()`

---

**งานที่ควรทำต่อ:**

### 1. LDAP เจ้าหน้าที่ทดสอบ
ตั้ง `LDAP_ENABLED=True` + credentials NPU AD ใน `.env` แล้วทดสอบ login จริง

### 2. Production Dry Run
รัน `collectstatic`, ทดสอบ `deploy/waitress_serve.py`, ติดตั้ง service ด้วย NSSM และทดสอบผ่าน IIS `/courses/`

### 3. Feature เพิ่มเติมที่อาจต้องการ
- หน้า Admin: bulk import questions จาก CSV
- Progress bar แสดง % บทเรียนที่เรียนแล้ว
- Email notification เมื่อได้รับ certificate

**Reference files:**
- `CLAUDE.md` — architecture overview + gotchas
- `lms/utils.py` — `mark_completed()` และ `generate_certificate_pdf()`
- `lms/views.py` — CBV patterns ที่ใช้อยู่
- `config/settings.py` — settings structure
- `tests/test_course_flow.py` — full flow test ครอบคลุมทุก endpoint
