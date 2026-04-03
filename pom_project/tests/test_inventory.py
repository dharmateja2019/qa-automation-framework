# from pages.login_page import LoginPage
# from pages.inventory_page import InventoryPage
import pytest

def test_inventory_loads_six_products(inventory_page,page):
    
    assert inventory_page.get_product_count() == 6

def test_product_names_are_not_empty(inventory_page,page):
    
    names = inventory_page.get_product_names()
    assert len(names) == 6
    assert all(len(name) > 0 for name in names)

def test_add_to_cart_updates_badge(inventory_page,page):
    inventory_page.add_first_product_to_cart()

    cart_badge = page.locator(".shopping_cart_badge")
    assert cart_badge.text_content() == "1"