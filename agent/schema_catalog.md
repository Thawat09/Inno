# Schema Catalog
## Ticket Routing & Standby Notification Platform
Version: 1.0  
Source basis: PostgreSQL schema (migrated from SQL Server DDL)
Purpose: provide a schema-locked reference for AI Assistant SQL generation

> Important: This file is a catalog and query guide.  
> It is not the final PostgreSQL migration script.
> Use this file to understand table purpose, safe joins, key columns, and restricted areas.  
> Sensitive fields must still be filtered by `sensitive_data_guardrails.md`.

Source schema reference: fileciteturn14file0

---

## 1) Schema Platform Note

The current schema is PostgreSQL-based (migrated from SQL Server).

Typical PostgreSQL characteristics:
- schema prefix: `public` (instead of `dbo`)
- identity keys: `bigserial`, `generated identity`, or `uuid`, depending on table design
- string types: `varchar` / `text`
- datetime types: `timestamp` / `timestamptz`
- boolean type: `boolean`
- UUID type: `uuid`
- triggers use PostgreSQL `CREATE TRIGGER` with trigger functions (typically `plpgsql`)

For AI query generation:
- generate **PostgreSQL-style read-only SQL**
- table names should conceptually map 1:1
- schema prefix may be `public`
- use PostgreSQL-compatible data types and syntax
- booleans are represented as `boolean`
- former SQL Server `datetime2` values are represented as `timestamp` / `timestamptz`
- former SQL Server `uniqueidentifier` values are represented as `uuid`

Do not rely on SQL Server-only syntax when generating runtime query text for the current system.

---

## 2) Querying Principles

1. Prefer operational tables over raw audit tables when answering normal user questions
2. Use raw/audit tables only when the question is specifically about ingestion/parsing/audit
3. Avoid sensitive columns entirely
4. Use joins through FK meaning, not guessed relationships
5. Prefer concise `select` lists
6. Apply permission filters in app/service layer if provided

---

# 3) Table Catalog

## 3.1 roles
**Purpose**: role master table  
**Primary key**: `id`  
**Important columns**:
- `role_code`
- `role_name`
- `description`
- `is_active`

**Typical use**:
- list role definitions
- join through `user_roles`

**Safe joins**:
- `user_roles.role_pk -> roles.id`

---

## 3.2 users
**Purpose**: web application users / internal personnel  
**Primary key**: `id`  
**Important non-sensitive columns**:
- `line_user_id`
- `employee_code`
- `first_name`
- `last_name`
- `nickname`
- `phone`
- `email`
- `main_team`
- `sub_team`
- `failed_login_count`
- `last_login_at`
- `is_active`
- `is_admin`
- `created_at`
- `updated_at`

**Sensitive columns — do not query**:
- `password_hash`
- `password_salt`

**Typical use**:
- find people
- identify ticket owners
- resolve standby assignees
- map to teams or line users

**Safe joins**:
- `user_roles.user_pk -> users.id`
- `team_members.user_pk -> users.id`
- `line_users.user_pk -> users.id`
- `ticket_acceptance_logs.accepted_by_user_pk -> users.id`
- `ticket_assignment_state.current_assigned_user_pk -> users.id`

---

## 3.3 user_roles
**Purpose**: link users to roles  
**Primary key**: `id`  
**Important columns**:
- `user_pk`
- `role_pk`
- `is_active`
- `created_at`

**Typical use**:
- resolve role membership

**Safe joins**:
- `user_pk -> users.id`
- `role_pk -> roles.id`

---

## 3.4 user_login_audit
**Purpose**: login attempt history  
**Primary key**: `id`  
**Important columns**:
- `user_pk`
- `login_at`
- `login_result`
- `failure_reason`
- `ip_address`
- `user_agent`

**Typical use**:
- admin login audit review

**Caution**:
- user agent and IP may be privacy-sensitive but are not secret
- expose only when appropriate for admins

---

## 3.5 user_account_locks
**Purpose**: account lock records  
**Primary key**: `id`  
**Important columns**:
- `user_pk`
- `locked_at`
- `lock_reason`
- `failed_login_count`
- `unlocked_at`
- `unlocked_by`
- `is_active`

**Typical use**:
- locked user management
- unlock audit

---

