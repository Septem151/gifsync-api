"""Test cases related to the /gifs resource."""
import typing as t
from http import HTTPStatus

from flask.testing import FlaskClient
from gifsync_api.models import Gif, GifSyncUser

from .utils.assertion import assert_error_response
from .utils.generation import (
    create_auth_token,
    create_random_username,
    populate_database_with_users,
    populate_users_with_gifs,
)
from .utils.requests import delete_gifs, get_gif, get_gifs, post_gifs


def test_get_gifs_non_admin(client: FlaskClient) -> None:
    """Assert when GET /gifs is requested, that non-admin users
    are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(username)
    response = get_gifs(client, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_get_gifs_unauthenticated(client: FlaskClient) -> None:
    """Assert when GET /gifs is requested, that unauthenticated
    users are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = get_gifs(client)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_get_gifs_admin(client: FlaskClient, db_session) -> None:
    """Assert when GET /gifs is requested, that admin users
    are allowed to make the request and returns a list of gifs
    that matches all the gifs in the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    populate_database_with_users(db_session)
    populate_users_with_gifs(db_session)
    username = create_random_username()
    auth_token = create_auth_token(username, admin=True)
    response = get_gifs(client, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    # List of gifs matches all the gifs in the database
    json_data: t.Optional[dict] = response.get_json()
    assert json_data is not None
    assert "gifs" in json_data
    assert isinstance(json_data["gifs"], list)
    resp_gifs: t.List[dict] = json_data["gifs"]
    db_gifs = Gif.get_all()
    assert len(db_gifs) == len(resp_gifs)
    for db_gif in db_gifs:
        match_resp_gif_list = [
            resp_gif for resp_gif in resp_gifs if resp_gif.get("id") == db_gif.id
        ]
        assert len(match_resp_gif_list) == 1
        match_resp_gif = match_resp_gif_list[0]
        assert match_resp_gif.get("user_id") == db_gif.user_id
        assert match_resp_gif.get("owner") == db_gif.owner.username
        assert match_resp_gif.get("image") == db_gif.image
        assert "image_url" in match_resp_gif
        assert match_resp_gif.get("beats_per_loop") == db_gif.beats_per_loop
        assert match_resp_gif.get("custom_tempo") == db_gif.custom_tempo


def test_post_gifs_existing_user(client: FlaskClient, db_session) -> None:
    """Assert when POST /gifs is requested, that users are allowed
    to make the request, and that the gif added matches
    the gif added in the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    populate_database_with_users(db_session, username)
    auth_token = create_auth_token(username)
    gif_name = create_random_username()
    beats_per_loop = 5
    response = post_gifs(client, gif_name, beats_per_loop, auth_token.signed)
    assert response.status_code == HTTPStatus.CREATED
    gif_data: t.Optional[dict] = response.get_json()
    assert gif_data is not None
    assert "id" in gif_data
    assert "name" in gif_data
    assert "owner" in gif_data
    assert "beats_per_loop" in gif_data
    assert "custom_tempo" in gif_data
    assert "image" in gif_data
    assert "image_url" in gif_data
    # Gif added matches the gif added in database
    db_gif = Gif.get_by_id(gif_data["id"])
    assert db_gif is not None
    assert gif_data["name"] == db_gif.name
    assert gif_data["owner"] == db_gif.owner.username
    assert gif_data["beats_per_loop"] == db_gif.beats_per_loop
    assert gif_data["custom_tempo"] == db_gif.custom_tempo
    assert gif_data["image"] == db_gif.image


