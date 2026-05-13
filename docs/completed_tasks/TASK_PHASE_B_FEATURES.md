# Task: Phase B — Feature Essentials — Micro-LMS (NPU Library)

## Overview
เพิ่ม 6 feature ที่ขาดเทียบกับ Enterprise LMS มาตรฐาน
ทำตามลำดับที่ระบุเพราะบางงานมี dependency กัน

## Stack Constraints
- Tailwind CSS via CDN — ไม่มี build step
- Django templates + class-based views
- Database: MySQL via mysqlclient
- หลังแก้ models.py ต้องรัน `python manage.py makemigrations lms && python manage.py migrate`
- รัน `python -m pytest tests/ --browser chromium -v` ต้องผ่าน 102 tests

---

## งานที่ 1: Course Search & Filter

### เป้าหมาย
เพิ่ม search box ให้นักศึกษาค้นหาวิชาจากชื่อหรือคำอธิบาย

### แก้ไข `lms/views.py` — CourseListView

```python
class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'lms/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        qs = Course.objects.filter(is_active=True)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                models.Q(title__icontains=q) | models.Q(description__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ...existing progress_map logic...
        context['search_query'] = self.request.GET.get('q', '')
        return context
```

**Note:** ต้อง import `from django.db import models` ถ้ายังไม่มี หรือใช้ `from django.db.models import Q` แล้วใช้ `Q(...)` ตรงๆ

### แก้ไข `lms/templates/lms/course_list.html`

เพิ่ม search form ด้านบน grid:

```html
<form method="get" class="mb-6 flex gap-2">
  <input type="text" name="q" value="{{ search_query }}"
         placeholder="ค้นหาวิชา..."
         class="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm
                focus:outline-none focus:ring-2 focus:ring-teal-500">
  <button type="submit"
          class="px-4 py-2 bg-teal-800 text-white text-sm rounded-lg hover:bg-teal-700 transition">
    ค้นหา
  </button>
  {% if search_query %}
  <a href="{% url 'course-list' %}"
     class="px-4 py-2 bg-gray-100 text-gray-600 text-sm rounded-lg hover:bg-gray-200 transition">
    ล้าง
  </a>
  {% endif %}
</form>

{% if search_query and not courses %}
<p class="text-gray-400 text-center py-12">ไม่พบวิชาที่ตรงกับ "{{ search_query }}"</p>
{% endif %}
```

---

## งานที่ 2: Configurable Pass Threshold

### เป้าหมาย
เปลี่ยนจาก hardcode 70% เป็นกำหนดต่อวิชาได้

### แก้ไข `lms/models.py` — Course model

เพิ่ม field:
```python
class Course(models.Model):
    # ...existing fields...
    pass_threshold = models.PositiveIntegerField(
        default=70,
        help_text='คะแนนขั้นต่ำที่ผ่าน (%)'
    )
```

### รัน migration
```bash
python manage.py makemigrations lms
python manage.py migrate
```

### แก้ไข `lms/utils.py` — `_mark_completed()`

หา `score_pct >= 70` แล้วเปลี่ยนเป็น:
```python
score_pct >= course.pass_threshold
```

### แก้ไข `lms/views.py` — QuizView.post()

หา `is_passed = score_pct >= 70` แล้วเปลี่ยนเป็น:
```python
is_passed = score_pct >= quiz.course.pass_threshold
```

### แก้ไข `lms/forms.py` — CourseForm (Staff)

ตรวจสอบว่า `pass_threshold` อยู่ใน `fields` ของ CourseForm แล้ว

### แก้ไข `lms/templates/lms/quiz.html`

เปลี่ยน hardcode "70%" เป็น:
```html
{{ course.pass_threshold }}%
```

### แก้ไข `lms/templates/lms/quiz_result.html`

เปลี่ยน hardcode "70%" เป็น:
```html
{{ course.pass_threshold }}%
```

---

## งานที่ 3: User Profile Page

### เป้าหมาย
นักศึกษาดูประวัติการเรียนของตัวเองได้ (ทุกวิชา + คะแนน + ใบประกาศฯ)

