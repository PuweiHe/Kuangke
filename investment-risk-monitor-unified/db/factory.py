"""
数据库连接池工厂模块

根据配置的数据库类型（MySQL/PostgreSQL）自动创建对应的连接池实例。
提供统一的接口，屏蔽底层数据库差异。
"""

import logging
import threading
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List

from config.settings import DB_TYPE, get_db_config

logger = logging.getLogger(__name__)


class BaseConnectionPool(ABC):
    """
    数据库连接池抽象基类

    所有具体的连接池实现都必须继承此类并实现其方法
    """

    @abstractmethod
    def get_connection(self):
        """获取一个数据库连接"""
        pass

    @abstractmethod
    def release_connection(self, conn):
        """归还连接到连接池"""
        pass

    @abstractmethod
    def close_all(self):
        """关闭所有连接"""
        pass

    @property
    @abstractmethod
    def pool_status(self) -> dict:
        """返回连接池状态"""
        pass


def create_connection_pool() -> BaseConnectionPool:
    """
    根据配置的数据库类型创建对应的连接池

    Returns
    -------
    BaseConnectionPool
        MySQL 或 PostgreSQL 连接池实例

    Raises
    ------
    ValueError
        不支持的数据库类型
    ImportError
        缺少必要的依赖包
    """
    logger.info(f"正在创建 {DB_TYPE.upper()} 数据库连接池...")

    if DB_TYPE == "mysql":
        # 使用现有的 MySQL 连接池
        from db.connection import DBConnectionPool
        return DBConnectionPool()

    elif DB_TYPE == "pg":
        # 使用 PostgreSQL 连接池（psycopg2 版本，兼容 openGauss）
        try:
            from db.pg_connection_psycopg2 import PGConnectionPool
            return PGConnectionPool()
        except ImportError as e:
            logger.error("PostgreSQL 支持需要安装 psycopg2-binary 包")
            raise ImportError(f"请运行 'pip install psycopg2-binary' 安装依赖: {e}")

    else:
        raise ValueError(f"不支持的数据库类型: {DB_TYPE}，仅支持 'mysql' 或 'pg'")


# 全局单例
_global_pool: Optional[BaseConnectionPool] = None
_pool_lock = threading.Lock()  # 将在首次使用时初始化


def get_pool() -> BaseConnectionPool:
    """
    获取全局连接池单例（懒加载，线程安全）

    根据配置自动选择 MySQL 或 PostgreSQL 连接池

    Returns
    -------
    BaseConnectionPool
        数据库连接池实例
    """
    global _global_pool, _pool_lock

    if _global_pool is None:

        with _pool_lock:
            if _global_pool is None:
                logger.info(f"首次调用 get_pool()，创建 {DB_TYPE.upper()} 连接池单例...")
                _global_pool = create_connection_pool()

    return _global_pool


def reset_pool():
    """
    重置全局连接池（主要用于测试或重新配置后）
    """
    global _global_pool
    if _global_pool is not None:
        logger.info("重置数据库连接池...")
        # 兼容不同连接池的关闭方法
        if hasattr(_global_pool, 'close_all'):
            _global_pool.close_all()
        elif hasattr(_global_pool, 'close'):
            _global_pool.close()
        else:
            logger.warning(f"连接池 {type(_global_pool).__name__} 没有 close 或 close_all 方法")
        _global_pool = None
