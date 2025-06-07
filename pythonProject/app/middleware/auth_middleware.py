"""
Authentication Middleware - Handle user authentication and bank identification
"""

from functools import wraps
from flask import session, request, jsonify, g, current_app
from app.models import User, db
from app.utils.hmac_generator import verify_hmac, generate_nack_response

def get_current_user():
    """Get current authenticated user"""
    if hasattr(g, 'current_user'):
        return g.current_user
    
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        g.current_user = user
        return user
    return None

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify(generate_nack_response('Authentication required')), 401
            
        user = get_current_user()
        if not user:
            return jsonify(generate_nack_response('User not found')), 404
            
        # Add user to request context
        g.current_user = user
        
        # Log authenticated request
        current_app.logger.info(f'Authenticated request by {user.name}: {request.method} {request.path}')
        
        return f(*args, **kwargs)
    return decorated_function

def validate_bank_request(f):
    """Decorator to validate inter-bank requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        bank_code = request.headers.get('X-Bank-Code')
        if not bank_code:
            return jsonify(generate_nack_response('Bank identification required')), 400
            
        # Load banks configuration
        from flask import current_app
        banks_config = current_app.config.get('BANKS', {})
        
        if bank_code not in banks_config:
            return jsonify(generate_nack_response('Invalid bank code')), 403
            
        # Add bank info to request context
        g.bank_info = {
            'code': bank_code,
            'name': banks_config[bank_code]['name'],
            'url': banks_config[bank_code]['url']
        }
        
        # Log bank request
        current_app.logger.info(f'Bank request from {bank_code}: {request.method} {request.path}')
        
        return f(*args, **kwargs)
    return decorated_function

def require_sinpe_auth(f):
    """Decorator to require SINPE authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for SINPE-specific headers
        sinpe_token = request.headers.get('X-SINPE-Token')
        if not sinpe_token:
            return jsonify(generate_nack_response('SINPE authentication required')), 401
            
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify(generate_nack_response('Request data required')), 400
            
        # Validate HMAC signature
        from app.utils.hmac_generator import verify_hmac, generate_nack_response
        signature = request.headers.get('X-SINPE-Signature')
        if not signature or not verify_hmac(data, signature):
            return jsonify(generate_nack_response('Invalid SINPE signature')), 403
            
        # Log SINPE request
        current_app.logger.info(f'SINPE request: {request.method} {request.path}')
        current_app.logger.debug(f'SINPE payload: {data}')
        
        return f(*args, **kwargs)
    return decorated_function
