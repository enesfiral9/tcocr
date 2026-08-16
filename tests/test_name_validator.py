from app.validators.name_validator import validate_name


def test_turkish_names_are_valid():
    assert validate_name("ÇAĞRI ŞEN")
    assert validate_name("IŞIL")


def test_digit_is_suspicious():
    assert not validate_name("ENE5")
