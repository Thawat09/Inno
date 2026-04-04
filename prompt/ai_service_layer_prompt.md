# AI Service Layer Prompt
## Orchestrator / Middleware Prompt for AI Assistant
Version: 1.0  
Purpose: Create a production-oriented AI service layer for the Ticket Routing & Standby Notification Platform  
Scope: AI orchestration between user message, system-only AI agent, schema catalog, sensitive data guardrails, SQL execution, retry handling, and final user response

---

## 1) Role

You are a **Senior AI Orchestration Architect**, **Senior Backend Architect**, and **Senior Middleware Engineer**.

Your task is to design and generate the **AI Service Layer** for the internal **Ticket Routing & Standby Notification Platform**.

This service layer sits between:
- frontend / chat UI
- Express.js API backend
- AI model runtime
- PostgreSQL database
- Python AI/worker components
- AI assistant prompt files

The service layer must enforce:
- system-only scope
- role-based permissions
- sensitive-data restrictions
- safe read-only SQL
- SQL retry flow
- safe final response generation

This service layer is mandatory.  
The AI model must **not** directly receive a user message and freely decide everything without orchestration.

---

## 2) Objective

Build a complete service-layer design that supports the following 7 actions:

1. `FLOW_RESPONSE`
2. `DB_QUERY`
3. `DB_QUERY_RETRY`
4. `FINAL_RESPONSE_AFTER_DB`
5. `OUT_OF_SCOPE`
6. `FORBIDDEN`
7. `QUERY_FAILURE`

The service layer must:
- accept user messages
- load companion prompt files
- assemble model context
- call the AI model
- validate returned action
- execute read-only SQL if needed
- retry intelligently on SQL errors
- return a final safe answer to the user

---

## 3) Companion Files Used by This Service Layer

The AI service layer must load and use these files every time:

1. `ai_assistant_agent.md`
   - defines the assistant’s behavioral rules

2. `schema_catalog.md`
   - defines allowed schema knowledge, table purposes, key columns, safe join paths

3. `sensitive_data_guardrails.md`
   - defines forbidden fields, restricted tables, safe summarization policy

These files are stored server-side and must **not** be sent from frontend.

The service layer is responsible for:
- loading them from disk or config-managed storage
- injecting them into the AI model context
- versioning them if needed
- making sure the current model call always uses the latest approved set

---

## 4) High-Level Architecture Responsibility

The AI service layer is the control layer between user intent and actual data retrieval.

### Frontend responsibility
Frontend only sends:
- session_id
- user message
- optional UI metadata

Frontend must not send the prompt files.

### AI service layer responsibility
The AI service layer must:
1. receive user message
2. validate session/user context
3. resolve current user role and data scope
4. load prompt companion files
5. assemble model prompt/context
6. call AI model round 1
7. inspect returned action
8. if SQL is needed, validate and execute it safely
9. if query fails, ask AI for corrected SQL
10. if query succeeds, ask AI for final user answer
11. return safe response to frontend
12. log all relevant steps

### Database responsibility
The database provides facts only.
The AI model never gets direct uncontrolled DB access.

---

## 5) System Scope

This AI service layer is only for the **Ticket Routing & Standby Notification Platform**.

The service layer must support questions related to:
- tickets
- routing
- main team / subteam
- standby
- SLA
- escalation
- LINE notification
- acceptance
- users
- teams
- leave / availability
- logs / audit
- reports
- mappings relevant to this system
- AI assistant behavior inside this system

If a user asks outside this scope, the service layer must guide the AI into returning:
> This request is outside the scope of this system. Please contact the administrator.

---

## 6) Required 7 Actions and Their Meaning

### 6.1 FLOW_RESPONSE
Use when the question can be answered from system flow / system knowledge only.

Examples:
- How does standby selection work?
- How is SLA calculated?
- What happens when no one accepts the ticket?

Behavior:
- no SQL execution
- AI returns direct answer
- service layer validates and returns it to user

---

### 6.2 DB_QUERY
Use when actual data from database is needed.

Examples:
- Who accepted RITM123456?
- Did INC0001 miss SLA?
- Who is the current AWS standby?

Behavior:
- AI returns a read-only PostgreSQL SQL query
- service layer validates it
- service layer executes it
- if success, continue to final-response round
- if failure, continue to retry round

---

### 6.3 DB_QUERY_RETRY
Use when the previous SQL failed.

Behavior:
- service layer sends back:
  - original user question
  - previous SQL
  - exact DB error
  - schema/guardrail context
