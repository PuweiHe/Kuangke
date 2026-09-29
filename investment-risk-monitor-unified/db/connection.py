"""
数据库连接池管理模块

基于 pymysql 实现线程安全的连接池，供查询工具和业务模块复用。
支持上下文管理器自动获取/归还连接。
"""

import threading
from contextlib import contextmanager
from typing import Optional
import logging

import pymysql
from pymysql.cursors import DictCursor

from config.settings import DB_POOL_MIN, DB_POOL_MAX, get_db_config
from db.factory import BaseConnectionPool

# 获取日志记录器
logger = logging.getLogger(__name__)


class DBConnectionPool(BaseConnectionPool):
    """
    线程安全的 MySQL 连接池

    Parameters
    ----------
    host : str
        数据库主机地址
    port : int
        数据库端口
    user : str
        用户名
    password : str
        密码
    database : str
        数据库名
    min_size : int
        最小连接数（预热连接数）
    max_size : int
        最大连接数
    charset : str
        字符集，默认 utf8mb4
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        min_size: int = DB_POOL_MIN,
        max_size: int = DB_POOL_MAX,
        charset: str = "utf8mb4",
    ):
        logger.info("开始初始化数据库连接池...")
        # 如果未提供参数，从配置中获取（自动解密密码）
        if any(v is None for v in [host, port, user, password, database]):
            logger.debug("使用配置文件中的数据库连接参数")
            db_config = get_db_config()
            host = host or db_config["host"]
            port = port or db_config["port"]
            user = user or db_config["user"]
            password = password or db_config["password"]
            database = database or db_config["dbname"]

        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database
        self._charset = charset
        self._min_size = min_size
        self._max_size = max_size

        self._pool: list = []          # 空闲连接
        self._used: set = set()        # 正在使用的连接 id 集合
        self._lock = threading.Lock()

        # 预热最小连接数
        logger.info("数据库连接池配置已加载")
        logger.info(f"连接池大小: min={min_size}, max={max_size}")
        self._warmup()
        logger.info(f"数据库连接池初始化完成，已创建 {len(self._pool)} 个预热连接")

    # -------------------- 内部方法 --------------------

    def _create_connection(self):
        """创建一条新的 pymysql 连接"""
        logger.debug("尝试创建新的数据库连接")
        try:
            conn = pymysql.connect(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=self._database,
                charset=self._charset,
                cursorclass=DictCursor,
                autocommit=False,
            )
            logger.debug(f"成功创建数据库连接 (conn_id={id(conn)})")
            return conn
        except Exception as e:
            logger.error("创建数据库连接失败: %s", type(e).__name__)
            raise

    def _warmup(self):
        """预热连接池，创建 min_size 条连接"""
        logger.info(f"开始预热连接池，创建 {self._min_size} 个初始连接...")
        success_count = 0
        fail_count = 0
        for i in range(self._min_size):
            try:
                conn = self._create_connection()
                self._pool.append(conn)
                success_count += 1
                logger.debug(f"预热连接 [{i+1}/{self._min_size}] 创建成功")
            except Exception as e:
                fail_count += 1
                logger.error(f"预热连接 [{i+1}/{self._min_size}] 创建失败: {e}")

        if fail_count > 0:
            logger.warning(f"连接池预热完成: 成功 {success_count}, 失败 {fail_count}")
        else:
            logger.info(f"连接池预热完成: 成功创建 {success_count} 个连接")

    def _is_alive(self, conn) -> bool:
        """检测连接是否仍然存活"""
        try:
            conn.ping(reconnect=True)
            return True
        except Exception as e:
            logger.debug(f"连接检测失败 (conn_id={id(conn)}): {e}")
            return False

    # -------------------- 公开 API --------------------

    def get_connection(self):
        """
        从连接池获取一条可用连接

        Returns
        -------
        pymysql.connections.Connection

        Raises
        ------
        RuntimeError
            连接池已耗尽（达到 max_size）
        """
        with self._lock:
            # 优先复用空闲连接
            while self._pool:
                conn = self._pool.pop()
                if self._is_alive(conn):
                    self._used.add(id(conn))
                    logger.debug(f"从连接池获取连接 (conn_id={id(conn)}, 空闲={len(self._pool)}, 使用中={len(self._used)})")
                    return conn
                # 死连接，直接关闭
                logger.debug(f"检测到死连接，关闭并丢弃 (conn_id={id(conn)})")
                try:
                    conn.close()
                except Exception as e:
                    logger.debug(f"关闭死连接时出错: {e}")
                    pass

            # 空闲池为空，尝试新建
            if len(self._used) < self._max_size:
                logger.debug(f"连接池空闲，创建新连接 (当前使用={len(self._used)}, 最大={self._max_size})")
                conn = self._create_connection()
                self._used.add(id(conn))
                return conn

            logger.error(f"连接池已耗尽! 当前使用 {len(self._used)}/{self._max_size}")
            raise RuntimeError(
                f"连接池已耗尽，当前使用 {len(self._used)}/{self._max_size}"
            )

    def release_connection(self, conn):
        """
        归还连接到连接池

        Parameters
        ----------
        conn : pymysql.connections.Connection
            要归还的连接
        """
        with self._lock:
            self._used.discard(id(conn))
            if self._is_alive(conn):
                self._pool.append(conn)
                logger.debug(f"归还连接到连接池 (conn_id={id(conn)}, 空闲={len(self._pool)}, 使用中={len(self._used)})")
            else:
                logger.debug(f"连接已失效，丢弃不归还 (conn_id={id(conn)})")
                try:
                    conn.close()
                except Exception as e:
                    logger.debug(f"关闭失效连接时出错: {e}")
                    pass

    def close_all(self):
        """关闭连接池中所有连接"""
        with self._lock:
            for conn in self._pool:
                try:
                    conn.close()
                except Exception:
                    pass
            for conn_id in list(self._used):
                # 已使用的连接无法安全关闭，仅记录
                pass
            self._pool.clear()
            self._used.clear()

    @property
    def pool_status(self) -> dict:
        """返回连接池当前状态"""
        with self._lock:
            return {
                "idle": len(self._pool),
                "in_use": len(self._used),
                "max_size": self._max_size,
            }

    @contextmanager
    def connection(self):
        """
        上下文管理器：自动获取与归还连接

        Yields
        ------
        pymysql.connections.Connection

        Examples
        --------
        >>> with pool.connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT 1")
        ...     result = cursor.fetchall()
        """
        conn = self.get_connection()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            self.release_connection(conn)


# -------------------- 全局单例 --------------------

_global_pool: Optional[DBConnectionPool] = None
_pool_lock = threading.Lock()


def get_pool() -> DBConnectionPool:
    """
    获取全局连接池单例（懒加载，线程安全）

    Returns
    -------
    DBConnectionPool
    """
    global _global_pool
    if _global_pool is None:
        with _pool_lock:
            if _global_pool is None:
                logger.info("首次调用 get_pool()，创建全局数据库连接池单例...")
                _global_pool = DBConnectionPool()
    return _global_pool
