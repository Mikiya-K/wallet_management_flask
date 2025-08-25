from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User
from app.errors.custom_errors import PermissionDeniedError

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.roles or not user.has_role('admin') :
            raise PermissionDeniedError("Admin access required")
        return fn(*args, **kwargs)
    return wrapper
