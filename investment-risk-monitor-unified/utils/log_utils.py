"""
日志工具模块

基于 loguru 提供统一的日志获取接口，
供所有模块使用。
"""

from loguru import logger

from config.settings import LOG_DIR, LOG_LEVEL


def get_logger(name: str = "risk_monitor") -> logger:
    """
    获取命名日志器

    Parameters
    ----------
    name : str
        日志器名称，默认 'risk_monitor'

    Returns
    -------
    loguru.Logger
    """
    import os

    log_dir = LOG_DIR
    os.makedirs(log_dir, exist_ok=True)

    # 移除默认 handler，避免重复输出
    logger.remove()

    # 控制台输出
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level}</level> | "
               f"<cyan>{{name}}</cyan> | "
               "{message}",
    )

    # 文件输出
    logger.add(
        os.path.join(log_dir, f"{name}.log"),
        level=LOG_LEVEL,
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
    )

    return logger.bind(name=name)
