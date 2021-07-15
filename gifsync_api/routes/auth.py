"""Resource route definitions for /auth and its sub-resources."""
import secrets
import typing as t
from base64 import urlsafe_b64encode
from http import HTTPStatus

import requests

from flask import Blueprint, current_app, make_response, request
from flask_pyjwt import current_token, require_token

from ..extensions import auth_manager, db
from ..models import Gif, GifSyncUser
from ..representations import AuthToken, SpotifyAuthToken

auth_blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@auth_blueprint.route("/token", methods=["POST"])
def token_route():  # pylint: disable=too-many-locals
    """POST /auth/token

    Returns a new GifSync API Auth Token based on an (optional) Spotify API Token
    provided, and sets a refresh_token cookie containing a GifSync API refresh token.
    """
    sub: str = secrets.token_urlsafe(16)
    old_sub: t.Optional[str] = None
    user: t.Optional[GifSyncUser] = None
    scope = {"admin": False, "spotify": False}
    req_json: t.Optional[dict] = request.get_json()
    if req_json and "spotify_token" in req_json:
        # Spotify login token requested
        spotify_token: str = req_json["spotify_token"]
        spotify_resp = requests.get(
            "https://api.spotify.com/v1/me",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {spotify_token}",
            },
        )
        resp_json: dict = spotify_resp.json()
        resp_status = spotify_resp.status_code
        if resp_status == 200:
            # Spotify token is valid
            sub = resp_json["id"]
            scope["spotify"] = True
        else:
            # Spotify token was invalid
            return {
                "error": f"Error from Spotify API: {resp_status}",
                "spotify_error": resp_json,
            }, resp_status
        auto_token = request.cookies.get("auto_token")
        if auto_token and auth_manager.verify_token(auto_token):
            # auto_token cookie was present
            old_auth_token = auth_manager.convert_token(auto_token)
            # set old sub to check for existing user
            old_sub = old_auth_token.sub
        user = GifSyncUser.get_by_username(sub)
        old_user: t.Optional[GifSyncUser] = GifSyncUser.get_by_username(old_sub)
        if user and old_user:
            # User signed in with spotify and already had existing anon user
            old_user_gifs: t.List[Gif] = old_user.gifs
            # Transfer anon user's gifs to spotify user
            for gif in old_user_gifs:
                gif.user_id = user.id
            db.session.commit()
            # Delete old user
            db.session.delete(old_user)
        elif old_user:
            # Already had existing anon user but no spotify user
            user = old_user
            user.username = sub
        elif not user:
            # User had no previous accounts but signed in with Spotify
            # Create new user
            user = GifSyncUser(username=sub)
            # Add spotify role
            user.set_role("spotify", True)
            db.session.add(user)
        db.session.commit()
    if user:
        # User already existed, put admin role on token's scope if admin
        scope["admin"] = user.has_role("admin")
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
    # Set auto_token cookie if signing in as anon user
    # Otherwise delete the auto_token cookie
    response.set_cookie(
        "auto_token",
        auth_token.signed if not scope["spotify"] else "",
        auth_token.max_age if not scope["spotify"] else 0,
        expires=None if not scope["spotify"] else 0,
        path="/auth/token",
        domain=current_app.config["DOMAIN"],
        secure=True,
        httponly=True,
    )
    return response, HTTPStatus.OK


@auth_blueprint.route("/refresh", methods=["POST"])
@require_token("refresh", "cookies", "refresh_token")
def refresh_route():
    """POST /auth/refresh

    Refreshes an auth token if provided a valid refresh token.
    """
    scope = {"admin": False, "spotify": False}
    user: t.Optional[GifSyncUser] = GifSyncUser.get_by_username(current_token.sub)
    if user:
        scope["admin"] = user.has_role("admin")
        scope["spotify"] = user.has_role("spotify")
    auth_token = auth_manager.auth_token(current_token.sub, scope)
    return AuthToken(auth_token).to_json(), HTTPStatus.OK


