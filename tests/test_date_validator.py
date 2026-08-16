from app.validators.date_validator import normalize_date, validate_date


def test_normalizes_supported_separators():
    for value in ("01/02/1990", "01-02-1990", "01 02 1990"):
        assert normalize_date(value) == "01.02.1990"


def test_rejects_impossible_date():
    assert not validate_date(normalize_date("32.14.1980"))


def test_accepts_valid_date():
    assert validate_date("01.02.1990")
