-- Fresh PostgreSQL schema. Use an empty database; no original data included.
create table risk_rule_config
(
    id               SERIAL
        primary key,
    monitor_type     varchar(50)                          not null ,
    monitor_type_2nd varchar(50)                          null ,
    monitor_type_3rd varchar(50)                          null ,
    monitor_id       varchar(50)                          not null ,
    monitor_item     varchar(255)                         not null ,
    monitor_title    varchar(255)                         null ,
    dimension_code   varchar(50)                          null ,
    trust_dimension  varchar(50)                          null ,
    alert_level      varchar(50)                          null ,
    requirements     varchar(512)                         null ,
    filter_logic     text                                 null ,
    indicator        varchar(100)                         null ,
    operator         varchar(20)                          null ,
    threshold        varchar(255)                         null ,
    alert_content    text                                 null ,
    normal_content   text                                 null ,
    scope            varchar(500)                         null ,
    default_value    varchar(255)                         null ,
    max_value        varchar(50)                          null ,
    is_enabled       SMALLINT default 1                 null ,
    created_at       timestamp  default CURRENT_TIMESTAMP null ,
    updated_at       timestamp  default CURRENT_TIMESTAMP null  ,
    constraint idx_monitor_id
        unique (monitor_id)
)
     ;

create index idx_monitor_item
    on risk_rule_config (monitor_item);

create index idx_monitor_type
    on risk_rule_config (monitor_type);




create table risk_dimension_config
(
    id              SERIAL
        primary key,
    monitor_id      varchar(100)                        not null ,
    dimension_code  varchar(100)                        not null ,
    trust_dimension varchar(100)                        not null ,
    created_at      timestamp default CURRENT_TIMESTAMP null ,
    constraint uk_mnt_dimension_config
        unique (monitor_id, dimension_code)
)

    ;




create table risk_assets_list
(
    id           SERIAL
        primary key,
    category     varchar(50)                          not null ,
    category_2nd varchar(50)                          not null ,
    asset_code   varchar(20)                          not null ,
    year         int                                  null ,
    is_valid     SMALLINT default 1                 null ,
    created_at   timestamp  default CURRENT_TIMESTAMP null ,
    updated_at   timestamp  default CURRENT_TIMESTAMP null
)
     ;

CREATE UNIQUE INDEX uk_assets_import ON risk_assets_list (category, category_2nd, asset_code, year);

create index idx_category
    on risk_assets_list (category);




create table risk_monitor_result
(
    id              BIGSERIAL
        primary key,
    portfolio_code  varchar(100)         not null ,
    portfolio_name  varchar(100)         not null ,
    monitor_id      varchar(100)                        not null ,
    monitor_name    varchar(200)         not null ,
    monitor_category varchar(100)        null ,
    dimension_code  varchar(100)         not null ,
    trust_dimension varchar(100)         not null ,
    monitor_item    varchar(200)         null ,
    check_date      varchar(10)          not null ,
    indicator_value varchar(500)         null ,
    alert_level     int       default 0                 not null ,
    alert_message   text                         null ,
    created_at      timestamp default CURRENT_TIMESTAMP not null ,
    constraint uk_mnt_monitor_result
        unique (monitor_id, check_date, portfolio_code, trust_dimension)
)

    ;

create index idx_mnt_monitor_result_category
    on risk_monitor_result (monitor_category);

create index idx_mnt_monitor_result_date
    on risk_monitor_result (check_date);

create index idx_mnt_monitor_result_level
    on risk_monitor_result (alert_level);

-- auto-generated definition
create table position_snapshot
(
    zcmc        varchar(200)    null ,
    zcdm        varchar(100)    null ,
    jydm        varchar(100)    null ,
    wstwd       varchar(100)    null ,
    fzhwd       varchar(100)    null ,
    ztbh        varchar(100)    null ,
    jjztmc      varchar(200)    null ,
    fzztmc      varchar(200)    null ,
    zcdl        varchar(100)    null ,
    zcfl_1st    varchar(100)    null ,
    zcfl_2nd    varchar(100)    null ,
    zcfl_3rd    varchar(100)    null ,
    jycl        varchar(100)    null ,
    tzjl        varchar(100)    null ,
    zcfl        varchar(200)    null ,
    zxwbpj      varchar(100)    null ,
    kjfl        varchar(100)    null ,
    jjsz        decimal(32, 16) null ,
    yslxgl      decimal(32, 16) null ,
    qjsz        decimal(32, 16) null ,
    pjye        decimal(32, 16) null ,
    pjye_rp     decimal(32, 16) null ,
    pjzjzy_bn   decimal(32, 16) null ,
    cwsy_bn     decimal(32, 16) null ,
    zhsy_bn     decimal(32, 16) null ,
    nhcwsyl_bn  decimal(32, 16) null ,
    nhzhsyl_bn  decimal(32, 16) null ,
    lxsr_bn     decimal(32, 16) null ,
    hlsr_bn     decimal(32, 16) null ,
    jcsr_bn     decimal(32, 16) null ,
    gyjzbdsy_bn decimal(32, 16) null ,
    qtzhsy_bn   decimal(32, 16) null ,
    qygjczjc_bn decimal(32, 16) null ,
    zcjzss_bn   decimal(32, 16) null ,
    zmye        decimal(32, 16) null ,
    hdsy_bn     decimal(32, 16) null ,
    jzzhsr_bn   decimal(32, 16) null ,
    jyfy_bn     decimal(32, 16) null ,
    lxzc_bn     decimal(32, 16) null ,
    qttzxgsz_bn decimal(32, 16) null ,
    pjzjzy_by   decimal(32, 16) null ,
    cwsy_by     decimal(32, 16) null ,
    zhsy_by     decimal(32, 16) null ,
    nhcwsyl_by  decimal(32, 16) null ,
    nhzhsyl_by  decimal(32, 16) null ,
    lxsr_by     decimal(32, 16) null ,
    hlsr_by     decimal(32, 16) null ,
    jcsr_by     decimal(32, 16) null ,
    gyjzbdsy_by decimal(32, 16) null ,
    qtzhsy_by   decimal(32, 16) null ,
    qygjczjc_by decimal(32, 16) null ,
    zcjzss_by   decimal(32, 16) null ,
    hdsy_by     decimal(32, 16) null ,
    jzzhsr_by   decimal(32, 16) null ,
    jyfy_by     decimal(32, 16) null ,
    lxzc_by     decimal(32, 16) null ,
    qttzxgsz_by decimal(32, 16) null ,
    ccsl        decimal(32, 16) null ,
    cccb        decimal(32, 16) null ,
    pmll        decimal(32, 16) null ,
    mrrq        varchar(20)     null ,
    scfxr       varchar(20)     null ,
    dqr         varchar(20)     null ,
    jq          decimal(32, 16) null ,
    dqsyl       decimal(32, 16) null ,
    pmjz        decimal(32, 8)  null ,
    fxpl        varchar(20)     null ,
    ncsz        decimal(32, 16) null ,
    cccb_jg     decimal(32, 16) null ,
    symye       decimal(32, 16) null ,
    jzssye      decimal(32, 16) null ,
    uptm        TIMESTAMP(6)     null ,
    p_dt        bigint          null
)
     ;
