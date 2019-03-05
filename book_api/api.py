import math
from functools import wraps
import datetime

from flask import request
from flask_restful import Resource
import jwt
import requests
from sqlalchemy import update


from database import db_session
from models import BookInfo, UserInfo, BookExtra, AuthorInfo, BookStar
from spider import get_book_info, get_author_info, QiDian
from analysis import Analysis
from utils import new_novel, hash_session
from config import (
    SECRET_KEY,
    WECHAT_API,
    PAGE_SIZE,
    BOOK_STATUS,
    BOOK_TYPE,
    END,
    QIDIAN,
    JWT_KEY
)


def autho_session(func):
    '''Check session
    '''
    @wraps(func)
    def inner(*args, **kwargs):
        sid = request.headers['sid']
        if not sid:
            return {'error': 'Invalid session'}, 400
        user = UserInfo.query.filter_by(session_id=sid).first()
        if not user:
            return {'error': 'Session expired'}, 400
        return func(*args, user=user, **kwargs)
    return inner


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
        except Exception as e:
            print(e)
            return {'error': 'Invalid token'}, 400
        return func(*args, **kwargs)
    return inner


class Login(Resource):
    '''微信登录'''

    def get(self):
        code = request.args.get('code')
        url = WECHAT_API.format(code)
        wx_data = requests.get(url).json()
        try:
            session_id = hash_session(wx_data['openid'])
        except KeyError:
            return {'error': 'Code invalid'}, 401
        user = UserInfo.query.filter_by(open_id=wx_data['openid']).first()
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
        query = BookInfo.query.order_by(BookInfo.pub_date.desc())
        total = math.ceil(query.count() / PAGE_SIZE)
        if page not in range(1, total+1):
            return {
                'error': 'No more data.'
            }, 400
        books = query.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

        data = [book.json() for book in books]

        return {
            'books': data,
            'total': total
        }


class Star(Resource):
    '''添加、删除、获取喜欢的书籍'''

    @auth_token
    @autho_session
    def get(self, user: UserInfo):
        stars = BookStar.query.filter_by(user_id=user.id)
        like = stars.filter_by(star=1).all()
        dislike = stars.filter_by(star=0).all()
        if request.args.get('type') == 'like':
            return {
                'star': [star.json() for star in like]
            }
        elif request.args.get('type') == 'dislike':
            return {
                'star': [star.json() for star in dislike]
            }
        else:
            return {
                'like': len(like),
                'dislike': len(dislike)
            }

    @auth_token
    @autho_session
    def post(self, user: UserInfo):
        res = request.get_json()
        star = BookStar.query.filter_by(user_id=user.id,
                                        book_id=res['book_id']).first()
        if star:
            star.star = res['star']
        else:
            book = BookInfo.query.filter_by(id=res['book_id']).first()
            if not book:
                return {
                    'error': 'Book not found'
                }, 404
            star = BookStar(user_id=user.id, book_id=res['book_id'],
                            name=book.book_name, star=res['star'])
        db_session.add(star)
        db_session.commit()
        return {
            'msg': 'Success'
        }

    @auth_token
    @autho_session
    def delete(self, user: UserInfo):
        res = request.get_json()
        star = BookStar.query.filter_by(user_id=user.id,
                                        book_id=res['book_id']).first()
        if not star:
            return {'error': 'Book not found'}, 404
        db_session.delete(star)
        db_session.commit()
        return {
            'msg': 'Success'
        }, 204


class Author(Resource):
    '''Author api'''

    @auth_token
    def get(self):
        name = request.args.get('name', '').strip()
        if not name:
            return {'error': 'Invalid parameter'}, 400
        author_info = AuthorInfo.query.filter_by(name=name).first()
        if not author_info:
            info = get_author_info(name)
            if not info:
                return {'error': 'Author not found'}, 404
            author_info = AuthorInfo(author_id=info['author_id'],
                                     source_id=QIDIAN,
                                     name=name,
                                     info=info)
            db_session.add(author_info)
            db_session.commit()
        elif (datetime.datetime.now() - author_info.update_time).days > 30:
            # If author info older than 30 days, update it.
            info = get_author_info(name)
            author_info.info = info
            db_session.add(author_info)
            db_session.commit()
        else:
            info = author_info.info
        return info


