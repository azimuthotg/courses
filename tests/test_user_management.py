"""
Browser tests: local user creation for admin/staff.
"""
import os
import subprocess

import pytest
from playwright.sync_api import Page, expect

from test_settings import BASE_URL  # noqa: E402


CREATE_USER_URL = "/users/create/"
NEW_LOCAL_USER = "playwright_local_staff"
NEW_LOCAL_PASS = "PlaywrightStaff1234!"


def delete_test_user():
    subprocess.run(
        [
            "./venv/bin/python",
            "manage.py",
            "shell",
            "-c",
            (
                "from django.contrib.auth import get_user_model; "
                f"get_user_model().objects.filter(username='{NEW_LOCAL_USER}').delete()"
            ),
        ],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        check=True,
        capture_output=True,
        text=True,
    )


def run_user_assertion(code):
    completed = subprocess.run(
        ["./venv/bin/python", "manage.py", "shell", "-c", code],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


@pytest.fixture(autouse=True)
def cleanup_local_user():
    delete_test_user()
    yield
    delete_test_user()


class TestLocalUserCreate:
    def test_admin_can_open_create_user_page(self, admin_page: Page):
        """Admin/staff เปิดหน้าเพิ่มผู้ใช้ local ได้."""
        page = admin_page
        page.goto(CREATE_USER_URL)
        expect(page).to_have_url(f"{BASE_URL}{CREATE_USER_URL}")
        expect(page.get_by_role("heading", name="เพิ่มผู้ใช้ Local")).to_be_visible()
        expect(page.get_by_role("button", name="สร้างผู้ใช้")).to_be_visible()

    def test_staff_sidebar_shows_user_management_link(self, admin_page: Page):
        """Staff sidebar แสดงเมนูจัดการผู้ใช้เฉพาะ staff."""
        page = admin_page
        page.goto("/staff/")
        expect(page.get_by_role("link", name="จัดการผู้ใช้")).to_be_visible()

    def test_student_cannot_open_create_user_page(self, student_page: Page):
        """Student API user ต้องเข้า user management ไม่ได้."""
        page = student_page
        page.goto(CREATE_USER_URL)
        expect(page).to_have_url(f"{BASE_URL}{CREATE_USER_URL}")
        expect(page.get_by_role("heading", name="403")).to_be_visible()

    def test_student_does_not_see_create_user_link(self, student_page: Page):
        """Navbar ของนักศึกษาไม่แสดงเมนูเพิ่มผู้ใช้."""
        page = student_page
        page.goto("/")
        expect(page.get_by_role("link", name="จัดการผู้ใช้")).not_to_be_visible()

    def test_admin_can_create_local_staff_user(self, admin_page: Page):
        """Admin สร้าง local staff user ได้ และ user login ได้จริง."""
        page = admin_page
        page.goto(CREATE_USER_URL)
        page.fill('input[name="username"]', NEW_LOCAL_USER)
        page.fill('input[name="first_name"]', "Playwright")
        page.fill('input[name="last_name"]', "Staff")
        page.fill('input[name="email"]', "playwright_staff@example.com")
        page.fill('input[name="department"]', "Library")
        page.check('input[name="is_staff"]')
        page.fill('input[name="password1"]', NEW_LOCAL_PASS)
        page.fill('input[name="password2"]', NEW_LOCAL_PASS)
        page.get_by_role("button", name="สร้างผู้ใช้").click()
        expect(page.locator(f"text=สร้างผู้ใช้ {NEW_LOCAL_USER} สำเร็จ")).to_be_visible()

        run_user_assertion(
            "from django.contrib.auth import get_user_model; "
            f"user = get_user_model().objects.get(username='{NEW_LOCAL_USER}'); "
            "assert user.is_staff is True; "
            "assert user.department == 'Library'; "
            f"assert user.check_password('{NEW_LOCAL_PASS}')"
        )

        page.get_by_role("button", name="ออกจากระบบ").click()
        page.wait_for_url(f"{BASE_URL}/login/")
        page.fill('input[name="username"]', NEW_LOCAL_USER)
        page.fill('input[name="password"]', NEW_LOCAL_PASS)
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/")
        page.goto("/staff/")
        expect(page.get_by_role("link", name="จัดการผู้ใช้")).to_be_visible()

    def test_duplicate_username_shows_validation_error(self, admin_page: Page):
        """Username ซ้ำต้องแสดง validation error และไม่สร้าง user ใหม่."""
        run_user_assertion(
            "from django.contrib.auth import get_user_model; "
            f"get_user_model().objects.create_user(username='{NEW_LOCAL_USER}', password='{NEW_LOCAL_PASS}')"
        )

        page = admin_page
        page.goto(CREATE_USER_URL)
        page.fill('input[name="username"]', NEW_LOCAL_USER)
        page.fill('input[name="password1"]', NEW_LOCAL_PASS)
        page.fill('input[name="password2"]', NEW_LOCAL_PASS)
        page.get_by_role("button", name="สร้างผู้ใช้").click()

        expect(page).to_have_url(f"{BASE_URL}{CREATE_USER_URL}")
        expect(page.locator(".text-red-600").first).to_be_visible()
        run_user_assertion(
            "from django.contrib.auth import get_user_model; "
            f"assert get_user_model().objects.filter(username='{NEW_LOCAL_USER}').count() == 1"
        )

    def test_password_mismatch_shows_validation_error(self, admin_page: Page):
        """Password confirmation ไม่ตรงกันต้องแสดง error."""
        page = admin_page
        page.goto(CREATE_USER_URL)
        page.fill('input[name="username"]', NEW_LOCAL_USER)
        page.fill('input[name="password1"]', NEW_LOCAL_PASS)
        page.fill('input[name="password2"]', "DifferentPass1234!")
        page.get_by_role("button", name="สร้างผู้ใช้").click()

        expect(page).to_have_url(f"{BASE_URL}{CREATE_USER_URL}")
        expect(page.locator(".text-red-600").first).to_be_visible()
        run_user_assertion(
            "from django.contrib.auth import get_user_model; "
            f"assert not get_user_model().objects.filter(username='{NEW_LOCAL_USER}').exists()"
        )
