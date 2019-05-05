from flask import Flask


def create_app():
    from . import database
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py')
    database.init_app(app)

    from . import wechat_api
    wechat_api.init_app(app)

    from . import web_app
    app.register_blueprint(web_app.bp)
    # app.register_error_handler(404, web_app.page_not_found)
    # app.register_error_handler(500, web_app.server_error)

    return app
