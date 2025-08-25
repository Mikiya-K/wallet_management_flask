from flask import jsonify
from flask_jwt_extended import jwt_required
from . import user_bp
from .schemas import UserUpdateSchema, UserDeleteSchema
from .services import UserService
from app.utils.decorators import admin_required

@user_bp.route('', methods=['GET'])
@user_bp.paginate()
@jwt_required()
@admin_required
def list_users(pagination_parameters):
    """列出所有用户（管理员）"""
    users = UserService.list_users(pagination_parameters.page, pagination_parameters.page_size)
    pagination_parameters.item_count = users['total']

    # 序列化用户
    serialized_users = [user.to_dict() for user in users['items']]

    return jsonify({
        "users": serialized_users,
    }), 200

@user_bp.route('', methods=['PUT'])
@user_bp.arguments(UserUpdateSchema)
@user_bp.response(200)
@jwt_required()
@admin_required
def update_user(data):
    """更新用户的状态、角色及管理钱包（管理员）"""
    UserService.update_user(data)

@user_bp.route('', methods=['DELETE'])
@user_bp.arguments(UserDeleteSchema, location='query')
@user_bp.response(204)
@jwt_required()
@admin_required
def delete_user(data):
    """删除用户（管理员）"""
    UserService.delete_user(data['username'])
