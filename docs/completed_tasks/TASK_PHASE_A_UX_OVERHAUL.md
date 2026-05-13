# Task: Phase A — UX Overhaul — Micro-LMS (NPU Library)

## Overview
ปรับปรุง UX ทั้ง Staff และ Student โดยไม่เปลี่ยน business logic ใดๆ
เน้น 5 งานหลัก ทำตามลำดับที่ระบุ

## Stack Constraints
- Tailwind CSS via CDN — ไม่มี build step
- Django templates + class-based views
- ห้ามเปลี่ยน models.py เว้นแต่ระบุให้เปลี่ยน
- ห้ามเปลี่ยน business logic ใน views.py เว้นแต่ระบุให้เปลี่ยน
- รัน `python -m pytest tests/ --browser chromium -v` ต้องผ่าน 102 tests

---

## งานที่ 1: Staff Left Sidebar (แทน navbar links)

### เป้าหมาย
ย้ายเมนู Staff ออกจาก Navbar มาเป็น Left Sidebar เฉพาะหน้า `/staff/*`

### ขั้นตอน

**1.1 สร้างไฟล์ใหม่: `lms/templates/lms/staff/_sidebar.html`**

```html
<aside class="w-56 min-h-screen bg-teal-900 text-white flex flex-col py-6 px-3 shrink-0">
  <div class="text-xs font-semibold uppercase tracking-widest text-teal-300 px-3 mb-4">
    เมนูจัดการ
  </div>
  <nav class="flex flex-col gap-1">
    <a href="{% url 'staff-dashboard' %}"
       class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm hover:bg-teal-800 transition
              {% if request.resolver_match.url_name == 'staff-dashboard' %}bg-teal-800 font-semibold{% endif %}">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
      </svg>
      Dashboard
    </a>
    <a href="{% url 'staff-course-list' %}"
       class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm hover:bg-teal-800 transition
              {% if 'course' in request.resolver_match.url_name %}bg-teal-800 font-semibold{% endif %}">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
      </svg>
      จัดการรายวิชา
    </a>
    <a href="{% url 'local-user-create' %}"
       class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm hover:bg-teal-800 transition
              {% if request.resolver_match.url_name == 'local-user-create' %}bg-teal-800 font-semibold{% endif %}">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
      </svg>
      จัดการผู้ใช้
    </a>
    <a href="{% url 'admin:index' %}"
       class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm hover:bg-teal-800 transition">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
      </svg>
      Django Admin
    </a>
  </nav>
</aside>
```

**1.2 แก้ไข `lms/templates/base.html`**

ใน navbar block — ลบ staff links ออกทั้งหมด:
```html
<!-- ลบออก: -->
{% if user.is_staff %}
  <a href="{% url 'staff-dashboard' %}" ...>จัดการเนื้อหา</a>
  <a href="{% url 'local-user-create' %}" ...>เพิ่มผู้ใช้</a>
  <a href="{% url 'admin:index' %}" ...>Admin</a>
{% endif %}
```

**1.3 สร้างไฟล์ใหม่: `lms/templates/lms/staff/base_staff.html`**

```html
{% extends 'base.html' %}

{% block content %}
<div class="flex min-h-screen">
  {% include 'lms/staff/_sidebar.html' %}
  <main class="flex-1 bg-amber-50 p-6 overflow-auto">
    {% block staff_content %}{% endblock %}
  </main>
</div>
{% endblock %}
```

**1.4 แก้ไข staff templates ทุกไฟล์** ให้ extends เปลี่ยนเป็น:

```html
<!-- เปลี่ยนจาก -->
{% extends 'base.html' %}
{% block content %}...{% endblock %}

<!-- เป็น -->
{% extends 'lms/staff/base_staff.html' %}
{% block staff_content %}...{% endblock %}
```

ไฟล์ที่ต้องแก้:
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
- `lms/templates/lms/user_create.html` (ถ้ามี)

---

## งานที่ 2: Breadcrumb Navigation

### เป้าหมาย
เพิ่ม breadcrumb ด้านบนของทุกหน้าที่ไม่ใช่ home

### Breadcrumb Component (inline ในแต่ละ template)

**รูปแบบ HTML:**
```html
<nav class="text-sm text-gray-500 mb-4" aria-label="breadcrumb">
  <ol class="flex items-center gap-1">
    <li><a href="{% url 'course-list' %}" class="hover:text-teal-700">หน้าแรก</a></li>
    <li class="text-gray-300">/</li>
    <li class="text-gray-700 font-medium">{{ ชื่อหน้าปัจจุบัน }}</li>
  </ol>
</nav>
```

**ใส่ breadcrumb ใน:**

| Template | Breadcrumb |
|----------|-----------|
| `course_detail.html` | หน้าแรก / {{ course.title }} |
| `lesson.html` | หน้าแรก / {{ course.title }} / {{ lesson.title }} |
| `quiz.html` | หน้าแรก / {{ course.title }} / {{ quiz_title }} |
| `quiz_result.html` | หน้าแรก / {{ course.title }} / ผลการทดสอบ |