### แก้ไข `lms/views.py` — เพิ่ม view ใหม่

```python
class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        progress_list = UserProgress.objects.filter(
            user=request.user
        ).select_related('course').order_by('-updated_at')

        attempts = UserQuizAttempt.objects.filter(
            user=request.user
        ).select_related('quiz__course').order_by('-attempted_at')

        best_attempts = {}
        for attempt in attempts:
            course_id = attempt.quiz.course_id
            if course_id not in best_attempts or attempt.score_percentage > best_attempts[course_id].score_percentage:
                best_attempts[course_id] = attempt

        certificates = Certificate.objects.filter(
            user=request.user
        ).select_related('course')
        cert_map = {c.course_id: c for c in certificates}

        return render(request, 'lms/profile.html', {
            'progress_list': progress_list,
            'best_attempts': best_attempts,
            'cert_map': cert_map,
        })
```

### แก้ไข `lms/urls.py` — เพิ่ม URL

```python
path('profile/', views.UserProfileView.as_view(), name='user-profile'),
```

### สร้างไฟล์ใหม่: `lms/templates/lms/profile.html`

```html
{% extends 'base.html' %}
{% load lms_extras %}

{% block content %}
<div class="max-w-4xl mx-auto px-4 py-6">
  <!-- Breadcrumb -->
  <nav class="text-sm text-gray-500 mb-4">
    <ol class="flex items-center gap-1">
      <li><a href="{% url 'course-list' %}" class="hover:text-teal-700">หน้าแรก</a></li>
      <li class="text-gray-300">/</li>
      <li class="text-gray-700 font-medium">โปรไฟล์ของฉัน</li>
    </ol>
  </nav>

  <!-- User Info -->
  <div class="bg-white rounded-xl shadow p-6 mb-6">
    <h1 class="text-2xl font-bold text-gray-800">{{ user.get_full_name|default:user.username }}</h1>
    <p class="text-gray-500 text-sm mt-1">{{ user.department }}</p>
    <p class="text-gray-400 text-xs mt-1">{{ user.username }}</p>
  </div>

  <!-- Course Progress -->
  <h2 class="text-lg font-semibold text-gray-800 mb-3">ประวัติการเรียน</h2>
  {% if progress_list %}
  <div class="space-y-4">
    {% for progress in progress_list %}
    {% with best=best_attempts|get_item:progress.course_id cert=cert_map|get_item:progress.course_id %}
    <div class="bg-white rounded-xl shadow p-5 flex items-center justify-between gap-4">
      <div class="flex-1">
        <a href="{% url 'course-detail' progress.course.pk %}"
           class="font-medium text-gray-900 hover:text-teal-700">{{ progress.course.title }}</a>
        <div class="flex items-center gap-3 mt-2 text-sm text-gray-500">
          {% if progress.status == 'completed' %}
            <span class="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs">เรียนจบแล้ว</span>
          {% else %}
            <span class="bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full text-xs">กำลังเรียน</span>
          {% endif %}
          {% if best %}
            <span>คะแนนดีสุด: {{ best.score_percentage|floatformat:0 }}%</span>
          {% endif %}
        </div>
      </div>
      {% if cert %}
      <a href="{% url 'certificate' progress.course.pk %}"
         class="flex items-center gap-1 px-3 py-1.5 bg-amber-500 text-white text-xs rounded-lg hover:bg-amber-400 transition">
        ใบประกาศฯ
      </a>
      {% endif %}
    </div>
    {% endwith %}
    {% endfor %}
  </div>
  {% else %}
  <p class="text-gray-400 text-center py-8">ยังไม่ได้เริ่มเรียนวิชาใดเลย</p>
  {% endif %}
</div>
{% endblock %}
```

### แก้ไข `lms/templates/base.html` — เพิ่มลิงก์ Profile ใน Navbar

เพิ่มปุ่มโปรไฟล์ข้าง Logout:
```html
<a href="{% url 'user-profile' %}"
   class="text-sm text-teal-200 hover:text-white transition">
  {{ user.get_full_name|default:user.username }}
</a>
```

