"""Testing utils for making requests to the GifSync API."""
import typing as t

from flask import Flask, Response
from flask.testing import FlaskClient
from flask_pyjwt import AuthManager


def add_refresh_token_cookie_to_client(
    app: Flask, auth_manager: AuthManager, client: FlaskClient, refresh_token: str
) -> None:
    """Adds a refresh_token cookie to the client in the expected format.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        auth_manager (:obj:`~flask_pyjwt.AuthManager`): The auth manager used to
            sign and provision tokens.
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


def get_users(client: FlaskClient, auth_token: t.Optional[str] = None) -> Response:
    """GET /users

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    if auth_token:
        response: Response = client.get(
            "/users", headers={"Authorization": f"Bearer {auth_token}"}
        )
    else:
        response = client.get("/users")
    return response


def post_users(
    client: FlaskClient,
    auth_token: t.Optional[str] = None,
    username: t.Optional[str] = None,
) -> Response:
    """POST /users

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.
        username (:obj:`str`, optional): Username of User to post. Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    if auth_token:
        response: Response = client.post(
            "/users",
            json={"username": username} if username else None,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
    else:
        response = client.post(
            "/users", json={"username": username} if username else None
        )
    return response


def delete_users(client: FlaskClient, auth_token: t.Optional[str] = None) -> Response:
    """DELETE /users

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    if auth_token:
        response: Response = client.delete(
            "/users", headers={"Authorization": f"Bearer {auth_token}"}
        )
    else:
        response = client.delete("/users")
    return response


def get_user(
    client: FlaskClient, username: str, auth_token: t.Optional[str] = None
) -> Response:
    """GET /users/<username>

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        username (:obj:`str`): The username of the User to retrieve.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    if auth_token:
        response: Response = client.get(
            f"/users/{username}", headers={"Authorization": f"Bearer {auth_token}"}
        )
    else:
        response = client.get(f"/users/{username}")
    return response
