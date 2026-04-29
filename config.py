import os
import warnings


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or f"sqlite:///{os.path.join(BASE_DIR, 'my_dark_sky.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    CACHE_TTL_SECONDS = 300
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dark-sky-dev-secret-key"

    @classmethod
    def check_secret_key(cls):
        if cls.SECRET_KEY == "dark-sky-dev-secret-key":
            warnings.warn(
                "SECRET_KEY is using the hardcoded development fallback. "
                "Set the SECRET_KEY environment variable in production.",
                RuntimeWarning,
                stacklevel=3,
            )
