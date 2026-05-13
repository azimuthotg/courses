# Task: UI Color Theme Redesign — Micro-LMS (NPU Library)

## Objective
Replace the current blue-based color theme with a **teal + amber** theme matching the ARC NPU brand identity (Academic Resources Center, Nakhon Phanom University). Font and layout must not change — colors only.

## Stack Constraints
- Tailwind CSS via CDN (no build step, no npm, no config file)
- Django templates (HTML files only)
- Font: Sarabun — do not change

## Color Replacement Rules

### Tailwind class replacements (apply across all template files)

| Old class | New class |
|-----------|-----------|
| `bg-blue-900` | `bg-teal-900` |
| `bg-blue-700` | `bg-teal-800` |
| `bg-blue-600` | `bg-teal-700` |
| `bg-blue-100` | `bg-teal-100` |
| `bg-blue-200` | `bg-teal-200` |
| `hover:bg-blue-600` | `hover:bg-teal-700` |
| `hover:bg-blue-700` | `hover:bg-teal-800` |
| `text-blue-900` | `text-teal-900` |
| `text-blue-700` | `text-teal-700` |
| `text-blue-600` | `text-teal-700` |
| `text-blue-400` | `text-teal-400` |
| `text-blue-300` | `text-teal-300` |
| `text-blue-200` | `text-teal-200` |
| `text-blue-100` | `text-teal-100` |
| `text-blue-800` | `text-teal-800` |
| `border-blue-200` | `border-teal-200` |
| `from-blue-900` | `from-teal-900` |
| `to-blue-700` | `to-teal-800` |
| `from-blue-100` | `from-teal-100` |
| `to-blue-200` | `to-teal-200` |
| `focus:ring-blue-500` | `focus:ring-teal-600` |
| `focus:border-blue-500` | `focus:border-teal-600` |
| `group-hover:text-blue-700` | `group-hover:text-teal-700` |
| `hover:text-blue-200` | `hover:text-teal-200` |
| `text-indigo-700` | `text-teal-700` |
| `hover:text-indigo-900` | `hover:text-teal-900` |
| `bg-yellow-500` | `bg-amber-500` |
| `bg-yellow-400` | `bg-amber-400` |
| `bg-yellow-100` | `bg-amber-100` |
| `bg-yellow-50` | `bg-amber-50` |
| `hover:bg-yellow-400` | `hover:bg-amber-400` |
| `text-yellow-700` | `text-amber-700` |
| `text-yellow-800` | `text-amber-800` |
| `text-yellow-600` | `text-amber-600` |
| `border-yellow-200` | `border-amber-200` |
| `from-yellow-50` | `from-amber-50` |
| `bg-orange-500` | `bg-amber-600` |
| `bg-orange-400` | `bg-amber-500` |
| `hover:bg-orange-400` | `hover:bg-amber-500` |
| `to-orange-50` | `to-amber-100` |
| `bg-gray-50` (page background only) | `bg-amber-50` |

### Do NOT change these (semantic — keep as-is)
- `text-red-*`, `bg-red-*`, `border-red-*` — error states
- `text-green-*`, `bg-green-*` — success / completed states
- `text-gray-*`, `bg-gray-*` (except `bg-gray-50` on body/page wrapper)
- `bg-white`, `shadow-*`, `rounded-*`, `border-*` (non-color structure)

### Hardcoded hex in `certificate_template.html` only
| Old hex | New hex |
|---------|---------|
| `#1e3a5f` | `#134e4a` |
| `#b8860b` | `#d97706` |

## Files to Modify (in order)

### Student templates
1. `lms/templates/base.html`
2. `lms/templates/registration/login.html`
3. `lms/templates/lms/course_list.html`
4. `lms/templates/lms/course_detail.html`
5. `lms/templates/lms/lesson.html`
6. `lms/templates/lms/quiz.html`
7. `lms/templates/lms/quiz_result.html`
8. `lms/templates/lms/certificate_template.html`

### Staff templates
9. `lms/templates/lms/staff/dashboard.html`
10. `lms/templates/lms/staff/course_list.html`
11. `lms/templates/lms/staff/course_form.html`
12. `lms/templates/lms/staff/course_report.html`
13. `lms/templates/lms/staff/lesson_form.html`
14. `lms/templates/lms/staff/lesson_confirm_delete.html`
15. `lms/templates/lms/staff/question_form.html`
16. `lms/templates/lms/staff/quiz_edit.html`

## Rules
1. Modify HTML template files only — no Python, no settings, no CSS files
2. Do not change font, layout, spacing, or element structure
3. Do not add new files
4. Semantic colors (red, green) must remain unchanged
5. Use only Tailwind built-in class names — no custom CSS or inline styles

## Verification
```bash
python manage.py runserver 8001
# Check visually: /login/ /  /course/<id>/ /staff/

python -m pytest tests/ --browser chromium -v
# Expected: 102 passed, 0 failed
```
