<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Manual Override</div>
                        <div class="page-subtitle">
                            Override routing decisions, reassign ownership, and handle exceptional ticket cases.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadData"
                        />
                    </div>
                </div>
            </template>

            <template #content>
                <Message v-if="pageError" severity="error" class="mb-3">
                    {{ pageError }}
                </Message>

                <Message v-if="successMessage" severity="success" class="mb-3">
                    {{ successMessage }}
                </Message>

                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Open Candidates</div>
                        <div class="summary-value">{{ filteredTickets.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Override History</div>
                        <div class="summary-value">{{ overrideHistory.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Reassigned</div>
                        <div class="summary-value">{{ reassignedCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Model Incorrect</div>
                        <div class="summary-value">{{ modelIncorrectCount }}</div>
                    </div>
                </div>

                <div class="page-two-column">
                    <Card class="content-card">
                        <template #title>
                            <span>Override Form</span>
                        </template>

                        <template #content>
                            <div class="toolbar-search mb-3">
                                <i class="pi pi-search toolbar-search-icon"></i>
                                <InputText
                                    v-model="ticketSearch"
                                    placeholder="Search ticket no, subject, team..."
                                />
                            </div>

                            <div class="ticket-candidate-list mb-3">
                                <button
                                    v-for="item in filteredTickets"
                                    :key="item.ticket_no"
                                    type="button"
                                    class="ticket-candidate-item"
                                    :class="{ active: selectedTicket?.ticket_no === item.ticket_no }"
                                    @click="selectTicket(item)"
                                >
                                    <div class="ticket-candidate-top">
                                        <div class="ticket-candidate-no">{{ item.ticket_no }}</div>
                                        <span class="status-badge" :class="statusClass(item.status)">
                                            {{ item.status }}
                                        </span>
                                    </div>
                                    <div class="ticket-candidate-subject">{{ item.subject }}</div>
                                    <div class="ticket-candidate-meta">
                                        {{ item.team_name }} | {{ item.current_tier }} | {{ item.assigned_user || 'Unassigned' }}
                                    </div>
                                </button>

                                <div v-if="filteredTickets.length === 0" class="empty-box">
                                    No candidate tickets found.
                                </div>
                            </div>

                            <template v-if="selectedTicket">
                                <div class="selected-ticket-box mb-3">
                                    <div class="selected-ticket-title">{{ selectedTicket.ticket_no }}</div>
                                    <div class="selected-ticket-sub">{{ selectedTicket.subject }}</div>
                                    <div class="selected-ticket-meta">
                                        Team: {{ selectedTicket.team_name }} |
                                        Current Tier: {{ selectedTicket.current_tier }} |
                                        Assigned: {{ selectedTicket.assigned_user || '-' }}
                                    </div>
                                </div>

                                <div class="form-grid">
                                    <div class="form-field">
                                        <label>Override Action</label>
                                        <Dropdown
                                            v-model="form.action_type"
                                            :options="actionOptions"
                                            optionLabel="label"
                                            optionValue="value"
                                            placeholder="Select action"
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>New Team</label>
                                        <Dropdown
                                            v-model="form.new_team"
                                            :options="teamOptions"
                                            optionLabel="label"
                                            optionValue="value"
                                            placeholder="Select team"
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>New Assignee</label>
                                        <Dropdown
                                            v-model="form.new_assignee"
                                            :options="assigneeOptions"
                                            optionLabel="label"
                                            optionValue="value"
                                            placeholder="Select assignee"
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>Force Tier</label>
                                        <Dropdown
                                            v-model="form.force_tier"
                                            :options="tierOptions"
                                            optionLabel="label"
                                            optionValue="value"
                                            placeholder="Select tier"
                                        />
                                    </div>

                                    <div class="form-field form-field-full">
                                        <label>Reason</label>
                                        <Textarea
                                            v-model="form.reason"
                                            rows="4"
                                            placeholder="Describe why this manual override is required"
                                        />
                                    </div>

                                    <div class="checkbox-grid form-field-full">
                                        <label class="checkbox-item">
                                            <input v-model="form.resend_line" type="checkbox" />
                                            <span>Resend LINE notification</span>
                                        </label>

                                        <label class="checkbox-item">
                                            <input v-model="form.mark_model_incorrect" type="checkbox" />
                                            <span>Mark model prediction as incorrect</span>
                                        </label>
                                    </div>

                                    <div class="form-actions">
                                        <Button
                                            label="Apply Override"
                                            icon="pi pi-check"
                                            @click="applyOverride"
                                        />
                                        <Button
                                            label="Reset"
                                            icon="pi pi-refresh"
                                            severity="secondary"
                                            outlined
                                            @click="resetForm"
                                        />
                                    </div>
                                </div>
                            </template>

                            <div v-else class="empty-box">
                                Select a ticket to perform manual override.
                            </div>
                        </template>
                    </Card>

                    <Card class="content-card">
                        <template #title>
                            <span>Override Guidance</span>
                        </template>

                        <template #content>
                            <div class="notes-list">
                                <div class="note-item">
                                    <div class="note-title">Reassign Team</div>
                                    <div class="note-desc">
                                        Use when the routing result selected the wrong team.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Reassign User</div>
                                    <div class="note-desc">
                                        Use when the current assignee is not appropriate or unavailable.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Force Next Tier</div>
                                    <div class="note-desc">
                                        Use when the next escalation step must happen immediately.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Resend Notification</div>
                                    <div class="note-desc">
                                        Useful when LINE delivery failed or the assignee missed the notification.
                                    </div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>

                <Card class="content-card">
                    <template #title>
                        <span>Override History</span>
                    </template>

                    <template #content>
                        <DataTable
                            :value="overrideHistory"
                            dataKey="id"
                            paginator
                            :rows="10"
                            responsiveLayout="scroll"
                            stripedRows
                        >
                            <Column header="#" style="width: 70px">
                                <template #body="{ index }">
                                    {{ index + 1 }}
                                </template>
                            </Column>

                            <Column field="created_at" header="Time" style="min-width: 180px">
                                <template #body="{ data }">
                                    {{ formatDateTime(data.created_at) }}
                                </template>
                            </Column>

                            <Column field="ticket_no" header="Ticket No" style="min-width: 140px" />

                            <Column field="action_type" header="Action" style="min-width: 180px">
                                <template #body="{ data }">
                                    <span class="type-chip" :class="actionClass(data.action_type)">
                                        {{ data.action_type }}
                                    </span>
                                </template>
                            </Column>

                            <Column field="override_by" header="Override By" style="min-width: 160px" />

                            <Column field="target_value" header="Target" style="min-width: 220px">
                                <template #body="{ data }">
                                    {{ data.target_value || "-" }}
                                </template>
                            </Column>

                            <Column field="reason" header="Reason" style="min-width: 320px">
                                <template #body="{ data }">
                                    <div class="history-reason">{{ data.reason || "-" }}</div>
                                </template>
                            </Column>

                            <Column header="Flags" style="min-width: 180px">
                                <template #body="{ data }">
                                    <div class="flag-group">
                                        <span v-if="data.resend_line" class="mini-flag">Resend LINE</span>
                                        <span v-if="data.mark_model_incorrect" class="mini-flag danger">Model Incorrect</span>
                                    </div>
                                </template>
                            </Column>

                            <template #empty>
                                <div class="empty-box">
                                    No override history found.
                                </div>
                            </template>
                        </DataTable>
                    </template>
                </Card>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for team reassignment, force escalation, resend notification, and model feedback workflow.
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

const pageError = ref("");
const successMessage = ref("");
const ticketSearch = ref("");
const selectedTicket = ref(null);
const tickets = ref([]);
const overrideHistory = ref([]);

const actionOptions = [
    { label: "Reassign Team", value: "Reassign Team" },
    { label: "Reassign User", value: "Reassign User" },
    { label: "Force Next Tier", value: "Force Next Tier" },
    { label: "Resend Notification", value: "Resend Notification" }
];

const teamOptions = [
    { label: "Cloud Operations", value: "Cloud Operations" },
    { label: "Security Operations", value: "Security Operations" },
    { label: "Standby Support", value: "Standby Support" }
];

const assigneeOptions = [
    { label: "Admin User", value: "Admin User" },
    { label: "Super Admin", value: "Super Admin" },
    { label: "Narin Sukjai", value: "Narin Sukjai" },
    { label: "Ploy Jinda", value: "Ploy Jinda" },
    { label: "User One", value: "User One" },
    { label: "Krit Meechai", value: "Krit Meechai" }
];

const tierOptions = [
    { label: "Tier 1", value: "Tier 1" },
    { label: "Tier 2", value: "Tier 2" },
    { label: "Tier 3", value: "Tier 3" }
];

const form = ref({
    action_type: "",
    new_team: "",
    new_assignee: "",
    force_tier: "",
    reason: "",
    resend_line: false,
    mark_model_incorrect: false
});

const mockTickets = [
    {
        ticket_no: "INC000124",
        subject: "Production alert on API gateway",
        team_name: "Security Operations",
        current_tier: "Tier 2",
        assigned_user: "",
        status: "Escalated"
    },
    {
        ticket_no: "TASK000981",
        subject: "Investigate suspicious login attempt",
        team_name: "Security Operations",
        current_tier: "Tier 3",
        assigned_user: "",
        status: "No Acceptance"
    },
    {
        ticket_no: "INC000130",
        subject: "Database backup failure alert",
        team_name: "Cloud Operations",
        current_tier: "Tier 1",
        assigned_user: "Admin User",
        status: "Pending"
    },
    {
        ticket_no: "RITM000250",
        subject: "Urgent access review request",
        team_name: "Standby Support",
        current_tier: "Tier 1",
        assigned_user: "",
        status: "Pending"
    }
];

const mockHistory = [
    {
        id: 1,
        created_at: "2026-04-01T09:10:00Z",
        ticket_no: "INC000124",
        action_type: "Reassign Team",
        override_by: "Super Admin",
        target_value: "Cloud Operations",
        reason: "Production impact required cloud team involvement.",
        resend_line: true,
        mark_model_incorrect: true
    },
    {
        id: 2,
        created_at: "2026-04-01T08:45:00Z",
        ticket_no: "TASK000981",
        action_type: "Force Next Tier",
        override_by: "Admin User",
        target_value: "Tier 3",
        reason: "Tier 2 did not respond within expected window.",
        resend_line: true,
        mark_model_incorrect: false
    }
];

const loadData = () => {
    pageError.value = "";
    successMessage.value = "";

    try {
        tickets.value = [...mockTickets];
        overrideHistory.value = [...mockHistory];
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load manual override data.";
    }
};

const filteredTickets = computed(() => {
    const keyword = ticketSearch.value.trim().toLowerCase();

    return tickets.value.filter((item) => {
        if (!keyword) return true;
        return [
            item.ticket_no,
            item.subject,
            item.team_name,
            item.current_tier,
            item.assigned_user,
            item.status
        ]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(keyword));
    });
});

const reassignedCount = computed(() =>
    overrideHistory.value.filter((item) =>
        item.action_type === "Reassign Team" || item.action_type === "Reassign User"
    ).length
);

const modelIncorrectCount = computed(() =>
    overrideHistory.value.filter((item) => item.mark_model_incorrect).length
);

const selectTicket = (ticket) => {
    selectedTicket.value = ticket;
    resetForm();
};

const resetForm = () => {
    form.value = {
        action_type: "",
        new_team: "",
        new_assignee: "",
        force_tier: "",
        reason: "",
        resend_line: false,
        mark_model_incorrect: false
    };
};

const applyOverride = () => {
    pageError.value = "";
    successMessage.value = "";

    if (!selectedTicket.value) {
        pageError.value = "Please select a ticket first.";
        return;
    }

    if (!form.value.action_type) {
        pageError.value = "Please select override action.";
        return;
    }

    if (!form.value.reason.trim()) {
        pageError.value = "Please provide override reason.";
        return;
    }

    let targetValue = "-";

    if (form.value.action_type === "Reassign Team") {
        targetValue = form.value.new_team || "-";
        selectedTicket.value.team_name = form.value.new_team || selectedTicket.value.team_name;
    } else if (form.value.action_type === "Reassign User") {
        targetValue = form.value.new_assignee || "-";
        selectedTicket.value.assigned_user = form.value.new_assignee || selectedTicket.value.assigned_user;
    } else if (form.value.action_type === "Force Next Tier") {
        targetValue = form.value.force_tier || "-";
        selectedTicket.value.current_tier = form.value.force_tier || selectedTicket.value.current_tier;
        selectedTicket.value.status = "Escalated";
    } else if (form.value.action_type === "Resend Notification") {
        targetValue = selectedTicket.value.assigned_user || selectedTicket.value.team_name;
    }

    overrideHistory.value.unshift({
        id: Date.now(),
        created_at: new Date().toISOString(),
        ticket_no: selectedTicket.value.ticket_no,
        action_type: form.value.action_type,
        override_by: "Current Admin",
        target_value: targetValue,
        reason: form.value.reason.trim(),
        resend_line: form.value.resend_line,
        mark_model_incorrect: form.value.mark_model_incorrect
    });

    successMessage.value = `Manual override applied to ${selectedTicket.value.ticket_no}. (mock)`;
    resetForm();
};

const statusClass = (status) => {
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

const actionClass = (action) => {
    switch (action) {
        case "Reassign Team":
            return "type-team";
        case "Reassign User":
            return "type-user";
        case "Force Next Tier":
            return "type-tier";
        case "Resend Notification":
            return "type-resend";
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
    loadData();
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

.page-two-column {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 1rem;
    margin-bottom: 1rem;
}

.toolbar-search {
    position: relative;
    width: 100%;
}

.toolbar-search .p-inputtext {
    width: 100%;
    padding-left: 2.4rem;
}

.toolbar-search-icon {
    position: absolute;
    left: 0.85rem;
    top: 50%;
    transform: translateY(-50%);
    color: #64748b;
    z-index: 2;
}

.ticket-candidate-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 300px;
    overflow-y: auto;
}

.ticket-candidate-item {
    width: 100%;
    text-align: left;
    border: 1px solid var(--border-color);
    background: var(--card-bg);
    border-radius: 16px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.ticket-candidate-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-sm);
}

.ticket-candidate-item.active {
    border-color: #86efac;
    box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.14);
    background: #f0fdf4;
}

.ticket-candidate-top {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.35rem;
}

.ticket-candidate-no {
    font-weight: 700;
    color: var(--text-color);
}

.ticket-candidate-subject {
    color: var(--text-color);
    font-weight: 600;
    margin-bottom: 0.2rem;
}

.ticket-candidate-meta {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.selected-ticket-box {
    border: 1px solid var(--border-color);
    border-radius: 16px;
    background: var(--card-bg);
    padding: 1rem;
}

.selected-ticket-title {
    font-weight: 700;
    color: var(--text-color);
    margin-bottom: 0.25rem;
}

.selected-ticket-sub {
    color: var(--text-color);
    margin-bottom: 0.25rem;
}

.selected-ticket-meta {
    color: var(--text-muted);
    font-size: 0.92rem;
}

.checkbox-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem 1rem;
}

.checkbox-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    color: var(--text-color);
    font-weight: 500;
}

.notes-list {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
}

.note-item {
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    background: var(--card-bg);
}

.note-title {
    font-weight: 700;
    color: var(--text-color);
    margin-bottom: 0.3rem;
}

.note-desc {
    color: var(--text-muted);
    line-height: 1.45;
}

.history-reason {
    color: var(--text-color);
    line-height: 1.45;
}

.type-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
}

.type-team {
    background: #dbeafe;
    color: #1d4ed8;
}

.type-user {
    background: #dcfce7;
    color: #166534;
}

.type-tier {
    background: #fef3c7;
    color: #92400e;
}

.type-resend {
    background: #f3e8ff;
    color: #7e22ce;
}

.flag-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
}

.mini-flag {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.55rem;
    border-radius: 999px;
    background: #e0f2fe;
    color: #075985;
    font-size: 0.8rem;
    font-weight: 700;
}

.mini-flag.danger {
    background: #fee2e2;
    color: #991b1b;
}

.action-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
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

    .page-two-column {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .summary-grid,
    .checkbox-grid {
        grid-template-columns: 1fr;
    }
}
</style>