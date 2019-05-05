import math

from flask import (
    Blueprint, render_template, request
)
from sqlalchemy import or_

from .models import Book
from .utils import paginate
from .settings import ABANDONED, SINGLE_CP


PAGE_SIZE = 10

bp = Blueprint('web_app', __name__)


# 主页
@bp.route('/')
@bp.route('/index')
# @bp.route('/<int:page>')
def index(page=1):
    query = Book.query.filter(Book.book_type < SINGLE_CP)
    query = query.filter(Book.status < ABANDONED)
    query = query.order_by(Book.pub_date.desc())
    total = math.ceil(query.count() / PAGE_SIZE)
    books = query.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
    return render_template('index.html',
                           books=books,
                           pagination=paginate(page, total))


@bp.route('/search')
def search():
    kw = request.args.get('kw')
    books = Book.query.filter(or_(Book.book_name == kw,
                                  Book.author == kw,
                                  Book.hero == kw,
                                  Book.heroine == kw)).all()
    return render_template('search.html',
                           books=books)


@bp.route('/contact')
def contact():
    return render_template('contact.html')


@bp.route('/help')
def help():
    return render_template('help.html')


def page_not_found(e):
    return render_template('404.html', data='页面'), 404


def server_error(e):
    return render_template('500.html'), 500
