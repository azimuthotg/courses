"""
Pytest / Playwright configuration for Micro-LMS browser tests.
"""
import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from test_settings import ADMIN_PASS, ADMIN_USER, BASE_URL, STUDENT_PASS, STUDENT_USER, TEST_USER, TEST_PASS


@pytest.fixture
def page(browser: Browser):
    """Fresh browser page for each test."""
    context: BrowserContext = browser.new_context(base_url=BASE_URL)
    pg: Page = context.new_page()
    yield pg
    context.close()


@pytest.fixture
def logged_in_page(page: Page):
    """Page already logged in as codex_test."""
    page.goto("/login/")
    page.fill('input[name="username"]', TEST_USER)
    page.fill('input[name="password"]', TEST_PASS)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/")
    return page


@pytest.fixture
def admin_page(page: Page):
    """Page already logged in as local admin."""
    page.goto("/login/")
    page.fill('input[name="username"]', ADMIN_USER)
    page.fill('input[name="password"]', ADMIN_PASS)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/")
    return page


@pytest.fixture
def student_page(page: Page):
    """Page already logged in as an NPU student."""
    page.goto("/login/")
    page.fill('input[name="username"]', STUDENT_USER)
    page.fill('input[name="password"]', STUDENT_PASS)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/")
    return page
