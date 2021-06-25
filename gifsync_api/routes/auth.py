"""Resource route definitions for /auth and its sub-resources."""
from flask import Blueprint
from flask_pyjwt import JWT

auth_blueprint = Blueprint("auth", __name__, url_prefix="/auth")


def format_token_response(auth_token: JWT) -> dict:
    """Formats a JWT's information into the correct API response structure.

    Args:
        auth_token (:obj:`~flask_pyjwt.JWT`): The JWT to format information from.

    Returns:
        :obj:`dict`: API response structure.

    API response structure is::

        {
            "token": str,
            "username": str,
            "scope": {
                "admin": bool,
                "spotify": bool
            },
            "expires_in": int
        }

    """
    return {
        "token": auth_token.signed,
        "username": auth_token.sub,
        "scope": auth_token.scope,
        "expires_in": auth_token.max_age,
    }
