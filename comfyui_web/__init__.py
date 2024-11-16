import os
from flask import Flask
from werkzeug.utils import import_string
from .routes import comfyui_bp


def create_app():
    app = Flask(__name__)

    # 注册蓝图
    app.register_blueprint(comfyui_bp)

    # get flask environment variable
    e = os.environ.get('FLASK_ENV', 'production')  # default flask environment is production

    # set running mode
    if e == 'dev':
        cfg_name = 'comfyui_web.config.DevelopmentConfig'
    elif e == 'testing':
        cfg_name = 'comfyui_web.config.TestingConfig'
    else:  # production as default
        cfg_name = 'comfyui_web.config.ProductionConfig'

    # load configration
    cfg = import_string(cfg_name)()
    app.config.from_object(cfg)


    return app
