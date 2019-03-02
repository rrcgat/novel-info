import datetime


def parse_ymd(date):
    '''
    Convert string to `datetime.datetime` object.

    Args:
        date: string contains year, month, day, split by `-`
    Returns:
        `datetime.datetime` object
    '''
    return datetime.datetime(*map(int, date.split('-')))


def next_date(date):
    '''Get next date from string'''
    return parse_ymd(date) + datetime.timedelta(days=1)


def day_interval(x, y):
    '''Get day interval between two strings represent datetime'''
    return abs((parse_ymd(x) - parse_ymd(y)).days)


if __name__ == "__main__":
    print(day_interval('2018-01-22', '2018-01-24'))
