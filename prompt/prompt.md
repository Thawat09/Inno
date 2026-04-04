You are a Principal Solution Architect, Principal Full-Stack Engineer, Senior Backend Engineer, Senior Frontend Engineer, Senior Database Architect, Senior ML Engineer, Senior DevOps Engineer, and Senior Product System Designer.

Your task is to design and help build a production-ready internal system called:

Ticket Routing & Standby Notification Platform

This system is business-critical. The design must be extremely detailed, practical, production-oriented, and complete. Do not skip any important detail. Do not answer only at a high level. Do not leave architecture, schema, flow, edge cases, or operational behavior ambiguous.

You must propose a concrete default design for every important area, not just generic options.

If some parts are intentionally deferred for a later phase, clearly mark them as:
- Phase 1: must build now
- Phase 2: prepare structure now, fully implement later

The goal is to produce a complete system design and implementation blueprint that can be used to build the system correctly without missing critical requirements.

==================================================
1. PROJECT OVERVIEW
==================================================

Build an internal platform that:

1. Reads incoming ticket emails from a single Service Desk mailbox
2. Parses and extracts ticket-related information from email text
3. Determines the Main Team using only the email to_address
4. If the Main Team is Cloud Support, classifies the Cloud Subteam as either:
   - AWS Team
   - GCP Team
5. Uses ML only for Cloud Subteam classification
6. Falls back to logic/rule-based classification if:
   - model confidence is below threshold
   - model fails
   - model is unavailable
7. Stores all important data into PostgreSQL
8. Resolves standby/on-duty assignee(s) based on team, tier, calendar, leave, and availability
9. Sends ticket notifications into LINE group
10. Mentions the responsible standby person
11. Allows the user to accept the ticket through LINE flex message
12. Assigns the ticket owner to the person who accepts it
13. Escalates to the next tier if nobody accepts within SLA
14. Supports up to 3 notification rounds total
15. Stops further escalation after the last tier / last round
16. Exposes ticket, team, standby, SLA, logs, and admin data via web UI
17. Uses Express.js for the web/API backend
18. Uses Python services/workers for AI-related logic and LINE-related worker processes
19. Deploys using Docker on Ubuntu VM
20. Must be practical for real production use, not just a prototype

==================================================
2. CONFIRMED SYSTEM BOUNDARIES
==================================================

Use the following as hard requirements:

Backend for web/API:
- Node.js
- Express.js
- JavaScript
- Sequelize ORM
- JWT authentication
- PostgreSQL

Frontend:
- Vue 3
- JavaScript only
- No TypeScript
- Vue Router
- PrimeVue
- English language UI
- Existing frontend already has mock data in many pages, but some pages still need correction/improvement

Python side:
- Python is used for:
  - AI/model-related processing
  - mailbox polling / worker processes
  - LINE-related worker orchestration
- Python worker is valid and intentional
- Python worker should not be replaced by Express for those functions

Database:
- PostgreSQL
- Must separate raw/audit data from operational data

Deployment:
- Docker
- Docker images run on Ubuntu VM
- At least 2 environments:
  - dev
  - prod

Source of tickets:
- Email only
- Single mailbox only
- Mailbox belongs to Service Desk and receives all teams’ tickets
- Email is text-only
- No attachment storage required

==================================================
3. HIGH-LEVEL BUSINESS FLOW
==================================================

Design the system with the following end-to-end flow:

Step 1: Read Email
- Poll one Service Desk mailbox regularly
- Read new incoming emails
- Avoid duplicate processing

Step 2: Parse Email
- Extract ticket-related fields from subject/body
- Normalize and clean text
- Store raw email for audit
- Store parsed/master representation for downstream classification and analytics

Step 3: Determine Main Team
- Main Team is derived only from to_address
- Main Team does NOT use ML in Phase 1
- Main Team values:
  - iNET Network Team
  - iNET Operation Team
  - iNET Cloud Support Team

Step 4: Determine Cloud Subteam
- Only if Main Team = iNET Cloud Support Team
- Classify as:
  - AWS Team
  - GCP Team
- Use ML model for classification
- Use fallback logic/rules if confidence < threshold or model unavailable/error
- Threshold must be configurable
- Current production threshold = 0.85

Step 5: Save Classification and Ticket
- Store all route decisions and classification metadata
- Store operational ticket record for frontend usage
- Track source of decision:
  - main team by to_address
  - subteam by explicit logic / ML / fallback logic

