import os
import uuid
import socket
import logging
from dataclasses import dataclass
from typing import Optional, Callable
import pymysql
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = 'utf8mb4'

@dataclass(frozen=True)
class JobConfig:
    job_name: str
    cron_hour: int
    cron_minute: int
    timezone: str
    lease_seconds: int

def load_db_config() -> DbConfig:
    return DbConfig(host=os.getenv('DB_HOST', '127.0.0.1'), port=int(os.getenv('DB_PORT', '3306')), user=os.getenv('DB_USER', 'demo_user'), password=os.getenv('DB_PASSWORD', ''), database=os.getenv('DB_NAME', 'job_mutex_demo'))

def load_job_config() -> JobConfig:
    return JobConfig(job_name=os.getenv('JOB_NAME', 'daily_data_sync_job'), cron_hour=int(os.getenv('JOB_CRON_HOUR', '1')), cron_minute=int(os.getenv('JOB_CRON_MINUTE', '0')), timezone=os.getenv('JOB_TIMEZONE', 'Asia/Shanghai'), lease_seconds=int(os.getenv('LOCK_LEASE_SECONDS', '1800')))

def get_instance_id() -> str:
    instance_id = os.getenv('INSTANCE_ID')
    if instance_id:
        return instance_id
    return f'demo-{uuid.uuid4().hex[:12]}'

class Database:

    def __init__(self, config: DbConfig):
        self.config = config

    def connect(self):
        return pymysql.connect(host=self.config.host, port=self.config.port, user=self.config.user, password=self.config.password, database=self.config.database, charset=self.config.charset, autocommit=False, cursorclass=pymysql.cursors.DictCursor)

    def execute(self, sql: str, params: tuple=()) -> int:
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                affected_rows = cursor.execute(sql, params)
            conn.commit()
            return affected_rows
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

def init_schema(db: Database, job_name: str) -> None:
    db.execute("\n    CREATE TABLE IF NOT EXISTS distributed_lock (\n        lock_name      VARCHAR(128) NOT NULL COMMENT '锁名称，例如 daily_data_sync_job',\n        locked_by      VARCHAR(128) DEFAULT NULL COMMENT '持锁实例 ID',\n        lock_token     VARCHAR(128) DEFAULT NULL COMMENT '本次持锁 token，用于安全释放锁',\n        lock_until     DATETIME(6) NOT NULL COMMENT '锁过期时间',\n        locked_at      DATETIME(6) DEFAULT NULL COMMENT '加锁时间',\n        released_at    DATETIME(6) DEFAULT NULL COMMENT '释放时间',\n        version        BIGINT NOT NULL DEFAULT 0 COMMENT '抢锁成功次数',\n        remark         VARCHAR(255) DEFAULT NULL COMMENT '备注',\n        created_at     DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),\n        updated_at     DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),\n        PRIMARY KEY (lock_name)\n    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库分布式锁表';\n    ")
    db.execute("\n    CREATE TABLE IF NOT EXISTS scheduled_job_log (\n        id              BIGINT AUTO_INCREMENT PRIMARY KEY,\n        job_name        VARCHAR(128) NOT NULL COMMENT '任务名称',\n        instance_id     VARCHAR(128) NOT NULL COMMENT '服务实例 ID',\n        lock_token      VARCHAR(128) DEFAULT NULL COMMENT '本次锁 token',\n        status          VARCHAR(32) NOT NULL COMMENT 'RUNNING/SUCCESS/FAILED/SKIPPED',\n        start_time      DATETIME(6) NOT NULL,\n        end_time        DATETIME(6) DEFAULT NULL,\n        message         TEXT DEFAULT NULL,\n        created_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),\n        INDEX idx_job_time (job_name, start_time),\n        INDEX idx_status (status)\n    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务执行日志表';\n    ")
    db.execute("\n    INSERT INTO distributed_lock (\n        lock_name,\n        locked_by,\n        lock_token,\n        lock_until,\n        locked_at,\n        released_at,\n        version,\n        remark\n    ) VALUES (\n        %s,\n        NULL,\n        NULL,\n        '1970-01-01 00:00:00.000000',\n        NULL,\n        NULL,\n        0,\n        '每日凌晨1点定时任务分布式锁'\n    )\n    ON DUPLICATE KEY UPDATE\n        remark = VALUES(remark);\n    ", (job_name,))

