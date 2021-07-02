"""Resource route definitions for /users"""
import typing as t
from http import HTTPStatus

from flask import Blueprint
from flask_pyjwt import require_token

from ..extensions import db
from ..models import GifSyncUser

users_blueprint = Blueprint("users", __name__, url_prefix="/users")


@users_blueprint.route("", methods=["GET"])
@require_token(scope={"admin": True})
def get_users_route():
    """GET /users

    Returns a list of all users. Only accessible by admins.
    """
    users: t.List[GifSyncUser] = GifSyncUser.get_all()
    return {"users": [user.to_json() for user in users]}, 200


@users_blueprint.route("", methods=["DELETE"])
@require_token(scope={"admin": True})
def delete_users_route():
    """DELETE /users

    Deletes all users. Only accessible by admin.
    """
    GifSyncUser.delete_all()
    db.session.commit()
    return "", 204


@users_blueprint.route("/<string:username>", methods=["GET"])
@require_token(sub="username", override={"scope": {"admin": True}})
def get_user_route(username: str):
    """GET /users/<username>

    Retrieve a user with the specified username.

    Args:
        username (:obj:`str`): Username of user to look up.
    """
    user: t.Optional[GifSyncUser] = GifSyncUser.get_by_username(username)
    if not user:
        return {"error": "User not found"}, HTTPStatus.NOT_FOUND
    return {"user": user.to_json()}, HTTPStatus.OK


@users_blueprint.route("/<string:username>", methods=["DELETE"])
@require_token(sub="username", override={"scope": {"admin": True}})
def delete_user_route(username: str):
    """DELETE /users/<username>

    Deletes a user with the specified username.

    Args:
        username (:obj:`str`): Username of user to delete.
    """
    user: t.Optional[GifSyncUser] = GifSyncUser.get_by_username(username)
    if not user:
        return {"error": "User not found"}, HTTPStatus.NOT_FOUND
    db.session.delete(user)
    db.session.commit()
    return "", HTTPStatus.NO_CONTENT
