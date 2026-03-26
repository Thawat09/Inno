/* =========================================================
   0) ROLES / USERS / SECURITY
   ========================================================= */

CREATE TABLE dbo.roles (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    role_code NVARCHAR(50) NOT NULL UNIQUE,
    role_name NVARCHAR(100) NOT NULL,
    description NVARCHAR(500) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_roles_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_roles_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_roles_updated_at DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE dbo.users (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    line_user_id NVARCHAR(100) NOT NULL,
    employee_code NVARCHAR(100) NULL,
    first_name NVARCHAR(255) NULL,
    last_name NVARCHAR(255) NULL,
    nickname NVARCHAR(255) NULL,
    phone NVARCHAR(50) NULL,
    email NVARCHAR(255) NULL,
    main_team NVARCHAR(255) NULL,
    sub_team NVARCHAR(255) NULL,

    password_hash NVARCHAR(500) NULL,
    password_salt NVARCHAR(255) NULL,
    failed_login_count INT NOT NULL CONSTRAINT DF_users_failed_login_count DEFAULT (0),
    last_login_at DATETIME2 NULL,
    is_active BIT NOT NULL CONSTRAINT DF_users_is_active DEFAULT (1),
    is_admin BIT NOT NULL CONSTRAINT DF_users_is_admin DEFAULT (0),

    created_at DATETIME2 NOT NULL CONSTRAINT DF_users_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_users_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT UQ_users_line_user_id UNIQUE (line_user_id)
);
GO

CREATE UNIQUE INDEX UX_users_email
ON dbo.users(email)
WHERE email IS NOT NULL;
GO

CREATE OR ALTER TRIGGER dbo.trg_users_updated_at
ON dbo.users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.users t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.user_roles (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_pk BIGINT NOT NULL,
    role_pk BIGINT NOT NULL,
    is_active BIT NOT NULL CONSTRAINT DF_user_roles_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_user_roles_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_user_roles_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id),
    CONSTRAINT FK_user_roles_roles FOREIGN KEY (role_pk) REFERENCES dbo.roles(id),
    CONSTRAINT UQ_user_roles UNIQUE (user_pk, role_pk)
);
GO

CREATE TABLE dbo.user_login_audit (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_pk BIGINT NULL,
    login_at DATETIME2 NOT NULL CONSTRAINT DF_user_login_audit_login_at DEFAULT (SYSUTCDATETIME()),
    login_result NVARCHAR(50) NOT NULL,
    failure_reason NVARCHAR(255) NULL,
    ip_address NVARCHAR(100) NULL,
    user_agent NVARCHAR(1000) NULL,

    CONSTRAINT FK_user_login_audit_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id)
);
GO

CREATE TABLE dbo.user_account_locks (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_pk BIGINT NOT NULL,
    locked_at DATETIME2 NOT NULL CONSTRAINT DF_user_account_locks_locked_at DEFAULT (SYSUTCDATETIME()),
    lock_reason NVARCHAR(255) NULL,
    failed_login_count INT NOT NULL,
    unlocked_at DATETIME2 NULL,
    unlocked_by BIGINT NULL,
    is_active BIT NOT NULL CONSTRAINT DF_user_account_locks_is_active DEFAULT (1),

    CONSTRAINT FK_user_account_locks_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id),
    CONSTRAINT FK_user_account_locks_unlocked_by FOREIGN KEY (unlocked_by) REFERENCES dbo.users(id)
);
GO

CREATE TABLE dbo.user_otp_requests (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_pk BIGINT NOT NULL,
    otp_code_hash NVARCHAR(500) NOT NULL,
    sent_to_email NVARCHAR(255) NOT NULL,
    requested_at DATETIME2 NOT NULL CONSTRAINT DF_user_otp_requests_requested_at DEFAULT (SYSUTCDATETIME()),
    expires_at DATETIME2 NOT NULL,
    verified_at DATETIME2 NULL,
    status NVARCHAR(50) NOT NULL CONSTRAINT DF_user_otp_requests_status DEFAULT ('pending'),
    attempt_count INT NOT NULL CONSTRAINT DF_user_otp_requests_attempt_count DEFAULT (0),

    CONSTRAINT FK_user_otp_requests_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id)
);
GO

CREATE TABLE dbo.password_reset_requests (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_pk BIGINT NOT NULL,
    token_hash NVARCHAR(500) NOT NULL,
    requested_at DATETIME2 NOT NULL CONSTRAINT DF_password_reset_requests_requested_at DEFAULT (SYSUTCDATETIME()),
    expires_at DATETIME2 NOT NULL,
    used_at DATETIME2 NULL,
    status NVARCHAR(50) NOT NULL CONSTRAINT DF_password_reset_requests_status DEFAULT ('pending'),

    CONSTRAINT FK_password_reset_requests_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id)
);
GO


/* =========================================================
   1) TEAMS / MEMBERS
   ========================================================= */

CREATE TABLE dbo.teams (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    team_code NVARCHAR(50) NOT NULL UNIQUE,
    team_name NVARCHAR(255) NOT NULL,
    description NVARCHAR(1000) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_teams_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_teams_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_teams_updated_at DEFAULT (SYSUTCDATETIME())
);
GO

