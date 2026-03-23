IF OBJECT_ID('dbo.line_chats', 'U') IS NOT NULL
    DROP TABLE dbo.line_chats;
GO

CREATE TABLE dbo.line_chats (
    id BIGINT IDENTITY(1,1) NOT NULL,
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

    CONSTRAINT PK_line_chats PRIMARY KEY (id)
);
GO

CREATE OR ALTER TRIGGER trg_line_chats_updated_at
ON dbo.line_chats
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET t.updated_at = SYSUTCDATETIME()
    FROM dbo.line_chats t
    INNER JOIN inserted i
        ON t.id = i.id;
END
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ตารางเก็บข้อมูล Chat ของ LINE (Group / Room / User 1:1) ใช้เป็นศูนย์กลางของการสนทนา',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Primary Key ของตาราง (Auto Increment)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'id';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ประเภทของ chat เช่น group, room, user (1:1 chat)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'chat_type';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ID ของ chat จาก LINE (เช่น groupId, roomId หรือ userId)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'chat_id';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ชื่อ group (ใช้ได้เฉพาะ chat_type = group, ดึงจาก LINE API)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'group_name';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'จำนวนสมาชิกใน chat (ใช้สำหรับ analytics หรือ dashboard)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'member_count';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'สถานะของ bot ใน chat เช่น active (อยู่ในกลุ่ม), left (ออกจากกลุ่ม)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'bot_status';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่ bot เข้าร่วม chat (group/room)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'bot_joined_at';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่ bot ออกจาก chat (NULL หากยังอยู่)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'bot_left_at';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาล่าสุดที่มี activity ใน chat นี้ (เช่น message, join, postback)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'last_seen_at';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่ record ถูกสร้าง',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'created_at';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่ record ถูกแก้ไขล่าสุด (update ผ่าน trigger)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chats',
    @level2type = N'COLUMN', @level2name = 'updated_at';
GO