---

## งานที่ 4: Certificate Serial Number

### เป้าหมาย
ใบประกาศฯ แต่ละใบมีเลขที่เฉพาะ รูปแบบ `CERT-{ปี พ.ศ.}-{XXXX}`

### แก้ไข `lms/models.py` — Certificate model

```python
import uuid

class Certificate(models.Model):
    user = models.ForeignKey(...)
    course = models.ForeignKey(...)
    issued_at = models.DateTimeField(auto_now_add=True)
    serial_number = models.CharField(max_length=30, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.serial_number:
            year_be = self.issued_at.year + 543 if self.issued_at else __import__('datetime').datetime.now().year + 543
            short_id = uuid.uuid4().hex[:6].upper()
            self.serial_number = f'CERT-{year_be}-{short_id}'
        super().save(*args, **kwargs)

    class Meta:
        unique_together = [('user', 'course')]
```

**หมายเหตุ:** `issued_at` ถูก set โดย `auto_now_add=True` ก่อน save() ถูกเรียกสำหรับ record ใหม่ ดังนั้นใน override save() ให้ใช้ `datetime.datetime.now()` แทน `self.issued_at` เพื่อความปลอดภัย:

```python
from datetime import datetime

def save(self, *args, **kwargs):
    if not self.serial_number:
        year_be = datetime.now().year + 543
        short_id = uuid.uuid4().hex[:6].upper()
        self.serial_number = f'CERT-{year_be}-{short_id}'
    super().save(*args, **kwargs)
```

### รัน migration
```bash
python manage.py makemigrations lms
python manage.py migrate
```

### แก้ไข `lms/templates/lms/certificate_template.html`

เพิ่ม serial number ใน PDF:
```html
<p style="font-size: 10px; color: #555; text-align: center; margin-top: 8px;">
  เลขที่ใบประกาศนียบัตร: {{ certificate.serial_number }}
</p>
```

---

## งานที่ 5: Report Export CSV

### เป้าหมาย
Staff ดาวน์โหลด report ของแต่ละวิชาเป็น CSV

### แก้ไข `lms/views.py` — เพิ่ม imports ด้านบน

```python
import csv
from django.http import StreamingHttpResponse
```

### เพิ่ม View ใหม่ใน `lms/views.py`

```python
class StaffCourseReportExportView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        progress_qs = UserProgress.objects.filter(
            course=course
        ).select_related('user')

        attempts = UserQuizAttempt.objects.filter(
            quiz__course=course,
            attempt_type='post'
        ).select_related('user')

        best_map = {}
        for a in attempts:
            uid = a.user_id
            if uid not in best_map or a.score_percentage > best_map[uid].score_percentage:
                best_map[uid] = a

        cert_set = set(
            Certificate.objects.filter(course=course).values_list('user_id', flat=True)
        )

        rows = []
        for p in progress_qs:
            best = best_map.get(p.user_id)
            rows.append([
                p.user.username,
                p.user.get_full_name(),
                p.user.department,
                'จบแล้ว' if p.status == 'completed' else 'กำลังเรียน',
                p.lessons_completed.count(),
                f'{best.score_percentage:.1f}' if best else '-',
                'ผ่าน' if best and best.is_passed else 'ไม่ผ่าน' if best else '-',
                'มี' if p.user_id in cert_set else 'ยังไม่มี',
            ])

        def stream():
            yield '﻿'  # BOM for Thai Excel compatibility
            writer_buf = []
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'รหัสนักศึกษา', 'ชื่อ-นามสกุล', 'สาขา/แผนก',
                'สถานะ', 'บทเรียนที่ดู', 'คะแนน Post-test', 'ผ่าน/ไม่ผ่าน', 'ใบประกาศฯ'
            ])
            yield output.getvalue()
            output.seek(0); output.truncate()
            for row in rows:
                writer.writerow(row)
                yield output.getvalue()
                output.seek(0); output.truncate()

        filename = f'report_{course.pk}_{course.title[:20]}.csv'
        response = StreamingHttpResponse(stream(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
```

### แก้ไข `lms/staff_urls.py` — เพิ่ม URL

