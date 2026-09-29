"""
数据库查询适配器模块

提供统一的查询接口，自动适配 MySQL 和 PostgreSQL 的语法差异。
主要处理：
1. SQL 占位符转换（MySQL: %s, PostgreSQL: $1, $2, ...）
2. 连接获取方式的统一
3. 结果集格式的统一
"""

import re
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from config.settings import DB_TYPE
from db.factory import get_pool


def _convert_placeholders(sql: str) -> str:
    """
    将 MySQL 风格的占位符 (%s) 转换为 PostgreSQL 风格 ($1, $2, ...)

    Parameters
    ----------
    sql : str
        SQL 语句

    Returns
    -------
    str
        转换后的 SQL 语句

    Examples
    --------
    >>> _convert_placeholders("SELECT * FROM users WHERE id = %s AND name = %s")
    'SELECT * FROM users WHERE id = $1 AND name = $2'
    """
    if DB_TYPE == "mysql":
        return sql

    # PostgreSQL: 将 %s 替换为 $1, $2, $3...
    placeholder_count = [0]

    def replace_placeholder(match):
        placeholder_count[0] += 1
        return f"${placeholder_count[0]}"

    # 匹配 %s 但不匹配 %%s (转义的百分号)
    converted_sql = re.sub(r'(?<!%)%s', replace_placeholder, sql)


    return converted_sql


def _execute_query_mysql(sql: str, params: Optional[Any] = None) -> List[Dict]:
    """
    执行 MySQL 查询

    Parameters
    ----------
    sql : str
        SQL 语句
    params : Any, optional
        参数化查询参数

    Returns
    -------
    list[dict]
        查询结果
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"执行 MySQL 查询:")
    logger.info(f"{'='*80}")

    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql, params)
                result = cursor.fetchall()
                logger.info(f"MySQL 查询完成，返回 {len(result)} 条记录")
                return result
            except Exception as e:
                logger.error(f"MySQL 查询失败: {type(e).__name__}")
                raise


def _execute_query_pg(sql: str, params: Optional[Any] = None) -> List[Dict]:
    """
    执行 PostgreSQL 查询（使用 psycopg2）

    Parameters
    ----------
    sql : str
        SQL 语句
    params : Any, optional
        参数化查询参数

    Returns
    -------
    list[dict]
        查询结果
    """
    # psycopg2 不需要转换占位符，直接使用 %s
    converted_sql = sql

    logger.info(f"\n{'='*80}")
    logger.info(f"执行 PostgreSQL 查询:")
    logger.info(f"{'='*80}")

    pool = get_pool()
    with pool.connection() as conn:
        try:
            cursor = conn.cursor()
            try:
                # psycopg2 使用 cursor.execute() 执行查询
                if params is None:
                    cursor.execute(converted_sql)
                elif isinstance(params, (list, tuple)):
                    cursor.execute(converted_sql, params)
                elif isinstance(params, dict):
                    cursor.execute(converted_sql, params)
                else:
                    cursor.execute(converted_sql, (params,))

                # 获取列名
                columns = [desc[0] for desc in cursor.description]

                # 将结果转换为字典列表
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

                logger.info(f"PostgreSQL 查询完成，返回 {len(result)} 条记录")
                return result
            finally:
                cursor.close()
        except Exception as e:
            logger.error(f"PostgreSQL 查询失败: {type(e).__name__}")
            raise


def execute_query(sql: str, params: Optional[Any] = None) -> List[Dict]:
    """
    执行 SELECT 查询，返回字典列表

    根据配置的数据库类型自动选择对应的执行方式

    Parameters
    ----------
    sql : str
        SQL 语句
    params : Any, optional
        参数化查询参数，支持 tuple / dict

    Returns
    -------
    list[dict]
        查询结果，每行一个字典

    Examples
    --------
    >>> rows = execute_query("SELECT * FROM t_user WHERE age > %s", (18,))
    """
    if DB_TYPE == "mysql":
        return _execute_query_mysql(sql, params)
    elif DB_TYPE == "pg":
        return _execute_query_pg(sql, params)
    else:
        raise ValueError(f"不支持的数据库类型: {DB_TYPE}")


def _execute_update_mysql(sql: str, params: Optional[Any] = None) -> int:
    """
    执行 MySQL 写操作

    Parameters
    ----------
    sql : str
        SQL 语句
    params : Any, optional
        参数化查询参数

    Returns
    -------
    int
        受影响行数
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"执行 MySQL 更新:")
    logger.info(f"{'='*80}")

    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            try:
                affected = cursor.execute(sql, params)
                logger.info(f"MySQL 更新完成，影响 {affected} 行")
                return affected
            except Exception as e:
                logger.error(f"MySQL 更新失败: {type(e).__name__}")
                raise


