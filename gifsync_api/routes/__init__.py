"""Resources module containing all blueprints for the GifSync API routes."""
from .auth import auth_blueprint
from .gifs import gifs_blueprint
from .tasks import tasks_blueprint
from .users import users_blueprint

# Helper variable for easy importing
blueprints = [auth_blueprint, gifs_blueprint, tasks_blueprint, users_blueprint]