```python
path('courses/<int:pk>/report/export/', views.StaffCourseReportExportView.as_view(), name='staff-course-report-export'),
```

### แก้ไข `lms/templates/lms/staff/course_report.html`

เพิ่มปุ่ม Export ด้านบน:
```html
<a href="{% url 'staff-course-report-export' course.pk %}"
   class="inline-flex items-center gap-2 px-4 py-2 bg-teal-800 text-white text-sm rounded-lg hover:bg-teal-700 transition">
  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
  </svg>
  Export CSV
</a>
```

---

## งานที่ 6: Learner Transcript PDF

### เป้าหมาย
นักศึกษาดาวน์โหลด transcript ส่วนตัวเป็น PDF แสดงทุกวิชาที่เรียน คะแนน และสถานะ

### เพิ่ม View ใหม่ใน `lms/views.py`

```python
class LearnerTranscriptView(LoginRequiredMixin, View):
    def get(self, request):
        progress_list = UserProgress.objects.filter(
            user=request.user
        ).select_related('course').order_by('course__title')

        attempts = UserQuizAttempt.objects.filter(
            user=request.user, attempt_type='post'
        ).select_related('quiz__course')

        best_map = {}
        for a in attempts:
            cid = a.quiz.course_id
            if cid not in best_map or a.score_percentage > best_map[cid].score_percentage:
                best_map[cid] = a

        certs = {c.course_id: c for c in Certificate.objects.filter(user=request.user).select_related('course')}

        context = {
            'user': request.user,
            'progress_list': progress_list,
            'best_map': best_map,
            'certs': certs,
            'generated_at': __import__('datetime').datetime.now(),
        }

        from django.template.loader import render_to_string
        from lms.utils import link_callback
        import io
        from xhtml2pdf import pisa

        html = render_to_string('lms/transcript_template.html', context, request=request)
        buf = io.BytesIO()
        pisa.CreatePDF(html, dest=buf, link_callback=link_callback)
        buf.seek(0)

        response = HttpResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="transcript_{request.user.username}.pdf"'
        return response
```

### แก้ไข `lms/urls.py` — เพิ่ม URL

```python
path('transcript/', views.LearnerTranscriptView.as_view(), name='learner-transcript'),
```

### สร้างไฟล์ใหม่: `lms/templates/lms/transcript_template.html`

(ใช้ inline CSS เท่านั้น เหมือน certificate_template.html — ห้ามใช้ Tailwind CDN)

```html
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <style>
    @font-face {
      font-family: 'Sarabun';
      src: url('{{ STATIC_URL }}lms/fonts/Sarabun-Regular.ttf');
    }
    body { font-family: 'Sarabun', sans-serif; font-size: 13px; color: #333; margin: 30px; }
    h1 { color: #134e4a; font-size: 20px; margin-bottom: 4px; }
    h2 { color: #134e4a; font-size: 14px; border-bottom: 1px solid #134e4a; padding-bottom: 4px; margin-top: 24px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th { background: #134e4a; color: white; padding: 6px 10px; text-align: left; font-size: 12px; }
    td { padding: 6px 10px; border-bottom: 1px solid #e5e7eb; font-size: 12px; }
    .passed { color: #16a34a; }
    .failed { color: #dc2626; }
    .footer { margin-top: 30px; font-size: 10px; color: #999; text-align: right; }
  </style>
</head>
<body>
  <h1>Transcript การเรียน</h1>
  <p>ชื่อ: {{ user.get_full_name }} &nbsp;|&nbsp; รหัส: {{ user.username }} &nbsp;|&nbsp; สาขา: {{ user.department }}</p>
  <p style="font-size:11px; color:#999;">สร้างเมื่อ: {{ generated_at|date:"j F Y" }}</p>

  <h2>รายวิชา</h2>
  <table>
    <tr>
      <th>วิชา</th>
      <th>สถานะ</th>
      <th>คะแนน Post-test</th>
      <th>ใบประกาศฯ</th>
    </tr>
    {% for p in progress_list %}
    {% with best=best_map|get_item:p.course_id cert=certs|get_item:p.course_id %}
    <tr>
      <td>{{ p.course.title }}</td>
      <td>{% if p.status == 'completed' %}เรียนจบแล้ว{% else %}กำลังเรียน{% endif %}</td>
      <td>
        {% if best %}
          <span class="{% if best.is_passed %}passed{% else %}failed{% endif %}">
            {{ best.score_percentage|floatformat:0 }}%
          </span>
        {% else %}-{% endif %}
      </td>
      <td>{% if cert %}{{ cert.serial_number }}{% else %}-{% endif %}</td>
    </tr>
    {% endwith %}
    {% endfor %}
  </table>

  <div class="footer">ระบบ E-Learning ห้องสมุดมหาวิทยาลัยนครพนม — lib.npu.ac.th/courses</div>
</body>
</html>
```

