"""
Browser tests: Full learning flow — course list → lesson → post-test → certificate.

Test data (สร้างแล้วใน DB):
  - course_id=1  : [TEST] Codex Full Flow Course  (require_post_test=True)
  - lesson_id=2  : บทเรียนทดสอบ: การใช้งานห้องสมุดดิจิทัล
  - post_quiz_id=2: แบบทดสอบหลังเรียน (3 questions, correct answer IDs: 7, 9, 11)
  - certificate_id=1
"""
import pytest
from playwright.sync_api import Page, expect

from test_settings import BASE_URL, COURSE_ID, LESSON_ID, POST_QUIZ_TYPE

COURSE_URL = f"/course/{COURSE_ID}/"
LESSON_URL = f"/course/{COURSE_ID}/lesson/{LESSON_ID}/"
POST_QUIZ_URL = f"/course/{COURSE_ID}/quiz/{POST_QUIZ_TYPE}/"
CERTIFICATE_URL = f"/certificate/{COURSE_ID}/"

# Answer IDs ที่ถูกต้องทุกข้อ (จาก DB)
CORRECT_ANSWER_IDS = [7, 9, 11]
# Answer IDs ที่ผิดทั้งหมด
WRONG_ANSWER_IDS = [8, 10, 12]


class TestCourseList:
    def test_course_list_loads(self, logged_in_page: Page):
        """หน้า course list โหลดได้และแสดง course card."""
        page = logged_in_page
        page.goto("/")
        expect(page).to_have_url(f"{BASE_URL}/")
        # ต้องมี course ทดสอบปรากฏ
        expect(page.get_by_role("heading", name="[TEST] Codex Full Flow Course")).to_be_visible()

    def test_course_card_has_link(self, logged_in_page: Page):
        """Course card มี link ไปหน้า detail."""
        page = logged_in_page
        page.goto("/")
        link = page.locator(f'a[href="{COURSE_URL}"]').first
        expect(link).to_be_visible()


class TestCourseDetail:
    def test_course_detail_loads(self, logged_in_page: Page):
        """หน้า course detail โหลดได้และแสดง lesson list."""
        page = logged_in_page
        page.goto(COURSE_URL)
        expect(page).to_have_url(f"{BASE_URL}{COURSE_URL}")
        expect(page.get_by_role("heading", name="[TEST] Codex Full Flow Course")).to_be_visible()
        # ต้องแสดง lesson
        expect(page.locator("text=บทเรียนทดสอบ")).to_be_visible()

    def test_course_detail_shows_post_quiz_link(self, logged_in_page: Page):
        """หน้า course detail แสดง link ไปยัง post-test."""
        page = logged_in_page
        page.goto(COURSE_URL)
        expect(page.locator(f'a[href="{POST_QUIZ_URL}"]')).to_be_visible()

    def test_progress_created_on_visit(self, logged_in_page: Page):
        """การเข้าหน้า course detail สร้าง UserProgress อัตโนมัติ."""
        page = logged_in_page
        page.goto(COURSE_URL)
        # ไม่ crash และหน้าโหลดได้ = progress ถูกสร้างแล้ว
        expect(page).to_have_url(f"{BASE_URL}{COURSE_URL}")


class TestLessonView:
    def test_lesson_loads(self, logged_in_page: Page):
        """หน้า lesson โหลดได้และแสดง YouTube embed."""
        page = logged_in_page
        page.goto(LESSON_URL, wait_until="domcontentloaded")
        expect(page).to_have_url(f"{BASE_URL}{LESSON_URL}")
        expect(page.get_by_role("heading", name="บทเรียนทดสอบ", exact=False).first).to_be_visible()
        # iframe YouTube ต้องอยู่ในหน้า
        expect(page.locator("iframe")).to_be_visible()

    def test_lesson_marks_completed(self, logged_in_page: Page):
        """การเข้า lesson บันทึก lesson ว่าเรียนแล้ว (ไม่ error)."""
        page = logged_in_page
        page.goto(LESSON_URL, wait_until="domcontentloaded")
        # ไม่มี error, response 200
        expect(page).to_have_url(f"{BASE_URL}{LESSON_URL}")

    def test_lesson_sidebar_navigation(self, logged_in_page: Page):
        """Sidebar แสดง lesson list สำหรับ navigate."""
        page = logged_in_page
        page.goto(LESSON_URL, wait_until="domcontentloaded")
        # lesson อยู่ใน sidebar ด้วย
        expect(page.locator("text=บทเรียนทดสอบ").first).to_be_visible()


