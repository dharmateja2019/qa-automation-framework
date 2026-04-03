from test_data.user_factory import UserFactory

def test_valid_login(login_page, page):
    user = UserFactory.standard()
    login_page.login(user.username, user.password)
    assert page.url == "https://www.saucedemo.com/inventory.html"

def test_invalid_password(login_page):
    user = UserFactory.build(password="wrong_password")
    login_page.login(user.username, user.password)
    assert "do not match" in login_page.get_error_message()

def test_empty_username(login_page):
    user = UserFactory.build(username="")
    login_page.login(user.username, user.password)
    assert "Username is required" in login_page.get_error_message()

def test_locked_user(login_page):
    user = UserFactory.locked()
    login_page.login(user.username, user.password)
    assert "locked out" in login_page.get_error_message()