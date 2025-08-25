from flask_smorest import Blueprint

user_bp = Blueprint('user', __name__, url_prefix='/api/users')

from . import routes