class Book(Resource):
    '''QiDian Novel api'''

    @auth_token
    def get(self):
        name = request.args.get('name')
        if name:
            book = BookInfo.query.filter_by(book_name=name,
                                            source_id=QIDIAN).first()
        elif request.args.get('id'):
            try:
                book_id = int(request.args.get('id'))
                book = BookInfo.query.filter_by(id=book_id).first()
                if not book:
                    return {'error': 'Book not found'}, 404
            except ValueError:
                return {'error': 'Invalid parameter'}, 400
        else:
            return {'error': 'Invalid parameter'}, 400

        if not book or (
            (datetime.datetime.now() - book.update_time).days > 7 and
                book.status != END):
            if book:
                qd = QiDian(book.book_name, book.book_id)
            else:
                qd = QiDian(name)
            book_info = qd.book_info()
            if not book_info:
                return {'error': 'Book not found'}, 404
            pub_info = qd.pub_info()
            if book:
                book.word_count = book_info['word_count']
                book.status = book_info['status']
                extra = BookExtra.query.filter_by(id=book.id).first()
                extra.info = pub_info
                db_session.add(book)
            else:
                book = new_novel(book_info)
                db_session.add(book)
                db_session.commit()
                extra = BookExtra(id=book.id, info=pub_info)
            db_session.add(extra)
            db_session.commit()
        else:
            extra = BookExtra.query.filter_by(id=book.id).first()
            pub_info = extra.info

        analysis = Analysis(pub_info, book.status == END)
        timeline = analysis.summary()
        dist = analysis.time_distribution(5)

        return {
            'info': book.json(),
            'timeline': timeline,
            'time_distribution': dist
        }

    @auth_token
    def post(self, name=None, source_id=0):
        content = request.get_json()
        book_name = content.get('book_name', '').strip()
        if not book_name:
            return {'error': '请输入书名'}, 400
        # source_id = int(content.get('source_id'))
        exists = BookInfo.query.filter_by(book_name=book_name,
                                          source_id=source_id).first()
        if exists:
            return {'msg': '书籍已存在'}

        qd = QiDian(book_name)
        book_info = qd.book_info()
        pub_info = qd.pub_info()
        # book_info = get_book_info(source_id, book_name)
        if not book_info:
            return {'error': f'《{book_name}》未找到'}, 404

        book_info['book_type'] = content.get('book_type')
        book = new_novel(book_info, content.get('hero', '').strip(),
                         content.get('heroine', '').strip())
        db_session.add(book)
        db_session.commit()
        extra = BookExtra(id=book.id, pub_info=pub_info)
        db_session.add(extra)
        db_session.commit()
        return {'msg': '已记录', 'id': book.id}, 201

    @auth_token
    def put(self):
        content = request.get_json()
        book = BookInfo.query.filter_by(id=content.get('id', -1)).first()
        if not book:
            return {
                'error': 'Book not found'
            }, 403

        # book.hero = content.get('hero', '').strip()
        # book.heroine = content.get('heroine', '').strip()
        if type(content.get('tag')) == str:
            if not book.tag:
                book.tag = []
            if content.get('new_tag'):  # 添加
                book.tag.append(content.get('tag'))
                book.tag = list(set(book.tag))
            else:  # 删除
                book.tag.remove(content.get('tag'))
            stmt = update(BookInfo).where(f'id={book.id}').values(tag=book.tag)
            db_session.execute(stmt)

        elif int(content.get('status', -1)) in BOOK_STATUS:
            book.status = int(content.get('status'))
            db_session.add(book)
        elif int(content.get('book_type', -1)) in BOOK_TYPE:
            db_session.add(book)
            book.book_type = int(content.get('book_type'))

        db_session.commit()
        return {
            'msg': 'Success',
        }
