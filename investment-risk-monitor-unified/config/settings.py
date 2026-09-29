"""Application settings loaded from environment variables.

Checked-in defaults are suitable only for a local demonstration database.
"""

import os
from dataclasses import dataclass


def _integer(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


@dataclass(frozen=True)
class SchedulerConfig:
    hour: int = _integer("MONITOR_HOUR", 8)
    minute: int = _integer("MONITOR_MINUTE", 0)


DB_TYPE = os.getenv("DB_TYPE", "mysql").lower()
if DB_TYPE not in {"mysql", "pg"}:
    raise ValueError("DB_TYPE must be 'mysql' or 'pg'")

DB_CONFIG = {
    "type": DB_TYPE,
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": _integer("DB_PORT", 3306 if DB_TYPE == "mysql" else 5432),
    "dbname": os.getenv("DB_NAME", "risk_monitor_demo"),
    "user": os.getenv("DB_USER", "demo_user"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_db_config() -> dict:
    return DB_CONFIG.copy()


DB_POOL_MIN = _integer("DB_POOL_MIN", 1)
DB_POOL_MAX = _integer("DB_POOL_MAX", 10)
WIDE_TABLE_NAME = os.getenv("WIDE_TABLE_NAME", "position_snapshot")
WIDE_TABLE_DATE_COLUMN = os.getenv("WIDE_TABLE_DATE_COLUMN", "biz_date")
WIDE_TABLE_ASSET_CATEGORY_COLUMN = os.getenv("WIDE_TABLE_ASSET_CATEGORY_COLUMN", "asset_category")
SCHEDULER_CRON = SchedulerConfig()
MONITOR_START_DATE = os.getenv("MONITOR_START_DATE", "2025-01-01")
BASE_DATE = os.getenv("BASE_DATE", "2024-12-31")
FORBIDDEN_PROVINCES = [v.strip() for v in os.getenv("FORBIDDEN_PROVINCES", "").split(",") if v.strip()]

# Optional example limits. Production rules belong in the rule configuration table.
BOND_INVESTMENT_LIMIT = _integer("BOND_INVESTMENT_LIMIT", 0)
STOCK_INVESTMENT_LIMIT = _integer("STOCK_INVESTMENT_LIMIT", 0)
FINANCIAL_PRODUCT_LIMIT = _integer("FINANCIAL_PRODUCT_LIMIT", 0)
BOND_HOLDING_RATIO_LIMIT = float(os.getenv("BOND_HOLDING_RATIO_LIMIT", "0"))
STOCK_HOLDING_RATIO_LIMIT = float(os.getenv("STOCK_HOLDING_RATIO_LIMIT", "0"))
LEVERAGE_RATIO_LIMIT = float(os.getenv("LEVERAGE_RATIO_LIMIT", "0"))
SINGLE_BOND_AMOUNT_LIMIT = _integer("SINGLE_BOND_AMOUNT_LIMIT", 0)
SINGLE_STOCK_AMOUNT_LIMIT = _integer("SINGLE_STOCK_AMOUNT_LIMIT", 0)
SINGLE_BOND_BALANCE_RATIO_LIMIT = float(os.getenv("SINGLE_BOND_BALANCE_RATIO_LIMIT", "0"))
BOND_TOTAL_ASSET_RATIO_LIMIT = float(os.getenv("BOND_TOTAL_ASSET_RATIO_LIMIT", "0"))
FINANCIAL_PRODUCT_TOTAL_ASSET_RATIO_LIMIT = float(os.getenv("FINANCIAL_PRODUCT_TOTAL_ASSET_RATIO_LIMIT", "0"))

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
EMAIL_API_URL = os.getenv("EMAIL_API_URL", "")
EMAIL_TO_LIST = [v.strip() for v in os.getenv("EMAIL_TO", "").split(",") if v.strip()]
EMAIL_CC_LIST = [v.strip() for v in os.getenv("EMAIL_CC", "").split(",") if v.strip()]
EMAIL_NOTIFICATION_ENABLED = os.getenv("EMAIL_NOTIFICATION_ENABLED", "false").lower() == "true"
