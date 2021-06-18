"""Testing utils for assertions."""
import typing as t
from http import HTTPStatus
from http.cookiejar import Cookie

from flask import Flask, Response
from flask.testing import FlaskClient


def assert_user_in_response(response: Response) -> None:
    """Assert that the response's body is json and contains a "username" and
    "gifs" value.

    Args:
        response (:obj:`~flask.Response`): The Flask Response object to check.
    """
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "user" in json_data
    user_json = json_data["user"]
    assert isinstance(user_json, dict)
    assert "username" in user_json
    assert "gifs" in user_json
    assert isinstance(user_json["gifs"], list)


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
