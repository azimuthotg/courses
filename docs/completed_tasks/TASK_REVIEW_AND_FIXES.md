# Task: Review & Fix — ตรวจสอบหลัง Phase A B C — Micro-LMS

## บริบท
เทียบ AUDIT_HANDOFF.md กับ task briefs ที่ออกแบบไว้ทั้ง 3 Phase
พบประเด็นที่ต้องแก้ไขและตรวจสอบ แบ่งเป็น 3 ระดับ

---

## 🔴 ต้องแก้ไขทันที (Critical)

### Fix 1: Full Test Suite ยังไม่ถูกรันหลัง Phase A/B/C

**สิ่งที่พบ:**
- Phase A: รันแค่ targeted 78 tests (test_course_flow + test_staff_content)
- Phase B: รัน targeted เท่านั้น มี 4 failures ที่แก้แล้ว แต่ไม่ยืนยัน full suite
- Phase C: รันแค่ 12 tests (test_user_management + test_login)
- **Full 102-test suite ไม่ได้รันเลยหลังจากมีการเปลี่ยนแปลงทั้ง 3 phase**

**สิ่งที่ต้องทำ:**
```bash
source venv/bin/activate
python -m pytest tests/ --browser chromium -v
```

Expected: ผ่านทุก test ที่มีอยู่ + ไม่มี failure ใหม่

ถ้ามี failure ให้แก้ไขและรันซ้ำจนผ่านทั้งหมด แล้วรายงานผลรวม

---

### Fix 2: forms.py ยังมี Tailwind สี Blue เดิม

**สิ่งที่พบ:**
AUDIT_HANDOFF.md ระบุชัดว่า:
> "forms.py still contains older blue Tailwind constants for generated form widgets from before the theme task. This was not changed in Phase B because the task did not request theme cleanup."

หมายความว่า quiz form และ staff form อาจยังแสดงสีน้ำเงินเดิม ไม่ตรงกับ theme teal ที่ redesign ไป

**สิ่งที่ต้องทำ:**
เปิดไฟล์ `lms/forms.py` แล้วหา Tailwind class ที่เกี่ยวกับสีทั้งหมด:
- ค้นหา: `blue-` ทุก instance
- เปลี่ยนตาม mapping:
  - `blue-600`, `blue-700` → `teal-700`, `teal-800`
  - `focus:ring-blue-500` → `focus:ring-teal-600`
  - `border-blue-*` → `border-teal-*`
  - `bg-blue-*` → `bg-teal-*`

ตรวจสอบผลโดยเปิดหน้า quiz (`/course/<id>/quiz/pre/`) และหน้า staff course form ดูว่า widget มีสี teal แล้ว

---

### Fix 3: ตรวจสอบ UI Theme Redesign (TASK_UI_THEME_REDESIGN.md)

**สิ่งที่พบ:**
มีไฟล์ `TASK_UI_THEME_REDESIGN.md` ถูกสร้างก่อน Phase A แต่ AUDIT_HANDOFF.md ไม่ได้กล่าวถึงว่าทำเสร็จแล้ว

**สิ่งที่ต้องทำ:**
1. grep หา `blue-` class ที่เหลืออยู่ในทุก template:
```bash
grep -r "bg-blue-\|text-blue-\|border-blue-\|from-blue-\|to-blue-\|ring-blue-\|indigo-" \
  lms/templates/ --include="*.html" -l
```

2. ถ้าพบไฟล์ที่ยังมี blue class → ให้แก้ตาม mapping ใน `TASK_UI_THEME_REDESIGN.md`

3. ตรวจพิเศษ 2 หน้านี้ว่า teal แล้ว:
   - `/login/` — gradient background, ปุ่ม Login
   - `/staff/` — navbar, sidebar, ปุ่ม

---

## 🟡 ต้องตรวจสอบและยืนยัน (Should Verify)

### Check 4: Audit Log — Logout action

**สิ่งที่พบ:**
`AuditLog.ACTION_CHOICES` มี `('logout', 'Logout')` ใน model
แต่ AUDIT_HANDOFF.md smoke test ไม่ได้กล่าวถึงว่า logout ถูก log จริง

**สิ่งที่ต้องทำ:**
ตรวจสอบ `lms/views.py` — `LMSLogoutView`:
- ต้องมีการเรียก `log_audit(request.user, 'logout', request=request)` ก่อน logout
- ถ้าไม่มี → เพิ่มใน `dispatch()` หรือ `get()` ของ LMSLogoutView

ทดสอบ: login → logout → ดู Django Admin `/admin/lms/auditlog/` ต้องเห็น logout log

---

### Check 5: Audit Log — staff_user_create action