Step 6: Resolve Standby
- Find the responsible standby person based on:
  - team / subteam
  - current active tier
  - calendar rules
  - leave / unavailable status
- Each tier contains exactly 1 person
- Each team has 2 or 3 tiers
- If current tier user is unavailable, skip to next valid tier
- Leave and unavailable are daily-based
- No approval process for leave/unavailable

Step 7: Send LINE Notification
- Use exactly one LINE group
- System stores group ID mainly to support future group replacement/migration
- Send ticket notification into LINE group
- Mention/tag the resolved responsible standby person
- If team/subteam resolution is unclear or assignee cannot be found, fallback behavior must mention:
  - one AWS standby
  - one GCP standby
- Notification uses LINE flex message
- Flex message includes accept action button

Step 8: Accept Ticket
- When a user accepts via LINE, response format is effectively:
  - “รับทราบ | task | ritm”
- The person who accepts becomes the ticket owner immediately
- The owner does not need to be the originally tagged person
- Acceptance time must be stored

Step 9: SLA and Escalation
- SLA is based on acceptance after LINE notification
- SLA rule:
  - after sending notification, someone must accept within 15 minutes
- If not accepted within 15 minutes:
  - escalate to next tier
  - send next notification round
- Maximum notification rounds per ticket = 3
- If final round or final tier is reached and still no acceptance:
  - stop sending
  - mark SLA miss / missed acceptance state for reporting and web display
- No further automatic action required after last round

Step 10: Reporting and Summary
- Provide reports:
  - SLA by Team
  - SLA by Subteam
- Export reports as CSV only
- Send daily summary to LINE group at 17:30
- Daily summary does not mention anyone
- Daily summary includes at least:
  - ticket count
  - accepted count
  - missed SLA count
  - grouped by team

==================================================
4. PHASE STRUCTURE
==================================================

Phase 1 (must implement now):
- Email polling
- Email parsing
- Main team routing by to_address
- Cloud subteam classification with ML + fallback logic
- PostgreSQL persistence
- Standby resolution
- LINE notification first-round structure
- Ticket acceptance via LINE
- SLA timing basis
- Escalation-ready structure
- Web UI pages and API connectivity
- JWT auth
- Role-based access control
- Audit logging
- Reporting basics
- Daily summary job
- Privacy/compliance-ready architecture
- Flexible standby scheduling structure

Phase 2 (prepare now, fully implement later):
- Full escalation engine logic if temporarily placeholder in dev
- Full LINE retry implementation if temporarily placeholder in dev
- Deeper AI assistant features
- Expanded keyword/url/domain mapping for future services
- More advanced masking/privacy enforcement rules
- More advanced analytics/retraining dashboard

Important:
Even if some Phase 2 parts are intentionally not fully activated now, the architecture and schema must support them from the beginning.

==================================================
5. ARCHITECTURE STYLE
==================================================

Design the system with clear separation of responsibilities:

A. Express.js Web/API Backend
Responsible for:
- authentication
- authorization
- REST APIs for frontend
- CRUD for users, teams, standby, leave, tickets, logs, reports
- querying PostgreSQL
- enforcing permissions
- service layer APIs that AI assistant may call

B. Python Worker / AI / LINE Services
Responsible for:
- polling mailbox
- parsing email
- running ML classification logic
- calling internal service layer endpoints or repositories where appropriate
- sending LINE messages
- processing LINE response callbacks/events
- running scheduled worker jobs
- handling daily summary sending
- preparing escalation structure

C. PostgreSQL
Responsible for:
- operational storage
- audit storage
- routing/classification history
- standby schedules
- acceptance/escalation logs
- mappings
- AI audit
- line logs
- retention-aware cleanup for selected logs

D. Frontend (Vue 3)
Responsible for:
- presenting operational data
- management pages
- monitoring pages
- admin tools
- reporting UI
- AI assistant UI
- monthly standby calendar UI
- consuming Express APIs only

==================================================
6. REQUIRED FRONTEND PAGES
==================================================

The frontend must include at least the following pages:

Auth Pages:
1. LoginPage
2. SetPasswordPage
3. OtpPage
4. ResetPasswordPage

