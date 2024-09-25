from flask import Flask
from .routes import zabbix_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    app.register_blueprint(zabbix_bp)

    return app
