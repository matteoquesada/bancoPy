"""
SINPE Banking System Flask Application Factory
"""

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from app.models import db
import os
import json
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app, project_root):
    """Configure application logging"""
    logs_dir = os.path.join(project_root, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'banco.log'), 
        maxBytes=10240, 
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Banco startup')

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Get the project root directory (where main.py is located)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Setup logging
    setup_logging(app, project_root)
    
    # Ensure database directory exists
    db_dir = os.path.join(project_root, 'database')
    os.makedirs(db_dir, exist_ok=True)
    
    # Configuration with absolute path
    db_path = os.path.join(db_dir, 'banking.db')
    app.config['SECRET_KEY'] = 'supersecreta123'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Load banks configuration
    banks_config_path = os.path.join(project_root, 'config', 'banks.json')
    with open(banks_config_path) as f:
        app.config['BANKS'] = json.load(f)
    
    # Configure session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    
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
    
    # Initialize session
    from flask_session import Session
    Session(app)
    
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
    
    # Log startup
    app.logger.info(f'Bank {app.config["BANKS"]["0666"]["name"]} initialized')
    
    return app