- AI returns corrected SQL
- service layer validates and retries execution

Constraint:
- maximum total query attempts = 3
  - first attempt
  - retry 1
  - retry 2

---

### 6.4 FINAL_RESPONSE_AFTER_DB
Use after a successful query result is available.

Behavior:
- service layer sends to AI:
  - original user message
  - successful SQL result or summarized result
  - system flow context if relevant
- AI returns final user-facing answer
- service layer validates and returns it

---

### 6.5 OUT_OF_SCOPE
Use when the question is not about this system.

Behavior:
- no SQL
- no extra processing
- return exact out-of-scope message

---

### 6.6 FORBIDDEN
Use when the question is about the system but user is not allowed to access the requested data.

Examples:
- employee asking for system-wide audit logs
- asking for password_hash
- asking for token_hash / otp_code_hash
- asking for cross-team restricted data without permission

Behavior:
- no SQL for forbidden data
- return exact forbidden message

---

### 6.7 QUERY_FAILURE
Use when all allowed query attempts fail.

Behavior:
- do not expose internal SQL stack traces to end user
- return exact failure message

---

## 7) Exact Standard User Messages

The service layer must standardize these exact messages:

### Out of scope
> This request is outside the scope of this system. Please contact the administrator.

### Forbidden
> You do not have permission to access that data. Please contact the administrator.

### Query failure
> I could not retrieve the data due to a database query issue. Please contact the administrator.

Use exact wording for consistency.

---

## 8) Input to the Service Layer

The service layer receives at least:

```json
{
  "session_id": "string",
  "message": "string"
}
```

Internally it must enrich the request with:
- current user identity
- current user role
- current user team scope
- conversation history
- timezone/date context
- loaded prompt file contents
- query retry settings
- feature flags if any

Recommended internal request model:

```json
{
  "session_id": "sess_001",
  "user_id": "u_123",
  "user_role": "admin",
  "user_team_scope": ["AWS Team"],
  "message": "Who accepted RITM123456?",
  "conversation_history": [],
  "timezone": "Asia/Bangkok",
  "max_query_attempts": 3,
  "prompt_files": {
    "agent_rules": "...",
    "schema_catalog": "...",
    "sensitive_guardrails": "..."
  }
}
```

---

## 9) Output Contract from AI Round 1

The first model call must always return a structured action object.

Allowed action outputs:

### FLOW_RESPONSE
```json
{
  "action": "FLOW_RESPONSE",
  "intent": "FLOW_ONLY",
  "answer": "..."
}
```

### DB_QUERY
```json
{
  "action": "DB_QUERY",
  "intent": "DB_ONLY or FLOW_PLUS_DB",
  "sql": "select ...",
  "reason": "why this query is needed",
  "result_usage_plan": "how the result will be used"
}
```

### OUT_OF_SCOPE
```json
{
  "action": "OUT_OF_SCOPE",
  "answer": "This request is outside the scope of this system. Please contact the administrator."
}
```

### FORBIDDEN
```json
{
  "action": "FORBIDDEN",
  "answer": "You do not have permission to access that data. Please contact the administrator."
}
```

Any other action in round 1 must be rejected by the service layer.

---

## 10) Output Contract from Retry Round

If SQL failed, the model must return:

```json
{
  "action": "DB_QUERY_RETRY",
  "intent": "DB_ONLY or FLOW_PLUS_DB",
  "sql": "select ... corrected ...",
  "reason": "why the previous query failed and how this fixes it",
  "result_usage_plan": "how the final answer should use the result"
}
```

No other action should be accepted in the retry round except:
- `DB_QUERY_RETRY`
- `QUERY_FAILURE`
- `FORBIDDEN`

---

## 11) Output Contract from Final Response Round

After successful DB query, the model must return:

```json
{
  "action": "FINAL_RESPONSE_AFTER_DB",
  "intent": "DB_ONLY or FLOW_PLUS_DB",
  "answer": "..."
}
```

No SQL should appear in this step.

---

## 12) Service Layer Execution Flow

### Flow A: Flow-only request
1. receive user message
2. load prompt files
3. build context
4. call AI
5. AI returns `FLOW_RESPONSE`
6. validate output
7. return answer to user
8. store chat history and audit

### Flow B: DB request success
1. receive user message
2. load prompt files
3. call AI
4. AI returns `DB_QUERY`
5. validate action
6. validate SQL safety
7. execute SQL
8. SQL succeeds
9. call AI again with result
10. AI returns `FINAL_RESPONSE_AFTER_DB`
11. validate and return to user
12. store logs/audit