## 3.6 user_otp_requests
**Purpose**: OTP issuance records  
**Primary key**: `id`  
**Allowed columns for reporting/admin**:
- `user_pk`
- `sent_to_email`
- `requested_at`
- `expires_at`
- `verified_at`
- `status`
- `attempt_count`

**Sensitive columns — do not query**:
- `otp_code_hash`

**Typical use**:
- admin troubleshooting of OTP flow
- never reveal OTP values/hashes

---

## 3.7 password_reset_requests
**Purpose**: reset request tracking  
**Primary key**: `id`  
**Allowed columns**:
- `user_pk`
- `requested_at`
- `expires_at`
- `used_at`
- `status`

**Sensitive columns — do not query**:
- `token_hash`

---

## 3.8 teams
**Purpose**: main teams  
**Primary key**: `id`  
**Important columns**:
- `team_code`
- `team_name`
- `description`
- `is_active`

**Typical use**:
- resolve main teams
- join team-based records

---

## 3.9 sub_teams
**Purpose**: subteams within a main team  
**Primary key**: `id`  
**Important columns**:
- `team_pk`
- `sub_team_code`
- `sub_team_name`
- `description`
- `is_active`

**Typical use**:
- AWS / GCP and future subteam mapping

**Safe joins**:
- `team_pk -> teams.id`

---

## 3.10 team_members
**Purpose**: membership of users in teams/subteams  
**Primary key**: `id`  
**Important columns**:
- `user_pk`
- `team_pk`
- `sub_team_pk`
- `member_role`
- `is_primary`
- `is_active`
- `effective_from`
- `effective_to`

**Typical use**:
- find who belongs to a team/subteam
- determine primary membership

**Safe joins**:
- `user_pk -> users.id`
- `team_pk -> teams.id`
- `sub_team_pk -> sub_teams.id`

---

## 3.11 line_users
**Purpose**: LINE user directory and mapping to web users  
**Primary key**: `id`  
**Important columns**:
- `user_id`
- `display_name`
- `picture_url`
- `status_message`
- `language`
- `user_pk`
- `is_friend`
- `status`
- `last_seen_at`

**Typical use**:
- map LINE user to web user
- resolve mention targets
- read action source identity

---

## 3.12 line_chats
**Purpose**: LINE chat/group metadata  
**Primary key**: `id`  
**Important columns**:
- `chat_type`
- `chat_id`
- `group_name`
- `member_count`
- `bot_status`
- `bot_joined_at`
- `bot_left_at`
- `last_seen_at`

**Typical use**:
- current active group reference
- monitoring

---

## 3.13 line_chat_memberships
**Purpose**: members of LINE chats/groups  
**Primary key**: `id`  
**Important columns**:
- `chat_pk`
- `line_user_pk`
- `status`
- `joined_at`
- `left_at`
- `last_seen_at`

**Typical use**:
- group membership inspection
- monitor if a user appears in tracked chat

---

## 3.14 line_event_logs
**Purpose**: raw webhook events from LINE  
**Primary key**: `id`  
**Important columns**:
- `event_type`
- `chat_type`
- `chat_id`
- `line_user_id`
- `event_timestamp`
- `raw_json`
- `created_at`

**Typical use**:
- webhook troubleshooting
- debugging action flows

**Caution**:
- `raw_json` may contain verbose payloads; expose carefully

---

## 3.15 line_processed_events
**Purpose**: dedupe of processed webhook events  
**Primary key**: `webhook_event_id`  
**Important columns**:
- `event_type`
- `processed_at`

**Typical use**:
- avoid duplicate event handling

---

## 3.16 line_message_logs
**Purpose**: outbound LINE message history  
**Primary key**: `id`  
**Important columns**:
- `ticket_pk`
- `chat_pk`
- `target_line_user_pk`
- `message_type`
- `message_payload_json`
- `sent_at`
- `delivery_status`
- `created_at`

**Restricted/technical column**:
- `reply_token` should not be exposed to normal users

**Typical use**:
- was a ticket sent?
- what type of message was sent?
- when was it sent?
- delivery status

---

## 3.17 line_action_logs
**Purpose**: user actions coming from LINE  
**Primary key**: `id`  
**Important columns**:
- `ticket_pk`
- `line_user_pk`
- `action_type`
- `action_value`
- `action_at`
- `raw_json`
- `created_at`

