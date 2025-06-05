# -*- encoding: utf-8 -*-
"""
App Init - cấu hình Flask app
"""

import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module

# Khởi tạo SQLAlchemy và LoginManager
db = SQLAlchemy()
login_manager = LoginManager()

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)

def register_blueprints(app):
    modules = {
        'authentication': 'blueprint',
        'home': 'blueprint',
        'dyn_dt': 'blueprint',
        'charts': 'charts_blueprint',
        'jobs': 'jobs_blueprint',
        'list_seeker': 'list_seeker_blueprint',
        'admin': 'admin_blueprint',
        'notifications': 'notifications_blueprint' 
    }

    for module_name, blueprint_name in modules.items():
        module = import_module(f'apps.{module_name}.routes')
        app.register_blueprint(getattr(module, blueprint_name))

def create_app(config):
    # Cấu hình thư mục tĩnh và template
    static_prefix = '/static'
    templates_dir = os.path.dirname(config.BASE_DIR)

    TEMPLATES_FOLDER = os.path.join(templates_dir, 'templates')
    STATIC_FOLDER = os.path.join(templates_dir, 'static')

    print(' > TEMPLATES_FOLDER: ' + TEMPLATES_FOLDER)
    print(' > STATIC_FOLDER:    ' + STATIC_FOLDER)

    app = Flask(__name__, static_url_path=static_prefix,
                template_folder=TEMPLATES_FOLDER,
                static_folder=STATIC_FOLDER)

    app.config.from_object(config)

    register_extensions(app)
    register_blueprints(app)

    return app
