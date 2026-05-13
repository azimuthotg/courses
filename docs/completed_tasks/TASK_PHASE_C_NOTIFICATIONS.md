# Task: Phase C — LINE OA Push Notification + Audit Trail — Micro-LMS (NPU Library)

## Overview
3 งานหลัก ทำตามลำดับ:
1. LINE OA Push Notification (เมื่อนักศึกษาผ่านคอร์ส/ได้รับใบประกาศฯ)
2. Audit Trail (log เหตุการณ์สำคัญสำหรับ Admin)
3. Bulk User Import CSV (สำหรับ Staff สร้าง local user จำนวนมาก)

## Stack Constraints
- Tailwind CSS via CDN — ไม่มี build step
- Django templates + CBV
- หลังแก้ models.py ต้องรัน migration
- รัน `python -m pytest tests/ --browser chromium -v` ต้องผ่านครบ

---

## งานที่ 1: LINE OA Push Notification

### เป้าหมาย
ส่ง LINE Push Message หานักศึกษาเป็นรายคนเมื่อ:
- เรียนจบคอร์ส (ได้ใบประกาศฯ)
- ผ่าน Post-test

### ขั้นตอนที่ 1.1 — เพิ่ม dependency

แก้ไข `requirements.txt` เพิ่ม:
```
requests>=2.31
```

รันติดตั้ง:
```bash
pip install requests
```

### ขั้นตอนที่ 1.2 — เพิ่ม env vars

แก้ไข `.env.example` เพิ่ม:
```env
# LINE OA Messaging API
LINE_OA_ENABLED=False
LINE_OA_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
```

แก้ไข `.env` (production) ใส่ค่าจริง

### ขั้นตอนที่ 1.3 — แก้ไข `config/settings.py`

เพิ่มท้าย settings:
```python
LINE_OA_ENABLED = env.bool('LINE_OA_ENABLED', default=False)
LINE_OA_CHANNEL_ACCESS_TOKEN = env.str('LINE_OA_CHANNEL_ACCESS_TOKEN', default='')
```

**หมายเหตุ:** ถ้า project ใช้ `os.environ.get` แทน `env.bool` ให้ปรับให้ตรงกับ pattern ที่มีอยู่ใน settings.py

### ขั้นตอนที่ 1.4 — แก้ไข `lms/models.py` — User model

เพิ่ม field ใน User:
```python
class User(AbstractUser):
    department = models.CharField(max_length=200, blank=True)
    line_user_id = models.CharField(
        max_length=50, blank=True,
        help_text='LINE User ID สำหรับส่ง Push Notification'
    )
```

รัน migration:
```bash
python manage.py makemigrations lms
python manage.py migrate
```

### ขั้นตอนที่ 1.5 — สร้างไฟล์ใหม่ `lms/line_notify.py`

```python
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

LINE_PUSH_URL = 'https://api.line.me/v2/bot/message/push'


def send_line_push(line_user_id: str, message: str) -> bool:
    """
    ส่ง Push Message ถึงผู้ใช้ผ่าน LINE Messaging API
    คืนค่า True ถ้าส่งสำเร็จ, False ถ้าไม่ได้เปิดใช้หรือล้มเหลว
    """
    if not getattr(settings, 'LINE_OA_ENABLED', False):
        return False
    if not line_user_id:
        return False

    token = getattr(settings, 'LINE_OA_CHANNEL_ACCESS_TOKEN', '')
    if not token:
        logger.warning('LINE_OA_CHANNEL_ACCESS_TOKEN ไม่ได้ตั้งค่า')
        return False

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'to': line_user_id,
        'messages': [{'type': 'text', 'text': message}],
    }

    try:
        resp = requests.post(LINE_PUSH_URL, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            return True
        logger.error('LINE push failed: %s %s', resp.status_code, resp.text)
        return False
    except requests.RequestException as e:
        logger.error('LINE push error: %s', e)
        return False


def notify_course_completed(user, course, certificate):
    """แจ้งเตือนเมื่อนักศึกษาเรียนจบและได้รับใบประกาศฯ"""
    if not user.line_user_id:
        return
    message = (
        f'🎉 ยินดีด้วยคุณ {user.get_full_name() or user.username}!\n'
        f'คุณเรียนจบวิชา "{course.title}" เรียบร้อยแล้ว\n'
        f'ใบประกาศนียบัตรของคุณพร้อมให้ดาวน์โหลดแล้ว\n'
        f'เลขที่: {certificate.serial_number}'
    )
    send_line_push(user.line_user_id, message)
```

