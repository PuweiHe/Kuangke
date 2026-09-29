"""
日期工具模块
提供常用的日期格式化、计算函数
"""

from datetime import datetime, timedelta


def normalize_business_date(value: str) -> str:
    """Validate YYYYMMDD or YYYY-MM-DD and return YYYYMMDD."""
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    raise ValueError("business date must be YYYYMMDD or YYYY-MM-DD")


def get_today() -> str:
    """
    获取今天日期，格式：YYYY-MM-DD

    Returns:
        str: 今天的日期字符串
    """
    return datetime.now().strftime("%Y-%m-%d")


def get_yesterday() -> str:
    """
    获取昨天日期，格式：YYYY-MM-DD

    Returns:
        str: 昨天的日期字符串
    """
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def get_quarter_end(date_str: str) -> str:
    """
    返回给定日期的上季末日期

    Args:
        date_str: 输入日期字符串（YYYYMMDD）

    Returns:
        str: 上季末日期（YYYYMMDD）
    """
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    year = date_obj.year
    month = date_obj.month

    # 根据当前月份确定所在季度及上季末
    if month <= 3:
        # 当前 Q1，上季末为去年 Q4（12-31）
        year -= 1
        quarter_end_month = 12
    elif month <= 6:
        quarter_end_month = 3
    elif month <= 9:
        quarter_end_month = 6
    else:
        quarter_end_month = 9

    # 计算季末最后一天
    if quarter_end_month == 12:
        last_day = 31
    elif quarter_end_month == 3:
        last_day = 31
    elif quarter_end_month == 6:
        last_day = 30
    else:  # 9月
        last_day = 30

    return f"{year}{quarter_end_month:02d}{last_day:02d}"


def format_date(date_str: str) -> str:
    """
    标准化日期格式为 YYYY-MM-DD

    支持输入格式：
    - YYYY-MM-DD
    - YYYY/MM/DD
    - YYYY.MM.DD
    - YYYYMMDD

    Args:
        date_str: 输入日期字符串

    Returns:
        str: 标准化后的 YYYY-MM-DD 格式日期

    Raises:
        ValueError: 无法解析的日期格式
    """
    separators = ["-", "/", ".", ""]
    for sep in separators:
        fmt = f"%Y{sep}%m{sep}%d" if sep else "%Y%m%d"
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue

    raise ValueError(f"无法解析日期格式: {date_str}")


def getYear(date_str: str) -> int:
    """
    获取日期字符串的年份

    Args:
        date_str: 输入日期字符串 YYYYMMDD

    Returns:
        int: 年份
    """
    if len(date_str) == 0 or date_str is None or date_str == "":
        # 返回当前日期年份
        return datetime.now().year

    date_str = date_str.replace("-", "")
    return date_str[:4]

def get_quarter_end_date(date_str: str) -> str:
    """
    获取指定日期所在季度的季末日期

    Args:
        date_str: 输入日期字符串 YYYYMMDD

    Returns:
        str: 季度末日期（YYYYMMDD）
    """
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    quarter = (date_obj.month - 1) // 3 + 1
    # 计算季末月份
    quarter_end_month = quarter * 3

    # 获取该月的最后一天
    if quarter_end_month == 12:
        # 12月直接返回12月31日
        quarter_end_date = date_obj.replace(month=12, day=31)
    else:
        # 其他季度：下个月1号减1天
        next_month_first = date_obj.replace(month=quarter_end_month + 1, day=1)
        quarter_end_date = next_month_first - timedelta(days=1)

    return quarter_end_date.strftime("%Y%m%d")

def get_all_quarter_end_dates(date_str: str) -> list:
    """
    获取指定日期当年的所有季末日期

    Args:
        date_str: 输入日期字符串 YYYYMMDD

    Returns:
        list: 当年所有季度末日期列表 [YYYYMMDD, ...]
              例如: ['20260331', '20260630', '20260930', '20261231']
    """
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    year = date_obj.year

    # 生成当年所有季度的季末日期
    quarter_end_dates = []
    for quarter in range(1, 5):  # Q1, Q2, Q3, Q4
        quarter_end_month = quarter * 3

        # 获取该月的最后一天
        if quarter_end_month == 12:
            # 12月直接返回12月31日
            quarter_end_date = datetime(year, 12, 31)
        else:
            # 其他季度：下个月1号减1天
            next_month_first = datetime(year, quarter_end_month + 1, 1)
            quarter_end_date = next_month_first - timedelta(days=1)

        quarter_end_dates.append(quarter_end_date.strftime("%Y%m%d"))

    return quarter_end_dates


def generate_date_range(start_date: str, end_date: str) -> list:
    """
    生成起始日期到结束日期之间的所有自然日日期列表

    Args:
        start_date: 起始日期字符串，格式 YYYYMMDD
        end_date: 结束日期字符串，格式 YYYYMMDD

    Returns:
        list: 日期列表 [YYYYMMDD, ...]，按时间顺序排列
              例如: ['20250101', '20250102', ..., '20251231']

    Raises:
        ValueError: 日期格式错误或起始日期晚于结束日期
    """
    try:
        start_obj = datetime.strptime(start_date, "%Y%m%d")
        end_obj = datetime.strptime(end_date, "%Y%m%d")
    except ValueError as e:
        raise ValueError(f"日期格式错误，请使用 YYYYMMDD 格式: {e}")

    if start_obj > end_obj:
        raise ValueError(f"起始日期 ({start_date}) 不能晚于结束日期 ({end_date})")

    date_list = []
    current_date = start_obj
    while current_date <= end_obj:
        date_list.append(current_date.strftime("%Y%m%d"))
        current_date += timedelta(days=1)

    return date_list
