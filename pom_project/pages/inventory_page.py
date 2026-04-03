from playwright.sync_api import Page

class InventoryPage:
    URL = "https://www.saucedemo.com/inventory.html"

    def __init__(self, page: Page):
        self.page = page
        self.product_items = page.locator(".inventory_item")
        self.cart_icon     = page.locator(".shopping_cart_link")
        self.sort_dropdown = page.locator("[data-test='product-sort-container']")

    def get_product_count(self) -> int:
        return self.product_items.count()

    def get_product_names(self) -> list[str]:
        return self.product_items.locator(".inventory_item_name").all_text_contents()

    def add_first_product_to_cart(self):
        self.product_items.first.locator("button").click()

    def go_to_cart(self):
        self.cart_icon.click()

    def sort_by(self, option: str):
        self.sort_dropdown.select_option(option)