from .utils import get_book_funcs


def get_book_info(source_id, book_name):
    '''根据书名以来源获取书籍信息

    :type book_name: str
    :type source_id: str
    :rtype: dict
    '''
    fn = get_book_funcs[int(source_id)]
    return fn(book_name)
