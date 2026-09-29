CREATE TABLE IF NOT EXISTS risk_job_lock (
    task_name VARCHAR(128) PRIMARY KEY,
    owner_token CHAR(32),
    instance_id VARCHAR(255),
    expires_at_epoch DOUBLE PRECISION NOT NULL DEFAULT 0
);
