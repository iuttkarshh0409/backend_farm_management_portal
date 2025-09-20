"""Application factory and configuration."""


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os


from config import config


# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)



def create_app(config_name=None):
    """Application factory."""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # CORS Configuration - UPDATED FOR REACT INTEGRATION
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",      # React dev server
                "http://127.0.0.1:3000",      # Alternative localhost
                "http://localhost:3001",      # Backup port
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": [
                "Content-Type", 
                "Authorization", 
                "Access-Control-Allow-Credentials",
                "Access-Control-Allow-Origin"
            ],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"]
        },
        r"/health": {
            "origins": [
                "http://localhost:3000",
                "http://127.0.0.1:3000", 
                "http://localhost:3001",
            ],
            "methods": ["GET", "OPTIONS"],
            "allow_headers": ["Content-Type", "Origin"]
        }
    })
    
    limiter.init_app(app)
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'message': 'Authorization token is required'}, 401
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request'}, 400
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    # Health check endpoint - Updated for React integration
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'Farm Management Portal API', 'message': 'Backend ready for React integration'}
    
    return app



# Import models to ensure they are registered with SQLAlchemy
from app.models import user, animal