import pytest
from app.validators.tc_validator import validate_tc_number


@pytest.mark.parametrize("value", ["", "1234567890", "123456789012", "01234567890", "12345A78901", "10000000140"])
def test_invalid_tc_numbers(value):
    assert not validate_tc_number(value)


def test_synthetic_valid_tc_number():
    # Algorithmically generated test value; it is not sourced from a person.
    assert validate_tc_number("10000000146")