def _execute_update_pg(sql: str, params: Optional[Any] = None) -> int:
    """
    执行 PostgreSQL 写操作（使用 psycopg2）

    Parameters
    ----------
    sql : str
        SQL 语句
    params : Any, optional
        参数化查询参数

    Returns
    -------
    int
        受影响行数
    """
    # psycopg2 不需要转换占位符，直接使用 %s
    converted_sql = sql

    logger.info(f"\n{'='*80}")
    logger.info(f"执行 PostgreSQL 更新:")
    logger.info(f"{'='*80}")

    pool = get_pool()
    with pool.connection() as conn:
        try:
            cursor = conn.cursor()
            try:
                # psycopg2 使用 cursor.execute() 执行写操作
                if params is None:
                    cursor.execute(converted_sql)
                elif isinstance(params, (list, tuple)):
                    cursor.execute(converted_sql, params)
                elif isinstance(params, dict):
                    cursor.execute(converted_sql, params)
                else:
                    cursor.execute(converted_sql, (params,))

                conn.commit()
                affected = cursor.rowcount

                logger.info(f"PostgreSQL 更新完成，影响 {affected} 行")
                return affected
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
        except Exception as e:
            logger.error(f"PostgreSQL 更新失败: {type(e).__name__}")
            raise


def execute_update(sql: str, params: Optional[Any] = None) -> int:
    """
    执行写操作（INSERT / UPDATE / DELETE），返回受影响行数

    根据配置的数据库类型自动选择对应的执行方式

    Parameters
    ----------
    sql : str
        SQL 语句
    params : Any, optional
        参数化查询参数

    Returns
    -------
    int
        受影响行数

    Examples
    --------
    >>> affected = execute_update("UPDATE t_user SET name=%s WHERE id=%s", ("Tom", 1))
    """
    if DB_TYPE == "mysql":
        return _execute_update_mysql(sql, params)
    elif DB_TYPE == "pg":
        return _execute_update_pg(sql, params)
    else:
        raise ValueError(f"不支持的数据库类型: {DB_TYPE}")


# ============================================================
#  查询快捷方式（与原有 db.query 保持一致）
# ============================================================

def query_one(sql: str, params: Optional[Any] = None) -> Optional[Dict]:
    """查询单条记录"""
    rows = execute_query(sql, params)
    return rows[0] if rows else None


def query_all(sql: str, params: Optional[Any] = None) -> List[Dict]:
    """查询全部匹配记录"""
    return execute_query(sql, params)


def query_to_dataframe(sql: str, params: Optional[Any] = None) -> pd.DataFrame:
    """查询结果直接转为 pandas DataFrame"""
    rows = execute_query(sql, params)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


# ============================================================
#  增删改快捷方式（与原有 db.query 保持一致）
# ============================================================

def insert_one(table: str, data: Dict[str, Any]) -> int:
    """向指定表插入单条记录"""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    params = tuple(data.values())
    return execute_update(sql, params)


def insert_many(table: str, data_list: List[Dict[str, Any]]) -> int:
    """批量插入记录"""
    if not data_list:
        return 0

    sample = data_list[0]
    columns = ", ".join(sample.keys())
    placeholders = ", ".join(["%s"] * len(sample))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    # 对于批量插入，需要逐条执行（psycopg2 的 executemany 行为不同）
    total_affected = 0
    for row in data_list:
        params = tuple(row.values())
        total_affected += execute_update(sql, params)

    return total_affected


def update(table: str, data: Dict[str, Any], where: str, where_params: Optional[Any] = None) -> int:
    """更新指定表中满足条件的记录"""
    set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
    sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

    values = list(data.values())
    if where_params:
        if isinstance(where_params, (list, tuple)):
            values.extend(where_params)
        else:
            values.append(where_params)

    return execute_update(sql, tuple(values))


def delete(table: str, where: str, where_params: Optional[Any] = None) -> int:
    """删除指定表中满足条件的记录"""
    sql = f"DELETE FROM {table} WHERE {where}"
    return execute_update(sql, where_params)
