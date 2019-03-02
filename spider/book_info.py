import requests
import re
import json

from bs4 import BeautifulSoup

from config import QIDIAN, UNKNOWN, ZONGHENG, STATUS_TO_ID
from .config import HEADERS_IPHONE, HEADERS_CHROME

QIDM_SEARCH_URL = 'https://m.qidian.com/search?kw={}'
QIQM_INFO_URL = 'https://book.qidian.com/info/{}#Catalog'
QIDM_PUB_URL = ('https://book.qidian.com/ajax/book/'
                'category?_csrfToken={}&bookId={}')

ZSHG_SEARCH_URL = ('https://m.zongheng.com/h5/ajax/'
                   'search?h5=1&keywords={}'
                   '&pageNum=1&field=all&pageCount=5')
ZSHG_DETAIL_URL = 'http://book.zongheng.com/book/{}.html'
ZSHG_CHAP_URL = 'book.zongheng.com/chapter/{}/{}.html'


class QiDian():
    '''起点小说信息爬取'''

    def __init__(self, name, book_id=None, headers=HEADERS_IPHONE):
        self.book_name = name
        self.headers = headers
        self.url = QIDM_SEARCH_URL.format(name)
        self._book_info = None
        self._pub_info = None
        self.book_id = book_id

    def book_info(self):
        '''获取书籍简要信息'''
        if not self._book_info is None:
            return self._book_info
        if not self.book_id:
            res = requests.get(self.url, headers=self.headers)
            if not res.ok:
                self._book_info = {}
                return self._book_info

            bsObj = BeautifulSoup(res.text, 'lxml')
            data = bsObj.find('a', class_='book-layout')

            if not data or data.h4.get_text().strip() != self.book_name:
                self._book_info = {}
                return self._book_info
            self.book_id = data['href'].split('/')[-1]  # 起点书籍编号
        author = data.span.get_text().strip()[2:]  # 作者
        word_info = data.find('em',
                              class_='tag-small blue').get_text().strip()
        infos = re.match(r'(\d+\.*\d*)(.*)', word_info).groups()
        if infos[1] == '字':
            word_count = int(infos[0])
        else:
            word_count = int(float(infos[0]) * 10000)

        status = data.find('em',
                           class_='tag-small red').get_text().strip()  # 状态
        label = data.em.get_text()  # 标签
        # 获取上架时间、详细简介
        res = requests.get(QIQM_INFO_URL.format(self.book_id),
                           headers=HEADERS_CHROME)
        self.token = res.cookies['_csrfToken']
        bsObj = BeautifulSoup(res.text, 'lxml')
        intro = str(bsObj.find('div', class_='book-intro').p)
        intro = re.sub(r'<p>|</p>|\u3000', '', intro)
        intro = re.sub(r'<br>|<br />|<br/>', '\n', intro).strip()
        pub_info = self.pub_info()
        pub_date = self.pub_date(pub_info)
        return {
            'source_id': QIDIAN,
            'book_id': self.book_id,
            'book_name': self.book_name,
            'author': author,
            'word_count': word_count,
            'pub_date': pub_date,
            'status': STATUS_TO_ID[status],
            'label': label,
            'intro': intro
        }

    def pub_date(self, data):
        '''获取首次发布日期时间'''
        ut = data[0]['cs'][0]['uT']
        for i in range(len(data)):
            if ut > data[i]['cs'][0]['uT']:
                ut = data[i]['cs'][0]['uT']
        return ut

    def pub_info(self):
        '''所有章节发布的日期时间信息'''
        if self._pub_info:
            return self._pub_info
        text = requests.get(QIDM_PUB_URL.format(self.token, self.book_id),
                            headers=self.headers).content
        res = json.loads(text.decode('utf-8'))
        return res['data']['vs']


def get_zshg_book_info(book_name, url=ZSHG_SEARCH_URL):
    '''纵横小说网'''
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


def qidian_book_info(name):
    return QiDian(name).book_info()


get_book_funcs = {
    UNKNOWN: unknown,
    QIDIAN: qidian_book_info,  # 起点
    ZONGHENG: get_zshg_book_info,  # 纵横
}