CREATE OR ALTER TRIGGER dbo.trg_teams_updated_at
ON dbo.teams
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.teams t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.sub_teams (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    team_pk BIGINT NOT NULL,
    sub_team_code NVARCHAR(50) NOT NULL,
    sub_team_name NVARCHAR(255) NOT NULL,
    description NVARCHAR(1000) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_sub_teams_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_sub_teams_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_sub_teams_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_sub_teams_teams FOREIGN KEY (team_pk) REFERENCES dbo.teams(id),
    CONSTRAINT UQ_sub_teams UNIQUE (team_pk, sub_team_code)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_sub_teams_updated_at
ON dbo.sub_teams
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.sub_teams t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.team_members (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_pk BIGINT NOT NULL,
    team_pk BIGINT NOT NULL,
    sub_team_pk BIGINT NULL,
    member_role NVARCHAR(100) NULL,
    is_primary BIT NOT NULL CONSTRAINT DF_team_members_is_primary DEFAULT (0),
    is_active BIT NOT NULL CONSTRAINT DF_team_members_is_active DEFAULT (1),
    effective_from DATETIME2 NOT NULL CONSTRAINT DF_team_members_effective_from DEFAULT (SYSUTCDATETIME()),
    effective_to DATETIME2 NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_team_members_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_team_members_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_team_members_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id),
    CONSTRAINT FK_team_members_teams FOREIGN KEY (team_pk) REFERENCES dbo.teams(id),
    CONSTRAINT FK_team_members_sub_teams FOREIGN KEY (sub_team_pk) REFERENCES dbo.sub_teams(id)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_team_members_updated_at
ON dbo.team_members
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.team_members t
    INNER JOIN inserted i ON t.id = i.id;
END
GO


/* =========================================================
   2) LINE INTEGRATION
   ========================================================= */

CREATE TABLE dbo.line_users (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_id NVARCHAR(100) NOT NULL,
    display_name NVARCHAR(255) NULL,
    picture_url NVARCHAR(1000) NULL,
    status_message NVARCHAR(1000) NULL,
    language NVARCHAR(50) NULL,

    user_pk BIGINT NULL,
    is_friend BIT NOT NULL CONSTRAINT DF_line_users_is_friend DEFAULT (0),
    status NVARCHAR(50) NOT NULL CONSTRAINT DF_line_users_status DEFAULT ('active'),
    last_seen_at DATETIME2 NULL,

    created_at DATETIME2 NOT NULL CONSTRAINT DF_line_users_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_line_users_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_line_users_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id),
    CONSTRAINT UQ_line_users_user_id UNIQUE (user_id)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_line_users_updated_at
ON dbo.line_users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.line_users t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.line_chats (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    chat_type NVARCHAR(20) NOT NULL,
    chat_id NVARCHAR(100) NOT NULL,
    group_name NVARCHAR(255) NULL,
    member_count INT NULL,

    bot_status NVARCHAR(50) NOT NULL CONSTRAINT DF_line_chats_bot_status DEFAULT ('active'),
    bot_joined_at DATETIME2 NULL,
    bot_left_at DATETIME2 NULL,
    last_seen_at DATETIME2 NULL,

    created_at DATETIME2 NOT NULL CONSTRAINT DF_line_chats_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_line_chats_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT UQ_line_chats_chat UNIQUE (chat_type, chat_id)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_line_chats_updated_at
ON dbo.line_chats
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.line_chats t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.line_chat_memberships (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    chat_pk BIGINT NOT NULL,
    line_user_pk BIGINT NOT NULL,

    status NVARCHAR(50) NOT NULL CONSTRAINT DF_line_chat_memberships_status DEFAULT ('active'),
    joined_at DATETIME2 NULL,
    left_at DATETIME2 NULL,
    last_seen_at DATETIME2 NULL,

    created_at DATETIME2 NOT NULL CONSTRAINT DF_line_chat_memberships_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_line_chat_memberships_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_line_chat_memberships_line_chats FOREIGN KEY (chat_pk) REFERENCES dbo.line_chats(id),
    CONSTRAINT FK_line_chat_memberships_line_users FOREIGN KEY (line_user_pk) REFERENCES dbo.line_users(id),
    CONSTRAINT UQ_line_chat_memberships UNIQUE (chat_pk, line_user_pk)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_line_chat_memberships_updated_at
ON dbo.line_chat_memberships
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.line_chat_memberships t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.line_event_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    event_type NVARCHAR(100) NOT NULL,
    chat_type NVARCHAR(20) NULL,
    chat_id NVARCHAR(100) NULL,
    line_user_id NVARCHAR(100) NULL,
    event_timestamp BIGINT NULL,
    raw_json NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_line_event_logs_created_at DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE dbo.line_processed_events (
    webhook_event_id NVARCHAR(100) NOT NULL PRIMARY KEY,
    event_type NVARCHAR(100) NOT NULL,
    processed_at DATETIME2 NOT NULL CONSTRAINT DF_line_processed_events_processed_at DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE dbo.line_message_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NULL,
    chat_pk BIGINT NULL,
    target_line_user_pk BIGINT NULL,
    message_type NVARCHAR(50) NOT NULL,
    message_payload_json NVARCHAR(MAX) NOT NULL,
    sent_at DATETIME2 NOT NULL CONSTRAINT DF_line_message_logs_sent_at DEFAULT (SYSUTCDATETIME()),
    delivery_status NVARCHAR(50) NULL,
    reply_token NVARCHAR(255) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_line_message_logs_created_at DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE dbo.line_action_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NULL,
    line_user_pk BIGINT NULL,
    action_type NVARCHAR(100) NOT NULL,
    action_value NVARCHAR(1000) NULL,
    action_at DATETIME2 NOT NULL CONSTRAINT DF_line_action_logs_action_at DEFAULT (SYSUTCDATETIME()),
    raw_json NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_line_action_logs_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_line_action_logs_line_users FOREIGN KEY (line_user_pk) REFERENCES dbo.line_users(id)
);
GO


/* =========================================================
   3) STANDBY / CALENDAR / SHIFT
   ========================================================= */

CREATE TABLE dbo.standby_calendars (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    team_pk BIGINT NOT NULL,
    sub_team_pk BIGINT NULL,
    calendar_name NVARCHAR(255) NOT NULL,
    description NVARCHAR(1000) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_standby_calendars_is_active DEFAULT (1),
    created_by BIGINT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_standby_calendars_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_standby_calendars_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_standby_calendars_teams FOREIGN KEY (team_pk) REFERENCES dbo.teams(id),
    CONSTRAINT FK_standby_calendars_sub_teams FOREIGN KEY (sub_team_pk) REFERENCES dbo.sub_teams(id),
    CONSTRAINT FK_standby_calendars_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_standby_calendars_updated_at
ON dbo.standby_calendars
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.standby_calendars t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.standby_shift_rules (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    calendar_pk BIGINT NOT NULL,
    rule_name NVARCHAR(255) NOT NULL,
    shift_start_time TIME NOT NULL,
    shift_end_time TIME NOT NULL,
    timezone_name NVARCHAR(100) NOT NULL CONSTRAINT DF_standby_shift_rules_timezone_name DEFAULT ('Asia/Bangkok'),
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    is_active BIT NOT NULL CONSTRAINT DF_standby_shift_rules_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_standby_shift_rules_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_standby_shift_rules_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_standby_shift_rules_calendars FOREIGN KEY (calendar_pk) REFERENCES dbo.standby_calendars(id)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_standby_shift_rules_updated_at
ON dbo.standby_shift_rules
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.standby_shift_rules t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.standby_slots (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    calendar_pk BIGINT NOT NULL,
    slot_date DATE NOT NULL,
    shift_rule_pk BIGINT NULL,
    tier_level INT NOT NULL,
    user_pk BIGINT NOT NULL,
    start_datetime DATETIME2 NOT NULL,
    end_datetime DATETIME2 NOT NULL,
    slot_status NVARCHAR(50) NOT NULL CONSTRAINT DF_standby_slots_slot_status DEFAULT ('active'),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_standby_slots_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_standby_slots_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_standby_slots_calendars FOREIGN KEY (calendar_pk) REFERENCES dbo.standby_calendars(id),
    CONSTRAINT FK_standby_slots_shift_rules FOREIGN KEY (shift_rule_pk) REFERENCES dbo.standby_shift_rules(id),
    CONSTRAINT FK_standby_slots_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id)
);
GO

CREATE INDEX IX_standby_slots_lookup
ON dbo.standby_slots(calendar_pk, slot_date, tier_level, start_datetime, end_datetime);
GO

CREATE OR ALTER TRIGGER dbo.trg_standby_slots_updated_at
ON dbo.standby_slots
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.standby_slots t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.standby_slot_change_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    standby_slot_pk BIGINT NOT NULL,
    old_user_pk BIGINT NULL,
    new_user_pk BIGINT NULL,
    old_tier_level INT NULL,
    new_tier_level INT NULL,
    change_reason NVARCHAR(1000) NULL,
    changed_by BIGINT NULL,
    changed_at DATETIME2 NOT NULL CONSTRAINT DF_standby_slot_change_logs_changed_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_standby_slot_change_logs_slots FOREIGN KEY (standby_slot_pk) REFERENCES dbo.standby_slots(id),
    CONSTRAINT FK_standby_slot_change_logs_old_user FOREIGN KEY (old_user_pk) REFERENCES dbo.users(id),
    CONSTRAINT FK_standby_slot_change_logs_new_user FOREIGN KEY (new_user_pk) REFERENCES dbo.users(id),
    CONSTRAINT FK_standby_slot_change_logs_changed_by FOREIGN KEY (changed_by) REFERENCES dbo.users(id)
);
GO

CREATE TABLE dbo.standby_replacement_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    original_slot_pk BIGINT NOT NULL,
    original_user_pk BIGINT NOT NULL,
    replacement_user_pk BIGINT NOT NULL,
    replacement_reason NVARCHAR(1000) NULL,
    created_by BIGINT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_standby_replacement_logs_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_standby_replacement_logs_slot FOREIGN KEY (original_slot_pk) REFERENCES dbo.standby_slots(id),
    CONSTRAINT FK_standby_replacement_logs_original_user FOREIGN KEY (original_user_pk) REFERENCES dbo.users(id),
    CONSTRAINT FK_standby_replacement_logs_replacement_user FOREIGN KEY (replacement_user_pk) REFERENCES dbo.users(id),
    CONSTRAINT FK_standby_replacement_logs_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id)
);
GO


/* =========================================================
   4) LEAVE / AVAILABILITY
   ========================================================= */

CREATE TABLE dbo.user_leave_requests (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_pk BIGINT NOT NULL,
    leave_type NVARCHAR(100) NOT NULL,
    start_datetime DATETIME2 NOT NULL,
    end_datetime DATETIME2 NOT NULL,
    reason NVARCHAR(1000) NULL,
    created_by BIGINT NULL,
    approved_by BIGINT NULL,
    status NVARCHAR(50) NOT NULL CONSTRAINT DF_user_leave_requests_status DEFAULT ('pending'),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_user_leave_requests_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_user_leave_requests_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_user_leave_requests_user FOREIGN KEY (user_pk) REFERENCES dbo.users(id),
    CONSTRAINT FK_user_leave_requests_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
    CONSTRAINT FK_user_leave_requests_approved_by FOREIGN KEY (approved_by) REFERENCES dbo.users(id)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_user_leave_requests_updated_at
ON dbo.user_leave_requests
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.user_leave_requests t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.user_availability_status (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_pk BIGINT NOT NULL,
    availability_status NVARCHAR(50) NOT NULL,
    start_datetime DATETIME2 NOT NULL,
    end_datetime DATETIME2 NULL,
    note NVARCHAR(1000) NULL,
    created_by BIGINT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_user_availability_status_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_user_availability_status_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id),
    CONSTRAINT FK_user_availability_status_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id)
);
GO


