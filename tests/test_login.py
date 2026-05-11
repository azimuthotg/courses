"""
Browser tests: Login / Logout flow.
"""
import pytest
from playwright.sync_api import Page, expect

from test_settings import BASE_URL, TEST_USER, TEST_PASS


class TestLoginPage:
    def test_login_page_loads(self, page: Page):
        """หน้า login โหลดได้และแสดง elements ครบ."""
        page.goto("/login/")
        expect(page).to_have_title("เข้าสู่ระบบ — NPU Library LMS")
        expect(page.locator('input[name="username"]')).to_be_visible()
        expect(page.locator('input[name="password"]')).to_be_visible()
        expect(page.locator('button[type="submit"]')).to_be_visible()

    def test_login_success(self, page: Page):
        """Login ด้วย credentials ถูกต้อง → redirect ไปหน้า course list."""
        page.goto("/login/")
        page.fill('input[name="username"]', TEST_USER)
        page.fill('input[name="password"]', TEST_PASS)
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/")
        expect(page).to_have_url(f"{BASE_URL}/")

    def test_login_wrong_password(self, page: Page):
        """Login ด้วยรหัสผ่านผิด → แสดง error message."""
        page.goto("/login/")
        page.fill('input[name="username"]', TEST_USER)
        page.fill('input[name="password"]', "WrongPassword!")
        page.click('button[type="submit"]')
        # ยังอยู่หน้า login
        expect(page).to_have_url(f"{BASE_URL}/login/")
        expect(page.locator("text=ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")).to_be_visible()

    def test_redirect_unauthenticated(self, page: Page):
        """เข้าหน้า course list โดยไม่ login → redirect ไปหน้า login."""
        page.goto("/")
        expect(page).to_have_url(f"{BASE_URL}/login/?next=/")

    def test_logout(self, logged_in_page: Page):
        """Logout → user ถูก logout จริง (ต้อง login ใหม่เพื่อเข้าหน้า protected).

        Django 6 ต้องการ POST สำหรับ logout จึง submit form ผ่าน JavaScript
        เพราะ navbar ใช้ <a> (GET) ซึ่งยังไม่ล้าง session
        """
        page = logged_in_page
        # POST ไปยัง /logout/ พร้อม CSRF token ผ่าน JS form submit
        page.evaluate("""
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/logout/';
            const csrf = document.createElement('input');
            csrf.type = 'hidden';
            csrf.name = 'csrfmiddlewaretoken';
            csrf.value = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
            form.appendChild(csrf);
            document.body.appendChild(form);
            form.submit();
        """)
        page.wait_for_load_state()
        # ตรวจว่า session หมดแล้ว
        page.goto("/")
        expect(page).to_have_url(f"{BASE_URL}/login/?next=/")