def test_post_gifs_non_existing_user(client: FlaskClient) -> None:
    """Assert when POST /gifs is requested, that users are allowed
    to make the request, that the gif added matches the gif added
    in the database, and that the user is added to the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(username)
    gif_name = create_random_username()
    beats_per_loop = 5
    response = post_gifs(client, gif_name, beats_per_loop, auth_token.signed)
    assert response.status_code == HTTPStatus.CREATED
    gif_data: t.Optional[dict] = response.get_json()
    assert gif_data is not None
    assert "id" in gif_data
    assert "name" in gif_data
    assert "owner" in gif_data
    assert "beats_per_loop" in gif_data
    assert "custom_tempo" in gif_data
    assert "image" in gif_data
    assert "image_url" in gif_data
    # User added to the database
    db_user = GifSyncUser.get_by_username(username)
    assert db_user is not None
    # Gif added matches the gif added in database
    db_gif = Gif.get_by_id(gif_data["id"])
    assert db_gif is not None
    assert gif_data["name"] == db_gif.name
    assert gif_data["owner"] == db_gif.owner.username
    assert gif_data["owner"] == db_user.username
    assert gif_data["beats_per_loop"] == db_gif.beats_per_loop
    assert gif_data["custom_tempo"] == db_gif.custom_tempo
    assert gif_data["image"] == db_gif.image


def test_post_gifs_unauthenticated(client: FlaskClient) -> None:
    """Assert when POST /gifs is requested, that unauthenticated
    users are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    gif_name = create_random_username()
    beats_per_loop = 5
    response = post_gifs(client, gif_name, beats_per_loop)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_post_gifs_existing_user_duplicate_name(
    client: FlaskClient, db_session
) -> None:
    """Assert when POST /gifs is requested, that users are allowed to
    make the request, but when a gif with the given name already exists,
    the response is 400 Bad Request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    gif_name = create_random_username()
    populate_users_with_gifs(db_session, extra_user_gif=(username, gif_name))
    auth_token = create_auth_token(username)
    response = post_gifs(client, gif_name, 5, auth_token.signed)
    assert_error_response(response, HTTPStatus.BAD_REQUEST)


def test_delete_gifs_non_admin(client: FlaskClient) -> None:
    """Assert when DELETE /gifs is requested, that non-admin users
    are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(username)
    response = delete_gifs(client, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_delete_gifs_unauthenticated(client: FlaskClient) -> None:
    """Assert when DELETE /gifs is requested, that unauthenticated
    users are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = delete_gifs(client)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_delete_gifs_admin(client: FlaskClient, db_session) -> None:
    """Assert when DELETE /gifs is requested, that admin users
    are allowed to make the request, and that all gifs are deleted
    from the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    populate_database_with_users(db_session)
    populate_users_with_gifs(db_session)
    username = create_random_username()
    auth_token = create_auth_token(username, admin=True)
    response = delete_gifs(client, auth_token.signed)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content_length is None
    # No gifs exist in the database
    all_gifs = Gif.get_all()
    assert len(all_gifs) == 0


def test_get_gif_by_id_non_admin(client: FlaskClient, db_session) -> None:
    """Assert when GET /gifs/<gif_id> is requested, that users with
    matching username in auth token are allowed to make the request, and
    that the gif retrieved matches the gif in the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    gif_name = create_random_username()
    populate_users_with_gifs(db_session, extra_user_gif=(username, gif_name))
    auth_token = create_auth_token(username)
    gif = Gif.get_by_username_and_name(username, gif_name)
    assert gif is not None
    response = get_gif(client, gif.id, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    gif_data: t.Optional[dict] = response.get_json()
    assert gif_data is not None
    assert "id" in gif_data
    assert "name" in gif_data
    assert "owner" in gif_data
    assert "beats_per_loop" in gif_data
    assert "custom_tempo" in gif_data
    assert "image" in gif_data
    assert "image_url" in gif_data
    # Gif response matches the gif in database
    db_gif = Gif.get_by_id(gif_data["id"])
    assert db_gif is not None
    assert gif_data["name"] == db_gif.name
    assert gif_data["owner"] == db_gif.owner.username
    assert gif_data["beats_per_loop"] == db_gif.beats_per_loop
    assert gif_data["custom_tempo"] == db_gif.custom_tempo
    assert gif_data["image"] == db_gif.image


def test_get_gif_by_id_unauthenticated(client: FlaskClient) -> None:
    """Assert when GET /gifs/<gif_id> is requested, that unauthenticated
    users are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    response = get_gif(client, 1)
    assert_error_response(response, HTTPStatus.UNAUTHORIZED)


def test_get_gif_by_id_admin(client: FlaskClient, db_session) -> None:
    """Assert when GET /gifs/<gif_id> is requested, that admin users
    are allowed to make the request, and that the gif retrieved matches
    the gif in the database.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
        db_session: The Database session fixture.
    """
    username = create_random_username()
    gif_name = create_random_username()
    populate_users_with_gifs(db_session, extra_user_gif=(username, gif_name))
    admin_username = create_random_username()
    auth_token = create_auth_token(admin_username, admin=True)
    gif = Gif.get_by_username_and_name(username, gif_name)
    assert gif is not None
    response = get_gif(client, gif.id, auth_token.signed)
    assert response.status_code == HTTPStatus.OK
    gif_data: t.Optional[dict] = response.get_json()
    assert gif_data is not None
    assert "id" in gif_data
    assert "name" in gif_data
    assert "owner" in gif_data
    assert "beats_per_loop" in gif_data
    assert "custom_tempo" in gif_data
    assert "image" in gif_data
    assert "image_url" in gif_data
    # Gif response matches the gif in database
    db_gif = Gif.get_by_id(gif_data["id"])
    assert db_gif is not None
    assert gif_data["name"] == db_gif.name
    assert gif_data["owner"] == db_gif.owner.username
    assert gif_data["beats_per_loop"] == db_gif.beats_per_loop
    assert gif_data["custom_tempo"] == db_gif.custom_tempo
    assert gif_data["image"] == db_gif.image


def test_get_gif_by_id_mismatch(client: FlaskClient, db_session) -> None:
    """Assert when GET /gifs/<gif_id> is requested, that users with
    mismatching username in auth token are not allowed to make the request.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    gif_name = create_random_username()
    populate_users_with_gifs(db_session, extra_user_gif=(username, gif_name))
    # added gif id will be 1
    other_username = create_random_username()
    auth_token = create_auth_token(other_username)
    gif = Gif.get_by_username_and_name(username, gif_name)
    assert gif is not None
    response = get_gif(client, gif.id, auth_token.signed)
    assert_error_response(response, HTTPStatus.FORBIDDEN)


def test_get_gif_by_id_non_existent(client: FlaskClient) -> None:
    """Assert when GET /gifs/<gif_id> is requested, that authenticated
    requests to non-existent gifs gives 404.

    Args:
        client (:obj:`~flask.testing.FlaskClient`): The Client fixture.
    """
    username = create_random_username()
    auth_token = create_auth_token(username)
    gif_id = 1
    response = get_gif(client, gif_id, auth_token.signed)
    assert_error_response(response, HTTPStatus.NOT_FOUND)