### ขั้นตอนที่ 1.6 — แก้ไข `lms/utils.py` — _mark_completed()

เพิ่ม import ด้านบน:
```python
from lms.line_notify import notify_course_completed
```

แก้ไข `_mark_completed()`:
```python
def _mark_completed(user, course, progress):
    if progress.status != 'completed':
        progress.status = 'completed'
        progress.save()
    certificate, created = Certificate.objects.get_or_create(user=user, course=course)
    if created:
        # ส่ง LINE notification เฉพาะเมื่อออกใบประกาศฯ ครั้งแรก
        notify_course_completed(user, course, certificate)
```

### ขั้นตอนที่ 1.7 — เพิ่ม line_user_id ใน Staff User Form

แก้ไข `lms/forms.py` — LocalUserCreationForm เพิ่ม `line_user_id` ใน fields:
```python
class LocalUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'department', 'line_user_id',
            'is_staff', 'is_active',
            'password1', 'password2',
        ]
```

แก้ไข `lms/templates/lms/local_user_form.html` — เพิ่มช่อง line_user_id ใน form:
```html
<div>
  <label class="block text-sm font-medium text-gray-700 mb-1">
    LINE User ID
    <span class="text-gray-400 font-normal">(สำหรับแจ้งเตือน — ไม่บังคับ)</span>
  </label>
  {{ form.line_user_id }}
  <p class="text-xs text-gray-400 mt-1">
    วิธีหา LINE User ID: ให้นักศึกษา follow LINE OA แล้วส่งข้อความ "ID" มาที่ OA
  </p>
</div>
```

### วิธีหา LINE User ID ของนักศึกษา

**แนะนำให้ตั้งค่า Webhook บน LINE OA:**
- เมื่อ follower ส่งข้อความ → webhook รับ event → ระบบตอบกลับ LINE User ID ของผู้นั้น
- Staff copy ค่า ID ไปใส่ในระบบ

**หรือ:** Staff ดูได้จาก LINE OA Manager → Chat → คลิกชื่อผู้ใช้ → ดู User ID

---

## งานที่ 2: Audit Trail

### เป้าหมาย
บันทึก log เหตุการณ์สำคัญใน DB ให้ Admin ตรวจสอบได้

### ขั้นตอนที่ 2.1 — เพิ่ม Model ใน `lms/models.py`

```python
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('course_complete', 'Course Completed'),
        ('quiz_pass', 'Quiz Passed'),
        ('quiz_fail', 'Quiz Failed'),
        ('certificate_issued', 'Certificate Issued'),
        ('staff_course_create', 'Course Created'),
        ('staff_course_edit', 'Course Edited'),
        ('staff_course_delete', 'Course Deleted'),
        ('staff_user_create', 'User Created'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} | {self.user} | {self.action}'
```

รัน migration:
```bash
python manage.py makemigrations lms
python manage.py migrate
```

### ขั้นตอนที่ 2.2 — สร้าง helper ใน `lms/utils.py`

```python
def log_audit(user, action, description='', request=None):
    """บันทึก audit log — ล้มเหลวแบบ silent ไม่ interrupt user flow"""
    try:
        ip = None
        if request:
            x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
        AuditLog.objects.create(
            user=user,
            action=action,
            description=description,
            ip_address=ip,
        )
    except Exception:
        pass
```

### ขั้นตอนที่ 2.3 — เรียก log_audit ใน views.py จุดสำคัญ

```python
# Login สำเร็จ — ใน LMSLoginView.form_valid() หรือ override dispatch
log_audit(user, 'login', request=request)

# Quiz ผ่าน — ใน QuizView.post() หลัง is_passed=True
log_audit(request.user, 'quiz_pass',
          f'{course.title} | {quiz_type} | {score_pct:.1f}%', request)

# Quiz ไม่ผ่าน
log_audit(request.user, 'quiz_fail',
          f'{course.title} | {quiz_type} | {score_pct:.1f}%', request)

# Course complete — ใน _mark_completed() ใน utils.py
log_audit(user, 'course_complete', course.title)

# Staff สร้างคอร์ส — ใน StaffCourseCreateView.form_valid()
log_audit(request.user, 'staff_course_create', form.instance.title, request)
```

