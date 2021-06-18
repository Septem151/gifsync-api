"""Testing utils for generating data."""
import typing as t
import uuid

from flask_pyjwt import JWT, AuthData, AuthManager, TokenType
from sqlalchemy.orm.scoping import scoped_session as Session


def create_random_username() -> str:
    """Creates and returns a random username.

    Returns:
        :obj:`str`: The random username.
    """
    return str(uuid.uuid4())


def create_expired_auth_token(auth_manager: AuthManager, username: str) -> JWT:
    """Creates and returns an expired auth token with a "sub" of the username given.

    Works by creating a new signer object based on the auth_manager's data, but sets
    the auth_max_age to a negative number. This makes the "exp" claim a time in the
    past, guaranteeing the token will always be expired.

    Args:
        auth_manager (:obj:`~flask_pyjwt.AuthManager`): The auth manager used to
            sign and provision tokens.
        username (:obj:`str`): Username to provision the auth token to.

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
    auth_token = JWT(TokenType.AUTH, username)
    auth_token.sign(signer)
    return auth_token


def create_expired_refresh_token(auth_manager: AuthManager, username: str) -> JWT:
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
    db_session: Session, extra_username: t.Optional[str] = None
) -> None:
    """Populates the test database with fake users.

    Args:
        db_session (:obj:`~sqlalchemy.orm.scoping.Session`): The Database Session
            fixture.
    """
    # TODO: Write this function.