/* =========================================================
   5) EMAIL / TICKET PIPELINE
   ========================================================= */

CREATE TABLE dbo.email_ticket_audit_raw (
    record_id VARCHAR(100) NOT NULL PRIMARY KEY,
    parent_id VARCHAR(100) NULL,
    message_id VARCHAR(255) NULL,
    email_date DATETIME2 NULL,

    subject_raw NVARCHAR(MAX) NULL,
    body_raw NVARCHAR(MAX) NULL,

    parsed_task_short_desc NVARCHAR(MAX) NULL,
    parsed_ritm_short_desc NVARCHAR(MAX) NULL,
    parsed_inc_short_desc NVARCHAR(MAX) NULL,
    parsed_ctask_short_desc NVARCHAR(MAX) NULL,
    parsed_description NVARCHAR(MAX) NULL,
    parsed_related_env NVARCHAR(MAX) NULL,
    parsed_requested_for VARCHAR(255) NULL,
    parsed_opened_by VARCHAR(255) NULL,
    parsed_business_service VARCHAR(255) NULL,
    parsed_service_offering VARCHAR(255) NULL,

    ip_list_json NVARCHAR(MAX) NULL,
    url_list_json NVARCHAR(MAX) NULL,

    created_at DATETIME2 NOT NULL CONSTRAINT DF_email_ticket_audit_raw_created_at DEFAULT (GETDATE()),
    created_by VARCHAR(100) NOT NULL CONSTRAINT DF_email_ticket_audit_raw_created_by DEFAULT ('email_pipeline'),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_email_ticket_audit_raw_updated_at DEFAULT (GETDATE()),
    updated_by VARCHAR(100) NOT NULL CONSTRAINT DF_email_ticket_audit_raw_updated_by DEFAULT ('email_pipeline')
);
GO

