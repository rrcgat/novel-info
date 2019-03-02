from .book_info import get_book_funcs, QiDian
from .author_info import author_info as get_author_info


def get_book_info(source_id, book_name):
    '''根据书名以来源获取书籍信息

    Args:
        source_id: 书籍来源 id
        book_name: 书名
    returns:
        对应获取书籍信息的函数
    '''
    fn = get_book_funcs[int(source_id)]
    return fn(book_name)
