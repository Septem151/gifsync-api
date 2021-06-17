"""Test cases related to the /auth resource."""
import typing as t
import uuid
from http import HTTPStatus
from http.cookiejar import Cookie

from flask import Flask, Response
from flask.testing import FlaskClient
from flask_pyjwt import JWT, AuthManager, TokenType
from gifsync_api import __version__


def post_token(client: FlaskClient, spotify_token: t.Optional[str] = None) -> Response:
    """POST /auth/token

    Optional body containing::

        {
            "spotify_token": "..."
        }

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        spotify_token (:obj:`str`, optional): The Spotify API Token. Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    response: Response
    if spotify_token:
        response = client.post("/auth/token", json={"spotify_token": spotify_token})
    else:
        response = client.post("/auth/token")
    return response


def post_refresh(client: FlaskClient) -> Response:
    """POST /auth/refresh

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    response: Response = client.post("/auth/refresh")
    return response


def add_refresh_token_cookie_to_client(
    app: Flask, auth_manager: AuthManager, client: FlaskClient, refresh_token: str
) -> None:
    """Adds a refresh_token cookie to the client in the expected format.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        auth_manager (:obj:`~flask_pyjwt.AuthManager`): The Flask app's AuthManager.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        refresh_token (:obj:`str`): The value for the "refresh_token" cookie.
    """
    client.set_cookie(
        app.config["DOMAIN"],
        "refresh_token",
        refresh_token,
        auth_manager.signer.refresh_max_age,
        path="/auth/refresh",
        domain=app.config["DOMAIN"],
        httponly=True,
        secure=True,
    )


def assert_token_in_response(response: Response) -> None:
    """Assert that the response's body is json and contains a "token" and
    "expires_in" value.

    Args:
        response (:obj:`~flask.Response`): The Flask Response object to check.
    """
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "username" in json_data
    assert "scope" in json_data
    json_scope = json_data["scope"]
    assert isinstance(json_scope, dict)
    assert "spotify" in json_scope
    assert isinstance(json_scope["spotify"], bool)
    assert "admin" in json_scope
    assert isinstance(json_scope["admin"], bool)
    assert "token" in json_data
    assert "expires_in" in json_data


def assert_refresh_token_in_client_cookies(app: Flask, client: FlaskClient) -> None:
    """Assert that the client has a correctly formatted "refresh_token" cookie set.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    assert client.cookie_jar is not None
    cookie: t.Optional[Cookie] = next(
        (cookie for cookie in client.cookie_jar if cookie.name == "refresh_token"), None
    )
    # Assert that API has set a refresh_token cookie
    assert cookie is not None
    assert cookie.domain == app.config["DOMAIN"]
    assert cookie.path == "/auth/refresh"
    assert cookie.secure is True
    assert cookie.has_nonstandard_attr("Max-Age")
    assert cookie.has_nonstandard_attr("HttpOnly")


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
    assert_refresh_token_in_client_cookies(app, client)


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
    auth_manager: AuthManager = app.auth_manager
    refresh_token = auth_manager.refresh_token(str(uuid.uuid4()))
    add_refresh_token_cookie_to_client(app, auth_manager, client, refresh_token.signed)
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
    auth_manager: AuthManager = app.auth_manager
    refresh_token = auth_manager.refresh_token(str(uuid.uuid4()))
    invalid_token = refresh_token.signed[:-2]
    add_refresh_token_cookie_to_client(app, auth_manager, client, invalid_token)
    response = post_refresh(client)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


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
    auth_manager: AuthManager = app.auth_manager
    signer = auth_manager.signer
    signer.refresh_max_age = int(-600)
    refresh_token = JWT(TokenType.REFRESH, str(uuid.uuid4()))
    refresh_token.sign(signer)
    assert refresh_token.signed is not None
    add_refresh_token_cookie_to_client(app, auth_manager, client, refresh_token.signed)
    response = post_refresh(client)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


def test_rejects_refresh_with_missing_refresh_token_cookie(
    client: FlaskClient,
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when POST /auth/refresh is requested with no cookie named "refresh_token".

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = post_refresh(client)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data
