'''
Database models
'''

from datetime import datetime

from sqlalchemy import (Column, DateTime, String, Float, SMALLINT,
                        Integer, ForeignKey)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from database import Base
from config import BOOK_TYPE, BOOK_SOURCE_NAME, BOOK_STATUS


class UserInfo(Base):
    __tablename__ = 'user_info'  # Table name
    id = Column(Integer, primary_key=True, comment='User ID')
    open_id = Column(String(28), comment='Wechat open_id')
    username = Column(String(32), default='')
    session_id = Column(String(16), default='')
    register_time = Column(DateTime, default=datetime.now,
                           comment='Regiter time')

    def __repr__(self):
        return f'<{self.username}: {self.id}>'


class Source(Base):
    __tablename__ = 'source_info'
    id = Column(SMALLINT, primary_key=True, comment='Souce website id')
    name = Column(String(32), comment='The name of the Website')

    def __repr__(self):
        return f'<{self.name}: {self.id}>'


class BookInfo(Base):
    '''小说基本信息
    '''
    __tablename__ = 'book_info'
    id = Column(Integer, primary_key=True)  # 小说唯一标识
    book_id = Column(String(32), default=0)  # 来源处书籍编号
    source_id = Column(Integer, ForeignKey('source_info.id'), default=0)
    book_name = Column(String(64), nullable=False)  # 书名
    author = Column(String(64))  # 作者
    pub_date = Column(String(19), default='')  # 上架日期
    word_count = Column(Integer, default=0)  # 字数
    hero = Column(String(32), default='')  # 男主
    heroine = Column(String(32), default='')  # 女主
    label = Column(String(32), default='')
    tag = Column(ARRAY(String(32)), comment='User tag')  # 用户标签
    status = Column(SMALLINT, default='', comment='Book status')
    book_type = Column(SMALLINT, default=0)  # 类型
    browse = Column(Integer, default=0, comment='Browse number')
    book_intro = Column(String(1000), default='', comment='Book introduction')
    update_time = Column(DateTime, default=datetime.now,
                         comment='Update time')

    @property
    def source_name(self):
        return BOOK_SOURCE_NAME[self.source_id]

    @property
    def type_name(self):
        return BOOK_TYPE[self.book_type]

    @property
    def status_name(self):
        return BOOK_STATUS[self.status]

    def json(self):
        return {
            'id': self.id,
            'source': self.source_name,
            'book_id': self.book_id,
            'book_name': self.book_name,
            'author': self.author,
            'pub_date': self.pub_date,
            'word_count': self.word_count,
            'hero': self.hero,
            'heroine': self.heroine,
            'label': self.label,
            'tag': self.tag,
            'status': self.status_name,
            'book_type': self.type_name,
            'intro': self.book_intro
        }

    def __repr__(self):
        return f'<{self.book_name}: {self.id}>'


class BookStar(Base):
    '''作品收藏'''
    __tablename__ = 'book_star'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    book_id = Column(Integer, ForeignKey('book_info.id'))
    star = Column(SMALLINT, comment='0 means dislike while 1 means like')
    name = Column(String(64))  # 书名

    def json(self):
        return {
            'star': self.star,
            'name': self.name,
            'book_id': self.book_id
        }

    def __repr__(self):
        return f'<{self.user_id}: {self.book_id} - {self.name}>'


class AuthorInfo(Base):
    '''作者信息'''
    __tablename__ = 'author_info'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer)
    source_id = Column(Integer, ForeignKey('source_info.id'),
                       default=0)
    name = Column(String(32))
    info = Column(JSONB)
    update_time = Column(DateTime, default=datetime.now,
                         comment='Update time')

    def __repr__(self):
        return f'<{self.author_id} - f{self.name}>'


class BookExtra(Base):
    '''小说其他相关信息
    '''
    __tablename__ = 'book_extra'
    id = Column(Integer, ForeignKey('book_info.id'),
                primary_key=True)  # 小说唯一标识
    info = Column(JSONB)
    update_time = Column(DateTime, default=datetime.now,
                         comment='Update time')
