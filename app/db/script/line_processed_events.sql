IF OBJECT_ID('dbo.line_processed_events', 'U') IS NOT NULL
    DROP TABLE dbo.line_processed_events;
GO

CREATE TABLE dbo.line_processed_events (
    webhook_event_id NVARCHAR(100) NOT NULL,
    event_type NVARCHAR(100) NOT NULL,
    processed_at DATETIME2 NOT NULL
        CONSTRAINT DF_line_processed_events_processed_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_line_processed_events PRIMARY KEY (webhook_event_id)
);
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ตารางเก็บ webhookEventId ของ LINE event ที่ระบบประมวลผลสำเร็จแล้ว ใช้สำหรับป้องกัน event ซ้ำจากการ redelivery',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_processed_events';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รหัส event จาก LINE Webhook ใช้เป็น Primary Key เพื่อกัน event ซ้ำ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_processed_events',
    @level2type = N'COLUMN', @level2name = 'webhook_event_id';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ประเภทของ event จาก LINE เช่น message, join, leave, memberJoined, memberLeft, follow, unfollow, postback',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_processed_events',
    @level2type = N'COLUMN', @level2name = 'event_type';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'วันเวลาที่ระบบบันทึกว่า event นี้ถูกประมวลผลสำเร็จแล้ว (UTC)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_processed_events',
    @level2type = N'COLUMN', @level2name = 'processed_at';
GO