Application Pages:
5. Dashboard
6. ChangePasswordPage
7. TicketsPage
8. TicketDetailPage
9. AcceptanceMonitorPage
10. ManualOverridePage
11. StandbyCalendarPage
12. CalendarManagementPage
13. LeaveAvailabilityPage
14. EscalationRulePage
15. TeamsMembersPage
16. MyProfilePage
17. UserManagementPage
18. LockedUsersPage
19. NotificationsPage
20. LineMonitoringPage
21. ReportsSlaPage
22. AuditLogPage
23. AIAuditPage
24. AIAssistantPage
25. DataMappingPage
26. GlobalSearchPage

Frontend rules:
- All UI language must be English
- Standby calendar page must be a real monthly calendar UI
- Existing mock data may remain in dev, but page behavior must be designed for real API use
- Every page must include:
  - loading state
  - empty state
  - error state
  - filtering where appropriate
  - pagination where appropriate
  - responsive behavior
- TicketDetailPage must act as the central case detail view
- AcceptanceMonitorPage must show unaccepted tickets and escalation-relevant state clearly

==================================================
7. DATA MAPPING PAGE REQUIREMENTS
==================================================

The DataMapping page must support at least:

1. LINE user ↔ web user mapping
2. web user ↔ team / subteam mapping
3. keyword / URL / domain / pattern ↔ team or subteam mapping

The mapping page is important for future-proofing cases such as:
- if Azure-related content needs to be routed under AWS Team in the future
- if certain URLs/domains repeatedly imply a team
- if future misrouted patterns need manual mapping support

Even if some mappings are not fully used in Phase 1 runtime, the structure must be designed now.

==================================================
8. GLOBAL SEARCH REQUIREMENTS
==================================================

Global Search must support searching only these types:
- ticket
- task
- RITM
- INC
- email
- user
- line

Do not design an overly deep or overly broad search system beyond this scope in Phase 1.

==================================================
9. AUTHENTICATION AND SECURITY
==================================================

Use:
- JWT for auth
- local authentication only
- OTP via email
- no SSO in Phase 1

Must support:
- login
- logout
- set password
- forgot password
- reset password
- change password
- OTP verification
- account lock after repeated failed logins
- login audit trail

Security requirements:
- password hashing
- secure JWT handling
- token expiry strategy
- login rate limiting
- account lock logic
- env-based secret management
- DB credential protection
- LINE token protection
- service-to-service secret protection
- audit for sensitive admin actions

Privacy/compliance requirement:
- implement the architecture in a privacy/compliance-ready way now
- even if full policy enforcement is not activated yet
- prepare for future:
  - data masking
  - field-level access restriction
  - role-based data visibility tightening
  - audit of sensitive data access

==================================================
10. ROLE-BASED ACCESS CONTROL
==================================================

Roles:
- employee
- admin
- super_admin

Rules:
- employee:
  - can view only relevant ticket/team data
  - can see their own relevant standby/ticket data
  - can accept tickets
  - can use allowed assistant/search/profile features
- admin:
  - can manage their own team only
  - can modify calendar/standby/team members for their own team
  - cannot manage other teams
- super_admin:
  - can manage all teams and all system-wide settings

You must design:
- page permissions
- action permissions
- data scoping
- admin-only actions
- super-admin-only actions

==================================================
11. DATABASE DESIGN REQUIREMENTS
==================================================

Database must be PostgreSQL and must separate raw/audit data from operational data.

Use UUID primary keys by default unless there is a very strong reason otherwise.

At minimum, design the following tables or equivalent structures:

Identity / Security:
- roles
- users
- user_roles
- user_login_audit
- user_account_locks
- user_otp_requests
- password_reset_requests

Team / Membership:
- teams
- sub_teams
- team_members

LINE:
- line_users
- line_chats
- line_chat_memberships
- line_event_logs
- line_processed_events
- line_message_logs
- line_action_logs

Standby:
- standby_calendars
- standby_shift_rules
- standby_slots
- standby_slot_change_logs
- standby_replacement_logs

Leave / Availability:
- user_leave_requests
- user_availability_status

Email / Ticket Pipeline:
- email_ticket_audit_raw
- email_ticket_master
- tickets
- ticket_classification_results
- ticket_contacts
- ticket_artifacts
- processed_emails

Routing / Acceptance / Escalation / SLA:
- escalation_rules
- ticket_routing_logs
- ticket_notifications
- ticket_acceptance_logs
- ticket_escalation_logs
- ticket_assignment_state
- ticket_sla_metrics

