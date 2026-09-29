"""DB-API queries shared by MySQL and PostgreSQL; bind values at call sites."""

import re
from decimal import Decimal
from db.factory import get_pool


def execute_query(sql, params=None):
    with get_pool().connection() as conn, conn.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if not rows or isinstance(rows[0], dict):
            return list(rows)
        columns = [column[0] for column in cursor.description]
        return [
            dict(zip(columns, (float(v) if isinstance(v, Decimal) else v for v in row)))
            for row in rows
        ]


def execute_update(sql, params=None):
    with get_pool().connection() as conn, conn.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.rowcount


def query_one(sql, params=None):
    rows = execute_query(sql, params)
    return rows[0] if rows else None


def query_all(sql, params=None):
    return execute_query(sql, params)


def query_to_dataframe(sql, params=None):
    import pandas as pd

    return pd.DataFrame(execute_query(sql, params))


def _identifier(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError("Invalid SQL identifier")
    return name


def insert_one(table, data):
    return insert_many(table, [data])


def insert_many(table, data_list):
    if not data_list:
        return 0
    columns = tuple(data_list[0])
    if not columns or any(set(row) != set(columns) for row in data_list):
        raise ValueError("Rows must have the same nonempty columns")
    column_sql = ", ".join(_identifier(c) for c in columns)
    sql = f"INSERT INTO {_identifier(table)} ({column_sql}) VALUES ({', '.join(['%s'] * len(columns))})"
    values = [tuple(row[c] for c in columns) for row in data_list]
    # The pool context commits the entire batch or rolls it back on failure.
    with get_pool().connection() as conn, conn.cursor() as cursor:
        cursor.executemany(sql, values)
        return cursor.rowcount


def update(table, data, where, where_params=None):
    """The WHERE expression is application SQL; user values belong in params."""
    if not data or not where.strip():
        raise ValueError("An update requires values and a WHERE expression")
    columns = ", ".join(f"{_identifier(k)} = %s" for k in data)
    params = list(data.values())
    if where_params is not None:
        params.extend(where_params if isinstance(where_params, (list, tuple)) else [where_params])
    return execute_update(f"UPDATE {_identifier(table)} SET {columns} WHERE {where}", tuple(params))


def delete(table, where, where_params=None):
    """The WHERE expression must be trusted application SQL."""
    if not where.strip():
        raise ValueError("A delete requires a WHERE expression")
    return execute_update(f"DELETE FROM {_identifier(table)} WHERE {where}", where_params)