**สำหรับ Staff (ใน `staff_content` block ของแต่ละหน้า):**

| Template | Breadcrumb |
|----------|-----------|
| `dashboard.html` | จัดการ / Dashboard |
| `course_list.html` | จัดการ / รายวิชาทั้งหมด |
| `course_form.html` (create) | จัดการ / รายวิชา / เพิ่มรายวิชา |
| `course_form.html` (edit) | จัดการ / รายวิชา / {{ course.title }} |
| `lesson_form.html` | จัดการ / {{ course.title }} / บทเรียน |
| `quiz_edit.html` | จัดการ / {{ course.title }} / แบบทดสอบ |
| `course_report.html` | จัดการ / {{ course.title }} / รายงาน |

---

## งานที่ 3: Previous / Next Lesson Buttons

### เป้าหมาย
เพิ่มปุ่ม ← บทที่แล้ว และ บทถัดไป → ใน `lesson.html`

### แก้ไข `lms/views.py` — LessonView.get()

เพิ่ม context variables ก่อน return:

```python
# ใน LessonView.get() หลังจากได้ lessons queryset แล้ว
lessons_list = list(lessons)  # แปลงเป็น list เพื่อ index
current_index = next((i for i, l in enumerate(lessons_list) if l.pk == lesson.pk), 0)
prev_lesson = lessons_list[current_index - 1] if current_index > 0 else None
next_lesson = lessons_list[current_index + 1] if current_index < len(lessons_list) - 1 else None
lesson_number = current_index + 1
lesson_total = len(lessons_list)

context = {
    ...existing context...,
    'prev_lesson': prev_lesson,
    'next_lesson': next_lesson,
    'lesson_number': lesson_number,
    'lesson_total': lesson_total,
}
```

### แก้ไข `lms/templates/lms/lesson.html`

เพิ่ม counter และปุ่ม nav ใต้ video:

```html
<!-- Progress counter ใต้ชื่อบทเรียน -->
<p class="text-sm text-gray-500 mt-1">บทที่ {{ lesson_number }} จาก {{ lesson_total }} บท</p>

<!-- Prev/Next buttons ใต้ video iframe -->
<div class="flex justify-between items-center mt-4">
  {% if prev_lesson %}
    <a href="{% url 'lesson' course.pk prev_lesson.pk %}"
       class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg
              text-sm text-gray-700 hover:bg-teal-50 hover:border-teal-300 transition">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
      </svg>
      {{ prev_lesson.title }}
    </a>
  {% else %}
    <div></div>
  {% endif %}

  {% if next_lesson %}
    <a href="{% url 'lesson' course.pk next_lesson.pk %}"
       class="flex items-center gap-2 px-4 py-2 bg-teal-800 text-white rounded-lg
              text-sm hover:bg-teal-700 transition">
      {{ next_lesson.title }}
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
      </svg>
    </a>
  {% else %}
    <a href="{% url 'course-detail' course.pk %}"
       class="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg
              text-sm hover:bg-amber-400 transition">
      กลับหน้าวิชา
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
      </svg>
    </a>
  {% endif %}
</div>
```

---

## งานที่ 4: Progress Bar %

### เป้าหมาย
แสดง % ความคืบหน้าใน course_detail.html และ lesson.html

### แก้ไข `lms/views.py`

**CourseDetailView.get_context_data()** — เพิ่ม:
```python
lessons_total = lessons.count()
lessons_done = progress.lessons_completed.count()
progress_pct = int(lessons_done / lessons_total * 100) if lessons_total > 0 else 0

context = {
    ...existing...,
    'lessons_total': lessons_total,
    'lessons_done': lessons_done,
    'progress_pct': progress_pct,
}
```

**LessonView.get()** — เพิ่ม (ใช้ context เดิม + เพิ่ม):
```python
lessons_total = len(lessons_list)
lessons_done = progress.lessons_completed.count()
progress_pct = int(lessons_done / lessons_total * 100) if lessons_total > 0 else 0

# เพิ่มใน context:
'progress_pct': progress_pct,
'lessons_done': lessons_done,
'lessons_total': lessons_total,
```

### Progress Bar HTML (ใช้ใน course_detail.html และ lesson.html)

```html
<div class="mb-4">
  <div class="flex justify-between text-sm text-gray-500 mb-1">
    <span>ความคืบหน้า</span>
    <span>{{ lessons_done }}/{{ lessons_total }} บท ({{ progress_pct }}%)</span>
  </div>
  <div class="w-full bg-gray-200 rounded-full h-2">
    <div class="bg-teal-600 h-2 rounded-full transition-all duration-300"
         style="width: {{ progress_pct }}%"></div>
  </div>
</div>
```

**ตำแหน่งที่ใส่:**
- `course_detail.html`: ใต้ชื่อวิชาและ description ก่อน lesson list
- `lesson.html`: ใต้ breadcrumb ก่อน video player

---

## งานที่ 5: Quiz Answer Review

### เป้าหมาย
หลัง submit quiz ให้นักศึกษาเห็นว่าข้อไหนถูก/ผิด และคำตอบที่ถูกต้องคืออะไร

