import math
from functools import wraps
import datetime

from flask import request
from flask_restful import Resource
import jwt
import requests


from database import db_session
from models import NovelInfo, UserInfo
from spider import get_book_info
from utils import new_novel, hash_session
from config import (
    SECRET_KEY,
    WECHAT_API,
    PAGE_SIZE,
    BOOK_STATUS,
    BOOK_TYPE,
    JWT_KEY
)


def auth_token(func):
    '''Verify token
    '''
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            token = request.headers['Authorization'].encode('utf-8')
            jwt.decode(token, JWT_KEY)
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}, 400
        except Exception:
            return {'error': 'Invalid token'}, 400
        return func(*args, **kwargs)
    return inner


class Login(Resource):
    '''Wechat login'''

    def get(self):
        code = request.args.get('code')
        url = WECHAT_API.format(code)
        wx_data = requests.get(url).json()
        try:
            session_id = hash_session(wx_data['openid'])
            user = UserInfo.query.filter_by(open_id=wx_data['openid']).first()
        except Exception:
            return {'error': 'Code invalid'}, 401
        if user:
            user.session_id = session_id
        else:
            user = UserInfo(session_id=session_id,
                            open_id=wx_data['openid'])
        db_session.add(user)
        db_session.commit()
        now = datetime.datetime.utcnow()
        payload = {
            'iss': 'rrcgat',
            'exp': now + datetime.timedelta(hours=3),
            'iat': now
        }
        token = jwt.encode(payload, JWT_KEY, algorithm='HS256')
        token = str(token, 'utf-8')
        return {
            'sid': session_id,
            'token': token
        }


class WIndex(Resource):
    '''Index of wechat'''

    @auth_token
    def get(self):
        page = int(request.args.get('page', 1))
        query = NovelInfo.query.order_by(NovelInfo.pub_date.desc())
        total = math.ceil(query.count() / PAGE_SIZE)
        books = query.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

        data = [book.json() for book in books]

        return {
            'books': data,
            'total': total
        }


class Novel(Resource):
    '''Novel api'''

    @auth_token
    def get(self):
        try:
            book_id = int(request.args.get('book_id', ''))
        except ValueError:
            return {'msg': 'Invalid parameter.'}, 400
        book = NovelInfo.query.filter_by(id=book_id).first()
        if not book:
            return {'msg': 'Book not found.'}, 404
        return book.to_json()

    @auth_token
    def post(self):
        content = request.get_json()

        book_name = content.get('book_name', '').strip()
        if not book_name:
            return {'error': '请输入书名'}, 400
        source_id = int(content.get('source_id'))
        exists = NovelInfo.query.filter_by(book_name=book_name,
                                           source_id=source_id).first()
        if exists:
            return {'msg': '书籍已存在'}

        # tag = content.get('tag')
        book_info = get_book_info(source_id, book_name)
        if not book_info:
            return {'error': f'《{book_name}》未找到'}, 404

        hero = content.get('hero', '').strip()
        heroine = content.get('heroine', '').strip()

        book_info['book_type'] = content.get('book_type')

        data = new_novel(book_info, hero, heroine)
        db_session.add(data)
        db_session.commit()
        return {'msg': '已记录'}, 201

    @auth_token
    def put(self):
        content = request.get_json()
        book = NovelInfo.query.filter_by(id=content.id,
                                         book_name=content.book_name).first()
        if not book:
            return {
                'error': 'Can not modify book name'
            }, 403

        book.hero = content.get('hero', '').strip()
        book.heroine = content.get('heroine', '').strip()
        book.tag = list(content.get('tag'))

        if int(content.get('status')) in BOOK_STATUS:
            book.status = int(content.get('status'))
        if int(content.get('book_type')) in BOOK_TYPE:
            book.book_type = int(content.get('book_type'))

        db_session.add(book)
        db_session.commit()
        return {
            'msg': 'Success',
        }