CREATE OR ALTER TRIGGER dbo.trg_update_email_ticket_audit_raw
ON dbo.email_ticket_audit_raw
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = GETDATE()
    FROM dbo.email_ticket_audit_raw t
    INNER JOIN inserted i ON t.record_id = i.record_id;
END
GO

CREATE TABLE dbo.email_ticket_master (
    record_id VARCHAR(100) NOT NULL PRIMARY KEY,
    parent_id VARCHAR(100) NULL,
    message_id VARCHAR(255) NULL,
    email_date DATETIME2 NULL,

    from_address VARCHAR(255) NULL,
    to_address VARCHAR(255) NULL,
    ticket_type VARCHAR(50) NULL,

    request_number VARCHAR(100) NULL,
    ritm_no VARCHAR(100) NULL,
    inc_no VARCHAR(100) NULL,
    itask_no VARCHAR(100) NULL,
    ctask_no VARCHAR(100) NULL,

    subject_clean NVARCHAR(MAX) NULL,
    short_desc_clean NVARCHAR(MAX) NULL,
    description_clean NVARCHAR(MAX) NULL,
    description_for_model NVARCHAR(MAX) NULL,
    related_env_raw NVARCHAR(MAX) NULL,
    body_for_model NVARCHAR(MAX) NULL,

    opened_by VARCHAR(255) NULL,
    requested_for VARCHAR(255) NULL,
    raised_by VARCHAR(255) NULL,
    business_service VARCHAR(255) NULL,
    service_offering VARCHAR(255) NULL,
    priority VARCHAR(100) NULL,
    urgency VARCHAR(100) NULL,
    impact VARCHAR(100) NULL,
    contact_email VARCHAR(255) NULL,

    ip_list_json NVARCHAR(MAX) NULL,
    url_list_json NVARCHAR(MAX) NULL,

    has_aws_ip BIT NULL,
    has_gcp_ip BIT NULL,
    has_aws_keyword_header BIT NULL,
    has_gcp_keyword_header BIT NULL,
    has_aws_keyword_body BIT NULL,
    has_gcp_keyword_body BIT NULL,
    has_aws_keyword_desc BIT NULL,
    has_gcp_keyword_desc BIT NULL,
    env_has_aws BIT NULL,
    env_has_gcp BIT NULL,

    assigned_group_from_to VARCHAR(255) NULL,
    route_scope VARCHAR(100) NULL,

    sibling_task_count INT NULL,
    sibling_known_sub_team VARCHAR(255) NULL,
    cross_task_inference_used BIT NULL,

    label_main_team VARCHAR(255) NULL,
    label_sub_team VARCHAR(255) NULL,
    label_source VARCHAR(100) NULL,
    text_input NVARCHAR(MAX) NULL,

    ml_confidence FLOAT NULL,
    decision_mode VARCHAR(100) NULL,

    created_at DATETIME2 NOT NULL CONSTRAINT DF_email_ticket_master_created_at DEFAULT (GETDATE()),
    created_by VARCHAR(100) NOT NULL CONSTRAINT DF_email_ticket_master_created_by DEFAULT ('email_pipeline'),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_email_ticket_master_updated_at DEFAULT (GETDATE()),
    updated_by VARCHAR(100) NOT NULL CONSTRAINT DF_email_ticket_master_updated_by DEFAULT ('email_pipeline')
);
GO