### แก้ไข `lms/templates/lms/profile.html` — เพิ่มปุ่ม Transcript

เพิ่มปุ่มในส่วน User Info:
```html
<a href="{% url 'learner-transcript' %}"
   class="inline-flex items-center gap-2 px-4 py-2 bg-teal-800 text-white text-sm rounded-lg hover:bg-teal-700 transition mt-3">
  ดาวน์โหลด Transcript PDF
</a>
```

---

## ลำดับการ implement

```
งาน 1 → งาน 2 → งาน 3 → งาน 4 → งาน 5 → งาน 6
```

งาน 2 และ 4 ต้องรัน migration หลังแก้ models.py:
```bash
python manage.py makemigrations lms
python manage.py migrate
```

---

## Verification

```bash
# Start dev server
source venv/bin/activate
python manage.py runserver 8001

# งาน 1: Course Search
# http://127.0.0.1:8001/ → พิมพ์คำค้นใน search box → ผลกรองถูกต้อง

# งาน 2: Pass Threshold
# Staff → แก้ไขวิชา → เปลี่ยน pass_threshold → ทำ quiz → ตรวจว่าใช้ค่าใหม่

# งาน 3: Profile Page
# http://127.0.0.1:8001/profile/ → ต้องเห็นประวัติวิชา + คะแนน + ลิงก์ใบประกาศฯ

# งาน 4: Serial Number
# ดาวน์โหลดใบประกาศฯ → เห็นเลขที่ CERT-256X-XXXXXX ใน PDF

# งาน 5: Export CSV
# Staff → Report → กดปุ่ม Export CSV → ดาวน์โหลด CSV ที่เปิดใน Excel ได้ (ภาษาไทยไม่แตก)

# งาน 6: Transcript PDF
# http://127.0.0.1:8001/profile/ → กด "ดาวน์โหลด Transcript PDF" → PDF แสดงวิชาทั้งหมด

# Run tests
python -m pytest tests/ --browser chromium -v
# Expected: 102 passed, 0 failed
```

---

## ไฟล์ที่แก้ไขทั้งหมด

| ไฟล์ | การเปลี่ยนแปลง |
|------|--------------|
| `lms/models.py` | เพิ่ม `pass_threshold` ใน Course + `serial_number` ใน Certificate |
| `lms/views.py` | CourseListView (search) + 3 views ใหม่ + import csv/StreamingHttpResponse |
| `lms/staff_urls.py` | เพิ่ม report export URL |
| `lms/urls.py` | เพิ่ม profile + transcript URLs |
| `lms/templates/lms/course_list.html` | เพิ่ม search form |
| `lms/templates/lms/quiz.html` | เปลี่ยน hardcode 70% |
| `lms/templates/lms/quiz_result.html` | เปลี่ยน hardcode 70% |
| `lms/templates/lms/certificate_template.html` | เพิ่ม serial number |
| `lms/templates/lms/staff/course_report.html` | เพิ่มปุ่ม Export CSV |
| `lms/templates/lms/profile.html` | **ไฟล์ใหม่** |
| `lms/templates/lms/transcript_template.html` | **ไฟล์ใหม่** |
| `lms/utils.py` | เปลี่ยน hardcode 70 → course.pass_threshold |
