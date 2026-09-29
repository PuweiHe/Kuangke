from config import get_configuration
from pathlib import Path
import datetime
import pytz
import holidays

def load_config():
    return get_configuration('application', None)
config = load_config()

def get_last_weekday(date):
    chinese_holidays = holidays.China()
    previous_day = date - datetime.timedelta(days=1)
    while previous_day.weekday() >= 5 or previous_day in chinese_holidays:
        previous_day -= datetime.timedelta(days=1)
    return previous_day.strftime('%Y/%m/%d')

def get_current_date():
    today = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    date_string = f'今天是{today.year}年{today.month}月{today.day}日{weekdays[today.isoweekday() - 1]}'
    t_minus_1 = get_previous_business_day(today)
    t_minus_1_str = f'{t_minus_1.year}年{t_minus_1.month}月{t_minus_1.day}日'
    return f'{date_string}，T-1交易日为{t_minus_1_str}'

def get_previous_business_day(date):
    cn_holidays = holidays.China()
    previous_day = date - datetime.timedelta(days=1)
    while previous_day.weekday() >= 5 or previous_day.date() in cn_holidays:
        previous_day -= datetime.timedelta(days=1)
    return previous_day
