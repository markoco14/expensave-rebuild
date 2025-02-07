import pytest
from app.services import winnings_service

@pytest.mark.parametrize("receipt_id, expected", [
    ("12345678", "12345678"),
    ("87654321", "87654321"),
    ("GL-12345678", "12345678"),
    ("KA87654321", "87654321"),
    ("KA:87654321", "87654321"),
    ("KA--87654321", "87654321")
])
def test_get_digits_from_receipt_id(receipt_id, expected):
    assert winnings_service.get_digits_from_receipt_id(receipt_id) == expected

@pytest.mark.parametrize("receipt_number, winning_number, expected", [
    ("12345678", "12345678", True),
    ("87654321", "87654321", True),
    ("18273645", "54637281", False),
    ("54637281", "18273645", False)
])
def test_check_all_digits_match(receipt_number, winning_number, expected):
    assert winnings_service.check_all_digits_match(receipt_number, winning_number) == expected

@pytest.mark.parametrize("receipt_number, expected", [
    ("12345678", "2345678"),
    ("87654321", "7654321")
])
def test_get_last_seven_digits(receipt_number, expected):
    assert winnings_service.get_last_seven_digits(receipt_number) == expected


@pytest.mark.parametrize("receipt_number, expected", [
    ("12345678", "345678"),
    ("87654321", "654321")
])
def test_get_last_six_digits(receipt_number, expected):
    assert winnings_service.get_last_six_digits(receipt_number) == expected


@pytest.mark.parametrize("receipt_number, expected", [
    ("12345678", "45678"),
    ("87654321", "54321")
])
def test_get_last_five_digits(receipt_number, expected):
    assert winnings_service.get_last_five_digits(receipt_number) == expected


@pytest.mark.parametrize("receipt_number, expected", [
    ("12345678", "5678"),
    ("87654321", "4321")
])
def test_get_last_four_digits(receipt_number, expected):
    assert winnings_service.get_last_four_digits(receipt_number) == expected


@pytest.mark.parametrize("receipt_number, expected", [
    ("12345678", "678"),
    ("87654321", "321")
])
def test_get_last_three_digits(receipt_number, expected):
    assert winnings_service.get_last_three_digits(receipt_number) == expected