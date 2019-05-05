
import datetime
from hashlib import md5


from .models import Book
from .settings import UNKNOWN


def hash_session(text):
    return md5((text+'SECRET_KEY').encode()).hexdigest()[8:-8]


class dotdict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


def paginate(current, total):
    '''产生分页数据
    '''
    pag = dotdict({})
    pag.page = current
    pag.prev = None if current == 1 else current - 1
    pag.next = None if current == total else current + 1
    if total <= 8:
        pag.iter_pages = [i for i in range(1, total+1)]
    elif current > 4:
        if current < total - 4:
            pag.iter_pages = [1, None, current-2, current - 1,
                              current, current+1, current+2, None, total]
        else:
            pag.iter_pages = [1, None] + [i for i in range(min(total-4, current-2),
                                                           total+1)]
    elif current < 4:
        pag.iter_pages = [1, 2, 3, 4, 5, None, total]
    else:
        pag.iter_pages = [1, 2, 3, 4, 5, 6, None, total]
    return pag


def new_novel(book_info, hero='', heroine='', tag=None):
    '''根据书籍信息产生 `Book` 以添加到数据库
    '''
    return Book(book_id=book_info.get('book_id', UNKNOWN),
                source_id=book_info.get('source_id', UNKNOWN),
                book_name=book_info['book_name'],
                author=book_info['author'],
                pub_date=book_info.get('pub_date'),
                word_count=book_info.get('word_count', UNKNOWN),
                hero=hero,
                heroine=heroine,
                status=book_info.get('status'),
                book_type=book_info.get('book_type', UNKNOWN),
                label=book_info.get('label', '未知'),
                tag=tag,
                book_intro=book_info.get('intro', '什么都没有。'))
