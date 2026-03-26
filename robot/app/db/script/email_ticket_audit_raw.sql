CREATE TABLE email_ticket_audit_raw (
    record_id VARCHAR(100) PRIMARY KEY,
    parent_id VARCHAR(100),
    message_id VARCHAR(255),
    email_date DATETIME2 NULL,

    subject_raw NVARCHAR(MAX),
    body_raw NVARCHAR(MAX),

    parsed_task_short_desc NVARCHAR(MAX),
    parsed_ritm_short_desc NVARCHAR(MAX),
    parsed_inc_short_desc NVARCHAR(MAX),
    parsed_ctask_short_desc NVARCHAR(MAX),
    parsed_description NVARCHAR(MAX),
    parsed_related_env NVARCHAR(MAX),
    parsed_requested_for VARCHAR(255),
    parsed_opened_by VARCHAR(255),
    parsed_business_service VARCHAR(255),
    parsed_service_offering VARCHAR(255),

    ip_list_json NVARCHAR(MAX),
    url_list_json NVARCHAR(MAX),

    created_at DATETIME2 DEFAULT GETDATE(),
    created_by VARCHAR(100) DEFAULT 'email_pipeline',

    updated_at DATETIME2 DEFAULT GETDATE(),
    updated_by VARCHAR(100) DEFAULT 'email_pipeline'
);
GO

CREATE TRIGGER trg_update_email_ticket_audit_raw
ON email_ticket_audit_raw
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = GETDATE()
    FROM email_ticket_audit_raw t
    INNER JOIN inserted i
        ON t.record_id = i.record_id;
END
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ตารางเก็บข้อมูล Email Ticket ที่รับเข้ามาจากระบบแจ้งงาน โดยเก็บทั้งข้อมูลต้นฉบับของ email และข้อมูลที่ parse ออกมาแล้ว เพื่อใช้สำหรับ audit, search, dashboard และ automation',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รหัส record หลักของข้อมูลที่เก็บในตารางนี้ จากข้อมูลจริงมักเป็นเลขงานประเภท TASK เช่น TASK1504683 และใช้เป็น Primary Key',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'record_id';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รหัสอ้างอิงของงานแม่หรือรายการต้นทาง จากข้อมูลจริงมักเป็นเลข RITM เช่น RITM0780598 ใช้เชื่อมโยง TASK กับคำขอบริการหลัก',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parent_id';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Message-ID ของ email จาก mail header ใช้ระบุ email แต่ละฉบับแบบไม่ซ้ำในระบบอีเมล',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'message_id';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'วันและเวลาของ email ที่รับเข้ามา ใช้อ้างอิงเวลาต้นทางของรายการงาน',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'email_date';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Subject ของ email แบบต้นฉบับที่รับเข้ามา ยังไม่ผ่านการแปลงหรือทำความสะอาดข้อมูล',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'subject_raw';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'เนื้อหา email แบบต้นฉบับทั้งหมด ใช้เก็บเพื่อ audit, ตรวจสอบย้อนหลัง และใช้ parse ข้อมูลเพิ่มเติมในภายหลัง',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'body_raw';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ข้อความ short description ที่ parse และจัดให้อยู่ในระดับงานย่อยหรือ Task โดยจากข้อมูลจริงมักเป็นหัวข้อสั้นของงานที่ใช้สื่อสารหรือค้นหา',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parsed_task_short_desc';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ข้อความ short description ที่ parse ในระดับ RITM หรือ service request หลัก จากข้อมูลจริงมักเป็นชื่อคำขอหลักของรายการงาน',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parsed_ritm_short_desc';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ข้อความ short description ที่ parse ในกรณี email เกี่ยวข้องกับ Incident เช่น INCxxxx หากไม่ใช่ incident จะเป็น NULL',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parsed_inc_short_desc';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ข้อความ short description ที่ parse สำหรับ Catalog Task หรือ CTASK หาก email หรือข้อมูลต้นทางมีงานประเภทนี้ หากไม่มีจะเป็น NULL',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parsed_ctask_short_desc';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รายละเอียดสำคัญของงานที่ parse ออกมาจากเนื้อหา email เช่น รายละเอียดคำขอ, รายละเอียด firewall, รายการที่ต้องดำเนินการ หรือข้อความที่ใช้สรุปงาน',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parsed_description';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Environment หรือขอบเขตระบบที่ parse ได้จาก email เช่น PROD, UAT, DEV, VPN User, AWS Hub, IT One Service หรือข้อความกลุ่มระบบที่เกี่ยวข้อง',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parsed_related_env';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อผู้ที่เป็นผู้ขอใช้บริการหรือผู้ที่ request นี้ถูกสร้างให้ จากข้อมูลจริงเป็นชื่อบุคคล เช่น Akarit Chaipecharakul',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parsed_requested_for';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อผู้เปิด ticket หรือผู้ส่งคำขอเข้าระบบ จากข้อมูลจริงเป็นชื่อบุคคลที่เปิดรายการงาน',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parsed_opened_by';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Business Service ที่ parse ได้จาก email หรือจาก template ของ ticket หาก email ไม่มีข้อมูลส่วนนี้จะเป็น NULL',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parsed_business_service';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Service Offering ที่ parse ได้จาก email หรือจาก template ของ ticket หากไม่มีข้อมูลจะเป็น NULL',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'parsed_service_offering';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รายการ IP Address ที่ตรวจพบและ extract ได้จาก subject หรือ body ของ email โดยเก็บเป็น JSON array เช่น ["10.42.131.0"]',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'ip_list_json';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รายการ URL ที่ตรวจพบและ extract ได้จาก subject หรือ body ของ email โดยเก็บเป็น JSON array หากไม่พบจะเป็น NULL',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'url_list_json';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'วันเวลาที่ record นี้ถูกบันทึกเข้าตาราง',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'created_at';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อ process หรือระบบที่สร้าง record นี้ โดยค่าปัจจุบันใช้ email_pipeline',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'created_by';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'วันเวลาที่ record นี้ถูกแก้ไขล่าสุด โดย trigger จะอัปเดตค่านี้ทุกครั้งที่มีการ UPDATE',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'updated_at';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อ process หรือ user ที่แก้ไข record ล่าสุด โดยค่าปัจจุบันตั้งต้นเป็น email_pipeline',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_audit_raw',
    @level2type = N'COLUMN', @level2name = 'updated_by';
GO