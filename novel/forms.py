'''
表单
'''

from wtforms import (Form, StringField, SelectField)


from .config import BOOK_SOURCE_NAME, BOOK_STATUS, BOOK_TYPE


WEBSITE_CHOICES = [(a, b) for a, b in BOOK_SOURCE_NAME.items()]

TYPE_CHOICES = [(a, b) for a, b in BOOK_TYPE.items()]

STATUS_CHOICES = [(a, b) for a, b in BOOK_STATUS.items()]


class BookForm(Form):
    book_name = StringField('书名')
    author = StringField('作者')
    hero = StringField('男主')
    heroine = StringField('女主')
    source_id = SelectField('源网站', choices=WEBSITE_CHOICES)
    book_type = SelectField('类型', choices=TYPE_CHOICES)


class EditBookForm(Form):
    id = StringField('', render_kw={'type': 'hidden'})
    book_name = StringField('书名')
    author = StringField('作者')
    hero = StringField('男主')
    heroine = StringField('女主')
    status = SelectField('状态', choices=STATUS_CHOICES)
    source_id = SelectField('源网站', choices=WEBSITE_CHOICES)
    book_type = SelectField('类型', choices=TYPE_CHOICES)
