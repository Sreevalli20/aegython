from datetime import date, timedelta

from src import expiry_engine, inventory


def _item(days, **kw):
    expiry = (date.today() + timedelta(days=days)).isoformat()
    base = {
        "id": 1, "name": "Test", "category": "Other", "quantity": 1,
        "unit": "pcs", "location": "Pantry",
        "purchase_date": date.today().isoformat(),
        "expiry_date": expiry, "date_type": "best_before", "status": "active",
    }
    base.update(kw)
    return base


def test_expired_classification():
    a = expiry_engine.classify_item(_item(-2))
    assert a["urgency"] == "expired"
    assert a["days_remaining"] == -2
    assert len(a["reasons"]) >= 1
    assert "action" in a and a["action"]


def test_use_by_expired_defers_to_label():
    a = expiry_engine.classify_item(_item(-1, date_type="use_by"))
    assert a["urgency"] == "expired"
    assert any("label" in r.lower() or "use-by" in r.lower() for r in a["reasons"])


def test_critical_one_day():
    a = expiry_engine.classify_item(_item(1))
    assert a["urgency"] == "critical"
    assert "Use today" in a["action"] or "use today" in a["action"].lower()


def test_high_three_days():
    assert expiry_engine.classify_item(_item(3))["urgency"] == "high"


def test_medium_seven_days():
    assert expiry_engine.classify_item(_item(7))["urgency"] == "medium"


def test_ok_fresh():
    a = expiry_engine.classify_item(_item(30))
    assert a["urgency"] == "ok"
    assert a["action"] and "no urgent action" in a["action"].lower()


def test_no_expiry_date():
    a = expiry_engine.classify_item(_item(30, expiry_date=None))
    assert a["urgency"] == "none"
    assert a["days_remaining"] is None


def test_invalid_date_string():
    a = expiry_engine.classify_item(_item(30, expiry_date="garbage"))
    assert a["urgency"] == "none"


def test_assess_inventory_sorted_by_urgency():
    items = [_item(30, id=1, name="Fresh"), _item(-1, id=2, name="Old"),
             _item(2, id=3, name="Soon")]
    assessed = expiry_engine.assess_inventory(items=items)
    assert assessed[0]["name"] == "Old"
    assert assessed[-1]["name"] == "Fresh"


def test_summary_counts():
    items = [_item(-1), _item(1), _item(2), _item(6), _item(30), _item(30, id=9, expiry_date=None)]
    s = expiry_engine.summary(expiry_engine.assess_inventory(items=items))
    assert s["total"] == 6
    assert s["expired"] == 1 and s["critical"] == 1 and s["high"] == 1
    assert s["medium"] == 1 and s["ok"] == 1 and s["none"] == 1
    assert s["needs_attention"] == 3


def test_days_remaining_helper():
    today = date.today()
    assert expiry_engine.days_remaining(today.isoformat(), today) == 0
    assert expiry_engine.days_remaining(None) is None
