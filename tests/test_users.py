"""Test cases related to the /users resource."""
import typing as t
import uuid
from http import HTTPStatus

from flask import Flask, Response
from flask.testing import FlaskClient
from flask_pyjwt import JWT, AuthManager, TokenType
from sqlalchemy.orm.scoping import scoped_session as Session


def populate_database_with_users(
    db_session: Session, extra_username: t.Optional[str] = None
) -> None:
    """Populates the test database with fake users.

    Args:
        db_session (:obj:`~sqlalchemy.orm.scoping.Session`): The Database Session
            fixture.
    """
    # TODO: Write this function.


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


def test_allows_admin_to_get_all_users(
    app: Flask, client: FlaskClient, db_session: Session
) -> None:
    """Assert that the GifSync API will respond with a list of users when GET /users
    is requested with an auth token owned by an admin.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session (:obj:`~sqlalchemy.orm.scoping.Session`): The Database Session
            fixture.
    """
    populate_database_with_users(db_session)
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token("test", scope={"admin": True})
    response = get_users(client, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "users" in json_data
    assert isinstance(json_data["users"], list)


def test_rejects_user_from_getting_all_users(app: Flask, client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 403 Forbidden and an error message
    when GET /users is requested with an auth token owned by a normal user.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token(str(uuid.uuid4()))
    response = get_users(client, auth_token.signed)
    assert response.status_code == HTTPStatus.FORBIDDEN
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


def test_rejects_unauthenticated_request_to_get_all_users(
    client: FlaskClient,
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when GET /users is requested with no auth token.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = get_users(client)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


def test_allows_post_to_users_with_matching_auth_token(
    app: Flask, client: FlaskClient
) -> None:
    """Assert that the GifSync API will respond with 201 Created and user info in
    the response when POST /users is requested by any user whose auth token contains
    a "sub" equal to that of the username of the user they are trying to POST.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = str(uuid.uuid4())
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token(username)
    response = post_users(client, auth_token.signed, username)
    assert response.status_code == HTTPStatus.CREATED
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "username" in json_data
    assert json_data["username"] == username
    assert "gifs" in json_data
    assert isinstance(json_data["gifs"], list)


def test_allows_admin_to_post_any_users(app: Flask, client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 201 Created and user info in
    the response when POST /users is requested by an admin.

    Args:
        app (Flask): [description]
        client (FlaskClient): [description]
    """
    username = str(uuid.uuid4())
    admin_username = str(uuid.uuid4())
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token(admin_username, scope={"admin": True})
    response = post_users(client, auth_token.signed, username)
    assert response.status_code == HTTPStatus.CREATED
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "username" in json_data
    assert json_data["username"] == username
    assert "gifs" in json_data
    assert isinstance(json_data["gifs"], list)


def test_rejects_post_to_users_with_mismatching_auth_token(
    app: Flask, client: FlaskClient
) -> None:
    """Assert that the GifSync API will respond with 403 Forbidden and an error message
    when POST /users is requested by a user whose auth token doesn't contain a "sub"
    equal to that of the username of the user they are trying to POST.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    post_username = str(uuid.uuid4())
    token_username = str(uuid.uuid4())
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token(token_username)
    response = post_users(client, auth_token.signed, post_username)
    assert response.status_code == HTTPStatus.FORBIDDEN
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


def test_rejects_post_to_users_with_invalid_auth_token(
    app: Flask, client: FlaskClient
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when POST /users is requested with an invalid auth token.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = str(uuid.uuid4())
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token(username)
    invalid_token = auth_token.signed[:-2]
    response = post_users(client, invalid_token, username)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


def test_rejects_post_to_users_with_expired_auth_token(
    app: Flask, client: FlaskClient
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when POST /users is requested with an expired auth token.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = str(uuid.uuid4())
    auth_manager: AuthManager = app.auth_manager
    signer = auth_manager.signer
    signer.auth_max_age = int(-600)
    auth_token = JWT(TokenType.AUTH, username)
    auth_token.sign(signer)
    assert auth_token.signed is not None
    response = post_users(client, auth_token.signed, username)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


def test_rejects_unauthenticated_post_to_users(client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized and an error
    message when POST /users is requested with no auth token.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = str(uuid.uuid4())
    response = post_users(client, username=username)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


def test_rejects_post_to_users_with_missing_args(
    app: Flask, client: FlaskClient
) -> None:
    """Assert that the GifSync API will respond with 400 Bad Request and an error
    message when POST /users is requested with no username specified in the body.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token(str(uuid.uuid4()))
    response = post_users(client, auth_token=auth_token.signed)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


def test_allows_admin_to_delete_all_users(
    app: Flask, client: FlaskClient, db_session: Session
) -> None:
    """Assert that the GifSync API will respond with 204 No Response when DELETE /users
    is requested by an admin.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session (:obj:`~sqlalchemy.orm.scoping.Session`): The Database Session
            fixture.
    """
    populate_database_with_users(db_session)
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token(str(uuid.uuid4()), scope={"admin": True})
    response = delete_users(client, auth_token)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content_length == 0


def test_rejects_user_from_deleting_all_users(app: Flask, client: FlaskClient) -> None:
    """Assert that the GifSync API will respond with 403 Forbidden and an error
    message when DELETE /users is requested with an auth token owned by a normal user.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token(str(uuid.uuid4()))
    response = delete_users(client, auth_token)
    assert response.status_code == HTTPStatus.FORBIDDEN
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


def test_rejects_unauthenticated_from_deleting_all_users(
    client: FlaskClient,
) -> None:
    """Assert that the GifSync API will respond with 401 Unauthorized an an error
    message when DELETE /users is requested without an auth token.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = delete_users(client)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "error" in json_data


def test_allows_getting_user_by_id_with_matching_auth_token(
    app: Flask, client: FlaskClient, db_session: Session
) -> None:
    """Assert that the GifSync API will respond with a user's username and their gifs
    when GET /user/<username> is requested when the auth token's "sub" matches the
    username in the route.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session (:obj:`~sqlalchemy.orm.scoping.Session`): The Database Session
            fixture.
    """
    username = str(uuid.uuid4())
    populate_database_with_users(db_session, username)
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token(username)
    response = get_user(client, username, auth_token)
    assert response.status_code == HTTPStatus.OK
    assert_user_in_response(response)


def test_allows_admin_to_get_any_user_by_id(
    app: Flask, client: FlaskClient, db_session: Session
) -> None:
    """Assert that the GifSync API will respond with a user's username and their figs
    when GET /user/<username> is requested by an admin.

    Args:
        app (:obj:`~flask.Flask`): The Flask app fixture.
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session (:obj:`~sqlalchemy.orm.scoping.Session`): The Database Session
            fixture.
    """
    username = str(uuid.uuid4())
    admin_username = str(uuid.uuid4())
    populate_database_with_users(db_session, username)
    auth_manager: AuthManager = app.auth_manager
    auth_token = auth_manager.auth_token(admin_username, scope={"admin": True})
    response = get_user(client, username, auth_token)
    assert response.status_code == HTTPStatus.OK
    assert_user_in_response(response)
