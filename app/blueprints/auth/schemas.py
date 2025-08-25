from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from app.models.user import User

class RegisterSchema(Schema):
    username = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=20))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=20))

    @validates_schema
    def validate_name(self, data, **kwargs):
        if User.find_by_name(data['username']):
            raise ValidationError("Username already registered")

class LoginSchema(Schema):
    username = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=20))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=20))

class AccessTokenSchema(Schema):
    access_token = fields.String(required=True, dump_only=True, validate=validate.Length(min=32))

#class ForgotPasswordSchema(Schema):
#class ResetPasswordSchema(Schema):
