CREATE TABLE IF NOT EXISTS risk_job_lock (
    task_name VARCHAR(128) NOT NULL PRIMARY KEY,
    owner_token CHAR(32) NULL,
    instance_id VARCHAR(255) NULL,
    expires_at_epoch DOUBLE NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