**สิ่งที่พบ:**
`AuditLog.ACTION_CHOICES` มี `('staff_user_create', 'User Created')`
แต่ handoff smoke test ยืนยันเฉพาะ bulk import log (`bulk_user_import`) ไม่ได้ยืนยัน `staff_user_create` จาก `LocalUserCreateView`

**สิ่งที่ต้องทำ:**
ตรวจสอบ `lms/views.py` — `LocalUserCreateView.form_valid()`:
- ต้องมี `log_audit(request.user, 'staff_user_create', user.username, request)`
- ถ้าไม่มี → เพิ่ม

ทดสอบ: Staff สร้าง user → ดู audit log → ต้องมี `staff_user_create`

---

### Check 6: ตรวจสอบ New Features มี Playwright Test ครอบคลุมไหม

**สิ่งที่พบ:**
Feature ใหม่ใน Phase B และ C ไม่มี Playwright test เลย:
- Course Search (`/?q=...`)
- User Profile (`/profile/`)
- Learner Transcript (`/transcript/`)
- Bulk User Import (`/staff/users/import/`)
- Audit Log (ใน Django Admin)

**สิ่งที่ต้องทำ:**
เพิ่ม test cases ใน `tests/test_course_flow.py` หรือไฟล์ใหม่ `tests/test_new_features.py`:

```python
# Test: Course Search
def test_course_search_returns_results(page, ...):
    # เข้า / → พิมพ์ชื่อวิชาในช่อง search → ตรวจว่ากรองได้
    pass

def test_course_search_no_results(page, ...):
    # ค้นหาคำที่ไม่มี → ต้องเห็นข้อความ "ไม่พบวิชา..."
    pass

# Test: User Profile
def test_user_profile_page_loads(page, ...):
    # เข้า /profile/ → ต้องเห็นชื่อ user และประวัติการเรียน
    pass

# Test: Learner Transcript
def test_transcript_pdf_download(page, ...):
    # กดปุ่ม Transcript ที่ /profile/ → ต้องได้ PDF
    pass

# Test: Bulk Import
def test_bulk_import_page_accessible_by_staff(page, ...):
    # Staff เข้า /staff/users/import/ → ต้องได้ 200
    pass

def test_bulk_import_page_blocked_for_student(page, ...):
    # Student เข้า /staff/users/import/ → ต้อง redirect ออก
    pass
```

ถ้าเขียน test ครบแล้ว รัน:
```bash
python -m pytest tests/ --browser chromium -v
```

---

## 🟢 ทำความสะอาด (Nice to Have)

### Cleanup 7: ลบหรือ archive ไฟล์ที่ไม่จำเป็น

ไฟล์ต่อไปนี้เป็น intermediate files ที่ Codex สร้างระหว่างการวางแผน:
- `PHASE_C_BRIEF.md` — Codex สร้างไว้ก่อน implement Phase C (ไม่จำเป็นแล้ว)
- `TASK_PHASE_A_UX_OVERHAUL.md` — เสร็จแล้ว
- `TASK_PHASE_B_FEATURES.md` — เสร็จแล้ว
- `TASK_PHASE_C_NOTIFICATIONS.md` — เสร็จแล้ว
- `TASK_UI_THEME_REDESIGN.md` — ตรวจสอบก่อน (Fix 3) แล้วค่อยลบ

ย้ายไปโฟลเดอร์ `docs/completed_tasks/` หรือลบทิ้ง ไม่ควรให้อยู่ใน root

---

## สรุปสิ่งที่ต้องทำตามลำดับ

| ลำดับ | งาน | ระดับ |
|-------|-----|-------|
| 1 | รัน full test suite 102 tests รายงานผล | 🔴 Critical |
| 2 | แก้ forms.py — เปลี่ยน blue → teal | 🔴 Critical |
| 3 | grep + แก้ template ที่ยังมี blue class | 🔴 Critical |
| 4 | ตรวจ / เพิ่ม logout audit log | 🟡 Should |
| 5 | ตรวจ / เพิ่ม staff_user_create audit log | 🟡 Should |
| 6 | เพิ่ม Playwright tests สำหรับ feature ใหม่ | 🟡 Should |
| 7 | ลบ / archive task brief files ที่เสร็จแล้ว | 🟢 Cleanup |

## Verification สุดท้าย

```bash
source venv/bin/activate

# ตรวจ theme
grep -r "bg-blue-\|text-blue-\|border-blue-" lms/templates/ --include="*.html"
# Expected: ไม่มี output

# Django check
python manage.py check
# Expected: no issues

# Full test suite
python -m pytest tests/ --browser chromium -v
# Expected: 102+ passed, 0 failed
```

รายงานผลกลับมาในรูป:
- จำนวน tests ที่ผ่าน / ไม่ผ่าน
- blue class ที่แก้ไปแล้ว (จำนวนไฟล์ / instances)
- audit log actions ที่ตรวจสอบแล้ว
