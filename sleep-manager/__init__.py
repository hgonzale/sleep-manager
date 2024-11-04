from flask import Flask
import json

from .waker import waker_bp
from .sleeper import sleeper_bp


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_file('config/sleep-manager-config.json', load=json.load, text=True)

    app.register_blueprint(waker_bp)
    app.register_blueprint(sleeper_bp)

    @app.route('/')
    def welcome():
        return 'Welcome to sleep manager!'

    return app
