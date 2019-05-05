'''
Database models
'''

from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB

from .database import db
from .settings import BOOK_TYPE, BOOK_SOURCE_NAME, BOOK_STATUS, UNKNOWN


class User(db.Model):
    '''用户'''

    __tablename__ = 'reader'
    id = db.Column(db.Integer, primary_key=True, comment='User ID')
    open_id = db.Column(db.String(28), unique=True, comment='Wechat open_id')
    username = db.Column(db.String(32), default='')
    session_id = db.Column(db.String(32), unique=True, default='')
    register_time = db.Column(db.DateTime, default=datetime.now,
                              comment='Regiter time')
    stars = db.relationship('Star', backref=db.backref('user', lazy=True),
                            order_by='Star.book_id', lazy='dynamic')

    def __repr__(self):
        return f'<{self.id}: {self.username}>'


class Source(db.Model):
    '''来源网站'''

    id = db.Column(db.SMALLINT, primary_key=True, comment='Souce website id')
    name = db.Column(db.String(32), unique=True,
                     comment='The name of the website')
    book = db.relationship('Book', backref='source', lazy=True)

    def __repr__(self):
        return f'<{self.id}: {self.name}>'


tags = db.Table(
    'tags',
    db.Column('tag_id', db.Integer,
              db.ForeignKey('tag.id'), primary_key=True),
    db.Column('book_id', db.Integer,
              db.ForeignKey('book.id'), primary_key=True)
)


keywords = db.Table(
    'keywords',
    db.Column('keyword_id', db.Integer,
              db.ForeignKey('keyword.id'), primary_key=True),
    db.Column('book_id', db.Integer,
              db.ForeignKey('book.id'), primary_key=True)
)


class Book(db.Model):
    '''小说基本信息'''

    id = db.Column(db.Integer, primary_key=True)  # 小说唯一标识
    source_book_id = db.Column(db.String(32), default=UNKNOWN)  # 来源处书籍编号
    source_id = db.Column(db.Integer,
                          db.ForeignKey('source.id'),
                          default=1)
    book_name = db.Column(db.String(64), nullable=False)  # 书名
    author = db.Column(db.String(64))  # 作者
    pub_date = db.Column(db.String(19), default='',
                         comment='Publication  date')  # 上架日期
    word_count = db.Column(db.Integer, default=0)  # 字数
    hero = db.Column(db.String(32), default='')  # 男主
    heroine = db.Column(db.String(32), default='')  # 女主
    status = db.Column(db.SMALLINT, default='', comment='Book status')
    book_type = db.Column(db.SMALLINT, default=UNKNOWN)  # 类型
    label_id = db.Column(db.Integer, db.ForeignKey('tag.id'))
    browse = db.Column(db.Integer, default=0, comment='Browse number')
    book_intro = db.Column(db.String(1000), default='',
                           comment='Book introduction')
    update_time = db.Column(db.DateTime, default=datetime.now,
                            comment='Update time')

    extra = db.relationship('BookExtra', backref='book',
                            lazy=True, uselist=False)
    label = db.relationship('Tag', lazy=False, uselist=False,
                            backref=db.backref('label_books', lazy='dynamic'))
    tags = db.relationship('Tag', secondary=tags, lazy='dynamic',
                           backref=db.backref('books', lazy='dynamic'))
    keywords = db.relationship('Keyword', secondary=keywords, lazy='dynamic',
                               backref=db.backref('books', lazy='dynamic'))

    @property
    def source_name(self):
        return BOOK_SOURCE_NAME[self.source_id]

    @property
    def type_name(self):
        return BOOK_TYPE[self.book_type]

    @property
    def status_name(self):
        return BOOK_STATUS[self.status]

    def json(self, full=True):
        info = {
            'id': self.id,
            'source': self.source_name,
            # 'source_book_id': self.source_book_id,
            'book_name': self.book_name,
            'author': self.author,
            'pub_date': self.pub_date,
            'word_count': self.word_count,
            'heroine': self.heroine,
            'label': self.label.name,
            'status': self.status_name,
            'book_type': self.type_name
        }
        if full:
            info['hero'] = self.hero
            info['heroine'] = self.heroine
            info['tag'] = [tag.name for tag in self.tags]
            info['intro'] = self.book_intro
        return info

    def __repr__(self):
        return f'<{self.id}: {self.book_name}>'


class Tag(db.Model):
    '''网站/用户标签'''

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True,
                     index=True, nullable=False)


class Keyword(db.Model):
    '''书籍关键字'''

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True,
                     index=True, nullable=False)


class Star(db.Model):
    '''作品收藏'''

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('reader.id'),
                        nullable=False)
    star = db.Column(db.SMALLINT,
                     comment='0 means dislike while 1 means like')
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    book = db.relationship('Book', backref=db.backref('star', lazy=True),
                           order_by=Book.id,
                           lazy=True, uselist=False)

    def __repr__(self):
        return f'<{self.user_id}: book-{self.book_id} star: {self.star}>'


class Author(db.Model):
    '''作者信息'''

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'),
                          default=0)
    name = db.Column(db.String(32), comment='Name of the author')
    info = db.Column(JSONB, comment='Basic info of the author')
    update_time = db.Column(db.DateTime, default=datetime.now,
                            comment='Update time')

    def __repr__(self):
        return f'<{self.author_id} - f{self.name}>'


class BookExtra(db.Model):
    '''小说其他相关信息'''

    id = db.Column(db.Integer, db.ForeignKey('book.id'),
                   primary_key=True)  # 小说唯一标识
    info = db.Column(JSONB, comment='Update info of the book')
    summarization = db.Column(db.Text, comment='Text summarization')
    update_time = db.Column(db.DateTime, default=datetime.now,
                            comment='Update time')

    def __repr__(self):
        return f'<{self.id} - f{self.update_time}>'