CREATE OR ALTER TRIGGER dbo.trg_update_email_ticket_master
ON dbo.email_ticket_master
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = GETDATE()
    FROM dbo.email_ticket_master t
    INNER JOIN inserted i ON t.record_id = i.record_id;
END
GO

CREATE TABLE dbo.tickets (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    record_id VARCHAR(100) NOT NULL,
    parent_id VARCHAR(100) NULL,
    source_type NVARCHAR(50) NOT NULL CONSTRAINT DF_tickets_source_type DEFAULT ('email'),
    ticket_type NVARCHAR(50) NULL,
    request_number VARCHAR(100) NULL,
    ritm_no VARCHAR(100) NULL,
    inc_no VARCHAR(100) NULL,
    itask_no VARCHAR(100) NULL,
    ctask_no VARCHAR(100) NULL,
    subject NVARCHAR(MAX) NULL,
    short_description NVARCHAR(MAX) NULL,
    description NVARCHAR(MAX) NULL,
    current_status NVARCHAR(50) NOT NULL CONSTRAINT DF_tickets_current_status DEFAULT ('new'),
    priority NVARCHAR(100) NULL,
    urgency NVARCHAR(100) NULL,
    impact NVARCHAR(100) NULL,
    email_date DATETIME2 NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_tickets_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_tickets_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT UQ_tickets_record_id UNIQUE (record_id),
    CONSTRAINT FK_tickets_email_ticket_master FOREIGN KEY (record_id) REFERENCES dbo.email_ticket_master(record_id)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_tickets_updated_at
ON dbo.tickets
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.tickets t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.ticket_classification_results (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NOT NULL,
    predicted_team_pk BIGINT NULL,
    predicted_sub_team_pk BIGINT NULL,
    label_source NVARCHAR(100) NULL,
    ml_confidence FLOAT NULL,
    decision_mode NVARCHAR(100) NULL,
    text_input NVARCHAR(MAX) NULL,
    model_version NVARCHAR(100) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_classification_results_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ticket_classification_results_tickets FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id),
    CONSTRAINT FK_ticket_classification_results_team FOREIGN KEY (predicted_team_pk) REFERENCES dbo.teams(id),
    CONSTRAINT FK_ticket_classification_results_sub_team FOREIGN KEY (predicted_sub_team_pk) REFERENCES dbo.sub_teams(id)
);
GO

CREATE TABLE dbo.ticket_contacts (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NOT NULL,
    contact_type NVARCHAR(50) NOT NULL,
    contact_name NVARCHAR(255) NULL,
    contact_email NVARCHAR(255) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_contacts_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ticket_contacts_tickets FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id)
);
GO

CREATE TABLE dbo.ticket_artifacts (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NOT NULL,
    artifact_type NVARCHAR(50) NOT NULL,
    artifact_value NVARCHAR(2000) NOT NULL,
    source_field NVARCHAR(100) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_artifacts_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ticket_artifacts_tickets FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id)
);
GO

CREATE INDEX IX_ticket_artifacts_lookup
ON dbo.ticket_artifacts(ticket_pk, artifact_type);
GO


