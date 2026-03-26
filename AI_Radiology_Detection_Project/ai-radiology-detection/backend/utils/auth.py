"""Shared authentication and RBAC utilities for all microservices."""

import jwt
import functools
from datetime import datetime, timedelta
from flask import request, jsonify

JWT_SECRET = None  # Set by each service at startup


def init_auth(secret):
    global JWT_SECRET
    JWT_SECRET = secret


def generate_token(user_id, email, role, secret=None):
    """Generate a JWT token for authenticated user."""
    payload = {
        'user_id': str(user_id),
        'email': email,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, secret or JWT_SECRET, algorithm='HS256')


def decode_token(token):
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator: require valid JWT token for endpoint access."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        request.user = payload
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    """Decorator: restrict endpoint to specific user roles (RBAC)."""
    def decorator(f):
        @functools.wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            user_role = request.user.get('role')
            if user_role not in allowed_roles:
                return jsonify({
                    'error': f'You do not have permission to access this resource. Required role: {", ".join(allowed_roles)}'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
