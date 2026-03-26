CREATE TABLE email_ticket_master (
    record_id VARCHAR(100) PRIMARY KEY,
    parent_id VARCHAR(100),
    message_id VARCHAR(255),
    email_date DATETIME2 NULL,

    from_address VARCHAR(255),
    to_address VARCHAR(255),
    ticket_type VARCHAR(50),

    request_number VARCHAR(100),
    ritm_no VARCHAR(100),
    inc_no VARCHAR(100),
    itask_no VARCHAR(100),
    ctask_no VARCHAR(100),

    subject_clean NVARCHAR(MAX),
    short_desc_clean NVARCHAR(MAX),
    description_clean NVARCHAR(MAX),
    description_for_model NVARCHAR(MAX),
    related_env_raw NVARCHAR(MAX),
    body_for_model NVARCHAR(MAX),

    opened_by VARCHAR(255),
    requested_for VARCHAR(255),
    raised_by VARCHAR(255),
    business_service VARCHAR(255),
    service_offering VARCHAR(255),
    priority VARCHAR(100),
    urgency VARCHAR(100),
    impact VARCHAR(100),
    contact_email VARCHAR(255),

    ip_list_json NVARCHAR(MAX),
    url_list_json NVARCHAR(MAX),

    has_aws_ip BIT,
    has_gcp_ip BIT,
    has_aws_keyword_header BIT,
    has_gcp_keyword_header BIT,
    has_aws_keyword_body BIT,
    has_gcp_keyword_body BIT,
    has_aws_keyword_desc BIT,
    has_gcp_keyword_desc BIT,
    env_has_aws BIT,
    env_has_gcp BIT,

    assigned_group_from_to VARCHAR(255),
    route_scope VARCHAR(100),

    sibling_task_count INT,
    sibling_known_sub_team VARCHAR(255),
    cross_task_inference_used BIT,

    label_main_team VARCHAR(255),
    label_sub_team VARCHAR(255),
    label_source VARCHAR(100),
    text_input NVARCHAR(MAX),

    ml_confidence FLOAT NULL,
    decision_mode VARCHAR(100) NULL,

    created_at DATETIME2 DEFAULT GETDATE(),
    created_by VARCHAR(100) DEFAULT 'email_pipeline',

    updated_at DATETIME2 DEFAULT GETDATE(),
    updated_by VARCHAR(100) DEFAULT 'email_pipeline'
);
GO

CREATE TRIGGER trg_update_email_ticket_master
ON email_ticket_master
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET updated_at = GETDATE()
    FROM email_ticket_master t
    INNER JOIN inserted i 
        ON t.record_id = i.record_id;
