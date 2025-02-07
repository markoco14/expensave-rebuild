import re

time_periods = ["1-2","3-4","5-6","7-8","9-10","11-12"]

prize_amounts = {
    "special": 10000000,
    "grand": 2000000,
    "eight": 200000,
    "seven": 40000,
    "six": 10000,
    "five": 4000,
    "four": 1000,
    "three": 200
}

winning_numbers = {
    "2024": {
        "9-10": {
            "special": "28630525",
            "grand": "90028580",
            "first": ["27435934", "39666605", "02550031"]
        },
        "11-12": {
            "special": "13965913",
            "grand": "29892710",
            "first": ["26649927", "59565539", "11460822"]
        }
    }
}

def get_digits_from_receipt_id(receipt_id: str) -> str:
    "Removes the prefix from the receipt_id and returns the digits"
    digit_regex = r"\d+"
    digits = re.search(digit_regex, receipt_id)
    return digits.group()


def check_all_digits_match(receipt_number: str, winning_number: str) -> bool:
    return receipt_number == winning_number


def get_last_seven_digits(receipt_number: str) -> str:
    return receipt_number[1:]


def get_last_six_digits(receipt_number: str) -> str:
    return receipt_number[2:]


def get_last_five_digits(receipt_number: str) -> str:
    return receipt_number[3:]


def get_last_four_digits(receipt_number: str) -> str:
    return receipt_number[4:]


def get_last_three_digits(receipt_number: str) -> str:
    return receipt_number[5:]