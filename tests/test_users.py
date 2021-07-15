"""Test cases related to the /users resource."""
# pylint: disable=wrong-import-order
import typing as t
from http import HTTPStatus

from flask.testing import FlaskClient
from gifsync_api.models import GifSyncUser

from .utils.assertion import assert_error_response, assert_user_in_response
from .utils.generation import (
    create_auth_token,
    create_random_username,
    populate_database_with_users,
)
from .utils.requests import delete_user, delete_users, get_user, get_users


def test_get_users_non_admin(client: FlaskClient) -> None:
    """Assert when GET /users is requested, that non-admin users
    are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    # Non-admin users are not allowed to make the request
    username = create_random_username()
    auth_token = create_auth_token(username)
    response = get_users(client, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_get_users_unauthenticated(client: FlaskClient) -> None:
    """Assert when GET /users is requested, that unauthenticated
    users are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    # Unauthenticated users are not allowed to make the request
    response = get_users(client)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_get_users_admin(client: FlaskClient, db_session) -> None:
    """Assert when GET /users is requested, that admin users
    are allowed to make the request and returns a list of users
    that matches all the users in the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    populate_database_with_users(db_session)
    # Admin users are allowed to make the request
    auth_token = create_auth_token(username, admin=True)
    response = get_users(client, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    # List of users matches all the users in the database
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "users" in json_data
    assert isinstance(json_data["users"], list)
    resp_users: t.List[dict] = json_data["users"]
    db_users = GifSyncUser.get_all()
    assert len(db_users) == len(resp_users)
    for db_user in db_users:
        match_resp_user_list = [
            resp_user for resp_user in resp_users if resp_user.get("id") == db_user.id
        ]
        assert len(match_resp_user_list) == 1
        match_resp_user = match_resp_user_list[0]
        assert match_resp_user.get("username") == db_user.username
        assert isinstance(match_resp_user.get("gifs"), list)
        assert len(match_resp_user["gifs"]) == len(db_user.gifs)


def test_delete_users_non_admin(client: FlaskClient) -> None:
    """Assert when DELETE /users is requested, that non-admin users
    are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    # Non-admin users are not allowed to make the request
    auth_token = create_auth_token(username)
    response = delete_users(client, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_delete_users_unauthenticated(client: FlaskClient) -> None:
    """Assert when DELETE /users is requested, that unauthenticated users
    are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    # Unauthenticated users are not allowed to make the request
    response = delete_users(client)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_delete_users_admin(client: FlaskClient, db_session) -> None:
    """Assert when DELETE /users is requested, that admin users
    are allowed to make the request and that no users exist in the
    database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    populate_database_with_users(db_session)
    # Admin users are allowed to make the request
    auth_token = create_auth_token(username, admin=True)
    response = delete_users(client, auth_token.signed)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content_length is None
    # No users exist in the database
    all_users = GifSyncUser.get_all()
    assert len(all_users) == 0


def test_get_user_by_id_non_admin(client: FlaskClient, db_session) -> None:
    """Assert when GET /users/<username> is requested, that users with
    matching username in auth token are allowed to make the request, and
    that the user retrieved matches the user in the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    populate_database_with_users(db_session, username)
    # Users with matching username in auth token are allowed to make
    # the request
    user = GifSyncUser.get_by_username(username)
    assert user is not None
    auth_token = create_auth_token(username)
    response = get_user(client, username, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    assert_user_in_response(response)
    # User retrieved matches the user in database
    json_data: dict = response.get_json()
    user_data = json_data.get("user")
    assert isinstance(user_data, dict)
    assert user_data.get("id") == user.id
    assert user_data.get("username") == user.username
    assert isinstance(user_data.get("gifs"), list)
    assert len(user_data["gifs"]) == len(user.gifs)


def test_get_user_by_id_unauthenticated(client: FlaskClient) -> None:
    """Assert when GET /users/<username> is requested, that unauthenticated
    users are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    # Unauthenticated users are not allowed to make the request
    response = get_user(client, username)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_get_user_by_id_admin(client: FlaskClient, db_session) -> None:
    """Assert when GET /users/<username> is requested, that admin users
    are allowed to make the request, and that the user retrieved matches
    the user in the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    admin_username = create_random_username()
    populate_database_with_users(db_session, username)
    user = GifSyncUser.get_by_username(username)
    assert user is not None
    # Admin users are allowed to make the request
    auth_token = create_auth_token(admin_username, admin=True)
    response = get_user(client, username, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    assert_user_in_response(response)
    # User retrieved matches the user in database
    json_data: dict = response.get_json()
    user_data = json_data.get("user")
    assert isinstance(user_data, dict)
    assert user_data.get("id") == user.id
    assert user_data.get("username") == user.username
    assert isinstance(user_data.get("gifs"), list)
    assert len(user_data["gifs"]) == len(user.gifs)


def test_get_user_by_id_mismatch(client: FlaskClient) -> None:
    """Assert when GET /users/<username> is requested, that users with
    mismatching username in auth token are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    # Users with mismatching username in auth token are not allowed
    # to make the request
    other_username = create_random_username()
    auth_token = create_auth_token(other_username)
    response = get_user(client, username, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_get_user_by_id_non_existent(client: FlaskClient) -> None:
    """Assert when GET /users/<username> is requested, that authenticated
    requests to non-existent usernames gives 404.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    # Authenticated requests to nonexistent usernames gives 404
    auth_token = create_auth_token(username)
    response = get_user(client, username, auth_token.signed)
    assert_error_response(response, HTTPStatus.NOT_FOUND)


def test_delete_user_by_id_non_admin(client: FlaskClient, db_session) -> None:
    """Assert when DELETE /users/<username> is requested, that users with
    matching username in auth token are allowed to make the request, and
    that the user with username is deleted from the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    populate_database_with_users(db_session, username)
    auth_token = create_auth_token(username)
    response = delete_user(client, username, auth_token.signed)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content_length is None
    assert GifSyncUser.get_by_username(username) is None


def test_delete_user_by_id_unauthenticated(client: FlaskClient) -> None:
    """Assert when DELETE /users/<username> is requested, that unauthenticated
    users are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    response = delete_user(client, username)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_delete_user_by_id_admin(client: FlaskClient, db_session) -> None:
    """Assert when DELETE /users/<username> is requested, that admin users
    are allowed to make the request, and that the user with username is
    deleted from the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    admin_username = create_random_username()
    populate_database_with_users(db_session, username)
    auth_token = create_auth_token(admin_username, admin=True)
    response = delete_user(client, username, auth_token.signed)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content_length is None
    assert GifSyncUser.get_by_username(username) is None


def test_delete_user_by_id_mismatch(client: FlaskClient) -> None:
    """Assert when DELETE /users/<username> is requested, that users with
    mismatching username in auth token are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    other_username = create_random_username()
    auth_token = create_auth_token(other_username)
    response = delete_user(client, username, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_delete_user_by_id_non_existent(client: FlaskClient) -> None:
    """Assert when DELETE /users/<username> is requested, that authenticated
    requests to non-existent usernames gives 404.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(username)
    response = delete_user(client, username, auth_token.signed)
    assert_error_response(response, HTTPStatus.NOT_FOUND)