AI / Mapping / Audit / Metrics:
- ai_chat_sessions
- ai_chat_messages
- ai_chat_feedback
- data_mapping_rules
- manual_override_logs
- audit_logs
- daily_team_metrics

Database design principles:
- proper foreign keys
- useful indexes
- created_at / updated_at
- optional soft delete only where appropriate
- retain historical logs where needed
- operational ticket table must be distinct from raw/master email tables
- prepare cleanup strategy for log retention

Retention rules:
- line logs retain for 3 months
- audit logs retain for 3 months

No attachment storage is required.

==================================================
12. MAIN TEAM ROUTING LOGIC
==================================================

Main Team routing rules for Phase 1:
- derive only from to_address
- do not use ML for main team
- do not overcomplicate main team logic

Main Team values:
- iNET Network Team
- iNET Operation Team
- iNET Cloud Support Team

Store:
- derived main team
- route reason
- to_address used
- timestamp
- source = deterministic_to_address

==================================================
13. CLOUD SUBTEAM CLASSIFICATION LOGIC
==================================================

Cloud subteam classification applies only when Main Team = iNET Cloud Support Team.

Available labels in Phase 1:
- AWS Team
- GCP Team

Rules:
1. Run explicit logic / mapping checks first if available
2. If not confidently resolved, run ML model
3. If confidence >= 0.85, accept ML result
4. If confidence < 0.85, fallback to logic/rules
5. If model errors or unavailable, fallback to logic/rules
6. If still unresolved, use fallback handling path that safely triggers shared attention

Must store:
- predicted_sub_team
- decision_mode
- label_source
- confidence
- model_version
- ml_candidate
- logic_candidate
- text_input_used
- cross_task_applied flag

Cross-task inference:
- keep support structure because prior code/design expects it
- make this behavior configurable
- can be enabled/disabled by config
- treat as supported architecture, even if tuning/refinement happens later

==================================================
14. ML REQUIREMENTS
==================================================

ML is only for Cloud subteam classification in Phase 1.

Required ML lifecycle:
- export training data to CSV
- build dataset from parsed/master records
- create relevant text and logic features
- train/evaluate model
- save model artifact
- save model version and metrics
- support runtime inference
- support confidence threshold
- support deterministic fallback
- support explainability metadata at least at practical debugging level

Threshold:
- production default = 0.85

Important:
Do not design a system that depends only on ML.
Deterministic fallback must always exist.

==================================================
15. STANDBY / CALENDAR / TIER DESIGN
==================================================

This area must be flexible and production-friendly.

Facts:
- 1 tier = exactly 1 person
- a team has 2 or 3 tiers
- not every team rotates the same way
- some teams change standby every Monday at 08:30
- some teams change at 00:00
- some teams rotate daily
- some teams split by time of day, such as senior in daytime and junior at night
- AWS/GCP teams may hold a tier for 7 days and rotate weekly

Therefore:
Do NOT design standby as a simple fixed weekly static table only.

You must design flexible standby scheduling with support for:
- daily rotation
- weekly rotation
- custom effective datetime ranges
- split shifts (for example day vs night)
- tier-specific assignee
- team-specific rotation rules
- manual replacement
- leave/unavailable skipping

Leave/unavailable:
- daily-based, not hourly-based in Phase 1
- no approval workflow
- when unavailable, automatically move to next valid tier

Frontend requirement:
- monthly calendar UI is mandatory

==================================================
16. LINE INTEGRATION DESIGN
==================================================

LINE constraints:
- system uses only one LINE group
- keep group metadata to support future group replacement
- notifications go into this one group
- acceptance is performed from LINE response/action

Notification requirements:
- use flex message
- include ticket details
- include accept action
- mention the responsible standby person

Fallback assignee behavior:
- if correct assignee cannot be resolved, mention:
  - one AWS standby
  - one GCP standby

Acceptance behavior:
- the user who accepts becomes owner immediately
- they do not have to be the originally tagged person

Current development behavior:
- sending may intentionally remain disabled/commented during development
- the architecture must support real sending cleanly
- system should support enable/disable sending using config/feature flag

Retry design:
- prepare for retry logic
- target retry count = 3
- actual full retry implementation may be Phase 2 if intentionally deferred
- keep clear placeholders and architecture support if not activated yet

==================================================
17. PYTHON WORKER DESIGN
==================================================

