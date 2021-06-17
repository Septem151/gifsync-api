"""
This module contains the application factory for creating the Flask app, registering
its extensions, and defines a version for the application.
"""
import typing as t

from flask import Flask

from .config import Config
from .extensions import auth_manager, cors, db, redis_client, rq_queue

__version__ = "0.1.0"


def create_app(
    config_type: t.Literal["production", "development", "testing"] = "production"
) -> Flask:
    """Application Factory for a GifSync API Flask instance.

    Args:
        config_type (:obj:`str`): The configuration to use for the Flask instance,
            which controls what environment variables to load into the app's config.

    Returns:
        :obj:`flask.Flask`: The Flask instance.
    """
    app = Flask(__name__)
    app.config.from_object(Config(config_type))
    register_extensions(app)
    print(app.config["DOMAIN"])
    return app


def register_extensions(app: Flask) -> None:
    """Registers extensions onto a GifSync API Flask instance and configures
    Redis, RQ and Postgres.

    Args:
        app (:obj:`flask.Flask`): The GifSync API Flask instance.
    """
    auth_manager.init_app(app)
    cors.init_app(app)
    redis_client.init_redis(app.config["REDIS_URL"])
    rq_queue.init_queue(redis_client.client)
    db.init_app(app)
