"""Testing utils for assertions."""
import typing as t
from http import HTTPStatus

from flask import Flask, Response
from werkzeug.http import parse_cookie


def assert_user_in_response(response: Response) -> None:
    """Assert that the response's body is json and contains a "username", "id",
    and "gifs" value.

    Args:
        response (:obj:`~flask.Response`): The Flask Response object to check.
    """
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "user" in json_data
    user_json = json_data["user"]
    assert isinstance(user_json, dict)
    assert "id" in user_json
    assert isinstance(user_json["id"], int)
    assert "username" in user_json
    assert "gifs" in user_json
    assert isinstance(user_json["gifs"], list)


def assert_gif_in_response(response: Response) -> None:
    """Assert that the response's body is json and contains an "id", "name",
    "beats_per_loop", "image", and "custom_tempo" value.

    Args:
        response (:obj:`~flask.Response`): The Flask Response object to check.
    """
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "gif" in json_data
    gif_json = json_data["gif"]
    assert isinstance(gif_json, dict)
    assert "id" in gif_json
    assert isinstance(gif_json["id"], int)
    assert "name" in gif_json
    assert "image" in gif_json
    assert "beats_per_loop" in gif_json
    assert isinstance(gif_json["beats_per_loop"], int)
    assert "custom_tempo" in gif_json


def assert_error_response(response: Response, status: HTTPStatus) -> None:
    """Assert that a response has the given status code and an error message in the
    response's body.

    Args:
        response (:obj:`~flask.Response`): The response to assert against.
        status (:obj:`~http.HTTPStatus`): The status code the response should give.
    """
    assert response.status_code == status
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


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


def assert_refresh_token_in_cookies(app: Flask, response: Response) -> None:
    """Assert that the client has a correctly formatted "refresh_token" cookie set.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    cookies = response.headers.getlist("Set-Cookie")
    cookie = next((cookie for cookie in cookies if "refresh_token" in cookie), None)
    # Assert that API has set a refresh_token cookie
    assert cookie is not None
    cookie_attrs = parse_cookie(cookie)
    assert "Domain" in cookie_attrs and cookie_attrs["Domain"] == app.config["DOMAIN"]
    assert "Path" in cookie_attrs and cookie_attrs["Path"] == "/auth/refresh"
    assert "Secure" in cookie_attrs
    assert "Max-Age" in cookie_attrs
    assert "HttpOnly" in cookie_attrs


def assert_deleted_cookies_in_response(
    app: Flask, response: Response, cookies: t.Iterable[t.Tuple[str, str]]
) -> None:
    """Assert that the client has correctly removed all cookies named in "cookie_names".

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        cookies (:obj:`Iterable[Tuple[str,str]]`): The cookie names and paths
            that should be deleted.
    """
    resp_cookies = response.headers.getlist("Set-Cookie")
    for cookie_name, cookie_path in cookies:
        deleted_cookie = next(
            (cookie for cookie in resp_cookies if cookie_name in cookie), None
        )
        # Assert that the API has set a cookie for "cookie_name"
        assert deleted_cookie is not None
        cookie_attrs = parse_cookie(deleted_cookie)
        assert (
            "Domain" in cookie_attrs and cookie_attrs["Domain"] == app.config["DOMAIN"]
        )
        assert "Path" in cookie_attrs and cookie_attrs["Path"] == cookie_path
        assert "Secure" in cookie_attrs
        assert "Max-Age" in cookie_attrs and int(cookie_attrs["Max-Age"]) == 0
        assert "HttpOnly" in cookie_attrs
