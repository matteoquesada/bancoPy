"""
SINPE Banking System Flask Application Factory
"""

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from app.models import db
import os

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Get the project root directory (where main.py is located)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Ensure database directory exists
    db_dir = os.path.join(project_root, 'database')
    os.makedirs(db_dir, exist_ok=True)
    
    # Configuration with absolute path
    db_path = os.path.join(db_dir, 'banking.db')
    app.config['SECRET_KEY'] = 'supersecreta123'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure CORS
    CORS(app, 
         origins=["http://localhost:5173", "http://127.0.0.1:5173"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=True)
    
    # Register blueprints
    from app.routes.sinpe_routes import sinpe_bp
    from app.routes.user_routes import user_bp
    from app.routes.account_routes import account_bp
    from app.routes.transaction_routes import transaction_bp
    from app.routes.phone_link_routes import phone_link_bp
    from app.routes.auth_routes import auth_bp
    
    app.register_blueprint(sinpe_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(account_bp, url_prefix='/api')
    app.register_blueprint(transaction_bp, url_prefix='/api')
    app.register_blueprint(phone_link_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'SINPE Banking System API'}
    
    return app