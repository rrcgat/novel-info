import requests
import re
import json

from bs4 import BeautifulSoup

from config import QIDIAN, UNKNOWN, ZONGHENG
from .config import (HEADERS_IPHONE, HEADERS_CHROME,
                     QIDM_SEARCH_URL, QIQM_INFO_URL,
                     QIDM_PUB_URL, ZSHG_SEARCH_URL,
                     ZSHG_DETAIL_URL, ZSHG_CHAP_URL)


def get_qidian_book_info(book_name):
    '''根据书名返回起点小说的基本信息
    '''
    url = QIDM_SEARCH_URL.format(book_name)
    res = requests.get(url, headers=HEADERS_IPHONE)
    if not res.ok:
        return ''

    bsObj = BeautifulSoup(res.text, 'lxml')
    data = bsObj.find('a', {'class': 'book-layout'})

    if not data or data.h4.get_text().strip() != book_name:
        return None

    book_id = data['href'].split('/')[-1]  # 起点书籍编号
    author = data.span.get_text().strip()[2:]  # 作者
    word_info = data.find('em',
                          {'class': 'tag-small blue'}).get_text().strip()

    infos = re.match(r'(\d+\.*\d*)(.*)', word_info).groups()
    if infos[1] == '字':
        word_count = int(infos[0])
    else:
        word_count = int(float(infos[0]) * 10000)
    # pub_date = get_qidm_pub_date(book_id)

    status = data.find('em', {'class': 'tag-small red'}
                       ).get_text().strip()  # 状态
    label = data.em.get_text()  # 标签
    # 获取上架时间、详细简介
    res = requests.get(QIQM_INFO_URL.format(book_id),
                       headers=HEADERS_CHROME)
    token = res.cookies['_csrfToken']
    bsObj = BeautifulSoup(res.text, 'lxml')
    intro = str(bsObj.find('div', {'class': 'book-intro'}).p)
    intro = re.sub(r'<p>|</p>|\u3000', '', intro).strip()
    pub_date = get_qidm_pub_date(book_id, token)
    return {
        'source_id': QIDIAN,
        'book_id': book_id,
        'book_name': book_name,
        'author': author,
        'word_count': word_count,
        'pub_date': pub_date,
        'status': status,
        'label': label,
        'intro': intro
    }


def get_qidm_pub_date(book_id, token):
    '''根据起点小说编号返回首发时间
    '''
    text = requests.get(QIDM_PUB_URL.format(token, book_id),
                        headers=HEADERS_CHROME).content
    jn = json.loads(text.decode('utf-8'))
    vs = jn['data']['vs']
    ut = vs[0]['cs'][0]['uT']
    for i in range(len(vs)):
        # cn = vs[i]['cs'][0]['cN']
        if ut > vs[i]['cs'][0]['uT']:
            ut = vs[i]['cs'][0]['uT']
    return ut


def get_zshg_book_info(book_name, url=ZSHG_SEARCH_URL):
    text = requests.get(url.format(book_name),
                        headers=HEADERS_IPHONE).content
    info = json.loads(text.decode('utf-8'))
    if 'searchBooks' not in info['searchlist']:
        return None
    book = info['searchlist']['searchBooks'][0]
    if book['bookName'].strip() != book_name:
        return None
    book_id = str(book['bookId'])
    author = book['authorName']
    # 根据书籍详情页获取状态、分类与字数
    detail = requests.get(ZSHG_DETAIL_URL.format(book_id),
                          headers=HEADERS_CHROME).text
    bsObj = BeautifulSoup(detail, 'lxml')
    status = bsObj.find('meta', {'name': 'og:novel:status'})['content']
    bs = bsObj.find('div', {'class': 'booksub'})
    label = bs.find_all('a')[1].text
    word_count = int(bs.span.text)
    first_chap = bsObj.find('div', {'class': 'book_btn'}).a['href']
    # 根据第一章所在页获取首发时间
    chap = requests.get(first_chap, headers=HEADERS_CHROME).text
    bsObj = BeautifulSoup(chap, 'lxml')
    pub_date = bsObj.find('span', {'itemprop': 'dateModified'}).text

    return {
        'source_id': ZONGHENG,
        'book_id': book_id,
        'book_name': book_name,
        'author': author,
        'word_count': word_count,
        'pub_date': pub_date,
        'status': status,
        'label': label
    }


def unknown(book_name):
    return {
        'book_name': book_name,
        'source_id': UNKNOWN
    }


get_book_funcs = {
    UNKNOWN: unknown,
    QIDIAN: get_qidian_book_info,  # 起点
    ZONGHENG: get_zshg_book_info,  # 纵横
}