/* =========================================================
   6) ROUTING / ESCALATION / ACCEPTANCE
   ========================================================= */

CREATE TABLE dbo.escalation_rules (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    team_pk BIGINT NOT NULL,
    sub_team_pk BIGINT NULL,
    rule_name NVARCHAR(255) NOT NULL,
    tier_level INT NOT NULL,
    wait_minutes INT NOT NULL,
    retry_count INT NOT NULL CONSTRAINT DF_escalation_rules_retry_count DEFAULT (0),
    skip_if_leave BIT NOT NULL CONSTRAINT DF_escalation_rules_skip_if_leave DEFAULT (1),
    skip_if_unavailable BIT NOT NULL CONSTRAINT DF_escalation_rules_skip_if_unavailable DEFAULT (1),
    escalate_to_next_tier BIT NOT NULL CONSTRAINT DF_escalation_rules_escalate_to_next_tier DEFAULT (1),
    notify_admin_if_unassigned BIT NOT NULL CONSTRAINT DF_escalation_rules_notify_admin_if_unassigned DEFAULT (1),
    is_active BIT NOT NULL CONSTRAINT DF_escalation_rules_is_active DEFAULT (1),
    effective_from DATETIME2 NOT NULL CONSTRAINT DF_escalation_rules_effective_from DEFAULT (SYSUTCDATETIME()),
    effective_to DATETIME2 NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_escalation_rules_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_escalation_rules_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_escalation_rules_team FOREIGN KEY (team_pk) REFERENCES dbo.teams(id),
    CONSTRAINT FK_escalation_rules_sub_team FOREIGN KEY (sub_team_pk) REFERENCES dbo.sub_teams(id)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_escalation_rules_updated_at
ON dbo.escalation_rules
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.escalation_rules t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.ticket_routing_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NOT NULL,
    route_round INT NOT NULL,
    routed_team_pk BIGINT NULL,
    routed_sub_team_pk BIGINT NULL,
    route_scope NVARCHAR(100) NULL,
    routing_source NVARCHAR(100) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_routing_logs_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ticket_routing_logs_tickets FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id),
    CONSTRAINT FK_ticket_routing_logs_team FOREIGN KEY (routed_team_pk) REFERENCES dbo.teams(id),
    CONSTRAINT FK_ticket_routing_logs_sub_team FOREIGN KEY (routed_sub_team_pk) REFERENCES dbo.sub_teams(id)
);
GO

CREATE TABLE dbo.ticket_notifications (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NOT NULL,
    route_round INT NOT NULL,
    notify_channel NVARCHAR(50) NOT NULL,
    target_user_pk BIGINT NULL,
    target_line_user_pk BIGINT NULL,
    target_tier INT NULL,
    sent_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_notifications_sent_at DEFAULT (SYSUTCDATETIME()),
    delivery_status NVARCHAR(50) NULL,
    response_deadline_at DATETIME2 NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_notifications_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ticket_notifications_tickets FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id),
    CONSTRAINT FK_ticket_notifications_target_user FOREIGN KEY (target_user_pk) REFERENCES dbo.users(id),
    CONSTRAINT FK_ticket_notifications_target_line_user FOREIGN KEY (target_line_user_pk) REFERENCES dbo.line_users(id)
);
GO

CREATE INDEX IX_ticket_notifications_lookup
ON dbo.ticket_notifications(ticket_pk, route_round, target_tier, sent_at);
GO

CREATE TABLE dbo.ticket_acceptance_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NOT NULL,
    notification_pk BIGINT NULL,
    accepted_by_user_pk BIGINT NULL,
    accepted_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_acceptance_logs_accepted_at DEFAULT (SYSUTCDATETIME()),
    accepted_tier INT NULL,
    response_minutes INT NULL,
    acceptance_status NVARCHAR(50) NOT NULL CONSTRAINT DF_ticket_acceptance_logs_acceptance_status DEFAULT ('accepted'),
    note NVARCHAR(1000) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_acceptance_logs_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ticket_acceptance_logs_tickets FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id),
    CONSTRAINT FK_ticket_acceptance_logs_notification FOREIGN KEY (notification_pk) REFERENCES dbo.ticket_notifications(id),
    CONSTRAINT FK_ticket_acceptance_logs_user FOREIGN KEY (accepted_by_user_pk) REFERENCES dbo.users(id)
);
GO

CREATE TABLE dbo.ticket_escalation_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NOT NULL,
    from_tier INT NULL,
    to_tier INT NULL,
    escalation_reason NVARCHAR(1000) NULL,
    started_at DATETIME2 NULL,
    escalated_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_escalation_logs_escalated_at DEFAULT (SYSUTCDATETIME()),
    elapsed_minutes INT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_escalation_logs_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ticket_escalation_logs_tickets FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id)
);
GO