### ขั้นตอนที่ 2.4 — เพิ่ม AuditLog ใน `lms/admin.py`

```python
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'action', 'description', 'ip_address']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False  # ห้ามสร้าง log ด้วยมือ

    def has_change_permission(self, request, obj=None):
        return False  # ห้ามแก้ไข
```

---

## งานที่ 3: Bulk User Import CSV

### เป้าหมาย
Staff อัปโหลด CSV เพื่อสร้าง local user จำนวนมาก (สำหรับ Staff / บัญชีทดสอบ)

### ขั้นตอนที่ 3.1 — CSV Format

```csv
username,first_name,last_name,email,department,password,is_staff,line_user_id
staff001,สมชาย,ใจดี,somchai@npu.ac.th,สำนักวิทยบริการ,Pass1234!,False,
staff002,สมหญิง,รักดี,somying@npu.ac.th,สำนักวิทยบริการ,Pass1234!,True,Uxxxxx
```

- `password` — plain text จะถูก hash ก่อนบันทึก
- `is_staff` — True/False
- `line_user_id` — optional (ว่างได้)

### ขั้นตอนที่ 3.2 — เพิ่ม View ใหม่ใน `lms/views.py`

```python
import csv
import io

class BulkUserImportView(LoginRequiredMixin, StaffRequiredMixin, View):
    template_name = 'lms/staff/bulk_user_import.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'กรุณาเลือกไฟล์ CSV')
            return render(request, self.template_name)

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'ไฟล์ต้องเป็น .csv เท่านั้น')
            return render(request, self.template_name)

        try:
            decoded = csv_file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded))
            created, skipped, errors = 0, 0, []

            for i, row in enumerate(reader, start=2):
                username = row.get('username', '').strip()
                if not username:
                    errors.append(f'แถว {i}: ไม่มี username')
                    continue
                if User.objects.filter(username=username).exists():
                    skipped += 1
                    continue
                try:
                    user = User(
                        username=username,
                        first_name=row.get('first_name', '').strip(),
                        last_name=row.get('last_name', '').strip(),
                        email=row.get('email', '').strip(),
                        department=row.get('department', '').strip(),
                        is_staff=row.get('is_staff', 'False').strip().lower() == 'true',
                        line_user_id=row.get('line_user_id', '').strip(),
                    )
                    password = row.get('password', '').strip()
                    if password:
                        user.set_password(password)
                    else:
                        user.set_unusable_password()
                    user.full_clean()
                    user.save()
                    created += 1
                except Exception as e:
                    errors.append(f'แถว {i} ({username}): {e}')

            messages.success(request,
                f'สร้างสำเร็จ {created} คน | ข้ามซ้ำ {skipped} คน | ผิดพลาด {len(errors)} รายการ')
            if errors:
                for err in errors[:10]:  # แสดงแค่ 10 รายการแรก
                    messages.warning(request, err)

        except Exception as e:
            messages.error(request, f'อ่านไฟล์ไม่ได้: {e}')

        return render(request, self.template_name)
```

### ขั้นตอนที่ 3.3 — เพิ่ม URL ใน `lms/staff_urls.py`

```python
path('users/import/', views.BulkUserImportView.as_view(), name='staff-bulk-user-import'),
```

### ขั้นตอนที่ 3.4 — สร้าง Template `lms/templates/lms/staff/bulk_user_import.html`

