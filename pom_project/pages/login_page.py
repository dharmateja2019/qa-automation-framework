from playwright.sync_api import Page

class LoginPage:
    URL = "https://www.saucedemo.com"

    def __init__(self, page: Page):
        self.page = page

        # locators — all in one place
        self.username_input = page.locator("#user-name")
        self.password_input = page.locator("#password")
        self.login_button   = page.locator("#login-button")
        self.error_message  = page.locator("[data-test='error']")

    def navigate(self):
        self.page.goto(self.URL)

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def get_error_message(self) -> str:
        return self.error_message.text_content() # type: ignore