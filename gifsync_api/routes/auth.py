"""Resource route definitions for /auth and its sub-resources."""
import secrets

import requests

from flask import Blueprint, current_app, make_response, request
from flask_pyjwt import current_token, require_token

from ..extensions import auth_manager
from ..representations import AuthToken

auth_blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@auth_blueprint.route("/token", methods=["POST"])
def token_route():
    """POST /auth/token

    Returns a new GifSync API Auth Token based on an (optional) Spotify API Token
    provided, and sets a refresh_token cookie containing a GifSync API refresh token.
    """
    sub: str = secrets.token_urlsafe(16)
    scope = {"admin": False, "spotify": False}
    req_json = request.get_json()
    if req_json and "spotify_token" in req_json:
        spotify_token = req_json["spotify_token"]
        resp = requests.get(
            "https://api.spotify.com/v1/me",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {spotify_token}",
            },
        )
        if resp.status_code == 200:
            sub = resp.json()["id"]
            scope["spotify"] = True
    auth_token = auth_manager.auth_token(sub, scope)
    refresh_token = auth_manager.refresh_token(sub)
    response = make_response(AuthToken(auth_token).to_json())
    response.set_cookie(
        "refresh_token",
        refresh_token.signed,
        refresh_token.max_age,
        path="/auth/refresh",
        domain=current_app.config["DOMAIN"],
        secure=True,
        httponly=True,
    )
    return response, 200


@auth_blueprint.route("/refresh", methods=["POST"])
@require_token("refresh", "cookies", "refresh_token")
def refresh_route():
    """POST /refresh

    Refreshes an auth token if provided a valid refresh token.
    """
    auth_token = auth_manager.auth_token(current_token.sub)
    # TODO: Query for user's scope
    return AuthToken(auth_token).to_json(), 200