class DatabaseDistributedLock:

    def __init__(self, db: Database, lock_name: str, instance_id: str, lease_seconds: int):
        self.db = db
        self.lock_name = lock_name
        self.instance_id = instance_id
        self.lease_seconds = lease_seconds
        self.lock_token: Optional[str] = None

    def try_acquire(self) -> bool:
        token = str(uuid.uuid4())
        affected_rows = self.db.execute('\n        UPDATE distributed_lock\n        SET\n            locked_by = %s,\n            lock_token = %s,\n            lock_until = DATE_ADD(NOW(6), INTERVAL %s SECOND),\n            locked_at = NOW(6),\n            released_at = NULL,\n            version = version + 1,\n            updated_at = NOW(6)\n        WHERE\n            lock_name = %s\n            AND lock_until <= NOW(6);\n        ', (self.instance_id, token, self.lease_seconds, self.lock_name))
        if affected_rows == 1:
            self.lock_token = token
            logger.info('Application event')
            return True
        logger.info('Application event')
        return False

    def release(self) -> bool:
        if not self.lock_token:
            return False
        affected_rows = self.db.execute('\n        UPDATE distributed_lock\n        SET\n            lock_until = NOW(6),\n            released_at = NOW(6),\n            updated_at = NOW(6)\n        WHERE\n            lock_name = %s\n            AND locked_by = %s\n            AND lock_token = %s;\n        ', (self.lock_name, self.instance_id, self.lock_token))
        if affected_rows == 1:
            logger.info('Application event')
            self.lock_token = None
            return True
        logger.warning('Application event')
        return False

class JobLogRepository:

    def __init__(self, db: Database):
        self.db = db

    def record(self, job_name: str, instance_id: str, lock_token: Optional[str], status: str, message: str='') -> None:
        self.db.execute('\n        INSERT INTO scheduled_job_log (\n            job_name,\n            instance_id,\n            lock_token,\n            status,\n            start_time,\n            end_time,\n            message\n        ) VALUES (\n            %s,\n            %s,\n            %s,\n            %s,\n            NOW(6),\n            NOW(6),\n            %s\n        );\n        ', (job_name, instance_id, lock_token, status, message))

def run_business_job() -> None:
    logger.info('Application event')
    logger.info('Application event')

class ExclusiveJobRunner:

    def __init__(self, db: Database, job_config: JobConfig, instance_id: str, business_func: Callable[[], None]):
        self.db = db
        self.job_config = job_config
        self.instance_id = instance_id
        self.business_func = business_func
        self.job_log_repo = JobLogRepository(db)

    def run_once(self) -> None:
        job_name = self.job_config.job_name
        logger.info('Application event')
        lock = DatabaseDistributedLock(db=self.db, lock_name=job_name, instance_id=self.instance_id, lease_seconds=self.job_config.lease_seconds)
        if not lock.try_acquire():
            self.job_log_repo.record(job_name=job_name, instance_id=self.instance_id, lock_token=None, status='SKIPPED', message='Another instance has acquired the lock. Current instance skipped.')
            return
        try:
            self.job_log_repo.record(job_name=job_name, instance_id=self.instance_id, lock_token=lock.lock_token, status='RUNNING', message='Job started.')
            self.business_func()
            self.job_log_repo.record(job_name=job_name, instance_id=self.instance_id, lock_token=lock.lock_token, status='SUCCESS', message='Job finished successfully.')
        except Exception as exc:
            logger.exception('Application event')
            self.job_log_repo.record(job_name=job_name, instance_id=self.instance_id, lock_token=lock.lock_token, status='FAILED', message=type(exc).__name__)
            raise
        finally:
            lock.release()

def start_scheduler(runner: ExclusiveJobRunner, job_config: JobConfig) -> None:
    scheduler = BlockingScheduler(timezone=job_config.timezone)
    scheduler.add_job(runner.run_once, trigger=CronTrigger(hour=job_config.cron_hour, minute=job_config.cron_minute, timezone=job_config.timezone), id=job_config.job_name, name=job_config.job_name, replace_existing=True, max_instances=1, coalesce=True, misfire_grace_time=300)
    logger.info('Application event')
    scheduler.start()

def main() -> None:
    db_config = load_db_config()
    job_config = load_job_config()
    instance_id = get_instance_id()
    logger.info('Application event')
    db = Database(db_config)
    if os.getenv('INIT_SCHEMA', 'false').lower() == 'true':
        init_schema(db, job_config.job_name)
        logger.info('Application event')
    runner = ExclusiveJobRunner(db=db, job_config=job_config, instance_id=instance_id, business_func=run_business_job)
    if os.getenv('RUN_ONCE', 'false').lower() == 'true':
        runner.run_once()
        return
    start_scheduler(runner, job_config)

if __name__ == "__main__":
    main()
