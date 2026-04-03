import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage


@pytest.fixture(scope="function")
def login_page(page):
    login_page = LoginPage(page)
    login_page.navigate()
    yield login_page

@pytest.fixture(scope="function")
def inventory_page(page):
    lp = LoginPage(page)
    lp.navigate()
    lp.login("standard_user", "secret_sauce")
    return InventoryPage(page)