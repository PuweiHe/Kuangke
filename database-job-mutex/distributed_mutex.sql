-- distributed_mutex.sql
-- 基于数据库的分布式互斥锁方案
-- 作用：生产双实例部署时，保证同一定时任务同一时间只有一个实例执行。

CREATE TABLE IF NOT EXISTS distributed_lock (
    lock_name      VARCHAR(128) NOT NULL COMMENT '锁名称，例如 daily_data_sync_job',
    locked_by      VARCHAR(128) DEFAULT NULL COMMENT '持锁实例 ID',
    lock_token     VARCHAR(128) DEFAULT NULL COMMENT '本次持锁 token，用于安全释放锁',
    lock_until     DATETIME(6) NOT NULL COMMENT '锁过期时间',
    locked_at      DATETIME(6) DEFAULT NULL COMMENT '加锁时间',
    released_at    DATETIME(6) DEFAULT NULL COMMENT '释放时间',
    version        BIGINT NOT NULL DEFAULT 0 COMMENT '抢锁成功次数',
    remark         VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at     DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at     DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (lock_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库分布式锁表';


CREATE TABLE IF NOT EXISTS scheduled_job_log (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_name        VARCHAR(128) NOT NULL COMMENT '任务名称',
    instance_id     VARCHAR(128) NOT NULL COMMENT '服务实例 ID',
    lock_token      VARCHAR(128) DEFAULT NULL COMMENT '本次锁 token',
    status          VARCHAR(32) NOT NULL COMMENT 'RUNNING/SUCCESS/FAILED/SKIPPED',
    start_time      DATETIME(6) NOT NULL,
    end_time        DATETIME(6) DEFAULT NULL,
    message         TEXT DEFAULT NULL,
    created_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_job_time (job_name, start_time),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务执行日志表';


-- 初始化每日凌晨 1 点任务对应的锁记录
INSERT INTO distributed_lock (
    lock_name,
    locked_by,
    lock_token,
    lock_until,
    locked_at,
    released_at,
    version,
    remark
) VALUES (
    'daily_data_sync_job',
    NULL,
    NULL,
    '1970-01-01 00:00:00.000000',
    NULL,
    NULL,
    0,
    '每日凌晨1点定时任务分布式锁'
)
ON DUPLICATE KEY UPDATE
    remark = VALUES(remark);
