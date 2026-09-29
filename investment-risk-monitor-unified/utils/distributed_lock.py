"""Database-backed lease for one scheduled job across multiple instances."""

import os
import socket
import threading
import time
import uuid
from typing import Any, Callable

from loguru import logger

from config.settings import DB_TYPE
from db.query_adapter import execute_update


class DistributedJobLock:
    """Acquire a named lease using a conditional database update.

    A random owner token prevents an expired owner from releasing a successor's
    lease. Long jobs renew the lease while they run; business writes should
    still be idempotent in case a process loses database connectivity.
    """

    def __init__(self, task_name: str, lease_seconds: int = 1800):
        if lease_seconds < 3:
            raise ValueError("lease_seconds must be at least 3")
        self.task_name = task_name
        self.lease_seconds = lease_seconds
        self.owner_token = uuid.uuid4().hex
        self.instance_id = f"{socket.gethostname()}:{os.getpid()}"
        self._held = False

    def acquire(self) -> bool:
        insert_sql = (
            "INSERT IGNORE INTO risk_job_lock (task_name, expires_at_epoch) VALUES (%s, 0)"
            if DB_TYPE == "mysql"
            else "INSERT INTO risk_job_lock (task_name, expires_at_epoch) VALUES (%s, 0) "
                 "ON CONFLICT (task_name) DO NOTHING"
        )
        execute_update(insert_sql, (self.task_name,))
        now = time.time()
        affected = execute_update(
            "UPDATE risk_job_lock SET owner_token = %s, instance_id = %s, "
            "expires_at_epoch = %s WHERE task_name = %s "
            "AND (owner_token IS NULL OR expires_at_epoch <= %s)",
            (self.owner_token, self.instance_id, now + self.lease_seconds, self.task_name, now),
        )
        self._held = affected == 1
        return self._held

    def renew(self) -> bool:
        if not self._held:
            return False
        now = time.time()
        affected = execute_update(
            "UPDATE risk_job_lock SET expires_at_epoch = %s WHERE task_name = %s "
            "AND owner_token = %s AND expires_at_epoch > %s",
            (now + self.lease_seconds, self.task_name, self.owner_token, now),
        )
        self._held = affected == 1
        return self._held

    def release(self) -> bool:
        if not self._held:
            return False
        affected = execute_update(
            "UPDATE risk_job_lock SET owner_token = NULL, instance_id = NULL, "
            "expires_at_epoch = 0 WHERE task_name = %s AND owner_token = %s",
            (self.task_name, self.owner_token),
        )
        self._held = False
        return affected == 1


def run_exclusive_job(task_name: str, callback: Callable[[], Any], lease_seconds: int = 1800) -> tuple[bool, Any]:
    """Run callback while owning the lease; return (executed, callback_result)."""
    lock = DistributedJobLock(task_name, lease_seconds)
    if not lock.acquire():
        logger.info("Scheduled job skipped because another instance owns the lease")
        return False, None

    stop = threading.Event()

    def keep_alive() -> None:
        while not stop.wait(max(1, lease_seconds // 3)):
            try:
                if not lock.renew():
                    logger.error("Scheduled job lease was lost while the job was running")
                    return
            except Exception:
                logger.exception("Unable to renew scheduled job lease")
                return

    heartbeat = threading.Thread(target=keep_alive, name="job-lease-heartbeat", daemon=True)
    heartbeat.start()
    try:
        return True, callback()
    finally:
        stop.set()
        heartbeat.join(timeout=2)
        try:
            lock.release()
        except Exception:
            logger.exception("Unable to release scheduled job lease")
