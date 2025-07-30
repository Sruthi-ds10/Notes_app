# app/__init__.py

import os
from dotenv import load_dotenv
load_dotenv()  # ✅ Load .env variables at app startup

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from .config import Config
from .models import db, User

migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Redirect to login if not authenticated

    # Register blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app

# ✅ Load user from session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