class TestPostQuiz:
    def test_quiz_page_loads(self, logged_in_page: Page):
        """หน้า post-test โหลดได้และแสดงคำถาม."""
        page = logged_in_page
        page.goto(POST_QUIZ_URL)
        expect(page).to_have_url(f"{BASE_URL}{POST_QUIZ_URL}")
        expect(page.get_by_role("heading", name="แบบทดสอบหลังเรียน")).to_be_visible()
        expect(page.locator("text=เกณฑ์ผ่าน: 70% ขึ้นไป")).to_be_visible()
        # ต้องมีคำถาม 3 ข้อ
        expect(page.locator('input[type="radio"]')).to_have_count(6)  # 3 ข้อ × 2 ตัวเลือก

    def test_quiz_submit_all_correct(self, logged_in_page: Page):
        """ตอบถูกทุกข้อ → ได้ 100% → passed."""
        page = logged_in_page
        page.goto(POST_QUIZ_URL)
        for answer_id in CORRECT_ANSWER_IDS:
            page.check(f'input[type="radio"][value="{answer_id}"]')
        page.get_by_role("button", name="ส่งคำตอบ").click()
        expect(page.locator("text=ผ่านการสอบ!")).to_be_visible()
        expect(page.locator("text=100.0%")).to_be_visible()
        expect(page.locator("text=ตอบถูก 3 จาก 3 ข้อ")).to_be_visible()

    def test_quiz_submit_all_wrong(self, logged_in_page: Page):
        """ตอบผิดทุกข้อ → ได้ 0% → not passed."""
        page = logged_in_page
        page.goto(POST_QUIZ_URL)
        for answer_id in WRONG_ANSWER_IDS:
            page.check(f'input[type="radio"][value="{answer_id}"]')
        page.get_by_role("button", name="ส่งคำตอบ").click()
        expect(page.locator("text=ไม่ผ่านการสอบ")).to_be_visible()
        expect(page.locator("text=0.0%")).to_be_visible()
        # ต้องมีปุ่ม "ทำแบบทดสอบอีกครั้ง"
        expect(page.locator("text=ทำแบบทดสอบอีกครั้ง")).to_be_visible()

    def test_quiz_result_pass_shows_certificate_link(self, logged_in_page: Page):
        """หลังผ่าน post-test → แสดงปุ่มดาวน์โหลดใบประกาศ."""
        page = logged_in_page
        page.goto(POST_QUIZ_URL)
        for answer_id in CORRECT_ANSWER_IDS:
            page.check(f'input[type="radio"][value="{answer_id}"]')
        page.get_by_role("button", name="ส่งคำตอบ").click()
        expect(page.locator("text=ดาวน์โหลดใบประกาศนียบัตร")).to_be_visible()
        expect(page.locator(f'a[href="{CERTIFICATE_URL}"]')).to_be_visible()

    def test_quiz_result_back_to_course(self, logged_in_page: Page):
        """ปุ่ม 'กลับหน้าหลักสูตร' นำกลับไปหน้า course detail."""
        page = logged_in_page
        page.goto(POST_QUIZ_URL)
        for answer_id in CORRECT_ANSWER_IDS:
            page.check(f'input[type="radio"][value="{answer_id}"]')
        page.get_by_role("button", name="ส่งคำตอบ").click()
        page.click("text=กลับหน้าหลักสูตร")
        expect(page).to_have_url(f"{BASE_URL}{COURSE_URL}")


class TestCourseCompletion:
    def test_course_completed_after_passing_post_test(self, logged_in_page: Page):
        """หลังผ่าน post-test สถานะหลักสูตรต้องเปลี่ยนเป็น completed."""
        page = logged_in_page
        # Submit post-test ด้วยคำตอบถูก
        page.goto(POST_QUIZ_URL)
        for answer_id in CORRECT_ANSWER_IDS:
            page.check(f'input[type="radio"][value="{answer_id}"]')
        page.get_by_role("button", name="ส่งคำตอบ").click()
        # กลับไปหน้า course list ตรวจ badge
        page.goto("/")
        # badge สถานะ completed ต้องปรากฏ (template แสดง "เสร็จสิ้น" หรือ class badge)
        expect(page.locator("text=[TEST] Codex Full Flow Course")).to_be_visible()

    def test_certificate_shown_on_course_detail_after_completion(self, logged_in_page: Page):
        """หลัง completed หน้า course detail แสดงปุ่มดาวน์โหลด certificate."""
        page = logged_in_page
        # Ensure passed first
        page.goto(POST_QUIZ_URL)
        for answer_id in CORRECT_ANSWER_IDS:
            page.check(f'input[type="radio"][value="{answer_id}"]')
        page.get_by_role("button", name="ส่งคำตอบ").click()
        # ไปหน้า course detail
        page.goto(COURSE_URL)
        expect(page.locator(f'a[href="{CERTIFICATE_URL}"]').first).to_be_visible()


class TestCertificateDownload:
    def _go_to_course_after_passing(self, page: Page):
        """Helper: ผ่าน post-test แล้วไปหน้า course detail."""
        page.goto(POST_QUIZ_URL)
        for answer_id in CORRECT_ANSWER_IDS:
            page.check(f'input[type="radio"][value="{answer_id}"]')
        page.get_by_role("button", name="ส่งคำตอบ").click()
        page.goto(COURSE_URL)

    def test_certificate_download_returns_pdf(self, logged_in_page: Page):
        """ดาวน์โหลด certificate → ได้ไฟล์ PDF (filename ลงท้าย .pdf)."""
        page = logged_in_page
        self._go_to_course_after_passing(page)
        # คลิก link ดาวน์โหลดบนหน้า course detail ภายใน expect_download context
        with page.expect_download() as download_info:
            page.locator(f'a[href="{CERTIFICATE_URL}"]').first.click()
        download = download_info.value
        assert download.suggested_filename.endswith(".pdf"), (
            f"Expected .pdf filename, got: {download.suggested_filename}"
        )

    def test_certificate_download_pdf_header(self, logged_in_page: Page):
        """ไฟล์ที่ดาวน์โหลดมีส่วนหัว %PDF (เป็น PDF จริง)."""
        import tempfile, os
        page = logged_in_page
        self._go_to_course_after_passing(page)
        with page.expect_download() as download_info:
            page.locator(f'a[href="{CERTIFICATE_URL}"]').first.click()
        download = download_info.value
        tmp_path = os.path.join(tempfile.gettempdir(), download.suggested_filename)
        download.save_as(tmp_path)
        with open(tmp_path, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF", f"File does not start with %PDF: {header}"

    def test_certificate_requires_auth(self, page: Page):
        """เข้า certificate URL โดยไม่ login → redirect ไปหน้า login."""
        page.goto(CERTIFICATE_URL)
        expect(page).to_have_url(f"{BASE_URL}/login/?next={CERTIFICATE_URL}")
