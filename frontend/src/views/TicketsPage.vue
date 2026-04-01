<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Tickets</div>
                        <div class="page-subtitle">
                            View and monitor all tickets across teams, status, and escalation flow.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadTickets"
                        />
                    </div>
                </div>
            </template>

            <template #content>
                <Message v-if="pageError" severity="error" class="mb-3">
                    {{ pageError }}
                </Message>

                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Total Tickets</div>
                        <div class="summary-value">{{ filteredTickets.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Pending</div>
                        <div class="summary-value">{{ pendingCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Accepted</div>
                        <div class="summary-value">{{ acceptedCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Escalated</div>
                        <div class="summary-value">{{ escalatedCount }}</div>
                    </div>
                </div>

                <div class="toolbar-row">
                    <div class="toolbar-search">
                        <i class="pi pi-search toolbar-search-icon"></i>
                        <InputText
                            v-model="searchText"
                            placeholder="Search ticket no, subject, requester, email, IP..."
                        />
                    </div>

                    <div class="toolbar-filters">
                        <Dropdown
                            v-model="teamFilter"
                            :options="teamOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Team"
                            class="filter-dropdown"
                        />
                        <Dropdown
                            v-model="statusFilter"
                            :options="statusOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Status"
                            class="filter-dropdown"
                        />
                        <Dropdown
                            v-model="priorityFilter"
                            :options="priorityOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Priority"
                            class="filter-dropdown"
                        />
                        <Dropdown
                            v-model="acceptFilter"
                            :options="acceptOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Accepted"
                            class="filter-dropdown"
                        />
                        <Dropdown
                            v-model="escalationFilter"
                            :options="escalationOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Escalation"
                            class="filter-dropdown"
                        />
                    </div>
                </div>

                <DataTable
                    :value="filteredTickets"
                    dataKey="ticket_no"
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

                    <Column field="ticket_no" header="Ticket No" style="min-width: 140px" />
                    <Column field="subject" header="Subject" style="min-width: 280px">
                        <template #body="{ data }">
                            <div class="ticket-subject">{{ data.subject }}</div>
                            <div class="ticket-sub">{{ data.requester_email }}</div>
                        </template>
                    </Column>

                    <Column field="team_name" header="Team" style="min-width: 170px" />
                    <Column field="decision_mode" header="Decision" style="min-width: 140px">
                        <template #body="{ data }">
                            {{ data.decision_mode || "-" }}
                        </template>
                    </Column>

                    <Column field="confidence" header="Confidence" style="min-width: 130px">
                        <template #body="{ data }">
                            {{ data.confidence }}%
                        </template>
                    </Column>

                    <Column field="assigned_user" header="Accepted By" style="min-width: 170px">
                        <template #body="{ data }">
                            {{ data.assigned_user || "-" }}
                        </template>
                    </Column>

                    <Column field="current_tier" header="Tier" style="min-width: 110px" />
                    <Column field="elapsed" header="Elapsed" style="min-width: 110px" />
                    <Column field="priority" header="Priority" style="min-width: 120px">
                        <template #body="{ data }">
                            <span class="priority-chip" :class="priorityClass(data.priority)">
                                {{ data.priority }}
                            </span>
                        </template>
                    </Column>

                    <Column header="Status" style="min-width: 150px">
                        <template #body="{ data }">
                            <span class="status-badge" :class="ticketStatusClass(data.status)">
                                {{ data.status }}
                            </span>
                        </template>
                    </Column>

                    <Column header="Actions" style="min-width: 140px">
                        <template #body="{ data }">
                            <Button
                                label="Open"
                                icon="pi pi-arrow-right"
                                size="small"
                                @click="openTicket(data)"
                            />
                        </template>
                    </Column>

                    <template #empty>
                        <div class="empty-box">
                            No tickets found.
                        </div>
                    </template>
                </DataTable>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for ticket search, filtering, acceptance monitoring, and routing workflow.
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const pageError = ref("");
const searchText = ref("");
const teamFilter = ref("all");
const statusFilter = ref("all");
const priorityFilter = ref("all");
const acceptFilter = ref("all");
const escalationFilter = ref("all");
const tickets = ref([]);

const teamOptions = [
    { label: "All Teams", value: "all" },
    { label: "Cloud Operations", value: "Cloud Operations" },
    { label: "Security Operations", value: "Security Operations" },
    { label: "Standby Support", value: "Standby Support" }
];

const statusOptions = [
    { label: "All Status", value: "all" },
    { label: "Pending", value: "Pending" },
    { label: "Accepted", value: "Accepted" },
    { label: "Escalated", value: "Escalated" },
    { label: "No Acceptance", value: "No Acceptance" }
];

const priorityOptions = [
    { label: "All Priority", value: "all" },
    { label: "High", value: "High" },
    { label: "Medium", value: "Medium" },
    { label: "Low", value: "Low" }
];

const acceptOptions = [
    { label: "All", value: "all" },
    { label: "Accepted", value: "accepted" },
    { label: "Not Accepted", value: "not_accepted" }
];

const escalationOptions = [
    { label: "All", value: "all" },
    { label: "Escalated", value: "escalated" },
    { label: "Not Escalated", value: "not_escalated" }
];

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
        first_notified_user: "Admin User",
        assigned_user: "",
        current_tier: "Tier 1",
        elapsed: "04m",
        priority: "High",
        status: "Pending",
        is_accepted: false,
        is_escalated: false
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
        first_notified_user: "Super Admin",
        assigned_user: "",
        current_tier: "Tier 2",
        elapsed: "12m",
        priority: "High",
        status: "Escalated",
        is_accepted: false,
        is_escalated: true
    },
    {
        ticket_no: "RITM000245",
        subject: "Request standby escalation review",
        requester_name: "Admin User",
        requester_email: "admin@company.com",
        requester_ip: "10.10.3.44",
        team_name: "Standby Support",
        decision_mode: "Manual",
        confidence: 100,
        first_notified_user: "User One",
        assigned_user: "Krit Meechai",
        current_tier: "Tier 1",
        elapsed: "02m",
        priority: "Medium",
        status: "Accepted",
        is_accepted: true,
        is_escalated: false
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
        first_notified_user: "Ploy Jinda",
        assigned_user: "",
        current_tier: "Tier 3",
        elapsed: "18m",
        priority: "High",
        status: "No Acceptance",
        is_accepted: false,
        is_escalated: true
    },
    {
        ticket_no: "CTASK000321",
        subject: "Check standby calendar mismatch",
        requester_name: "Narin Sukjai",
        requester_email: "narin@company.com",
        requester_ip: "10.10.5.77",
        team_name: "Cloud Operations",
        decision_mode: "Rule-based",
        confidence: 81,
        first_notified_user: "Admin User",
        assigned_user: "Admin User",
        current_tier: "Tier 1",
        elapsed: "06m",
        priority: "Low",
        status: "Accepted",
        is_accepted: true,
        is_escalated: false
    }
];

const loadTickets = () => {
    pageError.value = "";

    try {
        tickets.value = [...mockTickets];
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load tickets.";
    }
};

const filteredTickets = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    return tickets.value.filter((item) => {
        const matchKeyword = !keyword
            ? true
            : [
                  item.ticket_no,
                  item.subject,
                  item.requester_name,
                  item.requester_email,
                  item.requester_ip,
                  item.team_name,
                  item.assigned_user
              ]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        const matchTeam =
            teamFilter.value === "all" ? true : item.team_name === teamFilter.value;

        const matchStatus =
            statusFilter.value === "all" ? true : item.status === statusFilter.value;

        const matchPriority =
            priorityFilter.value === "all" ? true : item.priority === priorityFilter.value;

        const matchAccepted =
            acceptFilter.value === "all"
                ? true
                : acceptFilter.value === "accepted"
                ? item.is_accepted
                : !item.is_accepted;

        const matchEscalation =
            escalationFilter.value === "all"
                ? true
                : escalationFilter.value === "escalated"
                ? item.is_escalated
                : !item.is_escalated;

        return (
            matchKeyword &&
            matchTeam &&
            matchStatus &&
            matchPriority &&
            matchAccepted &&
            matchEscalation
        );
    });
});

const pendingCount = computed(() =>
    filteredTickets.value.filter((item) => item.status === "Pending").length
);

const acceptedCount = computed(() =>
    filteredTickets.value.filter((item) => item.status === "Accepted").length
);

const escalatedCount = computed(() =>
    filteredTickets.value.filter((item) => item.status === "Escalated").length
);

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

const openTicket = (ticket) => {
    router.push({
        path: "/ticket-detail",
        query: { ticketNo: ticket.ticket_no }
    });
};

onMounted(() => {
    loadTickets();
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

.toolbar-row {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.toolbar-search {
    position: relative;
    width: 100%;
    max-width: 360px;
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

.toolbar-filters {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.filter-dropdown {
    min-width: 170px;
}

.ticket-subject {
    font-weight: 600;
    color: var(--text-color);
}

.ticket-sub {
    font-size: 0.88rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
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
    .summary-grid {
        grid-template-columns: 1fr;
    }

    .toolbar-search {
        max-width: 100%;
    }
}
</style>