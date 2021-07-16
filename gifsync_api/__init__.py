"""
This module contains the application factory for creating the Flask app, registering
its extensions, and defines a version for the application.
"""
import json
import typing as t

from flask import Flask
from werkzeug.exceptions import HTTPException

from .config import Config
from .extensions import auth_manager, cors, db, migrate, redis_client, rq_queue, s3
from .models import Gif, GifSyncUser, Role, assigned_role
from .routes import blueprints

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
    app.env = config_type
    app.config.from_object(Config(config_type))
    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app


def register_extensions(app: Flask) -> None:
    """Registers extensions onto a GifSync API Flask instance and configures
    Redis, RQ and Postgres.

    Args:
        app (:obj:`flask.Flask`): The GifSync API Flask instance.
    """
    auth_manager.init_app(app)
    cors.init_app(app)
    test_mode = app.config["CONFIG_TYPE"] == "testing"
    redis_client.init_redis(app.config["REDIS_URL"], test_mode)
    rq_queue.init_queue(redis_client.client, test_mode)
    db.init_app(app)
    s3.init_s3(
        access_key=app.config["AWS_ACCESS_KEY"],
        secret_key=app.config["AWS_SECRET_KEY"],
        bucket_name=app.config["AWS_S3_BUCKET"],
    )
    migrate.init_app(app, db)


def register_blueprints(app: Flask) -> None:
    """Registers blueprint routes onto a GifSync API Flask instance.

    Args:
        app (:obj:`flask.Flask`): The GifSync API Flask instance.
    """
    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def register_error_handlers(app: Flask) -> None:
    """Registers error handling onto a GifSync API Flask instance.

    Args:
        app (:obj:`flask.Flask`): The GifSync API Flask instance.
    """

    @app.errorhandler(HTTPException)
    def handle_exception(exception: HTTPException):
        """Handler for all HTTP Exceptions, converts responseo to JSON"""
        response = exception.get_response()
        if response.content_type != "application/json":
            response.data = json.dumps({"error": exception.description})
            response.content_type = "application/json"
        return response
