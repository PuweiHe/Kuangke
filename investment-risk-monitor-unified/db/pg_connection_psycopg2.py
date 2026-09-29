"""
PostgreSQL 连接池实现（使用 psycopg2）
使用 psycopg2 库创建线程安全的 PostgreSQL 连接池
这是为了兼容某些 PostgreSQL 版本的特殊数据类型（如 int1）
"""
import threading
from contextlib import contextmanager
from typing import Optional, Any, Dict
import logging

import psycopg2
from psycopg2 import pool

from config.settings import get_db_config, DB_POOL_MIN, DB_POOL_MAX

logger = logging.getLogger(__name__)


class PGConnectionPool:
    """PostgreSQL 连接池（线程安全，使用 psycopg2）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 获取数据库配置（自动解密密码）
        db_config = get_db_config()

        # 数据库配置
        self._host = db_config['host']
        self._port = db_config['port']
        self._user = db_config['user']
        self._password = db_config['password']
        self._database = db_config['dbname']
        self._min_size = DB_POOL_MIN
        self._max_size = DB_POOL_MAX

        # 同步连接池
        self._pool: Optional[pool.ThreadedConnectionPool] = None
        self._pool_lock = threading.Lock()

        # 初始化连接池
        self._create_pool()

        self._initialized = True
        logger.info("PostgreSQL 连接池初始化完成（psycopg2）")

    def _create_pool(self):
        """创建 psycopg2 连接池"""
        logger.debug("尝试创建 psycopg2 连接池")
        try:
            self._pool = pool.ThreadedConnectionPool(
                minconn=self._min_size,
                maxconn=self._max_size,
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=self._database,
            )
            logger.debug(f"成功创建 psycopg2 连接池")
        except Exception as e:
            logger.error(f"创建 PostgreSQL 连接池失败: {e}")
            raise

    def get_connection(self):
        """获取一个数据库连接"""
        with self._pool_lock:
            if self._pool is None:
                raise RuntimeError("PostgreSQL 连接池未初始化")

            logger.debug(f"从 PostgreSQL 连接池获取连接")
            try:
                conn = self._pool.getconn()
                logger.debug(f"成功获取 PostgreSQL 连接")
                return conn
            except Exception as e:
                logger.error(f"获取 PostgreSQL 连接失败: {e}")
                raise

    def release_connection(self, conn):
        """释放一个数据库连接回连接池"""
        with self._pool_lock:
            if self._pool is None:
                return

            logger.debug(f"归还 PostgreSQL 连接到连接池")
            try:
                self._pool.putconn(conn)
                logger.debug(f"成功归还 PostgreSQL 连接")
            except Exception as e:
                logger.error(f"归还 PostgreSQL 连接失败: {e}")

    def execute_query(self, sql: str, params: tuple = None) -> list:
        """执行查询并返回结果"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            try:
                if params is None:
                    cursor.execute(sql)
                elif isinstance(params, (list, tuple)):
                    cursor.execute(sql, params)
                elif isinstance(params, dict):
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql, (params,))

                # 将结果转换为字典列表
                columns = [desc[0] for desc in cursor.description]
                result = []
                for row in cursor.fetchall():
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # 处理 Decimal 类型
                        if hasattr(value, '__class__') and 'Decimal' in value.__class__.__name__:
                            value = float(value)
                        row_dict[col] = value
                    result.append(row_dict)

                return result
            finally:
                cursor.close()
        finally:
            self.release_connection(conn)

    def execute_update(self, sql: str, params: tuple = None) -> int:
        """执行更新操作并返回影响行数"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            try:
                if params is None:
                    cursor.execute(sql)
                elif isinstance(params, (list, tuple)):
                    cursor.execute(sql, params)
                elif isinstance(params, dict):
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql, (params,))

                conn.commit()
                return cursor.rowcount
            finally:
                cursor.close()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.release_connection(conn)

    @contextmanager
    def connection(self):
        """上下文管理器，自动管理连接的获取和释放"""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception as e:
                logger.warning(f"回滚失败: {e}")
            raise
        finally:
            try:
                self.release_connection(conn)
            except Exception as e:
                logger.error(f"释放连接失败: {e}")

    def close(self):
        """关闭连接池"""
        with self._pool_lock:
            if self._pool is not None:
                logger.debug("正在关闭 PostgreSQL 连接池")
                try:
                    self._pool.closeall()
                    self._pool = None
                    logger.debug("PostgreSQL 连接池已关闭")
                except Exception as e:
                    logger.error(f"关闭 PostgreSQL 连接池失败: {e}")

    def __del__(self):
        """析构函数，确保连接池被正确关闭"""
        try:
            self.close()
        except:
            pass
