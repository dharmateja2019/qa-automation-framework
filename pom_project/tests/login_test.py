import pytest
# from pages.login_page import LoginPage

def test_valid_login(login_page, page):
    login_page.login("standard_user", "secret_sauce")
    assert page.url == "https://www.saucedemo.com/inventory.html"

def test_invalid_password(login_page):
    login_page.login("standard_user", "wrong_password")
    assert "do not match" in login_page.get_error_message()

def test_empty_username(login_page):
    login_page.login("", "secret_sauce")
    assert "Username is required" in login_page.get_error_message()

def test_locked_user(login_page):
    login_page.login("locked_out_user", "secret_sauce")
    assert "locked out" in login_page.get_error_message()