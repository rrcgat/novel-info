'''
章节发布时间解析
'''
try:
    from .utils import day_interval, next_date
except:
    from utils import day_interval, next_date

# 字段含义
FREE = 'sS'
TITLE = 'cN'
TIME = 'uT'
WORD_COUNT = 'cnt'

# 时间段开始值
AM = 6
NOON = 12
PM = 14
DUSK = 17
EVENING = 19
NIGHT = 23
EARLY_AM = 1

# 时间范围
TR_ZH = ('凌晨', '早上', '中午', '下午', '傍晚', '晚上', '深夜')
TR_EN = ('early_am', 'am', 'noon', 'pm', 'dusk', 'evening', 'night')


def _sort_data(pub_data):
    '''将更新时间信息按时间排序'''
    res = []
    for data in pub_data:
        res += data['cs']
    res.sort(key=lambda x: x[TIME])
    return res


def _info_wrapper(data):
    '''修改更新信息
    Args:
        data: 原始数据的 cs 字段中的一条数据
    Returns:
        基本数据保留标题、时间和字数信息，并修改对应的键
    To use:
    >>> data = {
                'uuid': 1,
                'cN': '第一章 小镇的早晨',
                'uT': '2008-05-21 10:06:31',
                'cnt': 8929,
                'cU': 'Ou8OEduEwkM1/7i3BL-us87sex0RJOkJclQ2',
                'id': 20361055,
                'sS': 1
            }
    >>> _info_wrapper(data)
    {
        'time': '2008-05-21 10:06:31',
        'word_count': 8929,
        'title': '第一章 小镇的早晨'
    }
    '''
    return {
        'time': data.get(TIME),
        'word_count': data.get(WORD_COUNT),
        'title': data.get(TITLE)
    }


def _date(data):
    '''从基本数据中获取日期信息'''
    return data[TIME].split()[0]


def _time(data):
    '''从基本数据中获取时间信息'''
    return data[TIME].split()[1]


def _time_range(time, lang='en'):
    '''根据时间返回时间范围
    Args:
        time: 0-23 的时间范围
        lang: 返回语言，默认 'en' 为英文
    Returns:
        时间返回的字符串表示
    '''
    if lang == 'en':
        tr = TR_EN
    else:
        tr = TR_ZH
    time = int(time)
    if EARLY_AM <= time < AM:
        return tr[0]
    elif AM <= time < NOON:
        return tr[1]
    elif NOON <= time < PM:
        return tr[2]
    elif PM <= time < DUSK:
        return tr[3]
    elif DUSK <= time < EVENING:
        return tr[4]
    elif EVENING <= time < NIGHT:
        return tr[5]
    else:
        return tr[6]


class TimeCounter():
    '''更新时间范围统计'''

    def __init__(self, content=None):
        self.counter = {}
        self.time_distribution = {}
        for i in range(24):
            self.counter[f'{i:0>2}'] = []
            self.time_distribution[f'{i:0>2}'] = 0
        self._len = 0
        if content:
            for data in content:
                self.update(data)

    def update(self, data):
        '''更新单条数据'''
        time = _time(data)[:2]
        self.counter[time].append(data)
        self.time_distribution[time] += 1
        self._len += 1

    def distribution(self):
        '''排序后的更新时间分布'''
        return sorted(self.time_distribution.items(),
                      key=lambda x: x[1], reverse=True)

    def __len__(self):
        return self._len


def _update_info(content):
    '''获取章节连续更新 / 断更信息
    Args:
        content: 所有排序好的基本数据
    Returns:
        最长连序更新信息、最长连续断更信息组成的元组
    '''
    update_count = 1
    break_count = 0
    longest_update = {}
    longest_break = {}
    i = 0
    while i < len(content) - 1:
        begin_date = _date(content[i])
        j = i
        while j < len(content) - 1:
            date = _date(content[j])
            interval = day_interval(date, _date(content[j+1]))
            if interval <= 1:
                j += 1
            else:
                break
        ndate = str(next_date(_date(content[j])))[:10]
        update_days = day_interval(begin_date, ndate) + 1
        if update_count < update_days:
            update_count = update_days
            longest_update = _info_wrapper(content[i])
            longest_update['days'] = update_days
        if j + 1 < len(content):
            break_days = day_interval(ndate, _date(content[j+1]))
            if break_count < break_days:
                break_count = break_days
                longest_break['days'] = break_days
                longest_break['time'] = str(next_date(_date(content[j])))
        i = j + 1
    return longest_update, longest_break