**Typical use**:
- acceptance button/activity history

---

## 3.18 standby_calendars
**Purpose**: standby calendar definitions  
**Primary key**: `id`  
**Important columns**:
- `team_pk`
- `sub_team_pk`
- `calendar_name`
- `description`
- `is_active`
- `created_by`

**Typical use**:
- find calendar for team/subteam

---

## 3.19 standby_shift_rules
**Purpose**: shift timing rules for a calendar  
**Primary key**: `id`  
**Important columns**:
- `calendar_pk`
- `rule_name`
- `shift_start_time`
- `shift_end_time`
- `timezone_name`
- `effective_from`
- `effective_to`
- `is_active`

**Typical use**:
- define daily/weekly/split shifts

---

## 3.20 standby_slots
**Purpose**: actual dated standby assignments  
**Primary key**: `id`  
**Important columns**:
- `calendar_pk`
- `slot_date`
- `shift_rule_pk`
- `tier_level`
- `user_pk`
- `start_datetime`
- `end_datetime`
- `slot_status`

**Typical use**:
- current standby lookup
- historical standby lookup
- who is tier 1/2/3 now?

**Safe joins**:
- `calendar_pk -> standby_calendars.id`
- `shift_rule_pk -> standby_shift_rules.id`
- `user_pk -> users.id`

---

## 3.21 standby_slot_change_logs
**Purpose**: slot edit/change history  
**Primary key**: `id`  
**Important columns**:
- `standby_slot_pk`
- `old_user_pk`
- `new_user_pk`
- `old_tier_level`
- `new_tier_level`
- `change_reason`
- `changed_by`
- `changed_at`

**Typical use**:
- who changed standby assignment

---

## 3.22 standby_replacement_logs
**Purpose**: replacement records when someone substitutes  
**Primary key**: `id`  
**Important columns**:
- `original_slot_pk`
- `original_user_pk`
- `replacement_user_pk`
- `replacement_reason`
- `created_by`
- `created_at`

**Typical use**:
- replacement audit

---

## 3.23 user_leave_requests
**Purpose**: leave records affecting standby eligibility  
**Primary key**: `id`  
**Important columns**:
- `user_pk`
- `leave_type`
- `start_datetime`
- `end_datetime`
- `reason`
- `created_by`
- `approved_by`
- `status`

**Important business note**:
- current project intent says no approval workflow in phase 1
- schema still contains `approved_by` and `status`, so treat them carefully

**Typical use**:
- skip unavailable standby due to leave

---

## 3.24 user_availability_status
**Purpose**: temporary availability/unavailability  
**Primary key**: `id`  
**Important columns**:
- `user_pk`
- `availability_status`
- `start_datetime`
- `end_datetime`
- `note`
- `created_by`
- `created_at`

**Typical use**:
- standby resolution skip logic

---

## 3.25 email_ticket_audit_raw
**Purpose**: raw parsed email audit record  
**Primary key**: `record_id`  
**Important columns**:
- `parent_id`
- `message_id`
- `email_date`
- `subject_raw`
- `body_raw`
- parsed short description fields
- parsed description/environment fields
- requested/opened/business info
- `ip_list_json`
- `url_list_json`

**Typical use**:
- raw ingestion audit
- parsing troubleshooting

**Caution**:
- do not use raw body by default for general user answers unless necessary

---

## 3.26 email_ticket_master
**Purpose**: cleaned/master email feature record  
**Primary key**: `record_id`  
**Important columns**:
- `parent_id`
- `message_id`
- `email_date`
- `from_address`
- `to_address`
- `ticket_type`
- `request_number`
- `ritm_no`
- `inc_no`
- `itask_no`
- `ctask_no`
- `subject_clean`
- `short_desc_clean`
- `description_clean`
- `description_for_model`
- `body_for_model`
- `opened_by`
- `requested_for`
- `raised_by`
- `business_service`
- `service_offering`
- `priority`
- `urgency`
- `impact`
- `contact_email`
- `ip_list_json`
- `url_list_json`
- feature flags such as `has_aws_ip`, `has_gcp_ip`, etc.
- `assigned_group_from_to`
- `route_scope`
- `sibling_task_count`
- `sibling_known_sub_team`
- `cross_task_inference_used`
- `label_main_team`
- `label_sub_team`
- `label_source`
- `text_input`
- `ml_confidence`
- `decision_mode`

