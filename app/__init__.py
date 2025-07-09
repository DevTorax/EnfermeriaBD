# app/__init__.py
import os
from flask import Flask
from .config     import Config
from .extensions import db, migrate, ma
from .models     import init_models

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.getcwd(),'app','templates'))
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    with app.app_context():
        init_models()

    # register blueprints...
    from .api.upload_routes import upload_bp
    app.register_blueprint(upload_bp, url_prefix='')

    return app