CREATE TABLE dbo.ticket_assignment_state (
    ticket_pk BIGINT NOT NULL PRIMARY KEY,
    current_team_pk BIGINT NULL,
    current_sub_team_pk BIGINT NULL,
    current_tier INT NULL,
    current_assigned_user_pk BIGINT NULL,
    assignment_status NVARCHAR(50) NOT NULL CONSTRAINT DF_ticket_assignment_state_status DEFAULT ('new'),
    last_notified_at DATETIME2 NULL,
    accepted_at DATETIME2 NULL,
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_assignment_state_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ticket_assignment_state_ticket FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id),
    CONSTRAINT FK_ticket_assignment_state_team FOREIGN KEY (current_team_pk) REFERENCES dbo.teams(id),
    CONSTRAINT FK_ticket_assignment_state_sub_team FOREIGN KEY (current_sub_team_pk) REFERENCES dbo.sub_teams(id),
    CONSTRAINT FK_ticket_assignment_state_user FOREIGN KEY (current_assigned_user_pk) REFERENCES dbo.users(id)
);
GO


/* =========================================================
   7) DATA MAPPING / OVERRIDE
   ========================================================= */

CREATE TABLE dbo.data_mapping_queue (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    queue_type NVARCHAR(100) NOT NULL,
    source_table NVARCHAR(255) NOT NULL,
    source_pk NVARCHAR(255) NOT NULL,
    issue_code NVARCHAR(100) NOT NULL,
    issue_detail NVARCHAR(2000) NULL,
    detected_at DATETIME2 NOT NULL CONSTRAINT DF_data_mapping_queue_detected_at DEFAULT (SYSUTCDATETIME()),
    status NVARCHAR(50) NOT NULL CONSTRAINT DF_data_mapping_queue_status DEFAULT ('open'),
    assigned_to BIGINT NULL,
    resolved_at DATETIME2 NULL,
    resolved_by BIGINT NULL,
    resolution_note NVARCHAR(2000) NULL,

    CONSTRAINT FK_data_mapping_queue_assigned_to FOREIGN KEY (assigned_to) REFERENCES dbo.users(id),
    CONSTRAINT FK_data_mapping_queue_resolved_by FOREIGN KEY (resolved_by) REFERENCES dbo.users(id)
);
GO

CREATE TABLE dbo.manual_override_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NOT NULL,
    override_type NVARCHAR(100) NOT NULL,
    old_value NVARCHAR(MAX) NULL,
    new_value NVARCHAR(MAX) NULL,
    reason NVARCHAR(2000) NULL,
    overridden_by BIGINT NOT NULL,
    overridden_at DATETIME2 NOT NULL CONSTRAINT DF_manual_override_logs_overridden_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_manual_override_logs_ticket FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id),
    CONSTRAINT FK_manual_override_logs_user FOREIGN KEY (overridden_by) REFERENCES dbo.users(id)
);
GO


/* =========================================================
   8) AI ASSISTANT
   ========================================================= */

CREATE TABLE dbo.ai_chat_sessions (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    user_pk BIGINT NOT NULL,
    session_uuid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_ai_chat_sessions_session_uuid DEFAULT (NEWID()),
    session_status NVARCHAR(50) NOT NULL CONSTRAINT DF_ai_chat_sessions_session_status DEFAULT ('active'),
    started_at DATETIME2 NOT NULL CONSTRAINT DF_ai_chat_sessions_started_at DEFAULT (SYSUTCDATETIME()),
    ended_at DATETIME2 NULL,
    closed_by_user BIT NOT NULL CONSTRAINT DF_ai_chat_sessions_closed_by_user DEFAULT (0),
    visible_in_ui BIT NOT NULL CONSTRAINT DF_ai_chat_sessions_visible_in_ui DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ai_chat_sessions_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_ai_chat_sessions_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ai_chat_sessions_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id)
);
GO

CREATE OR ALTER TRIGGER dbo.trg_ai_chat_sessions_updated_at
ON dbo.ai_chat_sessions
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.ai_chat_sessions t
    INNER JOIN inserted i ON t.id = i.id;
END
GO

CREATE TABLE dbo.ai_chat_messages (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    session_pk BIGINT NOT NULL,
    message_role NVARCHAR(20) NOT NULL,
    message_text NVARCHAR(MAX) NOT NULL,
    message_order INT NOT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ai_chat_messages_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ai_chat_messages_sessions FOREIGN KEY (session_pk) REFERENCES dbo.ai_chat_sessions(id)
);
GO

CREATE TABLE dbo.ai_chat_message_metadata (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    message_pk BIGINT NOT NULL,
    source_type NVARCHAR(100) NULL,
    source_ref NVARCHAR(255) NULL,
    confidence_score FLOAT NULL,
    token_count INT NULL,
    response_time_ms INT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ai_chat_message_metadata_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ai_chat_message_metadata_message FOREIGN KEY (message_pk) REFERENCES dbo.ai_chat_messages(id)
);
GO

CREATE TABLE dbo.ai_chat_feedback (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    message_pk BIGINT NOT NULL,
    user_pk BIGINT NOT NULL,
    feedback_type NVARCHAR(50) NOT NULL,
    feedback_note NVARCHAR(1000) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ai_chat_feedback_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ai_chat_feedback_message FOREIGN KEY (message_pk) REFERENCES dbo.ai_chat_messages(id),
    CONSTRAINT FK_ai_chat_feedback_user FOREIGN KEY (user_pk) REFERENCES dbo.users(id)
);
GO