**Typical use**:
- route/classification diagnostics
- training dataset source
- ingestion view

---

## 3.27 tickets
**Purpose**: main operational ticket table  
**Primary key**: `id`  
**Business key**: `record_id` unique  
**Important columns**:
- `record_id`
- `parent_id`
- `source_type`
- `ticket_type`
- `request_number`
- `ritm_no`
- `inc_no`
- `itask_no`
- `ctask_no`
- `subject`
- `short_description`
- `description`
- `current_status`
- `priority`
- `urgency`
- `impact`
- `email_date`
- `created_at`
- `updated_at`

**Typical use**:
- primary starting point for ticket questions

---

## 3.28 ticket_classification_results
**Purpose**: classification outcome for a ticket  
**Primary key**: `id`  
**Important columns**:
- `ticket_pk`
- `predicted_team_pk`
- `predicted_sub_team_pk`
- `label_source`
- `ml_confidence`
- `decision_mode`
- `text_input`
- `model_version`
- `created_at`

**Typical use**:
- which team/subteam was chosen
- confidence and decision mode

---

## 3.29 ticket_contacts
**Purpose**: normalized contacts associated with ticket  
**Primary key**: `id`  
**Important columns**:
- `ticket_pk`
- `contact_type`
- `contact_name`
- `contact_email`

**Typical use**:
- opened by / requested for / contact references

---

## 3.30 ticket_artifacts
**Purpose**: normalized artifacts such as IPs/URLs  
**Primary key**: `id`  
**Important columns**:
- `ticket_pk`
- `artifact_type`
- `artifact_value`
- `source_field`

**Typical use**:
- list artifacts extracted from ticket

---

## 3.31 escalation_rules
**Purpose**: escalation timing/rule configuration  
**Primary key**: `id`  
**Important columns**:
- `team_pk`
- `sub_team_pk`
- `rule_name`
- `tier_level`
- `wait_minutes`
- `retry_count`
- `skip_if_leave`
- `skip_if_unavailable`
- `escalate_to_next_tier`
- `notify_admin_if_unassigned`
- `is_active`
- `effective_from`
- `effective_to`

**Typical use**:
- config inspection
- not usually needed for ordinary users

---

## 3.32 ticket_routing_logs
**Purpose**: routing event history by round  
**Primary key**: `id`  
**Important columns**:
- `ticket_pk`
- `route_round`
- `routed_team_pk`
- `routed_sub_team_pk`
- `route_scope`
- `routing_source`
- `created_at`

**Typical use**:
- how was this ticket routed?

---

## 3.33 ticket_notifications
**Purpose**: notification history for each round/target  
**Primary key**: `id`  
**Important columns**:
- `ticket_pk`
- `route_round`
- `notify_channel`
- `target_user_pk`
- `target_line_user_pk`
- `target_tier`
- `sent_at`
- `delivery_status`
- `response_deadline_at`
- `created_at`

**Typical use**:
- when was notification sent?
- which tier/user was targeted?
- what deadline applied?

---

## 3.34 ticket_acceptance_logs
**Purpose**: acceptance actions  
**Primary key**: `id`  
**Important columns**:
- `ticket_pk`
- `notification_pk`
- `accepted_by_user_pk`
- `accepted_at`
- `accepted_tier`
- `response_minutes`
- `acceptance_status`
- `note`
- `created_at`

**Typical use**:
- who accepted?
- when?
- from which tier?
- how many minutes after notification?

---

## 3.35 ticket_escalation_logs
**Purpose**: escalation transitions  
**Primary key**: `id`  
**Important columns**:
- `ticket_pk`
- `from_tier`
- `to_tier`
- `escalation_reason`
- `started_at`
- `escalated_at`
- `elapsed_minutes`
- `created_at`

**Typical use**:
- did this ticket escalate?
- from which tier to which tier?

---

## 3.36 ticket_assignment_state
**Purpose**: latest assignment snapshot for each ticket  
**Primary key**: `ticket_pk`  
**Important columns**:
- `current_team_pk`
- `current_sub_team_pk`
- `current_tier`
- `current_assigned_user_pk`
- `assignment_status`
- `last_notified_at`
- `accepted_at`
- `updated_at`

**Typical use**:
- current owner/status
- latest assignment view