class TimeParser():
    '''从原始信息中筛选出需要的信息

    从原始信息中整理出书籍更新的相关信息，包括更新时间分布、
    vip 章节、vip 章节字数、免费章节、最长连续 更新/断更 开始时间、
    最早/早晚 更新信息、首次发布/入 V/完结 信息等。

    Attributes:
        content: 排序好的基本数据
        time_counter: 更新时间统计
        _finished: 书籍是否完结
        vip_content: vip 章节的基本数据
        free_content: 免费章节的基本数据
        _min_wc: 最少字数的 vip 章节数据
        _max_wc: 最多字数的 vip 章节数据
        vip_word_count: vip 章节字数
        _max_update: 章节更新最多的一天
        _longest_update: 最长连续更新
        _latest_update: 最晚更新
        _earliest_update: 最早更新
    '''

    def __init__(self, origin, finished):
        self.content = _sort_data(origin)
        self.time_counter = TimeCounter(self.content)
        self._finished = finished
        self.vip_content = []
        self.free_content = []
        self._min_wc = self.content[0]
        self._max_wc = self.content[0]
        self.vip_word_count = 0
        self._max_update = {}
        self._longest_update = {}
        self._longest_break = {}
        self._latest_update = self.content[0]
        self._earliest_update = self.content[0]
        self._init()

    def _init(self):
        for data in self.content:
            # vip 章节
            if data.get(WORD_COUNT) > 1000 and not data.get(FREE):
                self.vip_content.append(data)
                self.vip_word_count += data.get(WORD_COUNT)

                # 最少字数的 vip 章节
                if data.get(WORD_COUNT) < self._min_wc.get(WORD_COUNT):
                    self._min_wc = data
                # 最多字数的章节
                if data.get(WORD_COUNT) > self._max_wc.get(WORD_COUNT):
                    self._max_wc = data
            # 免费章节
            else:
                self.free_content.append(data)

            # 最早 / 最晚更新时间
            time = data.get(TIME).split()[1]
            if self._earliest_update.get(TIME).split()[1] > time >= '06:00:00':
                self._earliest_update = data
            latest_time = self._latest_update.get(TIME).split()[1]
            if latest_time < '06:00:00':
                if latest_time > time:
                    self._latest_update = data
            elif latest_time <= time:
                self._latest_update = data

    def pub_date_info(self):
        '''获取首次发布的章节信息'''
        return _info_wrapper(self.content[0])

    def first_vip(self):
        '''获取上架的章节信息'''
        if self.vip_content:
            return _info_wrapper(self.vip_content[0])
        return {}

    def ending_info(self):
        '''完结的章节信息'''
        if self.vip_content and self._finished:
            return _info_wrapper(self.vip_content[-1])
        return {}

    def max_word_count_info(self):
        '''更新字数最多的 vip 章节信息'''
        if self.vip_content:
            return _info_wrapper(self._max_wc)
        return {}

    def min_word_count_info(self):
        '''更新字数最少的 vip 章节信息'''
        if self.vip_content:
            return _info_wrapper(self._min_wc)
        return {}

    def longest_update(self):
        '''vip 章节最长连更的相关信息'''
        if self._longest_update:
            return self._longest_update
        if not self.vip_content:
            self._longest_update, _ = _update_info(self.content)
        else:
            info = _update_info(self.vip_content)
            self._longest_update, self._longest_break = info
        return self._longest_update

    def longest_break(self):
        '''vip 章节最长断更的相关信息'''
        if self._longest_break:
            return self._longest_break
        if not self.vip_content:
            return {}
        info = _update_info(self.vip_content)
        self._longest_update, self._longest_break = info
        return self._longest_break

    def average_word_count(self):
        '''vip 章节平均更新字数'''
        if self.vip_content:
            return self.vip_word_count // len(self.vip_content)
        return 0

    def max_update(self):
        '''章节最多更新的一天'''
        if self._max_update:
            return self._max_update
        i = 0
        max_update = 1
        while i < len(self.content) - 1:
            date = self.content[i].get(TIME).split()[0]
            update = 0
            j = i + 1
            while j < len(self.content):
                if date == self.content[j].get(TIME).split()[0]:
                    j += 1
                else:
                    break
            update = j - i
            i = j

            if update > max_update:
                self._max_update = _info_wrapper(self.content[i])
                max_update = update
                self._max_update['count'] = update
        return self._max_update

    def latest_update(self):
        '''最晚更新的章节信息'''
        return _info_wrapper(self._latest_update)

    def earliest_update(self):
        '''最早更新的章节信息'''
        return _info_wrapper(self._earliest_update)