@auth_blueprint.route("/spotify/token", methods=["POST"])
def spotify_token_route():
    """POST /auth/spotify/token

    Returns a Spotify token when given a Spotify API auth code, and sets a
    spotify_refresh_token cookie containing a spotify refresh token.
    """
    req_json = request.get_json()
    if not req_json or not "code" in req_json:
        return {"error": "Missing required parameter"}, HTTPStatus.BAD_REQUEST
    code = req_json["code"]
    client_id = current_app.config["CLIENT_ID"]
    client_secret = current_app.config["CLIENT_SECRET"]
    auth_payload = urlsafe_b64encode(
        ":".join([client_id, client_secret]).encode("utf-8")
    ).decode("utf-8")
    spotify_resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_payload}",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": current_app.config["REDIRECT_URI"],
        },
    )
    resp_json = spotify_resp.json()
    resp_status = spotify_resp.status_code
    if resp_status != 200:
        return {
            "error": f"Error from Spotify API: {resp_status}",
            "spotify_error": resp_json,
        }, resp_status
    spotify_refresh_token = resp_json["refresh_token"]
    token = SpotifyAuthToken(resp_json["access_token"], int(resp_json["expires_in"]))
    resp = make_response(token.to_json())
    resp.set_cookie(
        "spotify_refresh_token",
        spotify_refresh_token,
        max_age=15768000,
        path="/auth/spotify/refresh",
        domain=current_app.config["DOMAIN"],
        secure=True,
        httponly=True,
    )
    return resp, HTTPStatus.OK


@auth_blueprint.route("/spotify/refresh", methods=["POST"])
def spotify_refresh_route():
    """POST /auth/spotify/refresh

    Returns a Spotify token when given a Spotify API refresh token as a cookie called
    "spotify_refresh_token", and sets a spotify_refresh_token cookie containing a
    new Spotify refresh token if the Spotify API returns a new refresh token.
    """
    token_cookie = request.cookies.get("spotify_refresh_token")
    if not token_cookie:
        return {
            "error": "Missing Spotify refresh token cookie"
        }, HTTPStatus.UNAUTHORIZED
    client_id = current_app.config["CLIENT_ID"]
    client_secret = current_app.config["CLIENT_SECRET"]
    auth_payload = urlsafe_b64encode(
        ":".join([client_id, client_secret]).encode("utf-8")
    ).decode("utf-8")
    spotify_resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_payload}",
        },
        data={"grant_type": "refresh_token", "refresh_token": token_cookie},
    )
    resp_json = spotify_resp.json()
    resp_status = spotify_resp.status_code
    if resp_status != 200:
        return {
            "error": f"Error from Spotify API: {resp_status}",
            "spotify_error": resp_json,
        }, resp_status
    token = SpotifyAuthToken(resp_json["access_token"], int(resp_json["expires_in"]))
    resp = make_response(token.to_json())
    if "refresh_token" in resp_json:
        resp.set_cookie(
            "spotify_refresh_token",
            resp_json["refresh_token"],
            max_age=15768000,
            path="/auth/spotify/refresh",
            domain=current_app.config["DOMAIN"],
            secure=True,
            httponly=True,
        )
    return resp, HTTPStatus.OK


@auth_blueprint.route("/logout", methods=["POST"])
@require_token()
def logout_route():
    """POST /auth/logout

    Deletes a refresh_token, auto_token, and spotify_refresh_token cookie,
    which essentially logs out the user (provided the frontend deletes auth tokens)
    """
    resp = make_response("")
    resp.set_cookie(
        "refresh_token",
        "",
        max_age=0,
        expires=0,
        path="/auth/refresh",
        domain=current_app.config["DOMAIN"],
        secure=True,
        httponly=True,
    )
    resp.set_cookie(
        "auto_token",
        "",
        max_age=0,
        expires=0,
        path="/auth/token",
        domain=current_app.config["DOMAIN"],
        secure=True,
        httponly=True,
    )
    resp.set_cookie(
        "spotify_refresh_token",
        "",
        max_age=0,
        expires=0,
        path="/auth/spotify/refresh",
        domain=current_app.config["DOMAIN"],
        secure=True,
        httponly=True,
    )
    return resp, HTTPStatus.NO_CONTENT
