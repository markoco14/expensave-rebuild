"""Configuration for the application."""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

env_path = Path(".") / ".env"

load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Settings for the application."""

    # Database

    ENVIRONMENT: str = os.environ.get('ENVIRONMENT')


    if ENVIRONMENT == 'dev':
        SLEEP_TIME: int = 0
        DB_USER: str = os.environ.get('DEV_DB_USER')
        DB_PASSWORD: str = os.environ.get('DEV_DB_PASSWORD')
        DB_HOST: str = os.environ.get('DEV_DB_HOST')
        DB_PORT: str = os.environ.get('DEV_DB_PORT')
        DB_NAME: str = os.environ.get('DEV_DB_NAME')
        DATABASE_URL: str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        DB_USER: str = os.environ.get('DB_USER')
        DB_PASSWORD: str = os.environ.get('DB_PASSWORD')
        DB_HOST: str = os.environ.get('DB_HOST')
        DB_PORT: str = os.environ.get('DB_PORT')
        DB_NAME: str = os.environ.get('DB_NAME')
        DATABASE_URL: str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    AWS_ACCESS_KEY_ID: str = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY: str = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION: str = os.environ.get('AWS_DEFAULT_REGION')
    AWS_PROJECT_BUCKET: str = os.environ.get('AWS_PROJECT_BUCKET')



# or from config import get_settings -> var = get_settings()
def get_settings() -> Settings:
    """Get the settings to use within application."""
    return Settings()
