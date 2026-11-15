import pytest

from src import validators


def test_valid_name():
    assert validators.validate_name("Chicken Breast") == "Chicken Breast"
    with pytest.raises(ValueError):
        validators.validate_name("")
    with pytest.raises(ValueError):
        validators.validate_name("  ")
    with pytest.raises(ValueError):
        validators.validate_name("bad<script>name")
    with pytest.raises(ValueError):
        validators.validate_name("x" * 100)


def test_quantity():
    assert validators.validate_quantity(5) == 5.0
    assert validators.validate_quantity("2.5") == 2.5
    for bad in (0, -1, "abc", None):
        with pytest.raises(ValueError):
            validators.validate_quantity(bad)


def test_unit():
    assert validators.validate_unit("G") == "g"
    assert validators.validate_unit(None) == "pcs"
    with pytest.raises(ValueError):
        validators.validate_unit("furlong")


def test_category_location():
    assert validators.validate_category("Produce") == "Produce"
    assert validators.validate_category(None) == "Other"
    with pytest.raises(ValueError):
        validators.validate_category("Snacks!!")
    assert validators.validate_location("Fridge") == "Fridge"
    with pytest.raises(ValueError):
        validators.validate_location("Moon")


def test_dates():
    assert validators.validate_iso_date("2026-11-15") == "2026-11-15"
    assert validators.validate_iso_date("15/11/2026") == "2026-11-15"
    assert validators.validate_iso_date(None, allow_none=True) is None
    with pytest.raises(ValueError):
        validators.validate_iso_date(None)
    with pytest.raises(ValueError):
        validators.validate_iso_date("2026-13-45")


def test_price():
    assert validators.validate_price(3.5) == 3.5
    assert validators.validate_price(None) is None
    assert validators.validate_price("") is None
    with pytest.raises(ValueError):
        validators.validate_price(-1)
    with pytest.raises(ValueError):
        validators.validate_price("free")


def test_date_type():
    assert validators.validate_date_type("use_by") == "use_by"
    assert validators.validate_date_type(None) == "user"
    with pytest.raises(ValueError):
        validators.validate_date_type("vibes")
