"""Resource route definitions for /gifs"""
import typing as t
from http import HTTPStatus

from flask import Blueprint, request
from flask_pyjwt import current_token, require_token

from ..extensions import db, s3
from ..models import Gif, GifSyncUser

gifs_blueprint = Blueprint("gifs", __name__, url_prefix="/gifs")


@gifs_blueprint.route("", methods=["GET"])
@require_token(scope={"admin": True})
def get_gifs_route():
    """GET /gifs

    Returns a list of all gifs. Only accessible by admins.
    """
    gifs = Gif.get_all()
    return {"gifs": [gif.to_json() for gif in gifs]}, HTTPStatus.OK


@gifs_blueprint.route("", methods=["POST"])
@require_token()
def post_gifs_route():
    """POST /gifs

    Posts a new gif. If the user with a username of "sub" of the auth token
    does not exist, create the user.
    """
    gif_name: t.Optional[str] = request.form.get("name")
    beats_per_loop: t.Optional[int] = request.form.get("beats_per_loop")
    image_data = request.files.get("image")
    if not gif_name or not beats_per_loop or not image_data:
        return {
            "error": "missing required parameter in request body"
        }, HTTPStatus.BAD_REQUEST
    filename: str = image_data.filename
    if not ("." in filename and filename.rsplit(".", 1)[1].lower() == "gif"):
        return {"error": "only gifs can be uploaded"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    username: str = current_token.sub
    user = GifSyncUser.get_by_username(username)
    if not user:
        user = GifSyncUser(username=username)
        db.session.add(user)
        db.session.commit()
    for user_gif in user.gifs:
        if user_gif.name == gif_name:
            return {"error": "duplicate gif name"}, HTTPStatus.BAD_REQUEST
    try:
        image_bytes = image_data.stream.read()
        image_name = s3.add_image(image_bytes)
    except RuntimeError:
        return {"error": "unable to upload gif"}, HTTPStatus.INTERNAL_SERVER_ERROR
    gif = Gif(
        name=gif_name, owner=user, beats_per_loop=beats_per_loop, image=image_name
    )
    db.session.add(gif)
    db.session.commit()
    return gif.to_json(), HTTPStatus.CREATED


@gifs_blueprint.route("", methods=["DELETE"])
@require_token(scope={"admin": True})
def delete_gifs_route():
    """DELETE /gifs

    Deletes all gifs. Only accessible by admins.
    """
    Gif.delete_all()
    db.session.commit()
    return "", HTTPStatus.NO_CONTENT


@gifs_blueprint.route("/<int:gif_id>", methods=["GET"])
@require_token()
def get_gif_route(gif_id: int):
    """GET /gifs/<gif_id>

    Gets a gif with specified gif id. Token's "sub" must match
    owner's username of the gif, unless an admin.

    Args:
        gif_id (:obj:`int`): The gif id to get.
    """
    gif = Gif.get_by_id(gif_id)
    if not gif:
        return {"error": f"Gif with the id {gif_id} not found"}, HTTPStatus.NOT_FOUND
    token_username: str = current_token.sub  # type: ignore
    if (
        not bool(current_token.scope["admin"])  # type: ignore
        and gif.owner.username != token_username
    ):
        return {
            "error": "unable to access gif owned by another user"
        }, HTTPStatus.FORBIDDEN
    return gif.to_json(), HTTPStatus.OK


@gifs_blueprint.route("/<int:gif_id>", methods=["POST"])
@require_token()
def post_gif_route(gif_id: int):  # pylint: disable=too-many-return-statements
    """POST /gifs/<gif_id>

    Modifies a gif with specified gif id. Token's "sub" must match
    owner's username of the gif, unless an admin.

    Args:
        gif_id (:obj:`int`): The gif id to modify.
    """
    gif = Gif.get_by_id(gif_id)
    if not gif:
        return {"error": f"Gif with the id {gif_id} not found"}, HTTPStatus.NOT_FOUND
    token_username: str = current_token.sub  # type: ignore
    if (
        not bool(current_token.scope["admin"])  # type: ignore
        and gif.owner.username != token_username
    ):
        return {
            "error": "unable to modify gif owned by another user"
        }, HTTPStatus.FORBIDDEN
    req_json: t.Optional[dict] = request.get_json()
    if not req_json:
        return {"error": "missing request body"}, HTTPStatus.BAD_REQUEST
    if "name" in req_json:
        gif_name = req_json["name"]
        for user_gif in gif.owner.gifs:
            if user_gif.name == gif_name:
                return {"error": "duplicate gif name"}, HTTPStatus.BAD_REQUEST
        gif.name = gif_name
    if "beats_per_loop" in req_json:
        beats_per_loop = req_json["beats_per_loop"]
        if not isinstance(beats_per_loop, (int, float)):
            return {"error": "beats_per_loop must be a number"}, HTTPStatus.BAD_REQUEST
        gif.beats_per_loop = beats_per_loop
    if "custom_tempo" in req_json:
        custom_tempo = req_json["custom_tempo"]
        if not isinstance(custom_tempo, (int, float)):
            return {"error": "custom_tempo must be a number"}, HTTPStatus.BAD_REQUEST
        gif.custom_tempo = custom_tempo
    db.session.commit()
    return gif.to_json(), HTTPStatus.OK
