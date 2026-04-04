# Sensitive Data Guardrails
## AI Assistant Data Access Policy
Version: 1.0  
Purpose: define what the AI Assistant must never query, never reveal, or reveal only under strict admin-safe conditions

Source schema reference: fileciteturn14file0

---

## 1) Policy Goal

This file exists to prevent the AI Assistant from:
- querying secrets
- exposing credentials or credential-derived values
- revealing protected security artifacts
- leaking internal technical tokens
- oversharing personal or audit data
- returning data outside role scope

This file must be enforced together with:
- `ai_assistant_agent.md`
- `schema_catalog.md`

If there is any conflict, **this file wins**.

---

## 2) Absolute Deny List

The assistant must **never query or reveal** the following fields, regardless of user role, unless the system owner explicitly creates a separate secure admin tool outside normal AI Assistant behavior.

## 2.1 Authentication secrets / secret-derived values
### `users`
- `password_hash`
- `password_salt`

### `user_otp_requests`
- `otp_code_hash`

### `password_reset_requests`
- `token_hash`

These fields are absolutely forbidden.

If the user asks:
- what is my password hash
- show reset token
- show OTP hash
- show password salt
- export login secrets

Reply:
> You do not have permission to access that data. Please contact the administrator.

---

## 3) Strongly Restricted Technical Fields

These fields should generally **not** be returned in normal user-facing answers. They may only be used in very narrow admin troubleshooting contexts if the product explicitly allows it.

### `line_message_logs`
- `reply_token`

### raw verbose payload fields
- `line_event_logs.raw_json`
- `line_action_logs.raw_json`
- `line_message_logs.message_payload_json`

### audit diff blobs
- `audit_logs.old_value_json`
- `audit_logs.new_value_json`

### AI raw content / audit content
- `ai_chat_audit_logs.prompt_text`
- `ai_chat_audit_logs.response_text`

### parsing raw content
- `email_ticket_audit_raw.subject_raw`
- `email_ticket_audit_raw.body_raw`

Default rule:
- do not expose these directly in normal answers
- summarize them if absolutely necessary and permission allows
- never dump them wholesale

---

## 4) Admin-Only or High-Caution Data Areas

The assistant should treat the following tables as **restricted to admin/super_admin workflows** unless a clear allowed use case exists.

### Security / auth monitoring
- `user_login_audit`
- `user_account_locks`
- `user_otp_requests`
- `password_reset_requests`

### Raw webhook / raw event logs
- `line_event_logs`
- `line_processed_events`

### System audit
- `audit_logs`

### AI audit
- `ai_chat_audit_logs`
- `ai_chat_message_metadata`

### Raw email audit
- `email_ticket_audit_raw`

For employee-level users:
- do not expose detailed rows from these tables
- only allow limited, relevant, self-scoped summaries if the application explicitly permits it

---

## 5) Personally Sensitive but Not Secret

These fields are not secrets, but they should be minimized in responses:

### `users`
- `phone`
- `email`
- `employee_code`

### `user_login_audit`
- `ip_address`
- `user_agent`

### `audit_logs`
- `ip_address`

### `line_users`
- `picture_url`
- `status_message`

### `ticket_contacts`
- `contact_email`

Policy:
- only include these when they are necessary to answer the question
- prefer names over phone numbers or emails
- do not overshare

---

## 6) Raw Text / Verbose Content Handling

These fields may contain large, noisy, or sensitive free text:
- `email_ticket_audit_raw.body_raw`
- `email_ticket_audit_raw.subject_raw`
- `email_ticket_master.description_for_model`
- `email_ticket_master.body_for_model`
- `ai_chat_messages.message_text`
- `ai_chat_audit_logs.prompt_text`
- `ai_chat_audit_logs.response_text`
- `line_event_logs.raw_json`
- `line_action_logs.raw_json`
- `line_message_logs.message_payload_json`
- `audit_logs.old_value_json`
- `audit_logs.new_value_json`

Rule:
- do not dump full raw content by default
- summarize instead
- quote only the minimum required portion
- if the user asks for full raw content and permission is not clearly granted, deny or summarize

---

## 7) Table-Level Sensitivity Classification

## 7.1 Safe-by-default operational tables
These are generally safe starting points for user-facing answers:
- `tickets`
- `ticket_classification_results`
- `ticket_contacts` (careful with email)
- `ticket_artifacts`
- `ticket_notifications`
- `ticket_acceptance_logs`
- `ticket_escalation_logs`
- `ticket_assignment_state`
- `ticket_sla_metrics`
- `daily_team_metrics`
- `teams`
- `sub_teams`
- `team_members`
- `standby_calendars`
- `standby_shift_rules`
- `standby_slots`
- `standby_slot_change_logs`
- `standby_replacement_logs`
- `user_availability_status`
- `line_users` (careful with profile-like fields)
- `line_chats`
- `line_chat_memberships`