---

## 3.37 data_mapping_queue
**Purpose**: unresolved mapping/data-quality queue  
**Primary key**: `id`  
**Important columns**:
- `queue_type`
- `source_table`
- `source_pk`
- `issue_code`
- `issue_detail`
- `detected_at`
- `status`
- `assigned_to`
- `resolved_at`
- `resolved_by`
- `resolution_note`

**Typical use**:
- admin review of unresolved mappings/issues

---

## 3.38 manual_override_logs
**Purpose**: manual override history  
**Primary key**: `id`  
**Important columns**:
- `ticket_pk`
- `override_type`
- `old_value`
- `new_value`
- `reason`
- `overridden_by`
- `overridden_at`

**Typical use**:
- who manually changed a routing/assignment-related value?

---

## 3.39 ai_chat_sessions
**Purpose**: AI chat sessions  
**Primary key**: `id`  
**Important columns**:
- `user_pk`
- `session_uuid`
- `session_status`
- `started_at`
- `ended_at`
- `closed_by_user`
- `visible_in_ui`

**Typical use**:
- session tracking
- UI-visible vs hidden session behavior

---

## 3.40 ai_chat_messages
**Purpose**: AI chat messages per session  
**Primary key**: `id`  
**Important columns**:
- `session_pk`
- `message_role`
- `message_text`
- `message_order`
- `created_at`

**Typical use**:
- conversation history
- chat transcript retrieval if allowed

---

## 3.41 ai_chat_message_metadata
**Purpose**: metadata for AI responses/messages  
**Primary key**: `id`  
**Important columns**:
- `message_pk`
- `source_type`
- `source_ref`
- `confidence_score`
- `token_count`
- `response_time_ms`
- `created_at`

**Typical use**:
- AI performance/metadata monitoring

---

## 3.42 ai_chat_feedback
**Purpose**: user feedback on AI messages  
**Primary key**: `id`  
**Important columns**:
- `message_pk`
- `user_pk`
- `feedback_type`
- `feedback_note`
- `created_at`

**Typical use**:
- assistant quality feedback

---

## 3.43 ai_chat_audit_logs
**Purpose**: AI audit trail  
**Primary key**: `id`  
**Important columns**:
- `session_pk`
- `user_pk`
- `prompt_text`
- `response_text`
- `access_scope`
- `blocked_reason`
- `created_at`

**Typical use**:
- audit AI access/behavior
- admin review only

**Caution**:
- contains potentially sensitive user prompts and AI responses

---

## 3.44 audit_logs
**Purpose**: generic audit log  
**Primary key**: `id`  
**Important columns**:
- `actor_user_pk`
- `action_type`
- `entity_type`
- `entity_pk`
- `old_value_json`
- `new_value_json`
- `action_at`
- `ip_address`

**Typical use**:
- system audit review
- admin/super-admin tooling

---

## 3.45 ticket_sla_metrics
**Purpose**: per-ticket SLA metrics  
**Primary key**: `id`  
**Unique**: `ticket_pk`  
**Important columns**:
- `ticket_pk`
- `first_notified_at`
- `first_accepted_at`
- `total_response_minutes`
- `first_tier_response_minutes`
- `total_escalation_count`
- `accepted_tier`
- `had_timeout_before_accept`
- `no_acceptance_flag`
- `calculated_at`

**Typical use**:
- did ticket miss SLA?
- response timing
- escalation counts

---

## 3.46 daily_team_metrics
**Purpose**: daily aggregated metrics by team/subteam  
**Primary key**: `id`  
**Important columns**:
- `metric_date`
- `team_pk`
- `sub_team_pk`
- `total_tickets`
- `accepted_tickets`
- `escalated_tickets`
- `avg_response_minutes`
- `no_acceptance_tickets`
- `created_at`

**Typical use**:
- daily summary
- SLA/report pages

---

# 4) Recommended Join Paths

## 4.1 Ticket summary with classification and assignment
- `tickets t`
- left join `ticket_classification_results tcr on tcr.ticket_pk = t.id`
- left join `teams tm on tm.id = tcr.predicted_team_pk`
- left join `sub_teams stm on stm.id = tcr.predicted_sub_team_pk`
- left join `ticket_assignment_state tas on tas.ticket_pk = t.id`
- left join `users u on u.id = tas.current_assigned_user_pk`

