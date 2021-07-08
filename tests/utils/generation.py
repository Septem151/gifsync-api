"""Testing utils for generating data."""
import pathlib
import random
import typing as t
import uuid

from flask_pyjwt import JWT, AuthData, TokenType
from gifsync_api.extensions import auth_manager, s3
from gifsync_api.models import Gif, GifSyncUser


def create_random_username() -> str:
    """Creates and returns a random username.

    Returns:
        :obj:`str`: The random username.
    """
    return str(uuid.uuid4())


def create_auth_token(
    username: str,
    admin: t.Optional[bool] = False,
    spotify: t.Optional[bool] = False,
) -> JWT:
    """Creates and returns an auth token with a "sub" of the username given.

    Args:
        auth_manager (:obj:`~flask_pyjwt.AuthManager`): The auth manager used to
            sign and provision tokens.
        username (:obj:`str`): Username to provision the auth token to.
        admin (:obj:`bool`, optional): Whether to add "admin" scope.
            Defaults to False.
        spotify (:obj:`bool`, optional): Whether to add "spotify" scope.
            Defaults to False.

    Returns:
        :obj:`~flask_pyjwt.JWT`: The signed auth token.
    """
    auth_token: JWT = auth_manager.auth_token(
        username, {"admin": admin, "spotify": spotify}
    )
    return auth_token


def create_refresh_token(username: str) -> JWT:
    """Creates and returns a refresh token with a "sub" of the
    username given.

    Args:
        username (:obj:`str`): Username to provision the refresh token to.

    Returns:
        :obj:`~flask_pyjwt.JWT`: The signed refresh token.
    """
    refresh_token: JWT = auth_manager.refresh_token(username)
    return refresh_token


def create_expired_auth_token(
    username: str,
    admin: t.Optional[bool] = False,
    spotify: t.Optional[bool] = False,
) -> JWT:
    """Creates and returns an expired auth token with a "sub" of the username given.

    Works by creating a new signer object based on the auth_manager's data, but sets
    the auth_max_age to a negative number. This makes the "exp" claim a time in the
    past, guaranteeing the token will always be expired.

    Args:
        auth_manager (:obj:`~flask_pyjwt.AuthManager`): The auth manager used to
            sign and provision tokens.
        username (:obj:`str`): Username to provision the auth token to.
        admin (:obj:`bool`, optional): Whether to add "admin" scope.
            Defaults to False.
        spotify (:obj:`bool`, optional): Whether to add "spotify" scope.
            Defaults to False.

    Returns:
        :obj:`~flask_pyjwt.JWT`: The expired auth token.
    """
    signer = AuthData(
        auth_manager.signer.auth_type,
        auth_manager.signer.secret,
        auth_manager.signer.issuer,
        -600,
        auth_manager.signer.refresh_max_age,
        auth_manager.signer.public_key,
    )
    auth_token = JWT(TokenType.AUTH, username, {"admin": admin, "spotify": spotify})
    auth_token.sign(signer)
    return auth_token


def create_expired_refresh_token(username: str) -> JWT:
    """Creates and returns an expired refresh token with a "sub" of the username given.

    Works by creating a new signer object based on the auth_manager's data, but sets
    the refresh_max_age to a negative number. This makes the "exp" claim a time in the
    past, guaranteeing the token will always be expired.

    Args:
        auth_manager (:obj:`~flask_pyjwt.AuthManager`): The auth manager used to
            sign and provision tokens.
        username (:obj:`str`): Username to provision the refresh token to.

    Returns:
        :obj:`~flask_pyjwt.JWT`: The expired refresh token.
    """
    signer = AuthData(
        auth_manager.signer.auth_type,
        auth_manager.signer.secret,
        auth_manager.signer.issuer,
        auth_manager.signer.auth_max_age,
        -600,
        auth_manager.signer.public_key,
    )
    auth_token = JWT(TokenType.AUTH, username)
    auth_token.sign(signer)
    return auth_token


def populate_database_with_users(
    db_session, extra_username: t.Optional[str] = None
) -> None:
    """Populates the test database with fake users.

    Args:
        db_session: The Database session fixture.
        extra_username (:obj:`str`): An optional extra user to create with the
            given username.
    """
    for _ in range(0, 10):
        username = create_random_username()
        db_session.add(GifSyncUser(username=username))
    if extra_username:
        db_session.add(GifSyncUser(username=extra_username))
    db_session.commit()


def populate_users_with_gifs(db_session) -> None:
    """Populates the test database and S3 bucket with gifs.

    Args:
        db_session: The Database session fixture.
    """
    users = GifSyncUser.get_all()
    for user in users:
        test_image_path = pathlib.Path(__file__).parent.resolve() / "test-image.gif"
        for _ in range(0, 4):
            with open(test_image_path, "rb") as image_file:
                image_bytes = image_file.read()
                image_name = s3.add_image(image_bytes)
            gif = Gif(
                name=create_random_username(),
                owner=user,
                image=image_name,
                beats_per_loop=random.randint(1, 12),
            )
            db_session.add(gif)
    db_session.commit()