### Flow C: DB request with retry
1. AI returns `DB_QUERY`
2. execute SQL
3. SQL fails
4. call AI with original question + previous SQL + error
5. AI returns `DB_QUERY_RETRY`
6. validate and execute again
7. if success → final response round
8. if fail again → retry once more
9. if still fail → return `QUERY_FAILURE`

### Flow D: Out of scope
1. AI returns `OUT_OF_SCOPE`
2. return refusal

### Flow E: Forbidden
1. AI returns `FORBIDDEN`
2. return refusal

---

## 13) SQL Validation Rules in Service Layer

The service layer must never trust the AI-generated SQL blindly.

Before execution, validate:

1. SQL is read-only
2. SQL starts with allowed read statements only
3. no forbidden keywords:
   - insert
   - update
   - delete
   - truncate
   - drop
   - alter
   - create
   - grant
   - revoke
4. no multi-statement execution
5. no dangerous functions if policy forbids them
6. no forbidden columns from `sensitive_data_guardrails.md`
7. no obviously unrelated tables
8. enforce query timeout
9. enforce row limit strategy where appropriate
10. enforce parameterization if runtime supports templated query execution

If validation fails, do not run the SQL.
Return or trigger `FORBIDDEN` / `QUERY_FAILURE` depending on policy.

---

## 14) Sensitive Data Enforcement

The service layer must parse and enforce `sensitive_data_guardrails.md`.

Examples of absolutely forbidden fields:
- `users.password_hash`
- `users.password_salt`
- `user_otp_requests.otp_code_hash`
- `password_reset_requests.token_hash`

The service layer must block queries touching these fields even if the AI generates them.

Also apply strong caution to:
- raw JSON payload fields
- raw email body fields
- raw AI audit text
- reply tokens
- audit diff blobs

The service layer should prefer summarized answers over raw sensitive payload exposure.

---

## 15) Role and Scope Enforcement

The service layer must not rely only on the AI to enforce permission.

It must independently know:
- current user role
- current user team scope
- allowed data scope

Recommended enforcement pattern:
- add scoped filters before query execution where possible
- reject clearly forbidden requests before model call if obvious
- reject returned SQL if it violates scope

Examples:
- employee should not get system-wide audit logs
- admin should not read other teams unless policy permits
- super_admin can access broad scope, but still not forbidden secret fields

---

## 16) Conversation History Handling

The service layer must store and use conversation history for AI chat continuity.

Recommended history sources:
- `ai_chat_sessions`
- `ai_chat_messages`

Rules:
- history is useful for follow-up questions
- history must still remain within system scope
- previous context must not override permission rules
- if user closes chat and UI hides history, DB may still store it if system design allows

When passing history to AI:
- keep only relevant recent messages
- avoid overloading prompt
- preserve enough context for follow-up queries

---

## 17) Logging and Audit Requirements

The AI service layer must log at least:

1. incoming user message
2. current user role and scope
3. model round type
4. returned action
5. SQL validation result
6. SQL execution success/failure
7. retry count
8. final response returned
9. blocked reason if forbidden/out-of-scope
10. latency and token usage if available

Recommended storage:
- `ai_chat_sessions`
- `ai_chat_messages`
- `ai_chat_message_metadata`
- `ai_chat_audit_logs`

Do not store forbidden secrets in logs.

---

## 18) Failure Handling Rules

### If AI returns malformed JSON
- service layer should retry parsing if safely possible
- if unusable, treat as internal processing error
- return safe fallback message or log for admin

### If AI returns unknown action
- reject it
- log it
- optionally re-prompt once in strict format mode
- otherwise fail safely

### If SQL execution fails
- use retry flow
- maximum 3 total query attempts

### If final response round fails
- service layer may return a safe summary from query result if product allows
- otherwise return generic safe failure

---

## 19) Recommended API Design for AI Service Layer

### Endpoint from frontend
```http
POST /ai/chat/message
```

Request:
```json
{
  "session_id": "sess_001",
  "message": "Did INC0001 miss SLA and why?"
}
```

Response:
```json
{
  "session_id": "sess_001",
  "message_id": "msg_002",
  "answer": "Yes. This ticket missed the 15-minute acceptance SLA because it was first accepted after 20 minutes.",
  "action": "FINAL_RESPONSE_AFTER_DB"
}
```

Optional metadata:
```json
{
  "session_id": "sess_001",
  "message_id": "msg_002",
  "answer": "...",
  "action": "FINAL_RESPONSE_AFTER_DB",
  "meta": {
    "used_database": true,
    "query_attempts": 1
  }
}
```

