"""Resource route definitions for /users"""
import typing as t
from http import HTTPStatus

from flask import Blueprint, request
from flask_pyjwt import current_token, require_token

from ..extensions import db
from ..models import GifSyncUser, Role

users_blueprint = Blueprint("users", __name__, url_prefix="/users")


@users_blueprint.route("", methods=["GET"])
@require_token(scope={"admin": True})
def get_users_route():
    """GET /users

    Returns a list of all users. Only accessible by admins.
    """
    users: t.List[GifSyncUser] = GifSyncUser.query.all()
    return {"users": [user.to_json() for user in users]}, 200


@users_blueprint.route("", methods=["POST"])
@require_token()
def post_users_route():
    """POST /users

    Returns 201 Created if user is new, otherwise 200 OK.
    """
    user_json: t.Optional[dict] = request.get_json()
    if not user_json:
        return {"error": "Missing user in POST body"}, HTTPStatus.BAD_REQUEST
    if "username" not in user_json:
        return {
            "error": "Missing required parameter in POST body"
        }, HTTPStatus.BAD_REQUEST
    username = user_json["username"]
    is_admin_token = current_token.scope.get("admin")
    if not is_admin_token and username != current_token.sub:
        return {"error": "Auth token does not match given user"}, HTTPStatus.FORBIDDEN
    user: GifSyncUser = GifSyncUser.query.filter_by(username=username).first()
    return_code = HTTPStatus.OK
    if not user:
        user = GifSyncUser(username=username)
        return_code = HTTPStatus.CREATED
    scope = user_json.get("scope")
    spotify_role = Role.query.filter_by(name="spotify").first()
    admin_role = Role.query.filter_by(name="admin").first()
    if is_admin_token and scope:
        if (
            "spotify" in scope
            and bool(scope["spotify"])
            and not user.has_role("spotify")
        ):
            user.roles.append(spotify_role)
        if "admin" in scope and bool(scope["admin"]) and not user.has_role("admin"):
            user.roles.append(admin_role)
    else:
        if (
            "spotify" in scope
            and bool(scope["spotify"])
            and not user.has_role("spotify")
        ):
            user.roles.append(spotify_role)
        elif (
            "spotify" in scope
            and not bool(scope["spotify"])
            and user.has_role("spotify")
        ):
            user.roles.remove(spotify_role)
    db.session.add(user)
    db.session.commit()
    return {"user": user.to_json()}, return_code


@users_blueprint.route("", methods=["DELETE"])
@require_token(scope={"admin": True})
def delete_users_route():
    """DELETE /users

    Deletes all users. Only accessible by admin.
    """
    GifSyncUser.query.delete()
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
    user: t.Optional[GifSyncUser] = GifSyncUser.query.filter_by(
        username=username
    ).first()
    if not user:
        return {"error": "User not found"}, HTTPStatus.NOT_FOUND
    return {"user": user.to_json()}, HTTPStatus.OK


@users_blueprint.route("/<string:username>", methods=["POST"])
@require_token(sub="username", override={"scope": {"admin": True}})
def post_user_route(username: str):
    """POST /users/<username>

    Modify a user with the specified username.

    Args:
        username (:obj:`str`): Username of user modify.
    """
    user: t.Optional[GifSyncUser] = GifSyncUser.query.filter_by(
        username=username
    ).first()
    if not user:
        return {"error": "User not found"}, HTTPStatus.NOT_FOUND
    new_user_info = request.get_json()
    token_scope = current_token.scope
    if new_user_info:
        new_username = new_user_info.get("username")
        new_scope = new_user_info.get("scope")
        if new_username:
            user.username = new_username
        if new_scope and new_scope.get("spotify"):
            spotify_role = Role.query.filter_by(name="spotify").first()
            if bool(new_scope["spotify"]) and not user.has_role("spotify"):
                user.roles.append(spotify_role)
            elif not bool(new_scope["spotify"]) and user.has_role("spotify"):
                user.roles.remove(spotify_role)
        if (
            new_scope
            and new_scope.get("admin")
            and bool(token_scope.scope.get("admin"))  # type: ignore
            and not user.has_role("admin")
        ):
            user.roles.append(Role.query.filter_by(name="admin").first())
    db.session.commit()
    return {"user": user.to_json()}, HTTPStatus.OK
