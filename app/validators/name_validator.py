import re

NAME_PATTERN = re.compile(r"^[A-Za-zÇĞİIÖŞÜçğıöşü]+(?:[ '\-][A-Za-zÇĞİIÖŞÜçğıöşü]+)*$")


def validate_name(value: str) -> bool:
    return bool(value and NAME_PATTERN.fullmatch(value))
