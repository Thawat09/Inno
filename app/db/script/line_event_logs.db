IF OBJECT_ID('dbo.line_event_logs', 'U') IS NOT NULL
    DROP TABLE dbo.line_event_logs;
GO

CREATE TABLE dbo.line_event_logs (
    id BIGINT IDENTITY(1,1) NOT NULL,
    event_type NVARCHAR(100) NOT NULL,
    chat_type NVARCHAR(20) NULL,
    chat_id NVARCHAR(100) NULL,
    line_user_id NVARCHAR(100) NULL,
    event_timestamp BIGINT NULL,
    raw_json NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_line_event_logs_created_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_line_event_logs PRIMARY KEY (id)
);
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ตารางเก็บ Event Log จาก LINE Webhook แบบ Raw เพื่อใช้สำหรับ Audit, Debug และ Analytics',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_event_logs';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Primary Key ของตาราง (Auto Increment ใช้ระบุลำดับ event)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_event_logs',
    @level2type = N'COLUMN', @level2name = 'id';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ประเภทของ event จาก LINE เช่น message, follow, unfollow, join, leave, memberJoined, memberLeft, postback',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_event_logs',
    @level2type = N'COLUMN', @level2name = 'event_type';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ประเภทของ chat ที่เกิด event เช่น group, room, user (1:1 chat)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_event_logs',
    @level2type = N'COLUMN', @level2name = 'chat_type';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ID ของ chat จาก LINE (groupId, roomId หรือ userId ที่เกี่ยวข้องกับ event)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_event_logs',
    @level2type = N'COLUMN', @level2name = 'chat_id';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'LINE User ID ของผู้ที่เกี่ยวข้องกับ event (เช่น คนส่ง message หรือ join/leave)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_event_logs',
    @level2type = N'COLUMN', @level2name = 'line_user_id';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Timestamp ของ event จาก LINE (Unix Epoch หน่วย millisecond)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_event_logs',
    @level2type = N'COLUMN', @level2name = 'event_timestamp';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ข้อมูล JSON ดิบของ event จาก LINE Webhook ใช้สำหรับ debug และ reprocess',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_event_logs',
    @level2type = N'COLUMN', @level2name = 'raw_json';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่บันทึก event ลง database (UTC)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_event_logs',
    @level2type = N'COLUMN', @level2name = 'created_at';
GO