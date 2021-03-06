"""Test cases related to the /auth resource."""
from http import HTTPStatus

from flask import Flask
from flask.testing import FlaskClient

from .utils.assertion import (
    assert_deleted_cookies_in_response,
    assert_error_response,
    assert_refresh_token_in_cookies,
    assert_token_in_response,
)
from .utils.generation import (
    create_auth_token,
    create_expired_refresh_token,
    create_random_username,
    create_refresh_token,
)
from .utils.requests import (
    add_refresh_token_cookie_to_client,
    post_logout,
    post_refresh,
    post_token,
)


def test_gives_anon_user_auth_token_and_sets_refresh_token_cookie(
    app: Flask, client: FlaskClient
) -> None:
    """Assert that the GifSync API will respond with an auth token, the auth token's
    max age, and a refresh_token cookie when POST /auth/token is requested with no body.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = post_token(client)
    # Assert that API accepts the request
    assert response.status_code == HTTPStatus.OK
    assert_token_in_response(response)
    assert_refresh_token_in_cookies(app, response)


def test_refreshes_token_with_valid_refresh_token_cookie(
    app: Flask, client: FlaskClient
) -> None:
    """Assert that the GifSync API will respond with an auth token and the auth token's
    max age when POST /auth/refresh is requested with a cookie named "refresh_token"
    containing a valid refresh token.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    refresh_token = create_refresh_token(username)
    assert refresh_token.signed is not None
    add_refresh_token_cookie_to_client(app, client, refresh_token.signed)
    response = post_refresh(client)
    # Assert that API accepts the request
    assert response.status_code == HTTPStatus.OK
    assert_token_in_response(response)


def test_rejects_refresh_of_invalid_refresh_token_cookie(
    app: Flask, client: FlaskClient
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when POST /auth/refresh is requested with a cookie named "refresh_token"
    containing an invalid refresh token.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    refresh_token = create_refresh_token(username)
    assert refresh_token.signed is not None
    invalid_token = refresh_token.signed[:-2]
    add_refresh_token_cookie_to_client(app, client, invalid_token)
    response = post_refresh(client)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_rejects_refresh_of_expired_refresh_token_cookie(
    app: Flask, client: FlaskClient
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when POST /auth/refresh is requested with a cookie named "refresh_token"
    containing an expired refresh token.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    refresh_token = create_expired_refresh_token(username)
    assert refresh_token.signed is not None
    add_refresh_token_cookie_to_client(app, client, refresh_token.signed)
    response = post_refresh(client)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_rejects_refresh_with_missing_refresh_token_cookie(
    client: FlaskClient,
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when POST /auth/refresh is requested with no cookie named "refresh_token".

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = post_refresh(client)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_allows_logout_with_auth_token(app: Flask, client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 204 No Content and delete the
    "refresh_token", "spotify_refresh_token", and "auto_token" cookies when
    POST /auth/logout is requested.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(username)
    response = post_logout(client, auth_token.signed)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content_length is None
    assert_deleted_cookies_in_response(
        app,
        response,
        [
            ("refresh_token", "/auth/refresh"),
            ("spotify_refresh_token", "/auth/spotify/refresh"),
            ("auto_token", "/auth/token"),
        ],
    )
