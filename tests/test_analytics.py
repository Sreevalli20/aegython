from src import analytics_engine, inventory


def _item(name="X", qty=1, price=2.0):
    return {"name": name, "category": "Other", "quantity": qty, "unit": "pcs",
            "purchase_date": "2026-01-01", "price": price}


def test_empty_analytics(db):
    s = analytics_engine.consumption_summary(db_path=db)
    assert s["events"] == 0
    assert s["wasted_value"] == 0
    assert analytics_engine.top_wasted(db_path=db) == []
    assert analytics_engine.category_breakdown(db_path=db) == []
    assert analytics_engine.daily_series(db_path=db) == []
    assert analytics_engine.inventory_value(db_path=db) == 0


def test_consumption_summary(db):
    iid = inventory.add_item(_item(qty=4, price=8), db_path=db)
    inventory.consume_quantity(iid, 2, db_path=db)          # est 4.0
    inventory.mark_event(iid, "wasted", "spoiled", db_path=db)  # remaining 2, est 4.0
    s = analytics_engine.consumption_summary(db_path=db)
    assert s["consumed_events"] == 1 and s["wasted_events"] == 1
    assert s["consumed_qty"] == 2
    assert s["wasted_value"] == 4.0
    assert s["consumed_value"] == 4.0


def test_top_wasted_groups(db):
    for _ in range(2):
        iid = inventory.add_item(_item(name="Milk", qty=1, price=1), db_path=db)
        inventory.mark_event(iid, "wasted", "expired", db_path=db)
    inventory.add_item(_item(name="Bread", qty=1, price=2), db_path=db)
    top = analytics_engine.top_wasted(db_path=db)
    assert top[0]["item_name"] == "Milk"
    assert top[0]["times"] == 2
    assert len(top) == 1  # Bread never wasted


def test_category_breakdown(db):
    iid = inventory.add_item(_item(name="Spinach"), db_path=db)
    inventory.update_item(iid, {"category": "Produce"}, db_path=db)
    inventory.mark_event(iid, "wasted", "bad", db_path=db)
    rows = analytics_engine.category_breakdown(db_path=db)
    assert any(r["category"] == "Produce" and r["wasted_qty"] == 1 for r in rows)


def test_daily_series_groups_by_date(db):
    iid = inventory.add_item(_item(qty=5, price=5), db_path=db)
    inventory.consume_quantity(iid, 1, db_path=db)
    series = analytics_engine.daily_series(db_path=db, days=30)
    assert len(series) == 1
    assert series[0]["consumed"] == 1
    assert series[0]["wasted"] == 0


def test_weekly_series(db):
    iid = inventory.add_item(_item(qty=2, price=2), db_path=db)
    inventory.mark_event(iid, "wasted", "x", db_path=db)
    weekly = analytics_engine.weekly_series(db_path=db)
    assert weekly and weekly[0]["wasted"] == 2
    assert weekly[0]["wasted_value"] == 2.0


def test_inventory_value(db):
    inventory.add_item(_item(qty=1, price=3), db_path=db)
    inventory.add_item(_item(name="Y", qty=1, price=4), db_path=db)
    assert analytics_engine.inventory_value(db_path=db) == 7.0
