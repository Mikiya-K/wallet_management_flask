from flask_smorest import Blueprint

wallet_bp = Blueprint('wallet', __name__, url_prefix='/api/wallets')

from . import routes