END
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ตารางข้อมูล Email Ticket ที่ผ่านการ clean และเตรียม feature แล้ว ใช้เป็น master table สำหรับการ train model, classification, routing ไปยังทีมที่รับผิดชอบ และการวิเคราะห์ผลการตัดสินใจของระบบ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รหัสหลักของ record ในตารางนี้ ใช้เป็น Primary Key โดยจากข้อมูลจริงมักเป็นเลขงาน เช่น TASK..., ITASK..., หรือเลขอ้างอิงหลักของรายการ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'record_id';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รหัสอ้างอิงของงานแม่หรืองานต้นทาง เช่น RITM..., TASK..., ITASK... ใช้เชื่อมโยงรายการงานที่อยู่ใน chain เดียวกัน',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'parent_id';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Message-ID ของ email จาก mail header ใช้ระบุอีเมลต้นทางแบบไม่ซ้ำในระบบอีเมล',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'message_id';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'วันและเวลาของ email ต้นทางที่นำมาสร้างหรืออัปเดต ticket record นี้',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'email_date';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อหรือ email address ของผู้ส่ง email ต้นทาง เช่น SCG Ticket System',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'from_address';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'email address ของผู้รับปลายทางที่ระบบรับเข้ามา ใช้ช่วย infer ขอบเขตงานหรือทีมรับผิดชอบได้ในบางกรณี',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'to_address';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ประเภทของ ticket ที่ normalize แล้ว เช่น catalog_task, incident_task หรือประเภทอื่นที่ใช้ใน pipeline',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'ticket_type';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'เลข Request หลัก เช่น REQ... ใช้อ้างอิงคำขอระดับบนสุดของรายการงาน',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'request_number';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'เลข RITM ของ service request ที่เกี่ยวข้องกับ record นี้',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'ritm_no';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'เลข Incident เช่น INC... หาก record นี้เกี่ยวข้องกับ incident',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'inc_no';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'เลข Incident Task เช่น ITASK... หากเป็นงานย่อยของ incident',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'itask_no';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'เลข Catalog Task เช่น CTASK... หาก record นี้เกี่ยวข้องกับ catalog task',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'ctask_no';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Subject ของ email ที่ผ่านการ clean แล้ว เช่น ตัด prefix, normalize รูปแบบข้อความ และเตรียมไว้สำหรับค้นหา/feature engineering',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'subject_clean';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Short description ที่ผ่านการ clean แล้ว ใช้เป็นข้อความหลักในการ classify ticket และกำหนดทีม',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'short_desc_clean';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รายละเอียดของงานที่ผ่านการ clean แล้ว โดยยังคงความหมายเชิงธุรกิจและเทคนิคไว้สำหรับค้นหา วิเคราะห์ และตรวจสอบ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'description_clean';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ข้อความ description ที่ถูกเตรียมเพิ่มเติมเพื่อใช้เป็น input สำหรับ model โดยอาจมีการตัด noise, normalize token หรือคงเฉพาะข้อมูลสำคัญสำหรับการทำนาย',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'description_for_model';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ข้อมูล environment หรือระบบที่เกี่ยวข้องในรูปแบบ raw/normalized บางส่วน เช่น AWS Hub, GCP Hub, On-prem, PROD, DEV หรือชื่อระบบที่ extract ได้',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'related_env_raw';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ข้อความจาก body ที่เตรียมไว้สำหรับ model โดยอาจเป็น body ที่สกัดเฉพาะส่วนสำคัญหรือจัดรูปแบบใหม่เพื่อใช้ train/inference',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'body_for_model';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อผู้เปิด ticket หรือผู้ที่สร้างรายการงานในระบบ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'opened_by';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อผู้ที่เป็นผู้รับคำขอหรือผู้ที่ request นี้ถูกสร้างให้',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'requested_for';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อผู้ยกระดับหรือผู้แจ้งงานต้นทาง หากระบบสามารถแยกค่า raised by ออกมาได้',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'raised_by';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Business Service ที่เกี่ยวข้องกับ ticket ใช้ช่วยวิเคราะห์และจัดกลุ่มงานเชิงบริการ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'business_service';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Service Offering ที่เกี่ยวข้องกับ ticket ใช้ช่วยจัดหมวดงานหรือวิเคราะห์ในมุมบริการ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'service_offering';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ระดับความสำคัญของ ticket เช่น Priority จากระบบต้นทาง หากมี',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'priority';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ระดับความเร่งด่วนของ ticket จากระบบต้นทาง หากมี',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'urgency';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ระดับผลกระทบของ ticket จากระบบต้นทาง หากมี',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'impact';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'email ติดต่อหลักที่สกัดได้จาก ticket ใช้สำหรับแจ้งกลับหรือใช้เป็น feature ประกอบการตัดสินใจ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'contact_email';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รายการ IP Address ที่ extract ได้จากข้อมูล ticket โดยเก็บเป็น JSON array เพื่อใช้เป็น feature และตรวจจับขอบเขตงาน AWS/GCP/On-prem',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'ip_list_json';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รายการ URL ที่ extract ได้จากข้อมูล ticket โดยเก็บเป็น JSON array เพื่อใช้วิเคราะห์ต่อหรือทำ feature engineering',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'url_list_json';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าพบ IP ที่เข้าข่ายกลุ่ม AWS จากกฎหรือ logic ที่ระบบกำหนด',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'has_aws_ip';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าพบ IP ที่เข้าข่ายกลุ่ม GCP จากกฎหรือ logic ที่ระบบกำหนด',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'has_gcp_ip';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าพบ keyword ที่เกี่ยวข้องกับ AWS ในส่วนหัวข้อหรือ header ของข้อความ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'has_aws_keyword_header';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าพบ keyword ที่เกี่ยวข้องกับ GCP ในส่วนหัวข้อหรือ header ของข้อความ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'has_gcp_keyword_header';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าพบ keyword ที่เกี่ยวข้องกับ AWS ในเนื้อหา body หรือข้อความหลัก',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'has_aws_keyword_body';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าพบ keyword ที่เกี่ยวข้องกับ GCP ในเนื้อหา body หรือข้อความหลัก',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'has_gcp_keyword_body';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าพบ keyword ที่เกี่ยวข้องกับ AWS ใน short description หรือ description ที่ clean แล้ว',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'has_aws_keyword_desc';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าพบ keyword ที่เกี่ยวข้องกับ GCP ใน short description หรือ description ที่ clean แล้ว',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'has_gcp_keyword_desc';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าข้อมูล environment ที่ extract ได้มีความเกี่ยวข้องกับ AWS',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'env_has_aws';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าข้อมูล environment ที่ extract ได้มีความเกี่ยวข้องกับ GCP',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'env_has_gcp';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อ Assignment Group หรือกลุ่มรับงานที่ตรวจพบจากช่องทาง to-address หรือ metadata อื่น เช่น iNET Cloud Support Team',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'assigned_group_from_to';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ขอบเขตการ route งาน เช่น main_team, subteam, cloud_subteam หรือ scope อื่นตาม logic ของ pipeline',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'route_scope';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'จำนวนงานพี่น้องหรือรายการงานอื่นที่อยู่ภายใต้ parent เดียวกัน ใช้ช่วย infer ทีมจากบริบทของงานในชุดเดียวกัน',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'sibling_task_count';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'รายชื่อ sub team ที่ทราบจาก sibling tasks หรือจากประวัติงานใน family เดียวกัน ใช้เป็นบริบทเสริมในการตัดสินใจ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'sibling_known_sub_team';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Flag ระบุว่าได้ใช้การอนุมานจากงานอื่นในกลุ่มเดียวกันหรือ sibling tasks เพื่อช่วยตัดสินใจ route หรือติด label',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'cross_task_inference_used';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อทีมหลักที่ระบบกำหนดหรือใช้เป็น label หลัก เช่น iNET Cloud Support Team',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'label_main_team';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อทีมย่อยที่ระบบคาดการณ์หรือกำหนดให้รับผิดชอบงาน เช่น AWS Team หรือ GCP Team',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'label_sub_team';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'แหล่งที่มาของ label หรือเหตุผลหลักที่ใช้กำหนด label เช่น task_short_desc, ritm_short_desc, ip_match, keyword_header, ml_model_confidence',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'label_source';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ข้อความ input ที่ถูกประกอบหรือเลือกไว้เพื่อส่งเข้า model หรือใช้บันทึกว่า text อะไรเป็นตัวตั้งต้นของการตัดสินใจ',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'text_input';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ค่าความมั่นใจของ model หรือ scoring logic ในการทำนาย label/sub team โดยมีค่าเป็นตัวเลขทศนิยม',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'ml_confidence';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'โหมดการตัดสินใจของระบบ เช่น logic_explicit_rule, logic_fallback, ml_high_confidence ใช้บอกว่าผลลัพธ์นี้มาจาก rule หรือ model',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'decision_mode';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'วันเวลาที่ record นี้ถูกสร้างใน master table',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'created_at';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อ process หรือระบบที่สร้าง record นี้ โดยค่าตั้งต้นคือ email_pipeline',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'created_by';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'วันเวลาที่ record นี้ถูกแก้ไขล่าสุด โดย trigger จะอัปเดตค่านี้ทุกครั้งที่มีการ UPDATE',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'updated_at';
GO

EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'ชื่อ process หรือ user ที่แก้ไข record ล่าสุด โดยค่าตั้งต้นคือ email_pipeline',
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'email_ticket_master',
    @level2type = N'COLUMN', @level2name = 'updated_by';
GO