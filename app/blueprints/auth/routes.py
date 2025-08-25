from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import auth_bp
from .schemas import RegisterSchema, LoginSchema, AccessTokenSchema
from .services import AuthService

@auth_bp.route('/register', methods=['POST'])
@auth_bp.arguments(RegisterSchema)
@auth_bp.response(201)
def register(data):
    """用户注册接口"""
    AuthService.register_user(data['username'], data['password'])

@auth_bp.route('/login', methods=['POST'])
@auth_bp.arguments(LoginSchema)
def login(data):
    """用户登录接口"""
    user = AuthService.authenticate_user(data['username'], data['password'])
    tokens = AuthService.create_tokens(user)
    return jsonify(tokens), 200

@auth_bp.route('/refresh', methods=['POST'])
@auth_bp.response(200, AccessTokenSchema)
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌接口"""
    user_id = get_jwt_identity()
    tokens = AuthService.refresh_access_token(user_id)
    return tokens
