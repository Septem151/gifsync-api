"""Resource route definitions for /gifs"""
from flask import Blueprint

gifs_blueprint = Blueprint("gifs", __name__, url_prefix="/gifs")
