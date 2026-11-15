import pytest

from src import shopping_engine
from src.shopping_engine import ShoppingError


def test_add_and_list(db):
    shopping_engine.add_item("Olive Oil", quantity=2, unit="l", price_estimate=6,
                             db_path=db)
    items = shopping_engine.list_items(db_path=db)
    assert len(items) == 1
    assert items[0]["name"] == "Olive Oil"


def test_duplicate_name_rejected(db):
    shopping_engine.add_item("Milk", unit="l", db_path=db)
    with pytest.raises(ShoppingError):
        shopping_engine.add_item("Milk", unit="l", db_path=db)


def test_mark_and_clear_purchased(db):
    iid = shopping_engine.add_item("Eggs", db_path=db)
    shopping_engine.add_item("Bread", db_path=db)
    shopping_engine.mark_purchased(iid, db_path=db)
    pending = shopping_engine.list_items(db_path=db)
    assert len(pending) == 1 and pending[0]["name"] == "Bread"
    all_items = shopping_engine.list_items(include_purchased=True, db_path=db)
    assert len(all_items) == 2
    n = shopping_engine.clear_purchased(db_path=db)
    assert n == 1
    assert len(shopping_engine.list_items(include_purchased=True, db_path=db)) == 1


def test_remove_item(db):
    iid = shopping_engine.add_item("Sugar", db_path=db)
    assert shopping_engine.remove_item(iid, db_path=db) is True
    assert shopping_engine.list_items(db_path=db) == []


def test_pantry_match_detects_stock(db):
    from src import inventory
    inventory.add_item({"name": "Milk", "category": "Dairy & Eggs", "quantity": 2,
                        "unit": "l", "purchase_date": "2026-01-01"}, db_path=db)
    m = shopping_engine.pantry_match("Milk", db_path=db)
    assert m is not None
    assert m["total_quantity"] == 2
    assert shopping_engine.pantry_match("Caviar", db_path=db) is None


def test_restock_suggestions(db):
    from src import inventory
    inventory.add_item({"name": "Eggs", "category": "Dairy & Eggs", "quantity": 1,
                        "unit": "pcs", "purchase_date": "2026-01-01",
                        "min_threshold": 4}, db_path=db)
    inventory.add_item({"name": "Rice", "category": "Pantry", "quantity": 5,
                        "unit": "kg", "purchase_date": "2026-01-01",
                        "min_threshold": 1}, db_path=db)
    sugg = shopping_engine.restock_suggestions(db_path=db)
    assert len(sugg) == 1
    assert sugg[0]["item"]["name"] == "Eggs"


def test_estimate_total(db):
    shopping_engine.add_item("A", price_estimate=2.5, db_path=db)
    shopping_engine.add_item("B", price_estimate=1.0, db_path=db)
    assert shopping_engine.estimate_total(db_path=db) == 3.5


def test_duplicate_purchase_prevention_covers_purchased_and_pending(db):
    iid = shopping_engine.add_item("Milk", unit="l", db_path=db)
    shopping_engine.mark_purchased(iid, db_path=db)
    with pytest.raises(ShoppingError):
        shopping_engine.add_item("Milk", unit="l", db_path=db)
    assert shopping_engine.pantry_match("Milk", db_path=db) is None
