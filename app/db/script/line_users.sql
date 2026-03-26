IF OBJECT_ID('dbo.line_users', 'U') IS NOT NULL
    DROP TABLE dbo.line_users;
GO

CREATE TABLE dbo.line_users (
    id BIGINT IDENTITY(1,1) NOT NULL,
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

    CONSTRAINT PK_line_users PRIMARY KEY (id),
    CONSTRAINT FK_line_users_users FOREIGN KEY (user_pk) REFERENCES dbo.users(id)
);
GO

CREATE OR ALTER TRIGGER trg_line_users_updated_at
ON dbo.line_users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET t.updated_at = SYSUTCDATETIME()
    FROM dbo.line_users t
    INNER JOIN inserted i
        ON t.id = i.id;
END
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ตารางเก็บข้อมูลผู้ใช้งาน LINE (Profile + สถานะความสัมพันธ์กับระบบ เช่น friend/block และ mapping กับ user ภายใน)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Primary Key ของตาราง (Auto Increment)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'id';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'LINE User ID (ค่าที่ได้จาก LINE Platform ใช้เป็น unique identifier ของ user)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'user_id';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ชื่อที่แสดงของ user จาก LINE Profile',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'display_name';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'URL รูปโปรไฟล์ของ user จาก LINE',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'picture_url';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Status Message ของ user จาก LINE Profile',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'status_message';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'ภาษาที่ user ใช้ (เช่น th, en) จาก LINE Profile',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'language';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Foreign Key ไปยังตาราง users (ระบบภายใน) ใช้ mapping LINE User กับ Internal User',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'user_pk';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'สถานะว่า user เป็นเพื่อนกับ LINE OA หรือไม่ (1 = เป็นเพื่อน, 0 = ไม่เป็นเพื่อน / block)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'is_friend';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'สถานะของ user ในระบบ เช่น active, blocked (ใช้ร่วมกับ is_friend)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'status';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาล่าสุดที่ user มี activity (เช่น ส่ง message, postback)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'last_seen_at';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่ record ถูกสร้าง',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'created_at';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'วันเวลาที่ record ถูกแก้ไขล่าสุด (update ผ่าน trigger)',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'line_users',
    @level2type = N'COLUMN', @level2name = 'updated_at';
GO