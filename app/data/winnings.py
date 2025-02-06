time_periods = ["1-2","3-4","5-6","7-8","9-10","11-12"]

winning_numbers = {
    "2024": {
        "11-12": {
            "special": "13965913",
            "grand": "29892710",
            "first": ["26649927", "59565539", "11460822"]
        }
    }
}

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