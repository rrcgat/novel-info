'''
Configuration
'''
import uuid


SECRET_KEY = 'Secret key only you know.'
JWT_KEY = uuid.uuid1()


DB_ENGINE = 'postgresql'
DB_USER = '<database user>'
DB_PASS = 'database password'
DB_HOST = '127.0.0.1:5432'
DB_NAME = 'database name'


UNKNOWN = 0

SERIAL = 1
END = 2
ABANDONED = 3

NO_HEROINE = 1
SINGLE_HEROINE = 2
SINGLE_HERO = 3
BOY_LOVE = 4
LILY = 5
STALLION = 6

QIDIAN = 1
ZONGHENG = 2


# 状态
BOOK_STATUS = {
    UNKNOWN: '未知',
    SERIAL: '连载',
    END: '完结',
    ABANDONED: '太监',
}

# 类型
BOOK_TYPE = {
    UNKNOWN: '未知',
    NO_HEROINE: '无女主',
    SINGLE_HEROINE: '单女主',
    SINGLE_HERO: '无男主',
    BOY_LOVE: '耽美',
    LILY: '百合',
    STALLION: '种马'
}

# 书籍来源
BOOK_SOURCE_NAME = {
    UNKNOWN: '未知',
    QIDIAN: '起点',
    ZONGHENG: '纵横',
}

# 书籍详情页 URL
INFO_URL = {
    UNKNOWN: '#{}',
    QIDIAN: 'https://book.qidian.com/info/{}',
    ZONGHENG: 'http://book.zongheng.com/book/{}.html',
}

APPID = 'Wechat applet appid'
SECRET = 'Wechat secret'
WECHAT_API = ('https://api.weixin.qq.com/sns/jscode2session?'
              f'appid={APPID}&'
              f'secret={SECRET}&'
              'js_code={}&'
              'grant_type=authorization_code')

PAGE_SIZE = 10
