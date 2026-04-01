<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Reports & SLA</div>
                        <div class="page-subtitle">
                            Analyze SLA performance, escalation trends, and response efficiency.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Export CSV"
                            icon="pi pi-download"
                            severity="secondary"
                            outlined
                            @click="handleExport"
                        />
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadReports"
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

                <div class="toolbar-row">
                    <div class="toolbar-filters">
                        <Dropdown
                            v-model="teamFilter"
                            :options="teamOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Select Team"
                            class="filter-dropdown"
                        />
                        <Dropdown
                            v-model="periodFilter"
                            :options="periodOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Period"
                            class="filter-dropdown"
                        />
                    </div>

                    <div class="toolbar-note">
                        <span class="meta-text">
                            Team: <strong>{{ selectedTeamLabel }}</strong> |
                            Period: <strong>{{ selectedPeriodLabel }}</strong>
                        </span>
                    </div>
                </div>

                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Avg Email → LINE</div>
                        <div class="summary-value">{{ summary.avg_email_to_line }} min</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Avg LINE → Accepted</div>
                        <div class="summary-value">{{ summary.avg_line_to_accept }} min</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Escalated Tickets</div>
                        <div class="summary-value">{{ summary.escalated_count }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">No Acceptance</div>
                        <div class="summary-value">{{ summary.no_accept_count }}</div>
                    </div>
                </div>

                <div class="dashboard-grid">
                    <Card class="content-card">
                        <template #title>
                            <span>SLA Overview</span>
                        </template>

                        <template #content>
                            <Chart type="bar" :data="barChartData" :options="barChartOptions" />
                        </template>
                    </Card>

                    <Card class="content-card">
                        <template #title>
                            <span>Escalation Trend</span>
                        </template>

                        <template #content>
                            <Chart type="line" :data="lineChartData" :options="lineChartOptions" />
                        </template>
                    </Card>
                </div>

                <div class="dashboard-grid">
                    <Card class="content-card">
                        <template #title>
                            <span>Team SLA Breakdown</span>
                        </template>

                        <template #content>
                            <DataTable
                                :value="filteredTeamBreakdown"
                                dataKey="team_name"
                                responsiveLayout="scroll"
                                stripedRows
                            >
                                <Column field="team_name" header="Team" style="min-width: 180px" />
                                <Column field="ticket_count" header="Tickets" style="min-width: 120px" />
                                <Column field="avg_email_to_line" header="Email → LINE" style="min-width: 140px">
                                    <template #body="{ data }">
                                        {{ data.avg_email_to_line }} min
                                    </template>
                                </Column>
                                <Column field="avg_line_to_accept" header="LINE → Accept" style="min-width: 150px">
                                    <template #body="{ data }">
                                        {{ data.avg_line_to_accept }} min
                                    </template>
                                </Column>
                                <Column field="escalated_count" header="Escalated" style="min-width: 120px" />
                                <Column field="no_accept_count" header="No Acceptance" style="min-width: 140px" />
                            </DataTable>
                        </template>
                    </Card>

                    <Card class="content-card">
                        <template #title>
                            <span>Top Attention Items</span>
                        </template>

                        <template #content>
                            <div class="attention-list">
                                <div
                                    v-for="item in attentionItems"
                                    :key="item.id"
                                    class="attention-item"
                                >
                                    <div class="attention-top">
                                        <div class="attention-title">{{ item.title }}</div>
                                        <span
                                            class="status-badge"
                                            :class="item.level === 'High' ? 'status-inactive' : 'status-pending'"
                                        >
                                            {{ item.level }}
                                        </span>
                                    </div>

                                    <div class="attention-desc">{{ item.description }}</div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>

                <Card class="content-card">
                    <template #title>
                        <span>Detailed Ticket SLA</span>
                    </template>

                    <template #content>
                        <DataTable
                            :value="filteredTicketSla"
                            dataKey="ticket_no"
                            paginator
                            :rows="10"
                            responsiveLayout="scroll"
                            stripedRows
                        >
                            <Column field="ticket_no" header="Ticket No" style="min-width: 140px" />
                            <Column field="team_name" header="Team" style="min-width: 180px" />
                            <Column field="subject" header="Subject" style="min-width: 280px" />
                            <Column header="Email → LINE" style="min-width: 140px">
                                <template #body="{ data }">
                                    {{ data.email_to_line_min }} min
                                </template>
                            </Column>
                            <Column header="LINE → Accept" style="min-width: 150px">
                                <template #body="{ data }">
                                    {{ data.line_to_accept_min }} min
                                </template>
                            </Column>
                            <Column field="escalation_level" header="Escalation" style="min-width: 120px" />
                            <Column header="Status" style="min-width: 140px">
                                <template #body="{ data }">
                                    <span class="status-badge" :class="ticketStatusClass(data.status)">
                                        {{ data.status }}
                                    </span>
                                </template>
                            </Column>
                        </DataTable>
                    </template>
                </Card>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for SLA reporting, response analytics, escalation trend, and export workflow.
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

const pageError = ref("");
const successMessage = ref("");
const teamFilter = ref("all");
const periodFilter = ref("today");

const teamOptions = [
    { label: "All Teams", value: "all" },
    { label: "Cloud Operations", value: "Cloud Operations" },
    { label: "Security Operations", value: "Security Operations" },
    { label: "Standby Support", value: "Standby Support" }
];

const periodOptions = [
    { label: "Today", value: "today" },
    { label: "Last 7 Days", value: "7d" },
    { label: "Last 30 Days", value: "30d" }
];

const teamBreakdown = ref([]);
const ticketSla = ref([]);
const attentionItems = ref([]);

const mockTeamBreakdown = [
    {
        team_name: "Cloud Operations",
        ticket_count: 42,
        avg_email_to_line: 3,
        avg_line_to_accept: 7,
        escalated_count: 4,
        no_accept_count: 1
    },
    {
        team_name: "Security Operations",
        ticket_count: 28,
        avg_email_to_line: 4,
        avg_line_to_accept: 11,
        escalated_count: 7,
        no_accept_count: 2
    },
    {
        team_name: "Standby Support",
        ticket_count: 19,
        avg_email_to_line: 2,
        avg_line_to_accept: 6,
        escalated_count: 3,
        no_accept_count: 1
    }
];

const mockTicketSla = [
    {
        ticket_no: "INC000123",
        team_name: "Cloud Operations",
        subject: "Cannot access AWS console",
        email_to_line_min: 2,
        line_to_accept_min: 5,
        escalation_level: "Tier 1",
        status: "Accepted"
    },
    {
        ticket_no: "INC000124",
        team_name: "Security Operations",
        subject: "Production alert on API gateway",
        email_to_line_min: 4,
        line_to_accept_min: 14,
        escalation_level: "Tier 2",
        status: "Escalated"
    },
    {
        ticket_no: "RITM000245",
        team_name: "Standby Support",
        subject: "Request standby escalation review",
        email_to_line_min: 1,
        line_to_accept_min: 4,
        escalation_level: "Tier 1",
        status: "Accepted"
    },
    {
        ticket_no: "TASK000981",
        team_name: "Security Operations",
        subject: "Investigate suspicious login attempt",
        email_to_line_min: 3,
        line_to_accept_min: 18,
        escalation_level: "Tier 3",
        status: "No Acceptance"
    }
];

const mockAttentionItems = [
    {
        id: 1,
        title: "Security Operations response time increased",
        description: "Average LINE → Accept time is above normal baseline in the selected period.",
        level: "High"
    },
    {
        id: 2,
        title: "Repeated escalation observed",
        description: "Several tickets escalated to Tier 2 and Tier 3 in Security Operations.",
        level: "High"
    },
    {
        id: 3,
        title: "Coverage gap detected",
        description: "Standby Support had one time slot with no acceptance response.",
        level: "Medium"
    }
];

const loadReports = () => {
    pageError.value = "";
    successMessage.value = "";

    try {
        teamBreakdown.value = [...mockTeamBreakdown];
        ticketSla.value = [...mockTicketSla];
        attentionItems.value = [...mockAttentionItems];
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load SLA report data.";
    }
};

const filteredTeamBreakdown = computed(() => {
    if (teamFilter.value === "all") return teamBreakdown.value;
    return teamBreakdown.value.filter((item) => item.team_name === teamFilter.value);
});

const filteredTicketSla = computed(() => {
    if (teamFilter.value === "all") return ticketSla.value;
    return ticketSla.value.filter((item) => item.team_name === teamFilter.value);
});

const selectedTeamLabel = computed(() => {
    return teamOptions.find((item) => item.value === teamFilter.value)?.label || "All Teams";
});

const selectedPeriodLabel = computed(() => {
    return periodOptions.find((item) => item.value === periodFilter.value)?.label || "-";
});

const summary = computed(() => {
    const teams = filteredTeamBreakdown.value;

    if (!teams.length) {
        return {
            avg_email_to_line: 0,
            avg_line_to_accept: 0,
            escalated_count: 0,
            no_accept_count: 0
        };
    }

    const totalEmailToLine = teams.reduce((sum, item) => sum + item.avg_email_to_line, 0);
    const totalLineToAccept = teams.reduce((sum, item) => sum + item.avg_line_to_accept, 0);
    const totalEscalated = teams.reduce((sum, item) => sum + item.escalated_count, 0);
    const totalNoAccept = teams.reduce((sum, item) => sum + item.no_accept_count, 0);

    return {
        avg_email_to_line: Math.round((totalEmailToLine / teams.length) * 10) / 10,
        avg_line_to_accept: Math.round((totalLineToAccept / teams.length) * 10) / 10,
        escalated_count: totalEscalated,
        no_accept_count: totalNoAccept
    };
});

const barChartData = computed(() => ({
    labels: filteredTeamBreakdown.value.map((item) => item.team_name),
    datasets: [
        {
            label: "Email → LINE (min)",
            data: filteredTeamBreakdown.value.map((item) => item.avg_email_to_line)
        },
        {
            label: "LINE → Accept (min)",
            data: filteredTeamBreakdown.value.map((item) => item.avg_line_to_accept)
        }
    ]
}));

const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: "top"
        }
    }
};

const lineChartData = computed(() => ({
    labels: ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"],
    datasets: [
        {
            label: "Escalated Tickets",
            data: [1, 2, 1, 3, 2, 4, 3]
        },
        {
            label: "No Acceptance",
            data: [0, 1, 0, 1, 1, 1, 2]
        }
    ]
}));

const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: "top"
        }
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

const handleExport = () => {
    successMessage.value = "Export CSV clicked. (mock)";
};

onMounted(() => {
    loadReports();
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

.toolbar-row {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.toolbar-filters {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.filter-dropdown {
    min-width: 180px;
}

.toolbar-note {
    display: flex;
    align-items: center;
}

.meta-text {
    color: var(--text-muted);
    font-size: 0.95rem;
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

.attention-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.attention-item {
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1rem;
    background: var(--card-bg);
}

.attention-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.35rem;
}

.attention-title {
    font-weight: 700;
    color: var(--text-color);
}

.attention-desc {
    color: var(--text-color);
    line-height: 1.45;
}

.status-pending {
    background: #fef3c7;
    color: #92400e;
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
}
</style>