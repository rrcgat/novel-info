'''
起点作者信息爬取
'''

import requests
from bs4 import BeautifulSoup
import re


SEARCH_URL = 'https://www.qidian.com/search?kw='
AUTHOR_URL = 'https://my.qidian.com/author/'


def _author_id(text):
    return re.search(r'\d+$', text).group()


def get_author_id(author):
    '''Get author id, if not found, return None'''

    res = requests.get(SEARCH_URL + author)
    soup = BeautifulSoup(res.text, 'html5lib')
    author_info = soup.find('div', {'class': 'author-info fl'})
    if author_info:
        return _author_id(author_info.a['href'])
    result_list = soup('div', {'class': 'book-mid-info'})
    for result in result_list:
        if result.p.a.get_text() == author:
            return _author_id(result.p.a['href'])
    return None


def _book_info(soup, limit=False):
    if not soup:
        if limit:
            return {}
        return []
    items = soup('li', class_='author-item')
    res = []
    for soup in items:
        time = soup.find('div', class_='author-item-time')
        if time:
            time = time.get_text()
        else:
            time = ''
        name = soup.find('div', class_='author-item-title').get_text()
        exp = soup.find('div', class_='author-item-exp')
        label, status = [a.get_text() for a in exp('a')]
        word_count = re.sub(f'{label}|{status}', '', exp.get_text().strip())
        last_update = soup.find(
            'div', class_='author-item-update').get_text().split('·')[1].strip()
        res.append({
            'time': time,
            'name': name,
            'label': label,
            'status': status,
            'word_count': word_count,
            'last_update': last_update
        })
    if limit and res:
        return res[0]
    return res


def author_info(author, author_id=0):
    '''Get author info'''
    if not author_id:
        author_id = get_author_id(author)
        if not author_id:
            return None
    res = requests.get(AUTHOR_URL + author_id)
    soup = BeautifulSoup(res.text, 'html5lib')
    honor = soup.find('span', class_='header-avatar-vip').get_text()
    intro = soup.find('div', class_='header-msg-desc').get_text()
    # amount, word_count, days
    info = [s.get_text() for s in soup('strong', class_="header-msg-strong")]

    hot = _book_info(soup.find('ul', class_='author-hot'), True)
    books = _book_info(soup.find('ul', class_='author-work'))

    return {
        'author_id': author_id,
        'name': author,
        'honor': honor,
        'intro': intro,
        'amount': info[0],
        'word_count': info[1],
        'days': info[2],
        'hot': hot,
        'books': books
    }
