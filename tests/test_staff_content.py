"""
Browser tests: staff content management frontend.
"""
import os
import subprocess

from playwright.sync_api import Page, expect

from test_settings import BASE_URL


COURSE_TITLE = "[PW STAFF] Content Course"
UPDATED_COURSE_TITLE = "[PW STAFF] Updated Course"
LESSON_TITLE = "[PW STAFF] Lesson"
UPDATED_LESSON_TITLE = "[PW STAFF] Updated Lesson"
QUESTION_TEXT = "[PW STAFF] Question?"
UPDATED_QUESTION_TEXT = "[PW STAFF] Updated Question?"


def run_django(code):
    completed = subprocess.run(
        ["./venv/bin/python", "manage.py", "shell", "-c", code],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def cleanup_staff_data():
    run_django(
        "from lms.models import Course; "
        "Course.objects.filter(title__startswith='[PW STAFF]').delete()"
    )


def create_course(active=True):
    code = (
        "from lms.models import Course; "
        f"c=Course.objects.create(title='{COURSE_TITLE}', description='staff test', "
        f"is_active={active}, require_post_test=True); "
        "print(c.pk)"
    )
    return int(run_django(code).splitlines()[-1])


def create_course_with_lesson():
    code = (
        "from lms.models import Course, Lesson; "
        f"c=Course.objects.create(title='{COURSE_TITLE}', description='staff test', "
        "is_active=True, require_post_test=True); "
        f"l=Lesson.objects.create(course=c, title='{LESSON_TITLE}', youtube_video_id='dQw4w9WgXcQ', order=1); "
        "print(c.pk); print(l.pk)"
    )
    lines = run_django(code).splitlines()
    return int(lines[-2]), int(lines[-1])


def create_course_with_question():
    code = (
        "from lms.models import Answer, Course, Lesson, Quiz, Question; "
        f"c=Course.objects.create(title='{COURSE_TITLE}', description='staff test', "
        "is_active=True, require_post_test=True); "
        "qz=Quiz.objects.create(course=c, quiz_type='post'); "
        f"q=Question.objects.create(quiz=qz, text='{QUESTION_TEXT}', order=1); "
        "Answer.objects.create(question=q, text='A', is_correct=True); "
        "Answer.objects.create(question=q, text='B', is_correct=False); "
        "Answer.objects.create(question=q, text='C', is_correct=False); "
        "Answer.objects.create(question=q, text='D', is_correct=False); "
        "print(c.pk); print(q.pk)"
    )
    lines = run_django(code).splitlines()
    return int(lines[-2]), int(lines[-1])


class CleanupMixin:
    def setup_method(self):
        cleanup_staff_data()

    def teardown_method(self):
        cleanup_staff_data()


class TestStaffAccessControl(CleanupMixin):
    def test_staff_dashboard_requires_login(self, page: Page):
        page.goto("/staff/")
        expect(page).to_have_url(f"{BASE_URL}/login/?next=/staff/")

    def test_student_cannot_access_staff_dashboard(self, student_page: Page):
        page = student_page
        page.goto("/staff/")
        expect(page).to_have_url(f"{BASE_URL}/staff/")
        expect(page.get_by_role("heading", name="403")).to_be_visible()

    def test_admin_can_access_staff_dashboard(self, admin_page: Page):
        page = admin_page
        page.goto("/staff/")
        expect(page.get_by_role("heading", name="จัดการเนื้อหา")).to_be_visible()

    def test_navbar_shows_content_link_for_staff_only(self, student_page: Page):
        student_page.goto("/")
        expect(student_page.get_by_role("link", name="จัดการเนื้อหา")).not_to_be_visible()


class TestStaffCourseCrud(CleanupMixin):
    def test_course_list_loads(self, admin_page: Page):
        page = admin_page
        page.goto("/staff/courses/")
        expect(page.get_by_role("heading", name="หลักสูตรทั้งหมด")).to_be_visible()

    def test_create_course(self, admin_page: Page):
        page = admin_page
        page.goto("/staff/courses/create/")
        page.fill('input[name="title"]', COURSE_TITLE)
        page.fill('textarea[name="description"]', "Created by Playwright")
        page.check('input[name="require_post_test"]')
        page.check('input[name="is_active"]')
        page.get_by_role("button", name="บันทึก").click()
        page.wait_for_url(f"{BASE_URL}/staff/courses/")
        expect(page.locator(f"text={COURSE_TITLE}").first).to_be_visible()

    def test_edit_course(self, admin_page: Page):
        course_id = create_course()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/edit/")
        page.fill('input[name="title"]', UPDATED_COURSE_TITLE)
        page.get_by_role("button", name="บันทึก").click()
        expect(page.locator("text=บันทึกหลักสูตรสำเร็จ")).to_be_visible()
        expect(page.locator('input[name="title"]')).to_have_value(UPDATED_COURSE_TITLE)

    def test_delete_course(self, admin_page: Page):
        course_id = create_course()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/delete/")
        expect(page.get_by_role("heading", name="ยืนยันลบหลักสูตร")).to_be_visible()
        page.get_by_role("button", name="ลบหลักสูตร").click()
        page.wait_for_url(f"{BASE_URL}/staff/courses/")
        run_django(f"from lms.models import Course; assert not Course.objects.filter(pk={course_id}).exists()")

    def test_course_edit_shows_lesson_and_quiz_sections(self, admin_page: Page):
        course_id, _ = create_course_with_lesson()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/edit/")
        expect(page.get_by_role("heading", name="บทเรียน")).to_be_visible()
        expect(page.locator("text=คำถามชุดเดียวสำหรับ Pre-test และ Post-test")).to_be_visible()


class TestStaffLessonManagement(CleanupMixin):
    def test_create_lesson(self, admin_page: Page):
        course_id = create_course()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/lessons/create/")
        page.fill('input[name="title"]', LESSON_TITLE)
        page.fill('input[name="youtube_video_id"]', "dQw4w9WgXcQ")
        page.fill('input[name="order"]', "1")
        page.get_by_role("button", name="บันทึก").click()
        page.wait_for_url(f"{BASE_URL}/staff/courses/{course_id}/edit/")
        expect(page.locator(f"text={LESSON_TITLE}")).to_be_visible()

    def test_edit_lesson(self, admin_page: Page):
        course_id, lesson_id = create_course_with_lesson()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/lessons/{lesson_id}/edit/")
        page.fill('input[name="title"]', UPDATED_LESSON_TITLE)
        page.get_by_role("button", name="บันทึก").click()
        page.wait_for_url(f"{BASE_URL}/staff/courses/{course_id}/edit/")
        expect(page.locator(f"text={UPDATED_LESSON_TITLE}")).to_be_visible()

    def test_duplicate_lesson_order_shows_validation(self, admin_page: Page):
        course_id, _ = create_course_with_lesson()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/lessons/create/")
        page.fill('input[name="title"]', "Duplicate order")
        page.fill('input[name="youtube_video_id"]', "dQw4w9WgXcQ")
        page.fill('input[name="order"]', "1")
        page.get_by_role("button", name="บันทึก").click()
        expect(page).to_have_url(f"{BASE_URL}/staff/courses/{course_id}/lessons/create/")
        expect(page.locator("text=ลำดับนี้ถูกใช้แล้ว")).to_be_visible()

    def test_delete_lesson(self, admin_page: Page):
        course_id, lesson_id = create_course_with_lesson()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/lessons/{lesson_id}/delete/")
        page.get_by_role("button", name="ลบบทเรียน").click()
        page.wait_for_url(f"{BASE_URL}/staff/courses/{course_id}/edit/")
        expect(page.locator(f"text={LESSON_TITLE}")).not_to_be_visible()


class TestStaffQuizQuestionManagement(CleanupMixin):
    def test_quiz_auto_create_and_loads(self, admin_page: Page):
        course_id = create_course()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/quiz/post/")
        expect(page.get_by_role("heading", name="ชุดคำถาม Pre-test / Post-test")).to_be_visible()

    def test_create_question_with_answers(self, admin_page: Page):
        course_id = create_course()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/quiz/post/questions/create/")
        page.fill('textarea[name="question_text"]', QUESTION_TEXT)
        page.fill('input[name="question_order"]', "1")
        for idx, text in enumerate(["A", "B", "C", "D"], start=1):
            page.fill(f'input[name="answer_{idx}"]', text)
        page.check('input[name="correct_answer"][value="2"]')
        page.get_by_role("button", name="บันทึก").click()
        page.wait_for_url(f"{BASE_URL}/staff/courses/{course_id}/quiz/post/")
        expect(page.locator(f"text={QUESTION_TEXT}")).to_be_visible()

    def test_edit_question(self, admin_page: Page):
        course_id, question_id = create_course_with_question()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/quiz/post/questions/{question_id}/edit/")
        page.fill('textarea[name="question_text"]', UPDATED_QUESTION_TEXT)
        page.fill('input[name="answer_1"]', "Updated A")
        page.check('input[name="correct_answer"][value="1"]')
        page.get_by_role("button", name="บันทึก").click()
        page.wait_for_url(f"{BASE_URL}/staff/courses/{course_id}/quiz/post/")
        expect(page.locator(f"text={UPDATED_QUESTION_TEXT}")).to_be_visible()

    def test_delete_question(self, admin_page: Page):
        course_id, question_id = create_course_with_question()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/quiz/post/questions/{question_id}/delete/")
        page.get_by_role("button", name="ลบคำถาม").click()
        page.wait_for_url(f"{BASE_URL}/staff/courses/{course_id}/quiz/post/")
        expect(page.locator(f"text={QUESTION_TEXT}")).not_to_be_visible()

    def test_question_create_requires_all_answers(self, admin_page: Page):
        course_id = create_course()
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/quiz/post/questions/create/")
        page.fill('textarea[name="question_text"]', QUESTION_TEXT)
        page.fill('input[name="question_order"]', "1")
        page.fill('input[name="answer_1"]', "A")
        page.get_by_role("button", name="บันทึก").click()
        expect(page).to_have_url(f"{BASE_URL}/staff/courses/{course_id}/quiz/post/questions/create/")


class TestStaffReports(CleanupMixin):
    def test_report_loads(self, admin_page: Page):
        course_id = create_course_with_question()[0]
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/report/")
        expect(page.get_by_role("heading", name="รายงานหลักสูตร")).to_be_visible()

    def test_report_shows_stat_cards(self, admin_page: Page):
        course_id = create_course_with_question()[0]
        page = admin_page
        page.goto(f"/staff/courses/{course_id}/report/")
        expect(page.locator("text=ผู้เรียน")).to_be_visible()
        expect(page.locator("text=เรียนจบ")).to_be_visible()
        expect(page.locator("text=ใบประกาศ")).to_be_visible()

    def test_report_link_from_course_list(self, admin_page: Page):
        course_id = create_course()
        page = admin_page
        page.goto("/staff/courses/")
        page.locator(f'a[href="/staff/courses/{course_id}/report/"]').click()
        expect(page).to_have_url(f"{BASE_URL}/staff/courses/{course_id}/report/")
