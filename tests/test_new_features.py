"""
Browser tests: Phase B/C new features.
  - Course Search (/?q=)
  - User Profile (/profile/)
  - Learner Transcript (/transcript/)
  - Bulk User Import (/staff/users/import/)
"""
import io
import os
import subprocess

import pytest
from playwright.sync_api import Page, expect

from test_settings import BASE_URL, COURSE_ID

IMPORT_USER = "bulk_import_pw_test"


def run_django(code):
    completed = subprocess.run(
        ["./venv/bin/python", "manage.py", "shell", "-c", code],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


class TestCourseSearch:
    def test_search_returns_results(self, logged_in_page: Page):
        page = logged_in_page
        page.goto("/?q=Full+Flow")
        expect(page.get_by_role("heading", name="[TEST] Codex Full Flow Course")).to_be_visible()

    def test_search_no_results_shows_message(self, logged_in_page: Page):
        page = logged_in_page
        page.goto("/?q=xyzzy_notfound_12345")
        expect(page.locator('text=ไม่พบวิชา')).to_be_visible()

    def test_search_preserves_query_in_input(self, logged_in_page: Page):
        page = logged_in_page
        page.goto("/?q=Full+Flow")
        search_input = page.locator('input[name="q"]')
        expect(search_input).to_have_value("Full Flow")


class TestUserProfile:
    def test_profile_page_loads(self, logged_in_page: Page):
        page = logged_in_page
        page.goto("/profile/")
        expect(page).to_have_url(f"{BASE_URL}/profile/")

    def test_profile_requires_auth(self, page: Page):
        page.goto("/profile/")
        expect(page).to_have_url(f"{BASE_URL}/login/?next=/profile/")

    def test_profile_shows_username(self, logged_in_page: Page):
        page = logged_in_page
        page.goto("/profile/")
        from test_settings import TEST_USER
        expect(page.locator(f"text={TEST_USER}")).to_be_visible()

    def test_profile_has_transcript_link(self, logged_in_page: Page):
        page = logged_in_page
        page.goto("/profile/")
        transcript_link = page.locator('a[href="/transcript/"]')
        expect(transcript_link).to_be_visible()


class TestLearnerTranscript:
    def test_transcript_returns_pdf(self, logged_in_page: Page):
        page = logged_in_page
        page.goto("/profile/")
        with page.expect_download() as download_info:
            page.locator('a[href="/transcript/"]').click()
        download = download_info.value
        assert download.suggested_filename.endswith(".pdf")

    def test_transcript_requires_auth(self, page: Page):
        page.goto("/transcript/")
        expect(page).to_have_url(f"{BASE_URL}/login/?next=/transcript/")


class TestBulkUserImport:
    def test_import_page_accessible_by_staff(self, admin_page: Page):
        page = admin_page
        page.goto("/staff/users/import/")
        expect(page).to_have_url(f"{BASE_URL}/staff/users/import/")
        expect(page.locator('input[type="file"]')).to_be_visible()

    def test_import_page_blocked_for_student(self, student_page: Page):
        page = student_page
        page.goto("/staff/users/import/")
        expect(page.get_by_role("heading", name="403")).to_be_visible()

    def test_import_creates_users_from_csv(self, admin_page: Page):
        run_django(
            f"from django.contrib.auth import get_user_model; "
            f"get_user_model().objects.filter(username='{IMPORT_USER}').delete()"
        )
        page = admin_page
        page.goto("/staff/users/import/")

        csv_content = (
            f"username,first_name,last_name,email,department,is_staff,line_user_id,password\n"
            f"{IMPORT_USER},Bulk,Import,bulk@test.com,IT,False,,BulkPW1234!\n"
        )
        csv_bytes = csv_content.encode("utf-8-sig")
        page.set_input_files(
            'input[type="file"]',
            files=[{"name": "import.csv", "mimeType": "text/csv", "buffer": csv_bytes}],
        )
        page.get_by_role("button", name="นำเข้า").click()

        expect(page.locator("text=สร้างสำเร็จ 1 คน")).to_be_visible()

        run_django(
            f"from django.contrib.auth import get_user_model; "
            f"get_user_model().objects.filter(username='{IMPORT_USER}').delete()"
        )

    def test_import_skips_duplicate_username(self, admin_page: Page):
        page = admin_page
        page.goto("/staff/users/import/")

        csv_content = (
            "username,first_name,last_name,email,department,is_staff,line_user_id,password\n"
            "admin,Admin,Dup,dup@test.com,IT,False,,DupPW1234!\n"
        )
        csv_bytes = csv_content.encode("utf-8-sig")
        page.set_input_files(
            'input[type="file"]',
            files=[{"name": "dup.csv", "mimeType": "text/csv", "buffer": csv_bytes}],
        )
        page.get_by_role("button", name="นำเข้า").click()

        expect(page.locator("text=ข้ามซ้ำ 1 คน")).to_be_visible()
