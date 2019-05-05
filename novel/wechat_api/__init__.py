from flask_restful import Api


def init_app(app):
    from .api import Login, Author_, Book_, Star_, Search_
    api = Api(app)
    api.add_resource(Login, '/api/login')
    api.add_resource(Author_, '/api/authors')
    api.add_resource(Search_, '/api/s')
    api.add_resource(Book_, '/api/books')
    api.add_resource(Star_, '/api/stars')
