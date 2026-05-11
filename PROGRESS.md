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
| 3 | Auth (LDAP config) | ✅ บางส่วน |
| 4 | Core Views | ✅ เสร็จ |
| 5 | Quiz System | ✅ เสร็จ |
| 6 | Certificate PDF | ✅ เสร็จ |
| 7 | Django Admin | ✅ เสร็จ |
| 8 | Templates (HTML) | ✅ เสร็จ |
| 9 | Production Config | ✅ ไฟล์พื้นฐานเสร็จ |

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

### Phase 3 — Auth ✅ (บางส่วน)

- `LMSLoginView`, `LMSLogoutView` ใน `lms/views.py`
- หน้า `registration/login.html` — ใช้งานได้แล้ว
- ตอนนี้ใช้ `ModelBackend` (local admin login)
- **LDAP ยังไม่ได้ทดสอบ** — เปิดใช้งานได้โดยตั้ง `LDAP_ENABLED=True` + credentials ใน `.env`

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

- `lms/templatetags/lms_extras.py` — `get_item` filter สำหรับ dict lookup

**ผลทดสอบ:**
- หน้า Login โหลดได้ ✅
- Login ด้วย admin/admin1234 ผ่าน ✅
- Redirect ไปหน้า course list ✅
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
WAITRESS_PORT=8002
```

---

## งานค้างเพิ่มเติม

| รายการ | รายละเอียด |
|---|---|
| collectstatic | รันผ่านแล้วหลังเพิ่ม Sarabun font |
| LDAP ทดสอบ | ตั้ง `LDAP_ENABLED=True` + credentials NPU AD แล้วทดสอบ login จริง |
| ~~ทดสอบ full flow~~ | ✅ ผ่านแล้วทั้ง Django test client และ Playwright browser test |
| ~~Playwright test suite~~ | ✅ เสร็จแล้ว — 46 passed, 0 failed |

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
│   ├── forms.py            ✅ (QuizSubmitForm)
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
│           └── certificate_template.html ✅
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
    └── pytest.ini          ✅
```

---

## สรุปสำหรับ Codex

**อัพเดต:** 11 พฤษภาคม 2569

**สิ่งที่ทำแล้วทั้งหมด:**
- Phase 1–9 ครบ (bootstrap, models, auth, views, quiz, PDF, admin, templates, deploy config)
- Playwright browser test suite **46 passed, 0 failed**
- Push ขึ้น GitHub: `https://github.com/azimuthotg/courses.git` (branch: `main`)

### ผลการทดสอบ Playwright (browser จริง — Chromium)

```
รันด้วย: python -m pytest tests/ --browser chromium -v
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
| **รวม** | **23 tests × 2 = 46** | **✅ 46 passed, 0 failed** |

### ข้อสังเกตสำคัญจากการทดสอบ

1. **Logout ใน navbar ไม่ทำงานจริงบน Django 6** — `<a href="/logout/">` เป็น GET แต่ Django 6 ต้องการ POST เพื่อ logout จริง ควรเปลี่ยน navbar เป็น `<form method="post">` (ดูตัวอย่างใน `tests/test_login.py::test_logout`)
2. **Certificate download** — response เป็น `Content-Disposition: attachment` ต้องใช้ `expect_download()` ของ Playwright ไม่ใช่ `page.goto()`

---

**งานที่ควรทำต่อ:**

### 1. แก้ Logout ใน Navbar (สำคัญ)
เปลี่ยน `lms/templates/base.html` จาก `<a>` เป็น `<form method="post">` พร้อม CSRF token:
```html
<form method="post" action="{% url 'logout' %}" class="inline">
  {% csrf_token %}
  <button type="submit" class="text-sm bg-blue-700 hover:bg-blue-600 px-4 py-1.5 rounded-full transition">
    ออกจากระบบ
  </button>
</form>
```

### 2. LDAP ทดสอบ
ตั้ง `LDAP_ENABLED=True` + credentials NPU AD ใน `.env` แล้วทดสอบ login จริง

### 3. Production Dry Run
รัน `collectstatic`, ทดสอบ `deploy/waitress_serve.py`, ติดตั้ง service ด้วย NSSM และทดสอบผ่าน IIS `/courses/`

### 4. Feature เพิ่มเติมที่อาจต้องการ
- หน้า Admin: bulk import questions จาก CSV
- Progress bar แสดง % บทเรียนที่เรียนแล้ว
- Email notification เมื่อได้รับ certificate

**Reference files:**
- `CLAUDE.md` — architecture overview + gotchas
- `lms/utils.py` — `mark_completed()` และ `generate_certificate_pdf()`
- `lms/views.py` — CBV patterns ที่ใช้อยู่
- `config/settings.py` — settings structure
- `tests/test_course_flow.py` — full flow test ครอบคลุมทุก endpoint
