import re
import math
from functools import wraps
import json


from flask import Flask, render_template, request, jsonify, Markup
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import or_
from flask_restful import Api


from database import db_session
from models import BookInfo
from forms import BookForm, EditBookForm
from utils import dotdict, paginate, new_novel
from spider import get_book_info
from config import (SECRET_KEY, BOOK_STATUS, BOOK_TYPE, ABANDONED,
                    BOOK_SOURCE_NAME, INFO_URL, SINGLE_CP)
from book_api import Login, WIndex, Author, Book, Star


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
csrf = CSRFProtect(app)

api = Api(app, decorators=[csrf.exempt])
api.add_resource(Login, '/api/login')
api.add_resource(WIndex, '/api/index')
api.add_resource(Author, '/api/author')
api.add_resource(Book, '/api/book')
api.add_resource(Star, '/api/star')


PAGE_SIZE = 10


def book_handler(func):
    '''验证书籍是否存在
    '''
    @wraps(func)
    def inner(book_id):
        book = BookInfo.query.filter_by(id=book_id).first()
        if not book:
            return render_template('404.html', data='书籍'), 404
        return func(book)
    return inner


# 主页
@app.route('/')
@app.route('/index')
@app.route('/<int:page>')
def index(page=1):
    query = BookInfo.query.filter(BookInfo.book_type < SINGLE_CP)
    query = query.filter(BookInfo.status < ABANDONED)
    query = query.order_by(BookInfo.pub_date.desc())
    total = math.ceil(query.count() / PAGE_SIZE)
    books = query.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
    return render_template('index.html',
                           books=books,
                           pagination=paginate(page, total))


@app.route('/search')
def search():
    kw = request.args.get('kw')
    books = BookInfo.query.filter(or_(BookInfo.book_name == kw,
                                      BookInfo.author == kw,
                                      BookInfo.hero == kw,
                                      BookInfo.heroine == kw)).all()
    return render_template('search.html',
                           books=books)


@app.route('/edit', methods=['POST'])
def edit():
    info = dotdict(request.get_json())
    filters = {'id': info.id, 'book_name': info.book_name}
    book = BookInfo.query.filter_by(**filters).first()
    if book:
        book.hero = info.hero.strip()
        book.heroine = info.heroine.strip()
        book.status = int(info.status)
        book.source_id = info.source_id
        book.book_type = info.book_type
        book.tag = info.tags

        db_session.add(book)
        db_session.commit()
        return jsonify({
            'data': '已保存修改',
        })
    else:
        return jsonify({
            'data': '暂时不能修改书名，如需帮助，请联系。'
        }), 403


@app.route('/edit/<int:book_id>')
@book_handler
def edit_novel(book):
    edit_form = EditBookForm(id=book.id,
                             book_name=book.book_name,
                             author=book.author,
                             hero=book.hero,
                             heroine=book.heroine,
                             status=book.status,
                             source_id=book.source_id,
                             book_type=book.book_type)

    tag = Markup(json.dumps(book.tag))
    return render_template('edit.html', book=book, form=edit_form,
                           tags=tag)


@app.route('/info/<int:book_id>')
@book_handler
def book_info(book):
    url = INFO_URL[book.source_id].format(book.book_id)
    return render_template('info.html',
                           book=book,
                           book_info_url=url)


@app.route('/add', methods=['GET', 'POST'])
def add_novel():
    if request.method == 'GET':
        book_form = BookForm()
        return render_template('add.html', form=book_form)
    else:
        book = request.get_json()
        book_name = book.get('book_name').strip()
        if not book_name:
            return jsonify({'data': '请输入书名'}), 400
        source_id = int(book.get('source_id'))
        filters = {
            'book_name': book_name,
            'source_id': source_id
        }
        my_book = BookInfo.query.filter_by(**filters).first()
        if my_book:
            return jsonify({'data': '书籍已存在'})
        # comment = book.get('comment').strip()
        hero = book.get('hero').strip()
        heroine = book.get('heroine').strip()
        label = book.get('label')
        book_info = get_book_info(book_name, source_id)
        if not book_info and source_id != -1:
            return jsonify({'data': '未找到《' + book_name + '》'}), 404
        else:
            if source_id == -1:
                book_info = {'author': book.get('author').strip()}
            book_info['book_type'] = book.get('book_type')
            book_info['book_name'] = book_name
            data = get_new_novel(book_info, hero, heroine, label)
            db_session.add(data)
            db_session.commit()
            return jsonify({'data': '已记录'})


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/help')
def help():
    return render_template('help.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', data='页面'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
