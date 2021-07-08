"""Test cases related to the /gifs resource."""
import typing as t
from http import HTTPStatus

from flask.testing import FlaskClient
from gifsync_api.extensions import auth_manager

from .utils.assertion import assert_error_response
from .utils.generation import (
    create_random_username,
    populate_database_with_users,
    populate_users_with_gifs,
)
from .utils.requests import get_gifs


def test_allows_admin_to_get_all_gifs(client: FlaskClient, db_session) -> None:
    """Assert that the GifSync API allows admin to get all gifs.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    populate_database_with_users(db_session, username)
    populate_users_with_gifs(db_session)
    auth_token = auth_manager.auth_token(username, {"admin": True})
    response = get_gifs(client, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "gifs" in json_data
    assert isinstance(json_data["gifs"], list)


def test_rejects_user_from_getting_all_gifs(client: FlaskClient) -> None:
    """Assert that the GifSync API rejects non-admin users from getting all gifs
    by returning a 403 Forbidden and error message when GET /gifs is requested.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = auth_manager.auth_token(username)
    response = get_gifs(client, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_rejects_unauthenticated_request_to_get_all_gifs(client: FlaskClient) -> None:
    """Assert that the GifSync API rejects unauthenticated requests to GET /gifs
    and returns a 401 Unauthorized with an error message.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = get_gifs(client)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)
