"""Test cases related to the /users resource."""
# pylint: disable=wrong-import-order
import typing as t
from http import HTTPStatus

from flask.testing import FlaskClient
from gifsync_api.extensions import auth_manager

from .utils.assertion import assert_error_response, assert_user_in_response
from .utils.generation import (
    create_auth_token,
    create_expired_auth_token,
    create_random_username,
    populate_database_with_users,
)
from .utils.requests import delete_users, get_user, get_users, post_user, post_users


def test_allows_admin_to_get_all_users(client: FlaskClient, db_session) -> None:
    """Assert that the GifSync API will respond with a list of users when GET /users
    is requested with an auth token owned by an admin.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    populate_database_with_users(db_session)
    auth_token = create_auth_token(auth_manager, create_random_username(), admin=True)
    response = get_users(client, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "users" in json_data
    assert isinstance(json_data["users"], list)


def test_rejects_user_from_getting_all_users(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 403 Forbidden and an error message
    when GET /users is requested with an auth token owned by a normal user.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(auth_manager, username)
    response = get_users(client, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_rejects_unauthenticated_request_to_get_all_users(
    client: FlaskClient,
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when GET /users is requested with no auth token.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = get_users(client)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_allows_post_to_users_with_matching_auth_token(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 201 Created and user info in
    the response when POST /users is requested by any user whose auth token contains
    a "sub" equal to that of the username of the user they are trying to POST.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(auth_manager, username)
    response = post_users(client, auth_token.signed, username)
    assert response.status_code == HTTPStatus.CREATED
    assert_user_in_response(response)


def test_allows_admin_to_post_any_users(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 201 Created and user info in
    the response when POST /users is requested by an admin.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    admin_username = create_random_username()
    auth_token = create_auth_token(auth_manager, admin_username, admin=True)
    response = post_users(client, auth_token.signed, username)
    assert response.status_code == HTTPStatus.CREATED
    assert_user_in_response(response)


def test_rejects_post_to_users_with_mismatching_auth_token(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 403 Forbidden and an error message
    when POST /users is requested by a user whose auth token doesn't contain a "sub"
    equal to that of the username of the user they are trying to POST.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    post_username = create_random_username()
    token_username = create_random_username()
    auth_token = create_auth_token(auth_manager, token_username)
    response = post_users(client, auth_token.signed, post_username)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_rejects_post_to_users_with_invalid_auth_token(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when POST /users is requested with an invalid auth token.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(auth_manager, username)
    assert auth_token.signed is not None
    invalid_token = auth_token.signed[:-2]
    response = post_users(client, invalid_token, username)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_rejects_post_to_users_with_expired_auth_token(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when POST /users is requested with an expired auth token.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_expired_auth_token(auth_manager, username)
    assert auth_token.signed is not None
    response = post_users(client, auth_token.signed, username)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_rejects_unauthenticated_post_to_users(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when POST /users is requested with no auth token.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    response = post_users(client, username=username)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_rejects_post_to_users_with_missing_args(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 400 Bad Request and an error
    message when POST /users is requested with no username specified in the body.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(auth_manager, username)
    response = post_users(client, auth_token=auth_token.signed)
    assert_error_response(response, HTTPStatus.BAD_REQUEST)


def test_allows_admin_to_delete_all_users(client: FlaskClient, db_session) -> None:
    """Assert that the GifSync API will respond with 204 No Response when DELETE /users
    is requested by an admin.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    populate_database_with_users(db_session)
    auth_token = create_auth_token(auth_manager, username, admin=True)
    response = delete_users(client, auth_token.signed)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content_length == 0


def test_rejects_user_from_deleting_all_users(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 403 Forbidden and an error
    message when DELETE /users is requested with an auth token owned by a normal user.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(auth_manager, username)
    response = delete_users(client, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_rejects_unauthenticated_from_deleting_all_users(
    client: FlaskClient,
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized an an error
    message when DELETE /users is requested without an auth token.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = delete_users(client)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_allows_getting_user_by_id_with_matching_auth_token(
    client: FlaskClient, db_session
) -> None:
    """Assert that the GifSync API will respond with a user's username and their gifs
    when GET /user/<username> is requested when the auth token's "sub" matches the
    username in the route.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    populate_database_with_users(db_session, username)
    auth_token = create_auth_token(auth_manager, username)
    response = get_user(client, username, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    assert_user_in_response(response)


def test_allows_admin_to_get_any_user_by_id(client: FlaskClient, db_session) -> None:
    """Assert that the GifSync API will respond with a user's username and their figs
    when GET /user/<username> is requested by an admin.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    admin_username = create_random_username()
    populate_database_with_users(db_session, username)
    auth_token = create_auth_token(auth_manager, admin_username, admin=True)
    response = get_user(client, username, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    assert_user_in_response(response)


def test_rejects_getting_user_by_id_with_mismatching_auth_token(
    client: FlaskClient,
) -> None:
    """Assert that the GifSync API will respond with 403 Forbidden and an error message
    when GET /users/<username> is requested by a user whose auth token doesn't contain
    a "sub" equal to that of the username of the user they are trying to GET.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    get_username = create_random_username()
    auth_token = create_auth_token(auth_manager, username)
    response = get_user(client, get_username, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_rejects_getting_user_by_id_with_invalid_auth_token(
    client: FlaskClient,
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when GET /users/<username> is requested with an invalid auth token.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(auth_manager, username)
    assert auth_token.signed is not None
    invalid_token = auth_token.signed[:-2]
    response = get_user(client, username, invalid_token)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_rejects_getting_user_by_id_with_expired_auth_token(
    client: FlaskClient,
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when GET /users/<username> is requested with an expired auth token.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_expired_auth_token(auth_manager, username)
    response = get_user(client, username, auth_token.signed)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_rejects_unauthenticated_getting_user_by_id(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when GET /users/<username> is requested without an auth token.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    response = get_user(client, username)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_responds_404_when_getting_user_by_nonexistent_id(
    client: FlaskClient, db_session
) -> None:
    """Assert that the GifSync API will respond with 404 Not Found and an error message
    when GET /users/<username> is requested for a username that doesn't exist.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    populate_database_with_users(db_session)
    username = create_random_username()
    auth_token = create_auth_token(auth_manager, username)
    response = get_user(client, username, auth_token.signed)
    assert_error_response(response, HTTPStatus.NOT_FOUND)


def test_allows_post_to_user_by_id_with_matching_auth_token(
    client: FlaskClient, db_session
) -> None:
    """Assert that the GifSync API will respond with 200 OK and a user object when
    POST /users/<username> is requested by a user with the same username.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    populate_database_with_users(db_session, username)
    auth_token = create_auth_token(auth_manager, username)
    response = post_user(client, username, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