---

## 20) Prompt Construction Strategy

The service layer should construct prompts in layers.

### System prompt layer
Use:
- `ai_assistant_agent.md`
- `schema_catalog.md`
- `sensitive_data_guardrails.md`

### Runtime context layer
Inject:
- current user role
- current user scope
- current time/timezone
- query limits
- conversation history
- current task round (initial / retry / final-response)

### User layer
Inject:
- raw user question

This layering keeps the model consistent and easier to debug.

---

## 21) Prompt Templates by Round

### Round 1: Intent + Action Decision
Prompt should instruct AI to choose one:
- FLOW_RESPONSE
- DB_QUERY
- OUT_OF_SCOPE
- FORBIDDEN

### Round 2: Retry Round
Prompt should include:
- original question
- previous SQL
- exact DB error
- same schema + guardrails
- instruction to return only DB_QUERY_RETRY / FORBIDDEN / QUERY_FAILURE

### Round 3: Final Answer Round
Prompt should include:
- original question
- successful query result
- system flow context if needed
- instruction to return only FINAL_RESPONSE_AFTER_DB

---

## 22) Suggested Internal Function Breakdown

The generated service layer should include functions like:

- `load_prompt_files()`
- `get_user_scope_from_auth()`
- `build_initial_model_context()`
- `call_model_for_action()`
- `validate_ai_action()`
- `validate_sql_read_only()`
- `validate_sql_against_guardrails()`
- `execute_read_only_query()`
- `build_retry_context()`
- `call_model_for_retry_sql()`
- `build_final_answer_context()`
- `call_model_for_final_answer()`
- `persist_chat_and_audit_logs()`
- `format_safe_response()`

---

## 23) SQL Execution Safety Design

Recommended:
- read-only DB user for AI querying
- statement timeout
- row count guard
- max query duration
- no transaction writes
- parameter binding where possible
- DB result summarization if too large
- prevent multi-query payloads

Optional good practice:
- maintain an allowlist of queryable tables for Phase 1
- maintain a denylist from sensitive guardrails

---

## 24) Recommended Result Passing Strategy

After DB success, do not always pass huge raw result sets back to the model.

Recommended approach:
- if result is small → pass structured rows
- if result is large → pass summarized rows + top examples
- if result is aggregate → pass aggregate directly
- if result contains partially sensitive content → sanitize first

Then ask AI to generate the final user-facing answer.

---

## 25) Edge Cases to Support

The service layer design must explicitly handle:
- user follow-up question without repeating identifier
- ambiguous task number vs RITM vs INC
- SQL referencing wrong table/column
- restricted data request
- unrelated question
- empty query result
- large result set
- malformed AI response
- timeout from model
- timeout from DB
- retry exhaustion
- permission mismatch between AI guess and backend truth
- dev mode where some worker logic is placeholder
- PostgreSQL target schema while current source docs came from SQL Server DDL

---

## 26) Development vs Production Notes

### Dev mode
- easier logging
- mock data may exist
- some downstream worker behavior may still be placeholder
- SQL dry-run mode may be useful

### Production mode
- strict logging
- stricter guardrails
- real DB read-only execution
- full permission enforcement
- timeout and retry controls
- minimal information leakage

The design must support both.

---

## 27) Deliverables Required from This Prompt

Generate a complete AI service layer design and implementation prompt that includes:

1. architecture overview
2. the 7-action orchestration model
3. request/response flow
4. sequence flow for each action type
5. prompt assembly strategy
6. SQL validation rules
7. permission enforcement rules
8. sensitive-data enforcement rules
9. retry flow design
10. final answer generation flow
11. API endpoint design
12. storage/logging/audit design
13. error-handling strategy
14. suggested code/module structure
15. edge cases
16. development vs production notes

---

## 28) Hard Constraints

Do not violate these constraints:

- system is only for this platform
- AI must use service-layer orchestration
- AI must not directly write to DB
- SQL must be read-only
- 7 actions must be supported
- companion files must be loaded server-side
- permission enforcement must exist in backend logic, not only in prompt text
- sensitive data fields must be blocked even if AI tries to query them
- final output must be detailed and production-oriented

---

## 29) Output Format Requirement

Your response must be a **complete implementation-oriented design prompt** for building the AI service layer.

It must be:
- detailed
- structured
- practical
- ready to hand to an engineer or another AI for implementation

Do not answer only conceptually.
Do not give a short summary.
Do not skip flows.
Do not skip validation logic.
Do not skip edge cases.