```html
{% extends 'lms/staff/base_staff.html' %}
{% block staff_content %}
<nav class="text-sm text-gray-500 mb-4">
  <ol class="flex items-center gap-1">
    <li><a href="{% url 'staff-dashboard' %}" class="hover:text-teal-700">จัดการ</a></li>
    <li class="text-gray-300">/</li>
    <li class="font-medium text-gray-700">นำเข้าผู้ใช้ CSV</li>
  </ol>
</nav>

<div class="max-w-2xl">
  <h1 class="text-2xl font-bold text-gray-900 mb-6">นำเข้าผู้ใช้จาก CSV</h1>

  <div class="bg-white rounded-xl shadow p-6 mb-6">
    <h2 class="font-semibold text-gray-800 mb-3">รูปแบบไฟล์ CSV</h2>
    <code class="block bg-gray-50 rounded p-3 text-xs text-gray-700 whitespace-pre">username,first_name,last_name,email,department,password,is_staff,line_user_id
staff001,สมชาย,ใจดี,somchai@npu.ac.th,สำนักวิทยบริการ,Pass1234!,False,
staff002,สมหญิง,รักดี,somying@npu.ac.th,สำนักวิทยบริการ,Pass1234!,True,Uxxxxx</code>
    <ul class="mt-3 text-sm text-gray-500 space-y-1">
      <li>• username ที่ซ้ำกับในระบบจะถูกข้ามโดยอัตโนมัติ</li>
      <li>• ไฟล์ต้องเป็น UTF-8 หรือ UTF-8 with BOM</li>
      <li>• line_user_id และ email เว้นว่างได้</li>
    </ul>
  </div>

  <form method="post" enctype="multipart/form-data" class="bg-white rounded-xl shadow p-6">
    {% csrf_token %}
    <label class="block text-sm font-medium text-gray-700 mb-2">เลือกไฟล์ CSV</label>
    <input type="file" name="csv_file" accept=".csv"
           class="block w-full text-sm text-gray-500 border border-gray-300 rounded-lg p-2
                  file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0
                  file:bg-teal-800 file:text-white file:text-sm hover:file:bg-teal-700">
    <button type="submit"
            class="mt-4 px-6 py-2 bg-teal-800 text-white text-sm rounded-lg hover:bg-teal-700 transition">
      นำเข้า
    </button>
  </form>
</div>
{% endblock %}
```

### ขั้นตอนที่ 3.5 — เพิ่มลิงก์ใน Staff Sidebar

แก้ไข `lms/templates/lms/staff/_sidebar.html` ใน section จัดการผู้ใช้:
```html
<a href="{% url 'staff-bulk-user-import' %}" ...>
  นำเข้าผู้ใช้ CSV
</a>
```

---

## Verification

```bash
source venv/bin/activate

# 1. Migration
python manage.py makemigrations lms
python manage.py migrate
python manage.py check  # ต้องไม่มี error

# 2. ทดสอบ LINE (ปิด LINE_OA_ENABLED=False → ไม่ส่งจริง ไม่ error)
# เปิด LINE_OA_ENABLED=True + ใส่ token จริง + ใส่ line_user_id ใน user
# เรียนจบคอร์ส → ต้องได้รับข้อความ LINE

# 3. Audit Log
# ทำ login → quiz → complete course → เข้า Django Admin /admin/lms/auditlog/ → ต้องเห็น log

# 4. Bulk Import
# http://127.0.0.1:8001/staff/users/import/
# อัปโหลด CSV → ดูผลสรุป → เข้า Django Admin ตรวจ user ที่สร้าง

# 5. Full test suite
python -m pytest tests/ --browser chromium -v
# Expected: 102+ passed, 0 failed
```

---

## ไฟล์ที่แก้ไข / สร้างใหม่

| ไฟล์ | การเปลี่ยนแปลง |
|------|--------------|
| `requirements.txt` | เพิ่ม `requests>=2.31` |
| `.env.example` | เพิ่ม LINE_OA_* vars |
| `config/settings.py` | เพิ่ม LINE_OA settings |
| `lms/models.py` | User: `line_user_id` + AuditLog model ใหม่ |
| `lms/utils.py` | _mark_completed() + log_audit() helper |
| `lms/forms.py` | เพิ่ม line_user_id ใน LocalUserCreationForm |
| `lms/views.py` | QuizView + StaffCourseCreateView + BulkUserImportView ใหม่ |
| `lms/admin.py` | AuditLogAdmin |
| `lms/staff_urls.py` | เพิ่ม bulk import URL |
| `lms/line_notify.py` | **ไฟล์ใหม่** |
| `lms/templates/lms/local_user_form.html` | เพิ่มช่อง line_user_id |
| `lms/templates/lms/staff/_sidebar.html` | เพิ่มลิงก์ import CSV |
| `lms/templates/lms/staff/bulk_user_import.html` | **ไฟล์ใหม่** |