Use for:
- ticket detail
- current route
- current owner

---

## 4.2 Ticket acceptance trail
- `tickets t`
- join `ticket_acceptance_logs tal on tal.ticket_pk = t.id`
- left join `users u on u.id = tal.accepted_by_user_pk`
- left join `ticket_notifications tn on tn.id = tal.notification_pk`

Use for:
- who accepted and when

---

## 4.3 Ticket notification trail
- `tickets t`
- join `ticket_notifications tn on tn.ticket_pk = t.id`
- left join `users u on u.id = tn.target_user_pk`
- left join `line_users lu on lu.id = tn.target_line_user_pk`

Use for:
- who was notified
- when and at which tier

---

## 4.4 Current standby
- `standby_slots ss`
- join `standby_calendars sc on sc.id = ss.calendar_pk`
- left join `teams t on t.id = sc.team_pk`
- left join `sub_teams st on st.id = sc.sub_team_pk`
- join `users u on u.id = ss.user_pk`
- optional left join leave/availability tables for filtering

Use for:
- current standby per team/subteam/tier

---

## 4.5 Team membership
- `team_members tm`
- join `users u on u.id = tm.user_pk`
- join `teams t on t.id = tm.team_pk`
- left join `sub_teams st on st.id = tm.sub_team_pk`

Use for:
- list members by team/subteam

---

## 4.6 SLA reporting
- `ticket_sla_metrics sm`
- join `tickets t on t.id = sm.ticket_pk`
- left join `ticket_assignment_state tas on tas.ticket_pk = t.id`
- left join `teams tm on tm.id = tas.current_team_pk`
- left join `sub_teams stm on stm.id = tas.current_sub_team_pk`

Or use:
- `daily_team_metrics dtm`
- join `teams tm`
- left join `sub_teams stm`

Use for:
- SLA by team/subteam

---

# 5) Recommended Query Starting Tables

Use these defaults:

- Ticket-specific question → start from `tickets`
- Acceptance question → start from `ticket_acceptance_logs`
- Current assignment question → start from `ticket_assignment_state`
- Notification question → start from `ticket_notifications`
- Standby question → start from `standby_slots`
- Team membership question → start from `team_members`
- Daily report question → start from `daily_team_metrics`
- Raw parsing/audit question → start from `email_ticket_master` or `email_ticket_audit_raw`
- AI session question → start from `ai_chat_sessions`
- Generic admin audit question → start from `audit_logs`

---

# 6) Normalized Identifiers to Look For in User Questions

Common ticket identifiers:
- `record_id`
- `request_number`
- `ritm_no`
- `inc_no`
- `itask_no`
- `ctask_no`
- `parent_id`

If the user says:
- “RITM12345” → likely `ritm_no`
- “INC0001” → likely `inc_no`
- “task” → may be `itask_no` or `ctask_no`
- “request number” → likely `request_number`

---

# 7) Query Safety Notes

1. Prefer operational user-facing tables first:
   - `tickets`
   - `ticket_assignment_state`
   - `ticket_classification_results`
   - `ticket_notifications`
   - `ticket_acceptance_logs`
   - `ticket_sla_metrics`

2. Use raw/audit tables only when the user explicitly asks for parsing/raw details

3. Do not reveal secret/sensitive fields even if physically present

4. Treat auth-related and AI-audit-related tables as more restricted

---

# 8) Fields Most Likely to Be Useful in User-Facing Answers

Common safe fields:
- user name fields
- email
- team/subteam names
- ticket identifiers
- current status
- priority/urgency/impact
- accepted_at
- sent_at
- response_minutes
- escalation counts
- daily aggregated counts

---

# 9) Fields That Commonly Need Admin Caution

These are not always forbidden, but should be used carefully:
- `ip_address`
- `user_agent`
- `raw_json`
- `message_payload_json`
- `prompt_text`
- `response_text`
- `old_value_json`
- `new_value_json`
- `reply_token`

See `sensitive_data_guardrails.md` for final policy.

---

# 10) Minimum Good Practice for AI SQL Generation

Before generating SQL:
1. identify the business entity
2. choose the right starting table
3. confirm identifier field
4. include only needed columns
5. avoid forbidden columns
6. add `limit` when appropriate
7. use permission scoping if provided