Python worker is the correct place for:
- email polling
- AI/model workflow
- LINE worker behavior
- daily summary sending
- escalation-ready processing

Worker must not remain as a single undifferentiated loop forever in production design.
Instead, structure the worker as explicit jobs.

Required Python jobs:
1. Email polling job
   - every 10 seconds
   - read new mail
   - parse
   - classify
   - persist
   - send first notification if enabled

2. Escalation check job
   - every 1 minute
   - check tickets that are still unaccepted
   - determine if SLA window expired
   - trigger next round when appropriate
   - Phase 1 may keep placeholder structure if intentionally deferred

3. Daily summary job
   - every day at 17:30
   - send summary to LINE group
   - no mentions

Development reality:
- It is acceptable for notification sending to remain commented/disabled in dev
- It is acceptable for escalation job to remain placeholder in dev
- But the structure must remain clearly prepared for activation later

Worker design rules:
- clearly separated jobs
- clear logs
- clear TODO/placeholder markers where intentionally deferred
- avoid ambiguous code that looks forgotten
- support config flags such as ENABLE_LINE_SEND
- should evolve beyond simple while-true plus mixed responsibilities

==================================================
18. EXPRESS API BACKEND REQUIREMENTS
==================================================

Express.js is the web/API backend.
Use JavaScript + Sequelize + PostgreSQL + JWT.

Use clear module separation, such as:
- auth
- users
- roles
- teams
- standby
- leave
- tickets
- routing
- notifications
- line
- reports
- audit
- ai
- data-mapping
- search
- admin/system

At minimum, define APIs for:

Auth:
- POST /auth/login
- POST /auth/logout
- POST /auth/set-password
- POST /auth/verify-otp
- POST /auth/request-reset
- POST /auth/reset-password
- POST /auth/change-password
- GET /auth/me

Users / Roles:
- GET /users
- GET /users/:id
- POST /users
- PUT /users/:id
- PATCH /users/:id/status
- PUT /users/:id/roles
- GET /locked-users
- POST /locked-users/:id/unlock

Teams / Membership:
- GET /teams
- GET /sub-teams
- GET /team-members
- POST /team-members
- PUT /team-members/:id

Standby / Calendar:
- GET /standby/calendars
- POST /standby/calendars
- PUT /standby/calendars/:id
- GET /standby/slots
- POST /standby/slots
- PUT /standby/slots/:id
- POST /standby/slots/:id/replace
- GET /standby/current

Leave / Availability:
- GET /leave-requests
- POST /leave-requests
- PUT /leave-requests/:id
- GET /availability
- POST /availability
- PUT /availability/:id

Tickets:
- GET /tickets
- GET /tickets/:id
- GET /tickets/:id/classification
- GET /tickets/:id/notifications
- GET /tickets/:id/acceptance
- GET /tickets/:id/escalations
- GET /tickets/:id/artifacts
- GET /tickets/:id/contacts
- POST /tickets/:id/accept
- POST /tickets/:id/override
- POST /tickets/:id/reroute

Routing / Notification:
- POST /routing/reprocess/:ticketId
- POST /notifications/resend/:ticketId
- GET /notifications
- GET /acceptance-monitor

LINE:
- POST /line/webhook
- GET /line/logs
- GET /line/messages
- GET /line/actions
- POST /line/test-message

Reports:
- GET /reports/sla/team
- GET /reports/sla/subteam
- GET /reports/export/csv

Audit:
- GET /audit-logs

AI:
- POST /ai/chat/session
- POST /ai/chat/message
- GET /ai/chat/sessions
- GET /ai/chat/sessions/:id/messages
- POST /ai/chat/feedback

Data Mapping:
- GET /data-mapping
- POST /data-mapping
- PUT /data-mapping/:id
- DELETE /data-mapping/:id

Search:
- GET /search/global

==================================================
19. AI ASSISTANT DESIGN
==================================================

AI Assistant uses:
- Ollama
- model: qwen2.5vl:3b
- Dockerized runtime

AI assistant constraints:
- it is internal only
- it may answer using real data from this system
- it must not expose data outside the system
- it must follow access permissions

Critical rule:
The AI assistant must use service layer access only.
It must NOT directly generate arbitrary SQL and execute against the database.

Interpretation of “service layer only”:
- AI can call approved backend functions/services/endpoints
- AI must not freely query the DB directly
- permission control must remain enforced
- audit logging must be possible
- responses must remain within approved data boundaries

