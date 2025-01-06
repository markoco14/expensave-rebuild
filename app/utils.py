""" Utility functions to make things easier"""

def get_original_storage_string(user_id: int, environment: str, upload_time: int):
    if environment == "dev":
        return f"dev/receipts/original/{user_id}-{upload_time}.png"
    
    return f"prod/receipts/original/{user_id}-{upload_time}.png"


def get_thumbnail_storage_string(original_storage_string: str):
    return original_storage_string.replace("original", "thumbnail").replace("png", "jpg")
