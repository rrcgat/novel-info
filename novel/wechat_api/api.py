from functools import wraps
import datetime
from uuid import uuid1, uuid5

from flask import request, current_app
from flask_restful import Resource
import jwt
import requests
from sqlalchemy import or_


from novel.database import db
from novel.models import Book, User, BookExtra, Author, Star, Tag
from novel.spider import get_author_info, QiDian
from novel.analysis import Analysis
from novel.settings import (
    PAGE_SIZE,
    BOOK_STATUS,
    NO_CP,
    SINGLE_CP,
    MULTI_CP,
    END,
    QIDIAN,
    UNKNOWN
)

_book_type = {
    '无CP': NO_CP,
    '无 CP': NO_CP,
    '单CP': SINGLE_CP,
    '单 CP': SINGLE_CP,
    '多CP': MULTI_CP,
    '多 CP': MULTI_CP
}


def auth_session(func):
    '''Check session
    '''
    @wraps(func)
    def inner(*args, **kwargs):
        sid = request.headers['Sid']
        if not sid:
            return {'error': 'Invalid session'}, 400
        user = User.query.filter_by(session_id=sid).first()
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
            jwt.decode(token, current_app.config['JWT_KEY'])
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}, 400
        except Exception as e:
            print(e)
            return {'error': 'Invalid token'}, 400
        return func(*args, **kwargs)
    return inner


def _paginate(query, page):
    '''分页'''

    query = query.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
    return query


class Login(Resource):
    '''微信登录'''

    def get(self):
        code = request.args.get('code')
        url = current_app.config['WECHAT_API'].format(code)
        wx_data = requests.get(url).json()
        try:
            session_id = uuid5(uuid1(), wx_data['openid']).hex
        except KeyError:
            return {'error': 'Code invalid'}, 401
        user = User.query.filter_by(open_id=wx_data['openid']).first()
        if user:
            user.session_id = session_id
        else:
            user = User(session_id=session_id,
                        open_id=wx_data['openid'])
        db.session.add(user)
        db.session.commit()
        now = datetime.datetime.utcnow()
        payload = {
            'iss': 'rrcgat',
            'exp': now + datetime.timedelta(hours=3),
            'iat': now
        }
        token = jwt.encode(payload, current_app.config['JWT_KEY'],
                           algorithm='HS256')
        token = str(token, 'utf-8')
        return {
            'sid': session_id,
            'token': token
        }


class Search_(Resource):
    '''Search by tag, book name and other keywords'''

    # @auth_token
    def get(self):
        kw = request.args.get('kw')
        page = int(request.args.get('page', 1))
        book = Book.query.filter_by(book_name=kw).first()
        if book:
            return {
                'page': 1,
                'books': [book.json(full=False)]
            }
        if kw.upper() in _book_type:
            books = Book.query.filter_by(book_type=_book_type[kw.upper()])
        else:
            books = Book.query.filter(or_(Book.tags.any(name=kw),
                                          Book.keywords.any(name=kw)))

        books = books.order_by(Book.pub_date.desc())
        if not books.all():
            return {
                'error': 'Not found'
            }, 404
        books = _paginate(books, page)
        if not books.all():
            return {
                'error': 'No more data'
            }, 404
        return {
            'page': page,
            'books': [book.json(full=False) for book in books]
        }


class Star_(Resource):
    '''添加、删除、获取喜欢的书籍'''

    @auth_token
    @auth_session
    def get(self, user: User):
        stars = user.stars
        like = stars.filter_by(star=1)
        dislike = stars.filter_by(star=0)
        page = int(request.args.get('page', 1))
        if request.args.get('type') == 'like':
            like = _paginate(stars.filter_by(star=1), page)
            if not like:
                return {
                    'error': 'No more data.'
                }
            return {
                'star': [star.book.json(full=False) for star in like]
            }
        elif request.args.get('type') == 'dislike':
            dislike = _paginate(stars.filter_by(star=0), page)
            if not dislike:
                return {
                    'error': 'No more data.'
                }
            return {
                'star': [star.book.json(full=False) for star in dislike]
            }
        else:
            return {
                'like': stars.filter_by(star=1).count(),
                'dislike': stars.filter_by(star=0).count()
            }

    @auth_token
    @auth_session
    def post(self, user: User):
        res = request.get_json()
        star = user.stars.filter_by(book_id=res['book_id']).first()
        if star:
            star.star = res['star']
        else:
            book = Book.query.filter_by(id=res['book_id']).first()
            if not book:
                return {
                    'error': 'Book not found'
                }, 404
            star = Star(user_id=user.id, book_id=res['book_id'],
                        star=res['star'])
        db.session.add(star)
        db.session.commit()
        return {
            'msg': 'Success'
        }, 201

    @auth_token
    @auth_session
    def delete(self, user: User):
        res = request.get_json()
        star = user.stars.filter_by(book_id=res['book_id']).first()
        if not star:
            return {'error': 'Book not found'}, 404
        db.session.delete(star)
        db.session.commit()
        return {
            'msg': 'Success'
        }, 204