Must support:
- session storage
- message history
- feedback storage
- AI audit

==================================================
20. MANUAL OVERRIDE REQUIREMENTS
==================================================

Manual override in Phase 1 is primarily for controlling future notification/escalation behavior.

Example use:
- first round sent to tier 1
- 15 minutes pass with no acceptance
- next round should go to next tier
- manual override can influence next notification behavior

Manual override logs must be stored.
Override actions must be auditable.

==================================================
21. REPORTING REQUIREMENTS
==================================================

Must support:
1. SLA by Team
2. SLA by Subteam

Filters:
- date range
- main team
- subteam

Export:
- CSV only

Daily Summary content:
- ticket count
- accepted count
- missed SLA count
- grouped by team

==================================================
22. LOGGING / AUDIT / RETENTION
==================================================

Must include at least:
- request logs
- auth logs
- ticket routing logs
- classification logs
- notification logs
- acceptance logs
- escalation logs
- audit logs
- AI audit logs
- line message / line action / line event logs

Retention:
- line logs: 3 months
- audit logs: 3 months

Design cleanup jobs/processes accordingly.

==================================================
23. TESTING STRATEGY
==================================================

Recommend a practical production-oriented testing strategy.

At minimum include:

Unit tests:
- routing logic
- ML threshold behavior
- fallback logic
- standby resolution
- leave/unavailable skip logic
- SLA calculation
- line payload generation

Integration tests:
- email → parse → classify → store
- ticket → notify → accept → assign owner
- ticket → no accept → next round eligibility
- report generation
- auth + RBAC checks

UI tests:
- login flow
- ticket list/detail flow
- monthly calendar behavior
- admin pages
- report export

The design should emphasize business-critical test coverage first.

==================================================
24. DOCKER / DEPLOYMENT REQUIREMENTS
==================================================

Deployment target:
- Docker images on Ubuntu VM

Design should include:
- Express.js container
- Python worker / AI / LINE container(s)
- PostgreSQL connection strategy
- environment variable management
- dev vs prod configuration separation
- startup order and dependency handling
- logging strategy
- secrets strategy
- future support for scaling where practical

==================================================
25. IMPORTANT DEVELOPMENT REALITY
==================================================

The implementation should reflect the following practical current state:

- some frontend pages already exist with mock data
- some pages still need correction, especially standby calendar monthly visualization
- some Python worker actions are intentionally commented/disabled during development
- escalation logic may intentionally remain placeholder for now
- LINE retry logic may intentionally remain placeholder for now
- these deferred parts must still be represented cleanly and intentionally in the architecture
- the design must not mistake a temporary dev placeholder for a final production behavior

==================================================
26. HARD CONSTRAINTS
==================================================

Do not violate these:

- Backend API must use Express.js
- Frontend must use Vue 3 + JavaScript
- ORM must use Sequelize
- Auth must use JWT
- Database must use PostgreSQL
- Python is the correct worker/AI/LINE side
- Main team routing must use to_address only
- Main team does not use ML in Phase 1
- Cloud subteam labels are only AWS Team and GCP Team in Phase 1
- Source is email only
- No attachment storage
- Threshold = 0.85
- LINE group count = 1
- One tier = one person
- A team has 2 or 3 tiers
- Maximum notification rounds = 3
- If final round has no acceptance, stop and let web/report reflect SLA miss
- Leave/unavailable is daily-based
- No leave approval flow
- Daily summary time = 17:30
- Reports export only CSV
- UI language = English
- AI assistant must use service layer only
- Privacy/compliance-ready structure must be designed now

==================================================
27. OUTPUT FORMAT REQUIREMENT
==================================================

Your response must be a complete system design document.

For every section, provide:
- recommended default design
- reasoning
- edge cases
- future extension points

The document must include:
1. architecture overview
2. component breakdown
3. backend structure
4. frontend structure
5. database design
6. ERD-level explanation
7. routing logic
8. ML logic
9. standby design
10. LINE design
11. worker design
12. API design
13. RBAC design
14. reporting design
15. AI assistant design
16. logging/audit design
17. privacy/compliance-ready design
18. testing strategy
19. Docker deployment design
20. phased implementation plan

If there are any remaining ambiguities, list them only at the end under:
Open Questions

Do not skip important details.
Do not provide only generic guidance.
Do not oversimplify.
This is a critical project.