### แก้ไข `lms/views.py` — QuizView.post()

หา section ที่ render quiz_result แล้วเพิ่ม answer_review:

```python
# ใน QuizView.post() หลังจาก score calculation
# ดึง questions + answers สำหรับ review
questions = quiz.questions.prefetch_related('answers').order_by('order')
answer_review = []
for question in questions:
    user_answer_id = request.POST.get(f'question_{question.pk}')
    correct_answer = question.answers.filter(is_correct=True).first()
    user_answer = question.answers.filter(pk=user_answer_id).first() if user_answer_id else None
    answer_review.append({
        'question': question.text,
        'user_answer': user_answer.text if user_answer else '(ไม่ได้ตอบ)',
        'correct_answer': correct_answer.text if correct_answer else '',
        'is_correct': user_answer == correct_answer if user_answer else False,
    })

return render(request, 'lms/quiz_result.html', {
    ...existing context...,
    'answer_review': answer_review,
})
```

### แก้ไข `lms/templates/lms/quiz_result.html`

เพิ่ม section ใต้ score card:

```html
{% if answer_review %}
<div class="mt-6 bg-white rounded-xl shadow p-6">
  <h3 class="text-lg font-semibold text-gray-800 mb-4">ตรวจคำตอบ</h3>
  <div class="space-y-4">
    {% for item in answer_review %}
    <div class="border rounded-lg p-4
                {% if item.is_correct %}border-green-200 bg-green-50
                {% else %}border-red-200 bg-red-50{% endif %}">
      <p class="font-medium text-gray-800 mb-2">
        ข้อ {{ forloop.counter }}: {{ item.question }}
      </p>
      <p class="text-sm {% if item.is_correct %}text-green-700{% else %}text-red-700{% endif %}">
        คำตอบของคุณ: {{ item.user_answer }}
        {% if item.is_correct %}✅{% else %}❌{% endif %}
      </p>
      {% if not item.is_correct %}
      <p class="text-sm text-gray-600 mt-1">
        คำตอบที่ถูกต้อง: <span class="font-medium text-green-700">{{ item.correct_answer }}</span>
      </p>
      {% endif %}
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}
```

---

## Verification

```bash
# 1. รัน dev server
source venv/bin/activate
python manage.py runserver 8001

# 2. ตรวจ Staff Sidebar
# เปิด http://127.0.0.1:8001/staff/
# ต้องเห็น Left Sidebar ทางซ้าย ไม่มี staff links ใน navbar อีกต่อไป
# คลิกทุกลิงก์ใน sidebar ให้ทำงานได้

# 3. ตรวจ Breadcrumb
# เปิด course detail, lesson, quiz — ต้องเห็น breadcrumb ด้านบน

# 4. ตรวจ Prev/Next
# เปิด lesson ที่มีหลาย lesson — ต้องเห็นปุ่ม ← → ที่ใช้งานได้
# lesson แรก: ไม่มีปุ่ม ←
# lesson สุดท้าย: ปุ่ม → เปลี่ยนเป็น "กลับหน้าวิชา"

# 5. ตรวจ Progress Bar
# เปิด course detail ที่ดูบางบทเรียนแล้ว — ต้องเห็น bar และ % ถูกต้อง

# 6. ตรวจ Quiz Answer Review
# ทำ quiz แล้ว submit — ต้องเห็น section ตรวจคำตอบใต้ผลคะแนน

# 7. รัน tests
python -m pytest tests/ --browser chromium -v
# Expected: 102 passed, 0 failed
```

---

## ไฟล์ที่แก้ไขทั้งหมด

| ไฟล์ | การเปลี่ยนแปลง |
|------|--------------|
| `lms/views.py` | LessonView + CourseDetailView + QuizView.post() |
| `lms/templates/base.html` | ลบ staff navbar links |
| `lms/templates/lms/staff/_sidebar.html` | **ไฟล์ใหม่** |
| `lms/templates/lms/staff/base_staff.html` | **ไฟล์ใหม่** |
| `lms/templates/lms/staff/dashboard.html` | extends base_staff |
| `lms/templates/lms/staff/course_list.html` | extends base_staff |
| `lms/templates/lms/staff/course_form.html` | extends base_staff |
| `lms/templates/lms/staff/course_confirm_delete.html` | extends base_staff |
| `lms/templates/lms/staff/course_report.html` | extends base_staff |
| `lms/templates/lms/staff/lesson_form.html` | extends base_staff |
| `lms/templates/lms/staff/lesson_confirm_delete.html` | extends base_staff |
| `lms/templates/lms/staff/quiz_edit.html` | extends base_staff |
| `lms/templates/lms/staff/question_form.html` | extends base_staff |
| `lms/templates/lms/staff/question_confirm_delete.html` | extends base_staff |
| `lms/templates/lms/course_detail.html` | breadcrumb + progress bar |
| `lms/templates/lms/lesson.html` | breadcrumb + progress bar + prev/next |
| `lms/templates/lms/quiz.html` | breadcrumb |
| `lms/templates/lms/quiz_result.html` | breadcrumb + answer review |
