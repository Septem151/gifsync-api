"""Fixtures used for Test cases."""
# pylint: disable=wrong-import-order
import typing as t

import pytest
from flask import Flask
from flask.testing import FlaskClient
from gifsync_api import create_app
from gifsync_api.extensions import db, s3
from gifsync_api.models import Gif, GifSyncUser, Role
from moto import mock_s3


@pytest.fixture(name="app", scope="session")
def fixture_app() -> t.Generator[Flask, None, None]:
    """Fixture for the GifSync API Flask app.

    Yields:
        :obj:`Generator[FlaskClient, None, None]`: Flask app.
    """
    with mock_s3():
        app = create_app("testing")
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()
        s3.create_bucket()
        yield app

        with app.app_context():
            db.drop_all()


@pytest.fixture(name="client", scope="function")
def fixture_client(app: Flask) -> t.Generator[FlaskClient, None, None]:
    """Fixture for a client to interact with GifSync API's Flask app.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.

    Yields:
        :obj:`Generator[FlaskClient, None, None]`: Flask test client.
    """
    with app.test_client() as client:
        yield client


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(app: Flask):
    """Fixture for the GifSync API database session.

    Args:
        db (:obj:`~flask_sqlalchemy.SQLAlchemy`): The Flask database fixture.

    Yields:
        SQLAlchemy scoped_session.
    """
    with app.app_context():
        db_session = db.session
        db_session.add_all([Role(name="admin"), Role(name="spotify")])
        db_session.commit()
        yield db_session

        GifSyncUser.query.delete()
        Gif.query.delete()
        db_session.commit()
        db_session.remove()
