"""
日志配置模块
使用 loguru 配置控制台输出和按日期滚动的文件输出
"""

import os
import sys

from loguru import logger

from config.settings import LOG_DIR, LOG_LEVEL


def setup_logging() -> None:
    """
    初始化日志配置：
    - 输出到控制台
    - 输出到 logs/ 目录下按日期滚动的文件
    """
    # 确保日志目录存在
    os.makedirs(LOG_DIR, exist_ok=True)

    # 移除默认的 handler
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
    )

    # 文件输出：按日期滚动，每天生成一个新文件
    log_file_path = os.path.join(LOG_DIR, "risk_monitor_{time:YYYY-MM-DD}.log")
    logger.add(
        log_file_path,
        level=LOG_LEVEL,
        rotation="00:00",      # 每天午夜自动滚动
        retention="30 days",   # 保留最近30天的日志
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