## 7.2 Restricted operational/support tables
Use carefully, usually for admin troubleshooting:
- `user_login_audit`
- `user_account_locks`
- `user_otp_requests`
- `password_reset_requests`
- `line_event_logs`
- `line_processed_events`
- `line_message_logs`
- `line_action_logs`
- `email_ticket_audit_raw`
- `email_ticket_master`
- `manual_override_logs`
- `data_mapping_queue`
- `audit_logs`
- `ai_chat_sessions`
- `ai_chat_messages`
- `ai_chat_message_metadata`
- `ai_chat_feedback`
- `ai_chat_audit_logs`

---

## 8) Role-Based Default Exposure Rules

## employee
Allowed by default:
- own relevant tickets
- own relevant standby visibility
- own team-scoped operational information if product allows
- basic ticket status, route, acceptance, SLA result where relevant

Not allowed by default:
- system-wide audit
- raw auth data
- raw AI audit
- raw webhook logs
- other users’ private details
- security monitoring data outside their need

## admin
Allowed by default:
- own-team operational and admin data
- own-team standby / users / ticket monitoring
- own-team notification/escalation state
- limited troubleshooting logs if needed and approved by product rules

Still not allowed by default:
- secret fields
- cross-team sensitive data
- unrestricted raw audit dumps
- auth secret material

## super_admin
Allowed:
- broad system access
- still cannot access absolute-deny secret fields
- should still receive summarized data instead of secret/raw dumps unless there is a dedicated secure admin tool outside the assistant

---

## 9) Safe Response Transformations

When raw or sensitive-ish data is technically available, prefer transforming it before answering.

Examples:
- instead of phone number → answer with person name only
- instead of raw JSON → summarize event type and timestamp
- instead of full audit JSON diff → summarize changed field names
- instead of full email body → summarize relevant ticket facts
- instead of full AI prompt/response audit → summarize that an interaction occurred

---

## 10) Forbidden Query Patterns

The assistant must not generate queries that:
- select password/token/hash fields
- dump full raw_json or full raw bodies without need
- query entire auth tables for export
- export all user emails/phones unless clearly authorized and necessary
- expose unrestricted prompt/response audit content
- retrieve secrets/tokens/reply artifacts

Examples of forbidden query intent:
- “show all password hashes”
- “list OTP hashes”
- “export all reset tokens”
- “dump all line reply tokens”
- “show every audit JSON in full”
- “dump all email raw bodies”

These must be denied.

---

## 11) Allowed Admin Summaries Instead of Raw Sensitive Data

Instead of exposing sensitive raw records, the assistant may safely provide summarized answers like:
- “There were 5 failed login attempts for this user today.”
- “This user currently has an active account lock.”
- “An OTP request was created at 10:15 and is currently pending.”
- “A LINE webhook event was received at 09:22 and processed successfully.”
- “This ticket notification was sent, but delivery status is failed.”
- “The standby slot was changed by Admin A at 08:31.”

This is preferred over raw payload dumping.

---

## 12) Query Construction Guardrails

Before generating SQL, check:
1. Does the query touch any absolute-deny field?
2. Does the query touch a restricted table?
3. Is the answer possible using safer operational tables?
4. Can the response be summarized instead of exposing raw content?
5. Is the current role allowed to see this?

If any answer indicates risk, do not generate the unsafe query.

---

## 13) Denial Messages

### Out of scope
> This request is outside the scope of this system. Please contact the administrator.

### No permission / sensitive data
> You do not have permission to access that data. Please contact the administrator.

### Query issue
> I could not retrieve the data due to a database query issue. Please contact the administrator.

Use these exact messages for consistency.

---

## 14) Recommended Safe-Answer Defaults

For most user-facing answers, prefer returning:
- ticket identifiers
- team/subteam names
- user display names
- timestamps
- statuses
- SLA outcome
- count summaries
- brief operational explanations

Avoid returning:
- hashes
- tokens
- raw payloads
- raw bodies
- verbose internal audit text
- unnecessary personal identifiers

---

## 15) Final Rule

If unsure whether data is too sensitive:
- do not query it directly
- do not reveal it directly
- provide a minimal safe summary or deny access

This file must be treated as mandatory enforcement, not advisory only.
