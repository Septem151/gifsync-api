"""Resource route definitions for /tasks"""
from flask import Blueprint

tasks_blueprint = Blueprint("tasks", __name__, url_prefix="/tasks")
