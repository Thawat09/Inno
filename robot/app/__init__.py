from flask import Flask
from app.config import Config
from app.routes import webhook_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    app.register_blueprint(webhook_bp)
    
    return app