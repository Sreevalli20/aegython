import pytest

from src import inventory
from src.inventory import InventoryError


def _data(**kw):
    base = {
        "name": "Milk", "category": "Dairy & Eggs", "quantity": 1, "unit": "l",
        "purchase_date": "2026-01-01", "expiry_date": "2026-02-01",
        "date_type": "use_by", "location": "Fridge", "price": 1.5,
        "min_threshold": 0,
    }
    base.update(kw)
    return base


def test_add_and_get(db):
    iid = inventory.add_item(_data(), db_path=db)
    item = inventory.get_item(iid, db_path=db)
    assert item["name"] == "Milk"
    assert item["status"] == "active"
    assert item["quantity"] == 1.0


def test_add_invalid_quantity(db):
    with pytest.raises(ValueError):
        inventory.add_item(_data(quantity=-3), db_path=db)
    with pytest.raises(ValueError):
        inventory.add_item(_data(quantity="abc"), db_path=db)
    with pytest.raises(ValueError):
        inventory.add_item(_data(quantity=0), db_path=db)


def test_add_invalid_dates(db):
    with pytest.raises(ValueError):
        inventory.add_item(_data(expiry_date="not-a-date"), db_path=db)
    with pytest.raises(InventoryError):
        inventory.add_item(_data(expiry_date="2025-12-01",
                                  purchase_date="2026-01-01"), db_path=db)


def test_update_item(db):
    iid = inventory.add_item(_data(), db_path=db)
    inventory.update_item(iid, {"quantity": 2, "location": "Freezer"}, db_path=db)
    item = inventory.get_item(iid, db_path=db)
    assert item["quantity"] == 2.0
    assert item["location"] == "Freezer"
    assert item["name"] == "Milk"  # untouched field preserved


def test_update_missing_item(db):
    with pytest.raises(InventoryError):
        inventory.update_item(9999, {"quantity": 1}, db_path=db)


def test_delete_item(db):
    iid = inventory.add_item(_data(), db_path=db)
    assert inventory.delete_item(iid, db_path=db) is True
    assert inventory.get_item(iid, db_path=db) is None
    assert inventory.delete_item(iid, db_path=db) is False


def test_partial_consume(db):
    iid = inventory.add_item(_data(quantity=4, price=8.0), db_path=db)
    res = inventory.consume_quantity(iid, 1.5, db_path=db)
    assert res["remaining"] == 2.5
    item = inventory.get_item(iid, db_path=db)
    assert item["quantity"] == 2.5
    assert item["status"] == "active"
    # est value = unit price (8/4=2) * 1.5
    assert res["est_value"] == pytest.approx(3.0)


def test_consume_too_much(db):
    iid = inventory.add_item(_data(quantity=1), db_path=db)
    with pytest.raises(InventoryError):
        inventory.consume_quantity(iid, 5, db_path=db)


def test_consume_all_marks_consumed(db):
    iid = inventory.add_item(_data(quantity=1), db_path=db)
    inventory.consume_quantity(iid, 1, db_path=db)
    assert inventory.get_item(iid, db_path=db)["status"] == "consumed"


def test_mark_wasted_and_discarded(db):
    iid = inventory.add_item(_data(quantity=2, price=4), db_path=db)
    res = inventory.mark_event(iid, "wasted", "went bad", db_path=db)
    assert res["est_value"] == pytest.approx(4.0)
    item = inventory.get_item(iid, db_path=db)
    assert item["status"] == "wasted"
    with pytest.raises(InventoryError):
        inventory.mark_event(iid, "consumed", db_path=db)  # not active anymore


def test_consumption_history(db):
    iid = inventory.add_item(_data(name="Spinach"), db_path=db)
    inventory.mark_event(iid, "wasted", "expired", db_path=db)
    log = inventory.recent_activity(db_path=db)
    assert len(log) == 1
    assert log[0]["item_name"] == "Spinach"
    assert log[0]["event"] == "wasted"
    assert log[0]["est_value"] == pytest.approx(1.5)


def test_list_filters(db):
    inventory.add_item(_data(name="Milk"), db_path=db)
    inventory.add_item(_data(name="Bread", category="Bakery", location="Pantry"), db_path=db)
    assert len(inventory.list_items(db_path=db)) == 2
    assert len(inventory.list_items(db_path=db, category="Bakery")) == 1
    assert len(inventory.list_items(db_path=db, search="mil")) == 1
    assert len(inventory.list_items(db_path=db, location="Pantry")) == 1
    assert len(inventory.list_items(db_path=db, status="wasted")) == 0


def test_empty_dataset(db):
    assert inventory.list_items(db_path=db) == []
    assert inventory.recent_activity(db_path=db) == []