class Author_(Resource):
    '''Author api'''

    @auth_token
    def get(self):
        name = request.args.get('name', '').strip()
        if not name:
            return {'error': 'Invalid parameter'}, 400
        author_info = Author.query.filter_by(name=name).first()
        if not author_info:
            info = get_author_info(name)
            if not info:
                return {'error': 'Author not found'}, 404
            author_info = Author(author_id=info['author_id'],
                                 source_id=QIDIAN,
                                 name=name,
                                 info=info)
            db.session.add(author_info)
            db.session.commit()
        elif (datetime.datetime.now() - author_info.update_time).days > 30:
            # If author info older than 30 days, update it.
            info = get_author_info(name)
            author_info.info = info
            db.session.add(author_info)
            db.session.commit()
        else:
            info = author_info.info
        return info


def add_and_commit_new_book(book_info):
    '''Add new book and commit to database'''

    label = Tag.query.filter_by(name=book_info['label']).first()
    if not label:
        label = Tag(name=book_info['label'])
        db.session.add(label)
        db.session.commit()

    book = Book(source_book_id=book_info.get('book_id', UNKNOWN),
                source_id=book_info.get('source_id', UNKNOWN),
                book_name=book_info['book_name'],
                author=book_info['author'],
                pub_date=book_info.get('pub_date'),
                word_count=book_info.get('word_count', 0),
                status=book_info.get('status'),
                label_id=label.id,
                book_intro=book_info.get('intro', '什么都没有。'))
    db.session.add(book)
    db.session.commit()
    return book


def check_book(func):
    '''Check book'''

    @wraps(func)
    def inner(*args, **kwargs):
        content = request.get_json()
        book = Book.query.filter_by(id=content.get('id', -1)).first()
        if not book:
            return {
                'error': 'Book not found'
            }, 404
        return func(*args, book=book, content=content, **kwargs)
    return inner


class Book_(Resource):
    '''QiDian Novel api'''

    @auth_token
    def get(self):
        name = request.args.get('name')
        if name:
            book = Book.query.filter_by(book_name=name,
                                        source_id=QIDIAN).first()
        elif request.args.get('id'):
            try:
                book_id = int(request.args.get('id'))
                book = Book.query.filter_by(id=book_id).first()
                if not book:
                    return {'error': 'Book not found by id'}, 404
            except ValueError:
                return {'error': 'Invalid parameter'}, 400
        else:
            return {'error': 'Invalid parameter'}, 400

        if not book or (
            book.status != END
            and (datetime.datetime.now() - book.update_time).days > 7
        ):
            if book:
                qd = QiDian(book.book_name)
            else:
                qd = QiDian(name)
            book_info = qd.book_info()
            if not book_info:
                return {'error': 'Book not found by gived name'}, 404
            pub_info = qd.pub_info()
            if book:
                book.word_count = book_info['word_count']
                book.status = book_info['status']
                extra = book.extra
                extra.info = pub_info
                db.session.add(book)
            else:
                book = add_and_commit_new_book(book_info)
                extra = BookExtra(id=book.id, info=pub_info)
            db.session.add(extra)
            db.session.commit()
        else:
            pub_info = book.extra.info

        analysis = Analysis(pub_info, book.status == END)
        timeline = analysis.summary()
        dist = analysis.time_distribution(5)

        return {
            'info': book.json(),
            'timeline': timeline,
            'time_distribution': dist
        }

    @auth_token
    @check_book
    def post(self, book, content):
        '''Add tag'''
        tag = Tag.query.filter_by(name=content['tag']).first()
        if not tag:
            tag = Tag(name=content['tag'])
            db.session.add(tag)
            db.session.commit()
        book.tags.append(tag)
        db.session.add(book)
        db.session.commit()
        return {
            'msg': 'New tag created'
        }, 201

    @auth_token
    @check_book
    def put(self, book, content):
        if int(content.get('status', -1)) in BOOK_STATUS:
            book.status = int(content.get('status'))
            db.session.add(book)
        elif int(content.get('book_type', -1)) in (NO_CP, SINGLE_CP, MULTI_CP):
            book.book_type = int(content.get('book_type'))
            db.session.add(book)

        db.session.commit()
        return {
            'msg': 'Updated success',
        }

    @auth_token
    @check_book
    def delete(self, book, content):
        '''Delete tag'''
        tag = book.tags.filter_by(name=content['tag']).first()
        if tag:  # 删除
            book.tags.remove(tag)
            db.session.add(book)
            db.session.commit()
        return {
            'msg': 'Deleted success',
        }, 204
