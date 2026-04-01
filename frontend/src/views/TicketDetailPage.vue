<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Ticket Detail</div>
                        <div class="page-subtitle">
                            Review ticket routing, acceptance flow, escalation history, and audit details.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Back to Tickets"
                            icon="pi pi-arrow-left"
                            severity="secondary"
                            outlined
                            @click="goBack"
                        />
                    </div>
                </div>
            </template>

            <template #content>
                <Message v-if="pageError" severity="error" class="mb-3">
                    {{ pageError }}
                </Message>

                <template v-if="ticket">
                    <div class="summary-grid">
                        <div class="summary-card">
                            <div class="summary-label">Ticket No</div>
                            <div class="summary-value summary-value-sm">{{ ticket.ticket_no }}</div>
                        </div>

                        <div class="summary-card">
                            <div class="summary-label">Team</div>
                            <div class="summary-value summary-value-sm">{{ ticket.team_name }}</div>
                        </div>

                        <div class="summary-card">
                            <div class="summary-label">Current Tier</div>
                            <div class="summary-value summary-value-sm">{{ ticket.current_tier }}</div>
                        </div>

                        <div class="summary-card">
                            <div class="summary-label">Status</div>
                            <div class="summary-value summary-value-sm">
                                <span class="status-badge" :class="ticketStatusClass(ticket.status)">
                                    {{ ticket.status }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div class="dashboard-grid">
                        <Card class="content-card">
                            <template #title>
                                <span>Ticket Summary</span>
                            </template>

                            <template #content>
                                <div class="detail-grid">
                                    <div class="info-box">
                                        <div class="info-label">Subject</div>
                                        <div class="info-value">{{ ticket.subject }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Requester Name</div>
                                        <div class="info-value">{{ ticket.requester_name || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Requester Email</div>
                                        <div class="info-value">{{ ticket.requester_email || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Requester IP</div>
                                        <div class="info-value">{{ ticket.requester_ip || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Priority</div>
                                        <div class="info-value">
                                            <span class="priority-chip" :class="priorityClass(ticket.priority)">
                                                {{ ticket.priority }}
                                            </span>
                                        </div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Elapsed</div>
                                        <div class="info-value">{{ ticket.elapsed || "-" }}</div>
                                    </div>
                                </div>
                            </template>
                        </Card>

                        <Card class="content-card">
                            <template #title>
                                <span>Routing Result</span>
                            </template>

                            <template #content>
                                <div class="detail-grid">
                                    <div class="info-box">
                                        <div class="info-label">Decision Mode</div>
                                        <div class="info-value">{{ ticket.decision_mode || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Confidence</div>
                                        <div class="info-value">{{ ticket.confidence }}%</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Label Source</div>
                                        <div class="info-value">{{ ticket.label_source || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Assigned Team</div>
                                        <div class="info-value">{{ ticket.team_name || "-" }}</div>
                                    </div>

                                    <div class="info-box info-box-wide">
                                        <div class="info-label">Model Reason</div>
                                        <div class="info-value">{{ ticket.model_reason || "-" }}</div>
                                    </div>
                                </div>
                            </template>
                        </Card>
                    </div>

                    <div class="dashboard-grid">
                        <Card class="content-card">
                            <template #title>
                                <span>Source Email / Parsed Data</span>
                            </template>

                            <template #content>
                                <div class="detail-grid">
                                    <div class="info-box info-box-wide">
                                        <div class="info-label">Email Subject</div>
                                        <div class="info-value">{{ ticket.email_subject || "-" }}</div>
                                    </div>

                                    <div class="info-box info-box-wide">
                                        <div class="info-label">Email Body</div>
                                        <div class="info-value multiline">{{ ticket.email_body || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Parsed Application</div>
                                        <div class="info-value">{{ ticket.parsed_application || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Parsed Environment</div>
                                        <div class="info-value">{{ ticket.parsed_environment || "-" }}</div>
                                    </div>

                                    <div class="info-box info-box-wide">
                                        <div class="info-label">Parsed Keywords</div>
                                        <div class="info-value">{{ ticket.parsed_keywords || "-" }}</div>
                                    </div>
                                </div>
                            </template>
                        </Card>

                        <Card class="content-card">
                            <template #title>
                                <span>Acceptance Summary</span>
                            </template>

                            <template #content>
                                <div class="detail-grid">
                                    <div class="info-box">
                                        <div class="info-label">First Notified User</div>
                                        <div class="info-value">{{ ticket.first_notified_user || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Accepted By</div>
                                        <div class="info-value">{{ ticket.assigned_user || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Accepted Tier</div>
                                        <div class="info-value">{{ ticket.accepted_tier || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Time to Accept</div>
                                        <div class="info-value">{{ ticket.time_to_accept || "-" }}</div>
                                    </div>

                                    <div class="info-box info-box-wide">
                                        <div class="info-label">Acceptance Note</div>
                                        <div class="info-value">{{ ticket.acceptance_note || "-" }}</div>
                                    </div>
                                </div>
                            </template>
                        </Card>
                    </div>

                    <Card class="content-card">
                        <template #title>
                            <span>Acceptance Timeline</span>
                        </template>

                        <template #content>
                            <div class="timeline-list">
                                <div
                                    v-for="item in acceptanceTimeline"
                                    :key="item.id"
                                    class="timeline-item"
                                >
                                    <div class="timeline-time">{{ formatDateTime(item.time) }}</div>
                                    <div class="timeline-content">
                                        <div class="timeline-title">{{ item.title }}</div>
                                        <div class="timeline-desc">{{ item.description }}</div>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </Card>

                    <div class="dashboard-grid">
                        <Card class="content-card">
                            <template #title>
                                <span>Escalation History</span>
                            </template>

                            <template #content>
                                <DataTable
                                    :value="escalationHistory"
                                    responsiveLayout="scroll"
                                    stripedRows
                                >
                                    <Column field="time" header="Time" style="min-width: 180px">
                                        <template #body="{ data }">
                                            {{ formatDateTime(data.time) }}
                                        </template>
                                    </Column>
                                    <Column field="from_tier" header="From" style="min-width: 120px" />
                                    <Column field="to_tier" header="To" style="min-width: 120px" />
                                    <Column field="reason" header="Reason" style="min-width: 240px" />
                                </DataTable>
                            </template>
                        </Card>

                        <Card class="content-card">
                            <template #title>
                                <span>Admin Override</span>
                            </template>

                            <template #content>
                                <div v-if="adminOverride" class="detail-grid">
                                    <div class="info-box">
                                        <div class="info-label">Override By</div>
                                        <div class="info-value">{{ adminOverride.actor_name || "-" }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Override Time</div>
                                        <div class="info-value">{{ formatDateTime(adminOverride.time) }}</div>
                                    </div>

                                    <div class="info-box info-box-wide">
                                        <div class="info-label">Action</div>
                                        <div class="info-value">{{ adminOverride.action || "-" }}</div>
                                    </div>

                                    <div class="info-box info-box-wide">
                                        <div class="info-label">Reason</div>
                                        <div class="info-value">{{ adminOverride.reason || "-" }}</div>
                                    </div>
                                </div>

                                <div v-else class="empty-box">
                                    No admin override for this ticket.
                                </div>
                            </template>
                        </Card>
                    </div>

                    <Card class="content-card">
                        <template #title>
                            <span>Notes / Comments</span>
                        </template>

                        <template #content>
                            <div class="notes-list">
                                <div
                                    v-for="note in notes"
                                    :key="note.id"
                                    class="note-item"
                                >
                                    <div class="note-top">
                                        <div class="note-author">{{ note.author }}</div>
                                        <div class="note-time">{{ formatDateTime(note.time) }}</div>
                                    </div>
                                    <div class="note-desc">{{ note.message }}</div>
                                </div>
                            </div>
                        </template>
                    </Card>

                    <div class="mock-note mt-3">
                        This page currently uses frontend mock data and is ready for future backend integration
                        for parsed email, routing decision, acceptance timeline, escalation history, and audit evidence.
                    </div>
                </template>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const pageError = ref("");
const ticket = ref(null);
const acceptanceTimeline = ref([]);
const escalationHistory = ref([]);
const adminOverride = ref(null);
const notes = ref([]);

const mockTickets = [
    {
        ticket_no: "INC000123",
        subject: "Cannot access AWS console",
        requester_name: "User One",
        requester_email: "user1@company.com",
        requester_ip: "10.10.1.25",
        team_name: "Cloud Operations",
        decision_mode: "AI Routing",
        confidence: 92,
        label_source: "AI Classifier",
        model_reason: "Matched AWS and console access keywords with high confidence.",
        email_subject: "URGENT: Cannot access AWS console",
        email_body: "User reported inability to log in to AWS console since 08:15. MFA prompt failed repeatedly.",
        parsed_application: "AWS Console",
        parsed_environment: "Production",
        parsed_keywords: "aws, console, login, mfa",
        first_notified_user: "Admin User",
        assigned_user: "Admin User",
        current_tier: "Tier 1",
        accepted_tier: "Tier 1",
        time_to_accept: "05m",
        acceptance_note: "Accepted immediately after LINE notification.",
        elapsed: "08m",
        priority: "High",
        status: "Accepted"
    },
    {
        ticket_no: "INC000124",
        subject: "Production alert on API gateway",
        requester_name: "System Alert",
        requester_email: "alert@company.com",
        requester_ip: "10.10.2.10",
        team_name: "Security Operations",
        decision_mode: "Rule-based",
        confidence: 88,
        label_source: "Keyword Rule",
        model_reason: "Mapped from alert source and security event rule.",
        email_subject: "ALERT: API gateway anomaly detected",
        email_body: "Gateway error spike and multiple suspicious requests detected from public IP ranges.",
        parsed_application: "API Gateway",
        parsed_environment: "Production",
        parsed_keywords: "gateway, anomaly, alert, suspicious requests",
        first_notified_user: "Super Admin",
        assigned_user: "",
        current_tier: "Tier 2",
        accepted_tier: "",
        time_to_accept: "-",
        acceptance_note: "No confirmation received yet.",
        elapsed: "12m",
        priority: "High",
        status: "Escalated"
    },
    {
        ticket_no: "TASK000981",
        subject: "Investigate suspicious login attempt",
        requester_name: "Security Gateway",
        requester_email: "siem@company.com",
        requester_ip: "172.16.20.9",
        team_name: "Security Operations",
        decision_mode: "AI Routing",
        confidence: 76,
        label_source: "AI Classifier",
        model_reason: "Possible security incident based on login anomaly pattern.",
        email_subject: "Investigate suspicious login attempt",
        email_body: "Multiple failed logins followed by success from abnormal geolocation.",
        parsed_application: "Identity Service",
        parsed_environment: "Production",
        parsed_keywords: "login, failed, anomaly, suspicious",
        first_notified_user: "Ploy Jinda",
        assigned_user: "",
        current_tier: "Tier 3",
        accepted_tier: "",
        time_to_accept: "-",
        acceptance_note: "Escalated due to no acceptance in lower tiers.",
        elapsed: "18m",
        priority: "High",
        status: "No Acceptance"
    }
];

const mockTimeline = {
    INC000123: [
        {
            id: 1,
            time: "2026-04-01T08:15:00Z",
            title: "Ticket Received",
            description: "Email received and parsed by the system."
        },
        {
            id: 2,
            time: "2026-04-01T08:16:00Z",
            title: "LINE Notification Sent",
            description: "Tier 1 notification sent to Admin User."
        },
        {
            id: 3,
            time: "2026-04-01T08:20:00Z",
            title: "Accepted",
            description: "Admin User accepted ticket from LINE."
        }
    ],
    INC000124: [
        {
            id: 1,
            time: "2026-04-01T09:00:00Z",
            title: "Ticket Received",
            description: "Alert email received from monitoring system."
        },
        {
            id: 2,
            time: "2026-04-01T09:01:00Z",
            title: "Tier 1 Notified",
            description: "Tier 1 user notified but no response."
        },
        {
            id: 3,
            time: "2026-04-01T09:08:00Z",
            title: "Escalated to Tier 2",
            description: "No acceptance received within defined timeout."
        }
    ],
    TASK000981: [
        {
            id: 1,
            time: "2026-04-01T07:40:00Z",
            title: "Ticket Received",
            description: "Security alert created automatically."
        },
        {
            id: 2,
            time: "2026-04-01T07:41:00Z",
            title: "Tier 1 Notified",
            description: "No response from Tier 1."
        },
        {
            id: 3,
            time: "2026-04-01T07:48:00Z",
            title: "Escalated to Tier 2",
            description: "Tier 2 notified after timeout."
        },
        {
            id: 4,
            time: "2026-04-01T07:56:00Z",
            title: "Escalated to Tier 3",
            description: "No acceptance from Tier 2."
        }
    ]
};

const mockEscalation = {
    INC000123: [],
    INC000124: [
        {
            id: 1,
            time: "2026-04-01T09:08:00Z",
            from_tier: "Tier 1",
            to_tier: "Tier 2",
            reason: "Timeout without acceptance"
        }
    ],
    TASK000981: [
        {
            id: 1,
            time: "2026-04-01T07:48:00Z",
            from_tier: "Tier 1",
            to_tier: "Tier 2",
            reason: "Timeout without acceptance"
        },
        {
            id: 2,
            time: "2026-04-01T07:56:00Z",
            from_tier: "Tier 2",
            to_tier: "Tier 3",
            reason: "No response from Tier 2"
        }
    ]
};

const mockAdminOverride = {
    INC000123: null,
    INC000124: {
        actor_name: "Super Admin",
        time: "2026-04-01T09:10:00Z",
        action: "Forced reassignment to Security Operations Tier 2",
        reason: "Critical production alert required immediate attention."
    },
    TASK000981: null
};

const mockNotes = {
    INC000123: [
        {
            id: 1,
            author: "Admin User",
            time: "2026-04-01T08:22:00Z",
            message: "Issue reproduced and checking MFA policy."
        }
    ],
    INC000124: [
        {
            id: 1,
            author: "Super Admin",
            time: "2026-04-01T09:12:00Z",
            message: "Monitoring production impact and coordinating with gateway team."
        }
    ],
    TASK000981: [
        {
            id: 1,
            author: "System",
            time: "2026-04-01T07:57:00Z",
            message: "Escalation reached Tier 3 with no acceptance recorded."
        }
    ]
};

const loadTicket = () => {
    pageError.value = "";

    const ticketNo = String(route.query.ticketNo || "").trim();

    if (!ticketNo) {
        pageError.value = "Ticket number is missing.";
        return;
    }

    const found = mockTickets.find((item) => item.ticket_no === ticketNo);

    if (!found) {
        pageError.value = `Ticket ${ticketNo} not found.`;
        return;
    }

    ticket.value = found;
    acceptanceTimeline.value = mockTimeline[ticketNo] || [];
    escalationHistory.value = mockEscalation[ticketNo] || [];
    adminOverride.value = mockAdminOverride[ticketNo] || null;
    notes.value = mockNotes[ticketNo] || [];
};

const goBack = () => {
    router.push("/tickets");
};

const ticketStatusClass = (status) => {
    switch (status) {
        case "Accepted":
            return "status-active";
        case "Escalated":
            return "status-pending";
        case "No Acceptance":
            return "status-inactive";
        default:
            return "status-pending";
    }
};

const priorityClass = (priority) => {
    switch (priority) {
        case "High":
            return "priority-high";
        case "Medium":
            return "priority-medium";
        case "Low":
            return "priority-low";
        default:
            return "";
    }
};

const formatDateTime = (value) => {
    if (!value) return "-";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;

    return date.toLocaleString("en-GB", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    });
};

onMounted(() => {
    loadTicket();
});
</script>

<style scoped>
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    flex-wrap: wrap;
}

.page-title {
    font-size: 1.25rem;
    font-weight: 700;
}

.page-subtitle {
    color: var(--text-muted);
    margin-top: 0.25rem;
    font-size: 0.95rem;
}

.page-header-actions {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}

.summary-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1rem 1.1rem;
}

.summary-label {
    color: var(--text-muted);
    margin-bottom: 0.35rem;
}

.summary-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-color);
}

.summary-value-sm {
    font-size: 1rem;
}

.detail-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
}

.info-box {
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    background: var(--card-bg);
}

.info-box-wide {
    grid-column: span 2;
}

.info-label {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin-bottom: 0.3rem;
}

.info-value {
    font-weight: 600;
    color: var(--text-color);
    word-break: break-word;
    line-height: 1.45;
}

.multiline {
    white-space: pre-wrap;
}

.priority-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
}

.priority-high {
    background: #fee2e2;
    color: #991b1b;
}

.priority-medium {
    background: #fef3c7;
    color: #92400e;
}

.priority-low {
    background: #dcfce7;
    color: #166534;
}

.status-pending {
    background: #fef3c7;
    color: #92400e;
}

.timeline-list {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
}

.timeline-item {
    display: grid;
    grid-template-columns: 180px minmax(0, 1fr);
    gap: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1rem;
    background: var(--card-bg);
}

.timeline-time {
    font-weight: 600;
    color: var(--text-muted);
}

.timeline-title {
    font-weight: 700;
    color: var(--text-color);
    margin-bottom: 0.25rem;
}

.timeline-desc {
    color: var(--text-color);
    line-height: 1.45;
}

.notes-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.note-item {
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1rem;
    background: var(--card-bg);
}

.note-top {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 0.35rem;
}

.note-author {
    font-weight: 700;
    color: var(--text-color);
}

.note-time {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.note-desc {
    color: var(--text-color);
    line-height: 1.45;
}

.empty-box {
    padding: 1rem;
    border: 1px dashed var(--border-color);
    border-radius: 14px;
    text-align: center;
    color: var(--text-muted);
}

.mb-3 {
    margin-bottom: 1rem;
}

.mt-3 {
    margin-top: 1rem;
}

@media (max-width: 1200px) {
    .summary-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 768px) {
    .summary-grid,
    .detail-grid {
        grid-template-columns: 1fr;
    }

    .info-box-wide {
        grid-column: span 1;
    }

    .timeline-item {
        grid-template-columns: 1fr;
    }
}
</style>