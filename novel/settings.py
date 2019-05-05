
'''
Configuration
'''
UNKNOWN = 0

SERIAL = 1  # 连载
END = 2  # 完结
ABANDONED = 3  # 太监

NO_CP = 1  # 无 CP
SINGLE_CP = 2  # 单 CP
MULTI_CP = 3  # 多 CP

QIDIAN = 1
ZONGHENG = 2


# 状态
BOOK_STATUS = {
    UNKNOWN: '未知',  # 0
    SERIAL: '连载',  # 1
    END: '完结',  # 2
    ABANDONED: '太监',  # 3
}

STATUS_TO_ID = {v: k for k, v in BOOK_STATUS.items()}
STATUS_TO_ID['完本'] = END

# 类型
BOOK_TYPE = {
    UNKNOWN: '未知',
    NO_CP: '无 CP',
    SINGLE_CP: '单 CP',
    MULTI_CP: '多 CP/P'
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

PAGE_SIZE = 10
