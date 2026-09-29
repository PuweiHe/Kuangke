"""
定时监控任务调度器

独立运行的定时任务脚本，每日凌晨1点自动执行全量监控
可通过系统服务或后台进程方式启动

使用方法:
    # 前台运行（调试用）
    python scheduler.py

    # 后台运行（Linux/Mac）
    nohup python scheduler.py > logs/scheduler.log 2>&1 &

    # 后台运行（Windows PowerShell）
    Start-Process python -ArgumentList "scheduler.py" -WindowStyle Hidden
"""

import sys
import signal
from pathlib import Path
from datetime import datetime

from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入配置和工具
from config.logging_config import setup_logging
from config.settings import SCHEDULER_CRON
from utils.notifier import Notifier
from utils.distributed_lock import run_exclusive_job
from monitors.monitor_runner import MonitorRunner


class ScheduledMonitor:
    """
    定时监控调度器

    负责在指定时间自动执行全量监控任务
    """

    def __init__(self, hour: int = 1, minute: int = 0):
        """
        初始化调度器

        Parameters
        ----------
        hour : int
            执行小时（0-23），默认1点
        minute : int
            执行分钟（0-59），默认0分
        """
        # 初始化日志
        setup_logging()

        # 初始化组件
        self.runner = MonitorRunner()
        self.notifier = Notifier()
        self.scheduler = BlockingScheduler()

        # 保存执行时间配置
        self.hour = hour
        self.minute = minute

        logger.info("=" * 60)
        logger.info("定时监控调度器启动")
        logger.info(f"执行时间: 每日 {hour:02d}:{minute:02d}")
        logger.info("=" * 60)

        # 注册信号处理器，优雅退出
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        信号处理器，捕获中断信号并优雅退出
        """
        logger.info(f"收到信号 {signum}，正在关闭调度器...")
        self.shutdown()
        sys.exit(0)

    def execute_monitor_task(self):
        """
        执行监控任务

        被调度器定时调用的入口函数
        """
        try:
            executed, _ = run_exclusive_job("daily_risk_monitor", self._execute_monitor_task_unlocked)
            if not executed:
                logger.info("另一实例正在执行定时任务，本实例跳过")
        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _execute_monitor_task_unlocked(self):
        """Run monitoring and notifications after the scheduler lease is acquired."""
        try:
            logger.info("=" * 60)
            logger.info("开始执行定时监控任务")
            logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)

            # 使用昨天的日期作为业务日期
            from utils.date_utils import get_yesterday, normalize_business_date
            biz_date = normalize_business_date(get_yesterday())

            logger.info(f"业务日期: {biz_date}")

            # 执行全量监控
            result = self.runner.run(biz_date=biz_date)

            # 输出结果摘要
            status = result.get("status")
            total = result.get("total_count", 0)
            success = result.get("success_count", 0)
            fail = result.get("fail_count", 0)

            logger.info("=" * 60)
            logger.info(f"监控完成 | 状态: {status} | 总数: {total} | 成功: {success} | 失败: {fail}")
            logger.info("=" * 60)

            if status == "completed" and fail == 0:
                try:
                    self.notifier.send_email_alert(biz_date)
                except Exception as e:
                    logger.error(f"发送预警邮件异常: {e}")

            logger.info("定时监控任务完成")

        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def start(self):
        """
        启动调度器

        开始监听定时任务，阻塞运行
        """
        logger.info(f"添加定时任务: 每日 {self.hour:02d}:{self.minute:02d} 执行全量监控")

        # 添加定时任务
        self.scheduler.add_job(
            func=self.execute_monitor_task,
            trigger="cron",
            hour=self.hour,
            minute=self.minute,
            id="daily_full_monitor",
            name="每日全量监控",
            replace_existing=True,
            misfire_grace_time=3600,  # 允许1小时的容错时间
        )

        logger.info("调度器已启动，按 Ctrl+C 停止")
        logger.info(f"下次执行时间: 今天 {self.hour:02d}:{self.minute:02d} 或明天 {self.hour:02d}:{self.minute:02d}")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("调度器已停止")
            self.shutdown()

    def shutdown(self):
        """
        关闭调度器，清理资源
        """
        logger.info("正在关闭调度器...")

        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已停止")

        # 关闭数据库连接池
        try:
            from db.factory import get_pool
            pool = get_pool()
            # 兼容不同连接池的关闭方法
            if hasattr(pool, 'close_all'):
                pool.close_all()
            elif hasattr(pool, 'close'):
                pool.close()
            logger.info("数据库连接池已关闭")
        except Exception as e:
            logger.error(f"关闭连接池失败: {e}")

        logger.info("调度器已完全关闭")


def main():
    """
    主函数
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="定时监控任务调度器 - 每日凌晨1点执行全量监控",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认时间（凌晨1点）
  python scheduler.py

  # 自定义执行时间
  python scheduler.py --hour 2 --minute 30

  # 立即执行一次测试
  python scheduler.py --test
        """,
    )

    parser.add_argument(
        "--hour",
        type=int,
        default=1,
        help="执行小时（0-23），默认1",
    )

    parser.add_argument(
        "--minute",
        type=int,
        default=0,
        help="执行分钟（0-59），默认0",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="立即执行一次监控任务进行测试",
    )

    args = parser.parse_args()

    # 创建调度器实例
    scheduler = ScheduledMonitor(hour=args.hour, minute=args.minute)

    try:
        if args.test:
            # 测试模式：立即执行一次
            logger.info("测试模式：立即执行监控任务")
            scheduler.execute_monitor_task()
            logger.info("测试完成")
        else:
            # 正常模式：启动定时调度
            scheduler.start()
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"调度器运行异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
