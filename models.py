'''
Database models
'''

from sqlalchemy import (Column, DateTime, String, Float, SMALLINT,
                        Integer, ForeignKey)
from sqlalchemy.dialects.postgresql import ARRAY

from database import Base
from config import BOOK_TYPE, BOOK_SOURCE_NAME, BOOK_STATUS


class UserInfo(Base):
    __tablename__ = 'user_info'  # Table name
    id = Column(Integer, primary_key=True, comment='User ID')
    open_id = Column(Integer, comment='Wechat open_id')
    username = Column(String(32), default='')
    session_id = Column(String(16), default='')
    star_novel = Column(ARRAY(Integer), default=[], comment='Favorite novel')

    def __repr__(self):
        return f'<{self.username}: {self.id}>'


class Source(Base):
    __tablename__ = 'source_info'
    id = Column(SMALLINT, primary_key=True, comment='Souce website id')
    name = Column(String(32), comment='The name of the Website')

    def __repr__(self):
        return f'<{self.name}: {self.id}>'


class NovelInfo(Base):
    '''小说信息
    '''
    __tablename__ = 'novel_info'
    id = Column(Integer, primary_key=True)  # 小说唯一标识
    book_id = Column(String(16), default=0)  # 来源处书籍编号
    source_id = Column(Integer, ForeignKey('source_info.id'), default=0)
    book_name = Column(String(64), nullable=False)  # 书名
    author = Column(String(64))  # 作者
    pub_date = Column(String(16), default='')  # 上架日期
    word_count = Column(Integer, default=0)  # 字数
    hero = Column(String(32), default='')  # 男主
    heroine = Column(String(32), default='')  # 女主
    label = Column(String(32), default='')
    tag = Column(ARRAY(String(32)), comment='User tag')
    status = Column(SMALLINT, default='', comment='Book status')
    book_type = Column(SMALLINT, default=0)  # 类型
    star = Column(Integer, default=0, comment='Favorite number')
    book_intro = Column(String(1000), default='', comment='Book introduction')

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
            'book_intro': self.book_intro
        }

    def __repr__(self):
        return f'<{self.book_name}: {self.id}>'
