import pytest
from app.data import winnings


@pytest.mark.parametrize("receipt_number, winning_number, expected", [
    ("12345678", "12345678", True),
    ("87654321", "87654321", True),
    ("18273645", "54637281", False),
    ("54637281", "18273645", False)
])
def test_check_all_digits_match(receipt_number, winning_number, expected):
    assert winnings.check_all_digits_match(receipt_number, winning_number) == expected

@pytest.mark.parametrize("receipt_number, expected", [
    ("12345678", "2345678"),
    ("87654321", "7654321")
])
def test_get_last_seven_digits(receipt_number, expected):
    assert winnings.get_last_seven_digits(receipt_number) == expected


@pytest.mark.parametrize("receipt_number, expected", [
    ("12345678", "345678"),
    ("87654321", "654321")
])
def test_get_last_six_digits(receipt_number, expected):
    assert winnings.get_last_six_digits(receipt_number) == expected


@pytest.mark.parametrize("receipt_number, expected", [
    ("12345678", "45678"),
    ("87654321", "54321")
])
def test_get_last_five_digits(receipt_number, expected):
    assert winnings.get_last_five_digits(receipt_number) == expected


@pytest.mark.parametrize("receipt_number, expected", [
    ("12345678", "5678"),
    ("87654321", "4321")
])
def test_get_last_four_digits(receipt_number, expected):
    assert winnings.get_last_four_digits(receipt_number) == expected


@pytest.mark.parametrize("receipt_number, expected", [
    ("12345678", "678"),
    ("87654321", "321")
])
def test_get_last_three_digits(receipt_number, expected):
    assert winnings.get_last_three_digits(receipt_number) == expected