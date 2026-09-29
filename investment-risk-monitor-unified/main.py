"""
资管风险监控系统 - 主入口

功能:
1. 定时调度执行监控任务（默认每日08:00）
2. 支持立即执行全量监控
3. 支持按监控ID执行单个指标
4. 支持按监控类型批量执行

使用方法:
    # 启动定时调度器
    python main.py

    # 立即执行全部监控
    python main.py --run-now

    # 执行单个监控指标
    python main.py --run-now --monitor "BW-RB-0001"

    # 按监控类型执行
    python main.py --run-now --type "black_white"

    # 指定业务日期
    python main.py --run-now --date 2025-01-15
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import Optional

from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler

# 添加项目根目录到路径
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入配置和工具
from config.logging_config import setup_logging
from config.settings import SCHEDULER_CRON, MONITOR_START_DATE
from utils.date_utils import get_yesterday, generate_date_range, normalize_business_date
from utils.distributed_lock import run_exclusive_job
from utils.notifier import Notifier
from monitors.monitor_runner import MonitorRunner


class RiskMonitorApp:
    """
    风险监控系统主应用

    整合监控执行、通知、调度等功能
    """

    def __init__(self):
        # 初始化日志
        setup_logging()

        # 初始化组件
        self.runner = MonitorRunner()
        self.notifier = Notifier()
        self.scheduler = BlockingScheduler()

        logger.info("="*60)
        logger.info("资管风险监控系统启动")
        logger.info("="*60)

    def run_monitor(self, biz_date: Optional[str] = None, dimension: Optional[str] = None) -> dict:
        """
        执行全量监控任务

        Parameters
        ----------
        biz_date : str, optional
            业务日期，格式: YYYYMMDD
            如果不提供，使用昨天日期
        dimension : str, optional
            维度代码，如果不指定则执行所有维度

        Returns
        -------
        dict
            监控结果摘要
        """
        # 确定业务日期
        if biz_date is None:
            biz_date = get_yesterday()
        biz_date = normalize_business_date(biz_date)

        logger.info(f"开始执行业务日期 {biz_date} 的全量监控任务")

        try:
            result = self.runner.run(biz_date=biz_date, dimension=dimension)
            # 输出结果摘要
            status = result.get("status")
            total = result.get("total_count", 0)
            success = result.get("success_count", 0)
            fail = result.get("fail_count", 0)

            logger.info(f"监控完成 | 状态: {status} | 总数: {total} | 成功: {success} | 失败: {fail}")

            if status == "completed" and fail == 0:
                try:
                    self.notifier.send_email_alert(biz_date)
                except Exception as e:
                    logger.error(f"发送预警邮件异常: {e}")

            return result

        except Exception as e:
            logger.error(f"监控执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}

    def run_single_monitor(self, monitor_id: str, biz_date: Optional[str] = None, dimension: Optional[str] = None):
        """
        执行单个监控指标

        Parameters
        ----------
        monitor_id : str
            监控指标ID，如: "BW-RB-0001"
        biz_date : str, optional
            业务日期
        dimension : str, optional
            维度代码

        Returns
        -------
        dict
            监控执行结果
        """
        if biz_date is None:
            biz_date = get_yesterday()

        logger.info(f"执行单个监控指标: {monitor_id}, 日期: {biz_date}")

        result = self.runner.run_by_monitor_id(
            monitor_id=monitor_id,
            biz_date=biz_date,
            dimension=dimension
        )

        status = result.get("status")
        logger.info(f"监控指标 {monitor_id} 执行完成: {status}")

        if status == "error":
            logger.error(f"错误信息: {result.get('error')}")

        return result

    def run_monitor_by_type(self, monitor_type: str, biz_date: Optional[str] = None, dimension: Optional[str] = None):
        """
        按监控类型执行批量指标

        Parameters
        ----------
        monitor_type : str
            监控类型，如: "black_white", "investment_amount" 等
        biz_date : str, optional
            业务日期
        dimension : str, optional
            维度代码

        Returns
        -------
        dict
            监控结果摘要
        """
        if biz_date is None:
            biz_date = get_yesterday()

        logger.info(f"按监控类型执行: {monitor_type}, 日期: {biz_date}")

        result = self.runner.run_by_monitor_type(
            monitor_type=monitor_type,
            biz_date=biz_date,
            dimension=dimension
        )

        status = result.get("status")
        total = result.get("total_count", 0)
        success = result.get("success_count", 0)
        fail = result.get("fail_count", 0)

        logger.info(f"监控类型 {monitor_type} 执行完成 | 状态: {status} | 总数: {total} | 成功: {success} | 失败: {fail}")

        return result

    def run_batch_historical(self, start_date: str, end_date: str, dimension: Optional[str] = None):
        """
        批量重跑历史数据

        Parameters
        ----------
        start_date : str
            起始日期，格式: YYYYMMDD
        end_date : str
            结束日期，格式: YYYYMMDD
        dimension : str, optional
            维度代码，如果不指定则执行所有维度

        Returns
        -------
        dict
            批量执行结果摘要
        """
        logger.info("="*60)
        logger.info(f"开始批量重跑历史数据: {start_date} ~ {end_date}")
        logger.info("="*60)

        # 生成日期列表
        try:
            date_list = generate_date_range(start_date, end_date)
        except ValueError as e:
            logger.error(f"日期范围生成失败: {e}")
            raise

        total_days = len(date_list)
        logger.info(f"共需处理 {total_days} 天的数据")

        success_count = 0
        fail_count = 0
        failed_dates = []

        # 遍历日期列表
        for idx, biz_date in enumerate(date_list, 1):
            try:
                logger.info(f"[{idx}/{total_days}] 正在处理业务日期: {biz_date}")

                # 执行单日监控
                result = self.run_monitor(biz_date=biz_date, dimension=dimension)

                # 检查执行结果
                if result.get("status") in {"completed", "success"} and result.get("fail_count", 0) == 0:
                    success_count += 1
                    logger.info(f"[{idx}/{total_days}] 日期 {biz_date} 处理成功")
                else:
                    fail_count += 1
                    failed_dates.append(biz_date)
                    logger.warning(f"[{idx}/{total_days}] 日期 {biz_date} 处理失败: {result.get('error', '未知错误')}")

            except Exception as e:
                fail_count += 1
                failed_dates.append(biz_date)
                logger.error(f"[{idx}/{total_days}] 日期 {biz_date} 处理异常: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # 继续处理下一天，不中断整个流程
                continue

        # 输出总结
        logger.info("="*60)
        logger.info("批量重跑完成")
        logger.info(f"总天数: {total_days}")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {fail_count}")

        if failed_dates:
            logger.warning(f"失败日期列表: {', '.join(failed_dates)}")

        logger.info("="*60)

        return {
            "total": total_days,
            "success": success_count,
            "fail": fail_count,
            "failed_dates": failed_dates
        }

    def start_scheduler(self):
        """
        启动定时调度器

        根据配置的Cron表达式定时执行监控
        """
        hour = SCHEDULER_CRON.hour
        minute = SCHEDULER_CRON.minute

        logger.info(f"启动定时调度器: 每天 {hour:02d}:{minute:02d} 执行监控")

        # 添加定时任务
        self.scheduler.add_job(
            func=self._scheduled_run,
            trigger="cron",
            hour=hour,
            minute=minute,
            id="daily_monitor",
            name="每日风险监控",
            replace_existing=True,
        )

        logger.info("调度器已启动，按 Ctrl+C 停止")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("调度器已停止")
            self.shutdown()

    def _scheduled_run(self):
        """
        定时任务执行入口
        """
        try:
            logger.info("="*60)
            logger.info("开始执行定时监控任务")
            logger.info("="*60)

            # 使用昨天的日期作为业务日期
            biz_date = get_yesterday()
            executed, _ = run_exclusive_job(
                "daily_risk_monitor", lambda: self.run_monitor(biz_date)
            )
            if not executed:
                logger.info("另一实例正在执行定时任务，本实例跳过")
                return

            logger.info("定时监控任务完成")

        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def shutdown(self):
        """
        关闭应用，清理资源
        """
        logger.info("正在关闭系统...")

        if self.scheduler.running:
            self.scheduler.shutdown()

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

        logger.info("系统已关闭")


def parse_args():
    """
    解析命令行参数

    Returns
    -------
    argparse.Namespace
        解析后的参数
    """
    parser = argparse.ArgumentParser(
        description="资管风险监控系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动定时调度器
  python main.py

  # 立即执行全部监控
  python main.py --run-now

  # 执行单个监控指标
  python main.py --run-now --monitor "BW-RB-0001"

  # 按监控类型执行
  python main.py --run-now --type "black_white"

  # 指定业务日期
  python main.py --run-now --date 2025-01-15

  # 批量重跑历史数据（2025年全年）
  python main.py --run-now --start-date 20250101 --end-date 20251231

  # 批量重跑指定月份
  python main.py --run-now --start-date 20250601 --end-date 20250630
        """,
    )

    # 运行模式
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="立即执行监控任务（不启动调度器）",
    )

    # 业务日期
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="业务日期，格式: YYYYMMDD（默认使用昨天）",
    )

    # 监控类型
    parser.add_argument(
        "--type",
        type=str,
        default=None,
        help="监控类型，如: black_white, investment_amount 等",
    )

    # 单个监控指标
    parser.add_argument(
        "--monitor",
        type=str,
        default=None,
        help="监控指标ID，如: investment_amount_001",
    )

    # 批量重跑：起始日期
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="批量重跑起始日期，格式: YYYYMMDD（需与 --end-date 配合使用）",
    )

    # 批量重跑：结束日期
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="批量重跑结束日期，格式: YYYYMMDD（需与 --start-date 配合使用）",
    )



    args = parser.parse_args()
    if bool(args.start_date) != bool(args.end_date):
        parser.error("--start-date and --end-date must be provided together")
    if args.start_date and not args.run_now:
        parser.error("historical replay requires --run-now")
    return args


def main():
    """
    主函数
    """
    args = parse_args()

    # 创建应用实例
    app = RiskMonitorApp()

    try:
        # 立即执行模式
        if args.run_now:
            logger.info("立即执行监控任务")

            # 批量重跑历史数据
            if args.start_date and args.end_date:
                logger.info(f"检测到批量重跑参数: {args.start_date} ~ {args.end_date}")
                app.run_batch_historical(
                    start_date=args.start_date,
                    end_date=args.end_date,
                    dimension=None  # 可以后续扩展支持指定维度
                )
                logger.info("批量重跑任务执行完成")
                return

            # 按单个监控指标执行
            if args.monitor:
                app.run_single_monitor(args.monitor, args.date)

            # 按监控类型执行
            elif args.type:
                app.run_monitor_by_type(args.type, args.date)

            # 执行全量监控
            else:
                app.run_monitor(args.date)

            logger.info("监控任务执行完成")
            return

        # 默认模式：启动定时调度器
        logger.info("启动定时调度模式")
        app.start_scheduler()

    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"应用运行异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