CREATE TABLE dbo.ai_chat_audit_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    session_pk BIGINT NOT NULL,
    user_pk BIGINT NOT NULL,
    prompt_text NVARCHAR(MAX) NOT NULL,
    response_text NVARCHAR(MAX) NULL,
    access_scope NVARCHAR(255) NULL,
    blocked_reason NVARCHAR(1000) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_ai_chat_audit_logs_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ai_chat_audit_logs_session FOREIGN KEY (session_pk) REFERENCES dbo.ai_chat_sessions(id),
    CONSTRAINT FK_ai_chat_audit_logs_user FOREIGN KEY (user_pk) REFERENCES dbo.users(id)
);
GO


/* =========================================================
   9) AUDIT / SLA / REPORT
   ========================================================= */

CREATE TABLE dbo.audit_logs (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    actor_user_pk BIGINT NULL,
    action_type NVARCHAR(100) NOT NULL,
    entity_type NVARCHAR(100) NOT NULL,
    entity_pk NVARCHAR(255) NOT NULL,
    old_value_json NVARCHAR(MAX) NULL,
    new_value_json NVARCHAR(MAX) NULL,
    action_at DATETIME2 NOT NULL CONSTRAINT DF_audit_logs_action_at DEFAULT (SYSUTCDATETIME()),
    ip_address NVARCHAR(100) NULL,

    CONSTRAINT FK_audit_logs_user FOREIGN KEY (actor_user_pk) REFERENCES dbo.users(id)
);
GO

CREATE TABLE dbo.ticket_sla_metrics (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ticket_pk BIGINT NOT NULL,
    first_notified_at DATETIME2 NULL,
    first_accepted_at DATETIME2 NULL,
    total_response_minutes INT NULL,
    first_tier_response_minutes INT NULL,
    total_escalation_count INT NOT NULL CONSTRAINT DF_ticket_sla_metrics_total_escalation_count DEFAULT (0),
    accepted_tier INT NULL,
    had_timeout_before_accept BIT NOT NULL CONSTRAINT DF_ticket_sla_metrics_had_timeout_before_accept DEFAULT (0),
    no_acceptance_flag BIT NOT NULL CONSTRAINT DF_ticket_sla_metrics_no_acceptance_flag DEFAULT (0),
    calculated_at DATETIME2 NOT NULL CONSTRAINT DF_ticket_sla_metrics_calculated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_ticket_sla_metrics_tickets FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id),
    CONSTRAINT UQ_ticket_sla_metrics_ticket UNIQUE (ticket_pk)
);
GO

CREATE TABLE dbo.daily_team_metrics (
    id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    metric_date DATE NOT NULL,
    team_pk BIGINT NOT NULL,
    sub_team_pk BIGINT NULL,
    total_tickets INT NOT NULL CONSTRAINT DF_daily_team_metrics_total_tickets DEFAULT (0),
    accepted_tickets INT NOT NULL CONSTRAINT DF_daily_team_metrics_accepted_tickets DEFAULT (0),
    escalated_tickets INT NOT NULL CONSTRAINT DF_daily_team_metrics_escalated_tickets DEFAULT (0),
    avg_response_minutes DECIMAL(10,2) NULL,
    no_acceptance_tickets INT NOT NULL CONSTRAINT DF_daily_team_metrics_no_acceptance_tickets DEFAULT (0),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_daily_team_metrics_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT FK_daily_team_metrics_team FOREIGN KEY (team_pk) REFERENCES dbo.teams(id),
    CONSTRAINT FK_daily_team_metrics_sub_team FOREIGN KEY (sub_team_pk) REFERENCES dbo.sub_teams(id),
    CONSTRAINT UQ_daily_team_metrics UNIQUE (metric_date, team_pk, sub_team_pk)
);
GO


/************************************************************
 OPTIONAL FK ADDITIONS FOR LINE / TICKET TABLES
 Added after tickets table exists
************************************************************/

ALTER TABLE dbo.line_message_logs
ADD CONSTRAINT FK_line_message_logs_ticket
FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id);
GO

ALTER TABLE dbo.line_message_logs
ADD CONSTRAINT FK_line_message_logs_chat
FOREIGN KEY (chat_pk) REFERENCES dbo.line_chats(id);
GO

ALTER TABLE dbo.line_message_logs
ADD CONSTRAINT FK_line_message_logs_line_user
FOREIGN KEY (target_line_user_pk) REFERENCES dbo.line_users(id);
GO

ALTER TABLE dbo.line_action_logs
ADD CONSTRAINT FK_line_action_logs_ticket
FOREIGN KEY (ticket_pk) REFERENCES dbo.tickets(id);
GO


----------------------------------


INSERT INTO dbo.roles (role_code, role_name, description)
VALUES
('employee', 'Employee', 'พนักงานทั่วไป'),
('admin', 'Admin', 'ผู้ดูแลระดับทีม'),
('super_admin', 'Super Admin', 'ผู้ดูแลระบบสูงสุด');
GO