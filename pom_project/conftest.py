import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage

# session scope — one browser for the entire run
@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

# function scope — fresh page per test, no shared state
@pytest.fixture(scope="session")
def page(browser_instance):
    page = browser_instance.new_page()
    yield page
    page.close()

@pytest.fixture(scope="function")
def login_page(page):
    lp = LoginPage(page)
    lp.navigate()
    return lp

@pytest.fixture(scope="function")
def inventory_page(page):
    lp = LoginPage(page)
    lp.navigate()
    lp.login("standard_user", "secret_sauce")
    return InventoryPage(page)