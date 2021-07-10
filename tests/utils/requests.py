"""Testing utils for making requests to the GifSync API."""
import io
import pathlib
import typing as t

from flask import Flask, Response
from flask.testing import FlaskClient
from gifsync_api.extensions import auth_manager


def _get_request(
    client: FlaskClient, route: str, auth_token: t.Optional[str] = None
) -> Response:
    """GET <route>

    Generic GET request with optional parameters for Authorization header.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        route (:obj:`str`): The route to GET.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else None
    response: Response = client.get(route, headers=headers)
    return response


def _post_request(
    client: FlaskClient,
    route: str,
    auth_token: t.Optional[str] = None,
    data: t.Optional[dict] = None,
    is_json: bool = True,
) -> Response:
    """POST <route>

    Generic POST request with optional parameters for Authorization header
    and JSON data.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        route (:obj:`str`): The route to POST.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.
        json_data (:obj:`dict`, optional): JSON data to POST. Defaults to None.
        form_data (:obj:`dict`, optional): Form data to POST. Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    kwargs: dict = {"headers": {}}
    if auth_token:
        kwargs["headers"] = {"Authorization": f"Bearer {auth_token}"}
    if data:
        if is_json:
            kwargs["json"] = data
            kwargs["headers"]["Content-Type"] = "application/json"
        else:
            kwargs["data"] = data
            kwargs["headers"]["Content-Type"] = "multipart/form-data"
    response: Response = client.post(route, **kwargs)
    return response


def _delete_request(
    client: FlaskClient, route: str, auth_token: t.Optional[str] = None
) -> Response:
    """DELETE <route>

    Generic DELETE request with optional parameters for Authorization header.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        route (:obj:`str`): The route to GET.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else None
    response: Response = client.delete(route, headers=headers)
    return response


def add_refresh_token_cookie_to_client(
    app: Flask, client: FlaskClient, refresh_token: str
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
    return _post_request(
        client,
        "/auth/token",
        data={"spotify_token": spotify_token} if spotify_token else None,
    )


def post_refresh(client: FlaskClient) -> Response:
    """POST /auth/refresh

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    return _post_request(client, "/auth/refresh")


def post_logout(client: FlaskClient, auth_token: t.Optional[str] = None) -> Response:
    """POST /auth/logout

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    return _post_request(client, "/auth/logout", auth_token)


def get_users(client: FlaskClient, auth_token: t.Optional[str] = None) -> Response:
    """GET /users

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    return _get_request(client, "/users", auth_token)


def delete_users(client: FlaskClient, auth_token: t.Optional[str] = None) -> Response:
    """DELETE /users

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    return _delete_request(client, "/users", auth_token)


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
    return _get_request(client, f"/users/{username}", auth_token)


def delete_user(
    client: FlaskClient,
    username: t.Optional[str] = None,
    auth_token: t.Optional[str] = None,
) -> Response:
    """DELETE /users/<username>

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        username (:obj:`str`): The username of the User to retrieve.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    return _delete_request(client, f"/users/{username}", auth_token)


def get_gifs(client: FlaskClient, auth_token: t.Optional[str] = None) -> Response:
    """GET /gifs

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    return _get_request(client, "/gifs", auth_token)


def post_gifs(
    client: FlaskClient,
    gif_name: str,
    beats_per_loop: int,
    auth_token: t.Optional[str] = None,
) -> Response:
    """POST /gifs

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        gif_name (:obj:`str`): The name of the Gif to add.
        beats_per_loop (:obj:`int`): The number of beats per loop of the Gif to add.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    image_path = pathlib.Path(__file__).parent.resolve() / "test-image.gif"
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()
    return _post_request(
        client,
        "/gifs",
        auth_token,
        {
            "name": gif_name,
            "beats_per_loop": beats_per_loop,
            "image": (io.BytesIO(image_bytes), "test-image.gif"),
        },
        is_json=False,
    )


def delete_gifs(client: FlaskClient, auth_token: t.Optional[str] = None) -> Response:
    """DELETE /gifs

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    return _delete_request(client, "/gifs", auth_token)


def get_gif(
    client: FlaskClient, gif_id: int, auth_token: t.Optional[str] = None
) -> Response:
    """GET /gifs/<gif_id>

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        gif_id (:obj:`int`): The gif id.
        auth_token (:obj:`str`, optional): Auth token for the Authorization header.
            Defaults to None.

    Returns:
        :obj:`~flask.Response`: The Flask Response object.
    """
    return _get_request(client, f"/gifs/{gif_id}", auth_token)
