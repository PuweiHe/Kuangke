"""
通知模块

负责违规告警的通知发送，
支持日志通知、邮件通知（可扩展）等。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from config.settings import (
    EMAIL_API_URL,
    EMAIL_CC_LIST,
    EMAIL_NOTIFICATION_ENABLED,
    EMAIL_TO_LIST,
)
from utils.log_utils import get_logger


class Notifier:
    """
    通知器

    当前实现以日志方式发送告警，
    可扩展为邮件、短信、钉钉等渠道。
    """

    def __init__(self):
        self.logger = get_logger("notifier")

    def send_alert(self, violations: List[Dict[str, Any]], biz_date: str) -> None:
        """
        发送告警通知

        Parameters
        ----------
        violations : list[dict]
            高严重级别的违规记录列表
        biz_date : str
            业务日期
        """
        count = len(violations)
        self.logger.warning(
            f"[告警] {biz_date} 发现 {count} 条高严重级别违规"
        )

        for v in violations:
            self.logger.warning(
                f"  - {v.get('risk_type', '')}: "
                f"{v.get('security_name', '')} "
                f"({v.get('security_code', '')}) "
                f"{v.get('violation_detail', '')}"
            )

    def send_summary(self, summary: Dict[str, Any], biz_date: str) -> None:
        """
        发送监控结果摘要通知

        Parameters
        ----------
        summary : dict
            监控结果摘要
        biz_date : str
            业务日期
        """
        total = summary.get("total_count", 0)
        saved = summary.get("saved_count", 0)
        high = summary.get("high_severity_count", 0)

        self.logger.info(
            f"[摘要] {biz_date}: "
            f"共发现 {total} 条违规, "
            f"存储 {saved} 条, "
            f"高严重级别 {high} 条"
        )

    def send_email_alert(self, biz_date: str) -> Optional[bool]:
        """
        发送监控预警邮件

        从数据库查询当日预警数据，格式化为HTML表格并发送邮件

        Parameters
        ----------
        biz_date : str
            业务日期，格式: YYYYMMDD

        Returns
        -------
        bool or None
            True: 发送成功
            False: 发送失败
            None: 未启用邮件通知或无预警数据
        """
        # 检查是否启用邮件通知
        if not EMAIL_NOTIFICATION_ENABLED:
            self.logger.info("邮件通知未启用,跳过发送")
            return None

        # 检查收件人配置
        if not EMAIL_TO_LIST:
            self.logger.warning("邮件收件人列表为空，无法发送邮件")
            return None

        try:
            # 1. 从数据库查询预警数据
            from db.query_adapter import query_all

            sql = """
                SELECT portfolio_code, portfolio_name, monitor_item,
                       alert_message, check_date
                FROM risk_monitor_result
                WHERE check_date = %s AND alert_level > 0
                ORDER BY alert_level DESC, portfolio_name
            """
            rows = query_all(sql, (biz_date,))

            if not rows:
                self.logger.info(f"{biz_date} 无预警数据，不发送邮件")
                return None

            # 2. 格式化日期显示
            try:
                # 尝试多种日期格式
                for fmt in ["%Y-%m-%d", "%Y%m%d"]:
                    try:
                        date_obj = datetime.strptime(biz_date, fmt)
                        formatted_date = f"{date_obj.year}年{date_obj.month:02d}月{date_obj.day:02d}日"
                        break
                    except ValueError:
                        continue
                else:
                    formatted_date = biz_date
            except Exception:
                formatted_date = biz_date

            # 3. 构建 HTML 表格
            html_table = self._build_html_table(rows)

            # 4. 构建邮件内容
            subject = "投资指引监控预警"
            content = self._build_email_content(formatted_date, html_table)
            # Email bodies may contain portfolio data and must not enter logs.

            # 5. 发送邮件
            success = self._send_email_request(subject, content)

            if success:
                self.logger.info(f"邮件预警发送成功: {len(rows)} 条预警")
            else:
                self.logger.error(f"邮件预警发送失败")

            return success

        except Exception as e:
            self.logger.error(f"发送邮件预警异常: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def _build_html_table(self, rows: List[Dict[str, Any]]) -> str:
        """
        构建 HTML 表格

        Parameters
        ----------
        rows : list[dict]
            预警数据列表

        Returns
        -------
        str
            HTML 表格字符串
        """
        if not rows:
            return "<p>暂无预警数据</p>"

        # 表头
        html = """
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
  <thead>
    <tr style="background-color: #f2f2f2;">
      <th style="text-align: left;">组合名称</th>
      <th style="text-align: left;">监测事项</th>
      <th style="text-align: left;">预警内容</th>
      <th style="text-align: center;">日期</th>
    </tr>
  </thead>
  <tbody>
"""

        # 表格行
        for row in rows:
            portfolio_name = row.get("portfolio_name", "")
            monitor_item = row.get("monitor_item", "")
            alert_message = row.get("alert_message", "")
            check_date = row.get("check_date", "")

            # 格式化日期
            try:
                check_date_str = str(check_date)
                # 尝试多种日期格式
                for fmt in ["%Y-%m-%d", "%Y%m%d"]:
                    try:
                        date_obj = datetime.strptime(check_date_str, fmt)
                        formatted_date = date_obj.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
                else:
                    formatted_date = check_date_str
            except (ValueError, TypeError):
                formatted_date = str(check_date)

            html += f"""
    <tr>
      <td>{portfolio_name}</td>
      <td>{monitor_item}</td>
      <td>{alert_message}</td>
      <td style="text-align: center;">{formatted_date}</td>
    </tr>
"""

        html += """
  </tbody>
</table>
"""

        return html

    def _build_email_content(self, formatted_date: str, html_table: str) -> str:
        """
        构建邮件正文内容（HTML格式）

        Parameters
        ----------
        formatted_date : str
            格式化后的日期字符串
        html_table : str
            HTML 表格字符串

        Returns
        -------
        str
            完整的 HTML 邮件内容
        """
        content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h3 {{
            color: #d9534f;
            border-bottom: 2px solid #d9534f;
            padding-bottom: 10px;
        }}
        p {{
            margin: 10px 0;
        }}
        table {{
            margin-top: 20px;
            margin-bottom: 20px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h3>您好：</h3>
    <p>{formatted_date}新增预警如下，提醒您关注如下组合：</p>

    {html_table}

    <div class="footer">
        <p>数据来源：资管风险监控系统 | risk_monitor_result</p>
        <p>此邮件由系统自动发送，请勿直接回复。</p>
    </div>
</body>
</html>
"""
        return content

    def _send_email_request(self, subject: str, content: str) -> bool:
        """
        调用邮件发送 API

        Parameters
        ----------
        subject : str
            邮件主题
        content : str
            邮件正文（HTML格式）

        Returns
        -------
        bool
            发送是否成功
        """
        try:
            payload = {
                "subject": subject,
                "content": content,
                "contentType": "html",
                "toList": EMAIL_TO_LIST,
                "ccList": EMAIL_CC_LIST if EMAIL_CC_LIST else [],
            }

            self.logger.debug("发送邮件请求，收件人数: %s", len(EMAIL_TO_LIST))

            response = requests.post(
                EMAIL_API_URL,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )

            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200 or result.get("success"):
                    self.logger.info("邮件API返回成功")
                    return True
                else:
                    self.logger.error("邮件API返回失败")
                    return False
            else:
                self.logger.error(f"邮件API请求失败: HTTP {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            self.logger.error("邮件API请求超时")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error("邮件API连接错误")
            return False
        except Exception as e:
            self.logger.error("邮件API请求异常: %s", type(e).__name__)
            return False
