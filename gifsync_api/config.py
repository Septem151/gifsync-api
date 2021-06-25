"""
Configuration of the GifSync API, based on .env.* files, which are then injected
into the app's config.
"""
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
import os
import secrets
import typing as t

from dotenv import load_dotenv
from flask_pyjwt import AuthManager


class Config:
    """Object containing config values for the GifSync Flask app.

    Args:
        config_type (:obj:`str`, optional): Determines which environment variable
            file to load. Can be "production" which reads ".env", "development"
            which reads ".env.development", or "testing" which reads ".env.testing".
            Defaults to "development".

    Raises:
        :obj:`ValueError`: If the ``JWT_AUTHTYPE`` is not one of HS256, HS512,
            RS256, or RS512.
        :obj:`ValueError`: If the ``RSA_FILENAME`` environment variable is not set when
        using a ``JWT_AUTHTYPE`` of RS256 or RS512.
    """

    def __init__(
        self,
        config_type: t.Literal["production", "development", "testing"] = "development",
    ) -> None:
        # Load the environment variables from .env.* file
        self.CONFIG_TYPE = config_type.lower()
        if self.CONFIG_TYPE == "production":
            load_dotenv(".env.production", override=True)
        elif self.CONFIG_TYPE == "development":
            load_dotenv(".env.development", override=True)
        elif self.CONFIG_TYPE == "testing":
            load_dotenv(".env.testing", override=True)

        # Flask configuration
        self.DOMAIN = os.environ.get("DOMAIN", "dev.localhost")

        # Flask_PyJWT Configuration
        self.JWT_ISSUER = os.environ.get("JWT_ISSUER", "GifSync")
        self.JWT_AUTHTYPE = os.environ.get("JWT_AUTHTYPE", "HS256")
        if self.JWT_AUTHTYPE not in ("HS256", "HS512", "RS256", "RS512"):
            raise ValueError("JWT_AUTHTYPE must be HS256, HS512, RS256, or RS512")
        self.JWT_SECRET: t.Union[str, bytes] = os.environ.get(
            "JWT_SECRET", secrets.token_urlsafe(16)
        )
        if self.JWT_AUTHTYPE in ("RS256", "RS512"):
            rsa_filename = os.environ.get("RSA_FILENAME", "id_rsa")
            if not rsa_filename:
                raise ValueError(
                    f"Auth type of {self.JWT_AUTHTYPE} specified, "
                    "but no RSA_FILENAME given!"
                )
            with open(rsa_filename, "rb") as rsa_prvkey:
                self.JWT_SECRET = rsa_prvkey.read()
            with open(f"{rsa_filename}.pub", "rb") as rsa_pubkey:
                self.JWT_PUBLICKEY = rsa_pubkey.read()
        self.JWT_AUTHMAXAGE = int(
            os.environ.get("JWT_AUTHMAXAGE", AuthManager.default_auth_max_age)
        )
        self.JWT_REFRESHMAXAGE = int(
            os.environ.get("JWT_REFRESHMAXAGE", AuthManager.default_refresh_max_age)
        )

        # Flask_CORS Configuration
        self.CORS_ORIGINS = os.environ.get("CORS_ORIGINS")
        if not self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must be defined")
        self.CORS_SUPPORTS_CREDENTIALS = True

        # Flask-SQLAlchemy Configuration
        self.SQLALCHEMY_DATABASE_URI = os.environ.get(
            "SQLALCHEMY_DATABASE_URI",
            "postgresql://postgres:postgres@localhost:5432/postgres",
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False

        # Redis Configuration
        self.REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
