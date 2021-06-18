"""Fixtures used for Test cases."""
import typing as t

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from gifsync_api import create_app
from gifsync_api.extensions import db
from gifsync_api.models import Gif, User  # pylint: disable=unused-import


@pytest.fixture(name="app", scope="session")
def fixture_app() -> t.Generator[Flask, None, None]:
    """Fixture for the GifSync API Flask app.

    Yields:
        :obj:`Generator[FlaskClient, None, None]`: Flask app.
    """
    app = create_app("testing")
    app.config["TESTING"] = True
    yield app


@pytest.fixture(name="client")
def fixture_client(app: Flask) -> t.Generator[FlaskClient, None, None]:
    """Fixture for a client to interact with GifSync API's Flask app.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.

    Yields:
        :obj:`Generator[FlaskClient, None, None]`: Flask test client.
    """
    with app.test_client() as client:
        yield client


@pytest.fixture(name="database", scope="session")
def fixture_db(app: Flask) -> t.Generator[SQLAlchemy, None, None]:
    """Fixture for the GifSync API database.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.

    Yields:
        :obj:`Generator[SQLAlchemy, None, None]`: SQLAlchemy database.
    """
    with app.app_context():
        db.create_all()
        yield db

        db.drop_all()


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(database: SQLAlchemy):
    """Fixture for the GifSync API database session.

    Args:
        db (:obj:`~flask_sqlalchemy.SQLAlchemy`): The Flask database fixture.

    Yields:
        SQLAlchemy scoped_session.
    """
    connection = database.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    db_session = database.create_scoped_session(options=options)
    database.session = db_session
    yield db_session

    transaction.rollback()
    connection.close()
    db_session.remove()
