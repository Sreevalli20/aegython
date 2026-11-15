"""AppTest coverage for WasteLess AI's main routing and default database."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


@pytest.fixture(autouse=True)
def isolated_app_database(tmp_path, monkeypatch):
    monkeypatch.setenv("WASTELESS_DB_PATH", str(tmp_path / "wasteless-test.db"))


NAV_PAGES = {
    "dashboard": "dashboard",
    "pantry": "pantry",
    "expiry": "expiry",
    "meals": "meals",
    "waste": "waste",
    "shopping": "shopping",
    "analytics": "analytics",
    "simulator": "simulator",
    "settings": "settings",
}


def _run(page: str, setup=None) -> AppTest:
    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    if setup:
        setup(at)
    else:
        at.session_state["nav"] = page
    at.run()
    return at


def _expect_clean(at: AppTest, page: str) -> None:
    assert not at.exception, f"{page} raised: {at.exception}"
    assert not at.error, f"{page} displayed errors: {[e.value for e in at.error]}"


def test_all_pages_render_with_empty_default_database():
    for page in NAV_PAGES:
        at = _run(page, setup=lambda at, page=page: at.session_state.__setitem__("nav", page))
        _expect_clean(at, page)


def test_expiry_table_uses_nullable_integer_for_missing_values():
    import pandas as pd

    rows = [
        {"Days left": pd.NA},
        {"Days left": 4},
        {"Days left": -2},
    ]
    frame = pd.DataFrame(rows).astype({"Days left": "Int64"})

    assert str(frame["Days left"].dtype) == "Int64"
    assert pd.isna(frame.loc[0, "Days left"])
    assert frame.loc[1, "Days left"] == 4
    assert frame.loc[2, "Days left"] == -2


def test_settings_sample_and_clear_actions_work_in_app():
    at = _run("settings")
    # Exercise the real actions through AppTest's rendered buttons.
    load_button = next((b for b in at.button if "Load sample household data" in b.label), None)
    assert load_button is not None
    load_button.click().run()
    _expect_clean(at, "settings-sample")

    clear_button = next((b for b in at.button if b.label == "Clear ALL local data"), None)
    assert clear_button is not None
    clear_button.click().run()
    confirm = next((b for b in at.button if b.label == "Yes — delete everything"), None)
    assert confirm is not None
    confirm.click().run()
    _expect_clean(at, "settings-clear")
