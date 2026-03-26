"""Auth Service — JWT authentication, user registration, and RBAC."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from flask_cors import CORS
import bcrypt
from database.models import User, AuditLog, get_session
from utils.auth import init_auth, generate_token, token_required, role_required
from config.settings import Config

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
init_auth(Config.JWT_SECRET)


def get_db():
    return get_session(Config.DATABASE_URL)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'auth_service'})


@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user. Only ADMIN can create non-LAB_TECH roles."""
    data = request.get_json()
    required = ['email', 'password', 'full_name']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields: email, password, full_name'}), 400

    db = get_db()
    try:
        existing = db.query(User).filter_by(email=data['email']).first()
        if existing:
            return jsonify({'error': 'Email already registered'}), 409

        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        role = data.get('role', 'LAB_TECH')
        if role not in ('ADMIN', 'RADIOLOGIST', 'PHYSICIAN', 'LAB_TECH'):
            return jsonify({'error': 'Invalid role'}), 400

        user = User(
            email=data['email'],
            password_hash=password_hash,
            full_name=data['full_name'],
            role=role,
            department=data.get('department', '')
        )
        db.add(user)
        db.commit()

        token = generate_token(user.id, user.email, user.role)
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'token': token
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    db = get_db()
    try:
        user = db.query(User).filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account is deactivated. Contact administrator.'}), 403

        if not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({'error': 'Invalid email or password'}), 401

        token = generate_token(user.id, user.email, user.role)

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action='LOGIN',
            resource_type='user',
            resource_id=user.id,
            ip_address=request.remote_addr
        )
        db.add(audit)
        db.commit()

        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current authenticated user's profile."""
    db = get_db()
    try:
        user = db.query(User).filter_by(id=request.user['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'user': user.to_dict()}), 200
    finally:
        db.close()


@app.route('/api/auth/users', methods=['GET'])
@role_required('ADMIN')
def list_users():
    """List all users (Admin only)."""
    db = get_db()
    try:
        users = db.query(User).all()
        return jsonify({'users': [u.to_dict() for u in users]}), 200
    finally:
        db.close()


@app.route('/api/auth/users/<user_id>/toggle', methods=['PATCH'])
@role_required('ADMIN')
def toggle_user(user_id):
    """Activate/deactivate user (Admin only)."""
    db = get_db()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user.is_active = not user.is_active
        db.commit()
        return jsonify({'message': f'User {"activated" if user.is_active else "deactivated"}', 'user': user.to_dict()})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
