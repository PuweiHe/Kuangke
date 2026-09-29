create table risk_rule_config
(
    id               int auto_increment comment '唯一标识'
        primary key,
    monitor_type     varchar(50)                          not null comment '监控分类',
    monitor_type_2nd varchar(50)                          null comment '二级分类',
    monitor_type_3rd varchar(50)                          null comment '三级分类',
    monitor_id       varchar(50)                          not null comment '监控ID，如: BW-RB-0001',
    monitor_item     varchar(255)                         not null comment '监控事项（如“标的投资范围约束”）',
    monitor_title    varchar(255)                         null comment '监控标题（如“禁投标的监控”）',
    dimension_code   varchar(50)                          null comment '维度代码',
    trust_dimension  varchar(50)                          null comment '维度（如“资产分类”、“交易对手”）',
    alert_level      varchar(50)                          null comment '预警级别（如“一级”、“二级”）',
    requirements     varchar(512)                         null comment '监控要求',
    filter_logic     text                                 null comment '筛选逻辑（用于策略判断）',
    indicator        varchar(100)                         null comment '需要监控的指标（如“交易对手”）',
    operator         varchar(20)                          null comment '运算符（如 not in, >, <, = 等）',
    threshold        varchar(255)                         null comment '阈值（如 白名单、数值、列表等）',
    alert_content    text                                 null comment '触发预警时的内容',
    normal_content   text                                 null comment '正常状态下的提示内容',
    scope            varchar(500)                         null comment '范围（如“单只资产”、“组合级别”）',
    default_value    varchar(255)                         null comment '默认值',
    max_value        varchar(50)                          null comment '最大值限制（如“<=0”、“>=100”）',
    is_enabled       tinyint(1) default 1                 null comment '是否启用（0: 禁用, 1: 启用）',
    created_at       timestamp  default CURRENT_TIMESTAMP null comment '创建时间',
    updated_at       timestamp  default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP comment '更新时间',
    constraint idx_monitor_id
        unique (monitor_id)
)
    comment '委托投资监控系统 - 监控规则配置表' collate = utf8mb4_general_ci;

create index idx_monitor_item
    on risk_rule_config (monitor_item);

create index idx_monitor_type
    on risk_rule_config (monitor_type);




create table risk_dimension_config
(
    id              int auto_increment comment '自增主键'
        primary key,
    monitor_id      varchar(100)                        not null comment '监控指标ID',
    dimension_code  varchar(100)                        not null comment '委托维度ID',
    trust_dimension varchar(100)                        not null comment '委托维度',
    created_at      timestamp default CURRENT_TIMESTAMP null comment '创建时间',
    constraint uk_mnt_dimension_config
        unique (monitor_id, dimension_code)
)
    comment '委托投资监控系统 - 委托维度与监控指标配置关系表'
    collate = utf8mb4_general_ci;




create table risk_assets_list
(
    id           int auto_increment comment '主键ID'
        primary key,
    category     varchar(50)                          not null comment '分类',
    category_2nd varchar(50)                          not null comment '二级分类',
    asset_code   varchar(20)                          not null comment '资产代码',
    year         int                                  null comment '年份',
    is_valid     tinyint(1) default 1                 null comment '是否有效: 1-有效, 0-无效',
    created_at   timestamp  default CURRENT_TIMESTAMP null comment '创建时间',
    updated_at   timestamp  default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP comment '更新时间'
)
    comment '资产白/黑名单' collate = utf8mb4_general_ci;

CREATE UNIQUE INDEX uk_assets_import ON risk_assets_list (category, category_2nd, asset_code, year);

create index idx_category
    on risk_assets_list (category);




create table risk_monitor_result
(
    id              bigint auto_increment comment '自增主键'
        primary key,
    portfolio_code  varchar(100)         not null comment '监控组合CODE',
    portfolio_name  varchar(100)         not null comment '监控组合名称',
    monitor_id      varchar(100)                        not null comment '监控指标ID，如 credit_rating_001',
    monitor_name    varchar(200)         not null comment '监控标题',
    monitor_category varchar(100)        null comment '监控类别',
    dimension_code  varchar(100)         not null comment '委托维度ID',
    trust_dimension varchar(100)         not null comment '委托维度',
    monitor_item    varchar(200)         null comment '监控事项（信用评级约束、交易对手约束等',
    check_date      varchar(10)          not null comment '检查日期，格式YYYYMMDD',
    indicator_value varchar(500)         null comment '指标计算值',
    alert_level     int       default 0                 not null comment '预警等级：0/1/2 表示正常/黄色/红色',
    alert_message   text                         null comment '预警消息内容',
    created_at      timestamp default CURRENT_TIMESTAMP not null comment '记录创建时间',
    constraint uk_mnt_monitor_result
        unique (monitor_id, check_date, portfolio_code, trust_dimension)
)
    comment '监控结果主表（委托投资管理系统），存储每日各监控指标的计算结果、阈值比对及预警信息'
    collate = utf8mb4_general_ci;

create index idx_mnt_monitor_result_category
    on risk_monitor_result (monitor_category);

create index idx_mnt_monitor_result_date
    on risk_monitor_result (check_date);

create index idx_mnt_monitor_result_level
    on risk_monitor_result (alert_level);
