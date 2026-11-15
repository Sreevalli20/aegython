from src import inventory, simulator


def test_simulation_inputs_change_results(db):
    inventory.add_item({"name": "Eggs", "quantity": 6, "unit": "pcs",
                        "price": 3, "purchase_date": "2026-01-01"}, db_path=db)
    base = simulator.simulate(db_path=db, extra_purchases=[],
                              daily_extra_consumption=0.0, waste_rate_today=0.0)
    changed = simulator.simulate(
        db_path=db,
        extra_purchases=[{"name": "Spinach", "quantity": 1, "unit": "bunch",
                          "shelf_days": 1, "price": 2}],
        daily_extra_consumption=0.5,
        waste_rate_today=1.0,
    )
    assert changed["scenario"]["active_items"] == base["scenario"]["active_items"] + 1
    assert changed["scenario"]["estimated_daily_utilization_pct"] != 0
    assert changed["scenario"]["estimated_waste_value_at_risk"] > base["scenario"]["estimated_waste_value_at_risk"]
    assert changed["is_estimate"] is True
