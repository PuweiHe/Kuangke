"""
数据库配置模块

提供数据库连接与连接池配置的函数式接口，
便于按需获取配置信息。
"""

from config.settings import DB_POOL_MIN, DB_POOL_MAX
from config.settings import get_db_config as _get_environment_db_config


def get_db_config() -> dict:
    """
    获取环境变量中的数据库连接配置

    Returns
    -------
    dict
        包含 host / port / dbname / user / password 的连接配置
    """
    return _get_environment_db_config()


def get_pool_config() -> dict:
    """
    获取连接池配置

    Returns
    -------
    dict
        包含 min_connections / max_connections 的连接池配置
    """
    return {
        "min_connections": DB_POOL_MIN,
        "max_connections": DB_POOL_MAX,
    }
