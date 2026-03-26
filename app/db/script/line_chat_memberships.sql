IF OBJECT_ID('dbo.line_chat_memberships', 'U') IS NOT NULL
    DROP TABLE dbo.line_chat_memberships;
GO

CREATE TABLE dbo.line_chat_memberships (
    id BIGINT IDENTITY(1,1) NOT NULL,
    chat_pk BIGINT NOT NULL,
    line_user_pk BIGINT NOT NULL,

    status NVARCHAR(50) NOT NULL CONSTRAINT DF_line_chat_memberships_status DEFAULT ('active'),
    joined_at DATETIME2 NULL,
    left_at DATETIME2 NULL,
    last_seen_at DATETIME2 NULL,

    created_at DATETIME2 NOT NULL CONSTRAINT DF_line_chat_memberships_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_line_chat_memberships_updated_at DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_line_chat_memberships PRIMARY KEY (id),
    CONSTRAINT FK_line_chat_memberships_line_chats FOREIGN KEY (chat_pk) REFERENCES dbo.line_chats(id),
    CONSTRAINT FK_line_chat_memberships_line_users FOREIGN KEY (line_user_pk) REFERENCES dbo.line_users(id)
);
GO

CREATE OR ALTER TRIGGER trg_line_chat_memberships_updated_at
ON dbo.line_chat_memberships
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET t.updated_at = SYSUTCDATETIME()
    FROM dbo.line_chat_memberships t
    INNER JOIN inserted i
        ON t.id = i.id;
END
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ตารางเก็บความสัมพันธ์ระหว่าง LINE User กับ Chat (Group/Room/User) รวมถึงสถานะการเข้าร่วม',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chat_memberships';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Primary Key ของตาราง (Auto Increment)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chat_memberships',
    @level2type = N'COLUMN', @level2name = 'id';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Foreign Key ไปยัง line_chats.id (ระบุว่า user อยู่ใน chat ไหน)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chat_memberships',
    @level2type = N'COLUMN', @level2name = 'chat_pk';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Foreign Key ไปยัง line_users.id (ระบุว่าเป็น user คนไหน)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chat_memberships',
    @level2type = N'COLUMN', @level2name = 'line_user_pk';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'สถานะของ user ใน chat เช่น active (อยู่ในกลุ่ม), left (ออกจากกลุ่ม)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chat_memberships',
    @level2type = N'COLUMN', @level2name = 'status';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่ user เข้าร่วม chat ครั้งแรก (หรือครั้งล่าสุด)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chat_memberships',
    @level2type = N'COLUMN', @level2name = 'joined_at';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่ user ออกจาก chat (NULL หากยังอยู่)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chat_memberships',
    @level2type = N'COLUMN', @level2name = 'left_at';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาล่าสุดที่พบ user ใน chat (มี activity เช่น message, postback)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chat_memberships',
    @level2type = N'COLUMN', @level2name = 'last_seen_at';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่ record ถูกสร้าง',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chat_memberships',
    @level2type = N'COLUMN', @level2name = 'created_at';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่ record ถูกแก้ไขล่าสุด (update ผ่าน trigger)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_chat_memberships',
    @level2type = N'COLUMN', @level2name = 'updated_at';
GO