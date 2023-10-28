import os
from dotenv import find_dotenv, load_dotenv

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


class Config:
    SECRET_KEY = os.environ.get("APP_SECRET_KEY")
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")

    # Auth0 configurations
    AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
    ALGORITHMS = os.environ.get("ALGORITHMS")
    API_AUDIENCE = os.environ.get("API_AUDIENCE")

    # Database configurations
    DB_NAME = os.environ.get("DB_NAME")
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = "sqlite:///{}".format(os.path.join(PROJECT_DIR, DB_NAME))
