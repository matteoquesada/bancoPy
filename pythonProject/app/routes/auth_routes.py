"""
Authentication Routes - API endpoints for authentication
"""

from flask import Blueprint, request, jsonify, session
from app.models import User
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        if 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = User.query.filter_by(name=data['username']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Store user session (simplified)
        session['user_id'] = user.id
        session['username'] = user.name
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/me', methods=['GET'])
def get_current_user():
    """Get current authenticated user"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    try:
        authenticated = 'user_id' in session
        
        return jsonify({
            'authenticated': authenticated,
            'user_id': session.get('user_id'),
            'username': session.get('username')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/current-user', methods=['GET'])
def get_current_user_info():
    """Get detailed current user information"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user accounts with phone links
        from app.services.sinpe_service import SinpeService
        accounts = SinpeService.get_user_accounts_with_phone_links(user.name)
        
        user_data = user.to_dict()
        user_data['accounts'] = accounts
        user_data['bank_code'] = '152'  # Local bank code
        user_data['bank_name'] = 'Local Bank'
        
        return jsonify({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
