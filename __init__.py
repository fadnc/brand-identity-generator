from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from celery import Celery
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
celery = Celery(__name__, broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Load configuration
    if config_name == 'production':
        app.config.from_object('app.config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('app.config.TestingConfig')
    else:
        app.config.from_object('app.config.DevelopmentConfig')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configure Celery
    celery.conf.update(app.config)
    
    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.projects import projects_bp
    from app.api.generation import generation_bp
    from app.api.analytics import analytics_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(generation_bp, url_prefix='/api/generate')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'brand-identity-generator'}, 200
    
    return app