class Analysis():
    def __init__(self, origin, finished):
        self.tp = TimeParser(origin, finished)
        self.res = []

    def _template(self, info, text, *args):
        date, time = info['time'].split()
        return {
            'time': date,
            'content': text.format(time, *args)
        }

    def publish(self):
        info = self.tp.pub_date_info()
        text = '【{}】新书发布 - {}'
        return self._template(info, text,  info['title'])

    def first_vip(self):
        info = self.tp.first_vip()
        text = '【{}】上架 - {}'
        return self._template(info, text, info['title'])

    def earliest_update(self):
        info = self.tp.earliest_update()
        text = '【{}】最早更新 - {}'
        return self._template(info, text, info['title'])

    def latest_update(self):
        info = self.tp.latest_update()
        text = '【{}】最晚更新 - {}'
        return self._template(info, text, info['title'])

    def longest_update(self):
        info = self.tp.longest_update()
        text = '【{}】最长连续更新 {} 天'
        return self._template(info, text, info['days'])

    def longest_break(self):
        info = self.tp.longest_break()
        if not info:
            return None
        text = '【{}】最长连续断更{} 天'
        return self._template(info, text, info['days'])

    def ending(self):
        text = '【{}】{}\n历时 {} 天，大结局(￣▽￣)~*'
        info = self.tp.ending_info()
        interval = day_interval(self.tp.pub_date_info()['time'].split()[0],
                                info['time'].split()[0])
        return self._template(info, text, info['title'], interval)

    def max_update(self):
        text = '【{}】一天最多更新 {} 章'
        max_update = self.tp.max_update()
        return self._template(max_update, text, max_update['count'])

    def max_word_count(self):
        text = '【{}】{}\n更新字数最多 {} 字'
        info = self.tp.max_word_count_info()
        return self._template(info, text, info['title'], info['word_count'])

    def min_word_count(self):
        text = '【{}】{}\n更新字数最少 {} 字'
        info = self.tp.min_word_count_info()
        return self._template(info, text, info['title'], info['word_count'])

    def _sort(self, data):
        '''排序'''
        res = {}
        data = [d for d in data if d]
        for d in data:
            if d['time'] in res:
                res[d['time']]['content'].append(d['content'])
            else:
                res[d['time']] = {}
                res[d['time']]['time'] = d['time']
                res[d['time']]['content'] = [d['content']]
        res = sorted(res.values(), key=lambda x: x['time'])
        return res

    def time_distribution(self, limit=0):
        dist = []
        total = len(self.tp.time_counter)
        count = 0
        for i, (name, value) in enumerate(self.tp.time_counter.distribution()):
            if value and (not limit or i + 1 <= limit):
                count += value
                dist.append({
                    'value': value,
                    'name': name
                })
            elif total - count:
                dist.append({
                    'value': total - count,
                    'name': '其他'
                })
                break
            else:
                break

        return dist

    def summary(self):
        '''总结'''
        if self.res:
            return self.res

        res = [
            self.publish(),
            self.earliest_update(),
            self.latest_update(),
            self.max_update()
        ]
        if len(self.tp.vip_content) >= 10:
            res += [
                self.longest_update(),
                self.longest_break(),
                self.first_vip(),
                self.max_word_count(),
                self.min_word_count()
            ]
        if self.tp.ending_info():
            res.append(self.ending())

        self.res = self._sort(res)

        content = []
        if self.tp.vip_content:
            wc = self.tp.average_word_count()
            content.append(f'上架后，平均每章更新 {wc} 字。')
        dist = self.tp.time_counter.distribution()[:2]
        if _time_range(dist[0][0]) == _time_range(dist[1][0]):
            time = _time_range(dist[0][0], lang='zh')
        else:
            time = ' {} 点和 {} 点'.format(dist[0][0], dist[1][0])
        content.append(f'这部作品在{time}最活跃，或许这时作者的灵感更强吧。')

        summary = {
            'time': '(^_^)',
            'content': content
        }
        self.res.append(summary)

        return self.res

