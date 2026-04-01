<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Acceptance Monitor</div>
                        <div class="page-subtitle">
                            Monitor tickets waiting for acceptance, escalation progress, and response risk.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Auto Refresh"
                            :icon="autoRefresh ? 'pi pi-pause' : 'pi pi-refresh'"
                            severity="secondary"
                            outlined
                            @click="toggleAutoRefresh"
                        />
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadMonitorData"
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
                        <div class="summary-label">Waiting Acceptance</div>
                        <div class="summary-value">{{ waitingCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Escalated</div>
                        <div class="summary-value">{{ escalatedCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Near Timeout</div>
                        <div class="summary-value">{{ nearTimeoutCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Accepted</div>
                        <div class="summary-value">{{ acceptedCount }}</div>
                    </div>
                </div>

                <div class="toolbar-row">
                    <div class="toolbar-search">
                        <i class="pi pi-search toolbar-search-icon"></i>
                        <InputText
                            v-model="searchText"
                            placeholder="Search ticket no, subject, team, user..."
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
                            v-model="riskFilter"
                            :options="riskOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Risk"
                            class="filter-dropdown"
                        />
                    </div>
                </div>

                <div class="dashboard-grid">
                    <Card class="content-card">
                        <template #title>
                            <span>Live Queue</span>
                        </template>

                        <template #content>
                            <DataTable
                                :value="filteredQueue"
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

                                <Column field="subject" header="Subject" style="min-width: 260px">
                                    <template #body="{ data }">
                                        <div class="ticket-subject">{{ data.subject }}</div>
                                        <div class="ticket-sub">{{ data.team_name }}</div>
                                    </template>
                                </Column>

                                <Column field="current_tier" header="Current Tier" style="min-width: 120px" />

                                <Column field="last_notified_user" header="Last Notified" style="min-width: 180px">
                                    <template #body="{ data }">
                                        {{ data.last_notified_user || "-" }}
                                    </template>
                                </Column>

                                <Column field="elapsed_min" header="Elapsed" style="min-width: 120px">
                                    <template #body="{ data }">
                                        {{ data.elapsed_min }} min
                                    </template>
                                </Column>

                                <Column field="countdown_sec" header="Next Escalation" style="min-width: 150px">
                                    <template #body="{ data }">
                                        <span
                                            class="countdown-chip"
                                            :class="countdownClass(data)"
                                        >
                                            {{ formatCountdown(data.countdown_sec) }}
                                        </span>
                                    </template>
                                </Column>

                                <Column field="risk_level" header="Risk" style="min-width: 120px">
                                    <template #body="{ data }">
                                        <span class="risk-chip" :class="riskClass(data.risk_level)">
                                            {{ data.risk_level }}
                                        </span>
                                    </template>
                                </Column>

                                <Column header="Status" style="min-width: 140px">
                                    <template #body="{ data }">
                                        <span class="status-badge" :class="statusClass(data.status)">
                                            {{ data.status }}
                                        </span>
                                    </template>
                                </Column>

                                <Column header="Action" style="min-width: 130px">
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
                                        No monitored tickets found.
                                    </div>
                                </template>
                            </DataTable>
                        </template>
                    </Card>

                    <Card class="content-card">
                        <template #title>
                            <span>Watchlist</span>
                        </template>

                        <template #content>
                            <div class="watchlist">
                                <div
                                    v-for="item in watchlistItems"
                                    :key="item.ticket_no"
                                    class="watch-item"
                                >
                                    <div class="watch-top">
                                        <div class="watch-ticket">{{ item.ticket_no }}</div>
                                        <span class="risk-chip" :class="riskClass(item.risk_level)">
                                            {{ item.risk_level }}
                                        </span>
                                    </div>

                                    <div class="watch-subject">{{ item.subject }}</div>
                                    <div class="watch-meta">
                                        Team: {{ item.team_name }} | Tier: {{ item.current_tier }}
                                    </div>
                                    <div class="watch-meta">
                                        Last notified: {{ item.last_notified_user || "-" }}
                                    </div>
                                    <div class="watch-meta">
                                        Countdown: {{ formatCountdown(item.countdown_sec) }}
                                    </div>
                                </div>

                                <div v-if="watchlistItems.length === 0" class="empty-box">
                                    No attention items right now.
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>

                <Card class="content-card">
                    <template #title>
                        <span>Tier Summary</span>
                    </template>

                    <template #content>
                        <div class="tier-summary-grid">
                            <div class="tier-box">
                                <div class="tier-title">Tier 1</div>
                                <div class="tier-value">{{ tier1Count }}</div>
                                <div class="tier-desc">Currently in first-level notification</div>
                            </div>

                            <div class="tier-box">
                                <div class="tier-title">Tier 2</div>
                                <div class="tier-value">{{ tier2Count }}</div>
                                <div class="tier-desc">Escalated from Tier 1</div>
                            </div>

                            <div class="tier-box">
                                <div class="tier-title">Tier 3</div>
                                <div class="tier-value">{{ tier3Count }}</div>
                                <div class="tier-desc">Final escalation stage</div>
                            </div>
                        </div>
                    </template>
                </Card>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for live queue monitoring, countdown timer, escalation tracking, and operator watchlist workflow.
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const pageError = ref("");
const successMessage = ref("");
const searchText = ref("");
const teamFilter = ref("all");
const statusFilter = ref("all");
const riskFilter = ref("all");
const autoRefresh = ref(false);
const queueItems = ref([]);
let timer = null;

const teamOptions = [
    { label: "All Teams", value: "all" },
    { label: "Cloud Operations", value: "Cloud Operations" },
    { label: "Security Operations", value: "Security Operations" },
    { label: "Standby Support", value: "Standby Support" }
];

const statusOptions = [
    { label: "All Status", value: "all" },
    { label: "Pending", value: "Pending" },
    { label: "Escalated", value: "Escalated" },
    { label: "Accepted", value: "Accepted" },
    { label: "Timeout", value: "Timeout" }
];

const riskOptions = [
    { label: "All Risk", value: "all" },
    { label: "High", value: "High" },
    { label: "Medium", value: "Medium" },
    { label: "Low", value: "Low" }
];

const mockQueue = [
    {
        ticket_no: "INC000123",
        subject: "Cannot access AWS console",
        team_name: "Cloud Operations",
        current_tier: "Tier 1",
        last_notified_user: "Admin User",
        elapsed_min: 4,
        countdown_sec: 80,
        risk_level: "Medium",
        status: "Pending"
    },
    {
        ticket_no: "INC000124",
        subject: "Production alert on API gateway",
        team_name: "Security Operations",
        current_tier: "Tier 2",
        last_notified_user: "Super Admin",
        elapsed_min: 12,
        countdown_sec: 25,
        risk_level: "High",
        status: "Escalated"
    },
    {
        ticket_no: "RITM000245",
        subject: "Request standby escalation review",
        team_name: "Standby Support",
        current_tier: "Tier 1",
        last_notified_user: "User One",
        elapsed_min: 2,
        countdown_sec: 150,
        risk_level: "Low",
        status: "Accepted"
    },
    {
        ticket_no: "TASK000981",
        subject: "Investigate suspicious login attempt",
        team_name: "Security Operations",
        current_tier: "Tier 3",
        last_notified_user: "Ploy Jinda",
        elapsed_min: 18,
        countdown_sec: 0,
        risk_level: "High",
        status: "Timeout"
    },
    {
        ticket_no: "CTASK000321",
        subject: "Check standby calendar mismatch",
        team_name: "Cloud Operations",
        current_tier: "Tier 1",
        last_notified_user: "Narin Sukjai",
        elapsed_min: 6,
        countdown_sec: 45,
        risk_level: "High",
        status: "Pending"
    }
];

const loadMonitorData = () => {
    pageError.value = "";
    successMessage.value = "";

    try {
        queueItems.value = mockQueue.map((item) => ({ ...item }));
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load acceptance monitor data.";
    }
};

const filteredQueue = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    return queueItems.value.filter((item) => {
        const matchKeyword = !keyword
            ? true
            : [
                  item.ticket_no,
                  item.subject,
                  item.team_name,
                  item.current_tier,
                  item.last_notified_user,
                  item.status
              ]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        const matchTeam =
            teamFilter.value === "all" ? true : item.team_name === teamFilter.value;

        const matchStatus =
            statusFilter.value === "all" ? true : item.status === statusFilter.value;

        const matchRisk =
            riskFilter.value === "all" ? true : item.risk_level === riskFilter.value;

        return matchKeyword && matchTeam && matchStatus && matchRisk;
    });
});

const waitingCount = computed(() =>
    filteredQueue.value.filter((item) => item.status === "Pending").length
);

const escalatedCount = computed(() =>
    filteredQueue.value.filter((item) => item.status === "Escalated").length
);

const nearTimeoutCount = computed(() =>
    filteredQueue.value.filter(
        (item) =>
            (item.status === "Pending" || item.status === "Escalated") &&
            item.countdown_sec > 0 &&
            item.countdown_sec <= 60
    ).length
);

const acceptedCount = computed(() =>
    filteredQueue.value.filter((item) => item.status === "Accepted").length
);

const tier1Count = computed(() =>
    filteredQueue.value.filter((item) => item.current_tier === "Tier 1").length
);

const tier2Count = computed(() =>
    filteredQueue.value.filter((item) => item.current_tier === "Tier 2").length
);

const tier3Count = computed(() =>
    filteredQueue.value.filter((item) => item.current_tier === "Tier 3").length
);

const watchlistItems = computed(() =>
    filteredQueue.value.filter(
        (item) =>
            item.risk_level === "High" ||
            item.status === "Timeout" ||
            (item.countdown_sec > 0 && item.countdown_sec <= 60)
    )
);

const formatCountdown = (seconds) => {
    if (seconds <= 0) return "Now";
    const min = Math.floor(seconds / 60);
    const sec = seconds % 60;
    return `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
};

const riskClass = (risk) => {
    switch (risk) {
        case "High":
            return "risk-high";
        case "Medium":
            return "risk-medium";
        case "Low":
            return "risk-low";
        default:
            return "";
    }
};

const statusClass = (status) => {
    switch (status) {
        case "Accepted":
            return "status-active";
        case "Escalated":
            return "status-pending";
        case "Timeout":
            return "status-inactive";
        default:
            return "status-pending";
    }
};

const countdownClass = (item) => {
    if (item.countdown_sec <= 0) return "countdown-expired";
    if (item.countdown_sec <= 60) return "countdown-warning";
    return "countdown-normal";
};

const tickCountdown = () => {
    queueItems.value = queueItems.value.map((item) => {
        if (item.status === "Pending" || item.status === "Escalated") {
            const nextCountdown = Math.max(0, item.countdown_sec - 1);
            return {
                ...item,
                countdown_sec: nextCountdown
            };
        }
        return item;
    });
};

const startTimer = () => {
    stopTimer();
    timer = setInterval(() => {
        tickCountdown();
    }, 1000);
};

const stopTimer = () => {
    if (timer) {
        clearInterval(timer);
        timer = null;
    }
};

const toggleAutoRefresh = () => {
    autoRefresh.value = !autoRefresh.value;

    if (autoRefresh.value) {
        startTimer();
        successMessage.value = "Auto refresh enabled. (mock)";
    } else {
        stopTimer();
        successMessage.value = "Auto refresh paused. (mock)";
    }
};

const openTicket = (ticket) => {
    router.push({
        path: "/ticket-detail",
        query: { ticketNo: ticket.ticket_no }
    });
};

onMounted(() => {
    loadMonitorData();
});

onBeforeUnmount(() => {
    stopTimer();
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

.watchlist {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.watch-item {
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1rem;
    background: var(--card-bg);
}

.watch-top {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.35rem;
}

.watch-ticket {
    font-weight: 700;
    color: var(--text-color);
}

.watch-subject {
    color: var(--text-color);
    font-weight: 600;
    margin-bottom: 0.35rem;
}

.watch-meta {
    color: var(--text-muted);
    font-size: 0.92rem;
    margin-top: 0.15rem;
}

.tier-summary-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
}

.tier-box {
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1rem;
    background: var(--card-bg);
}

.tier-title {
    font-weight: 700;
    color: var(--text-color);
    margin-bottom: 0.35rem;
}

.tier-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-color);
    margin-bottom: 0.35rem;
}

.tier-desc {
    color: var(--text-muted);
    line-height: 1.45;
}

.risk-chip,
.countdown-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
}

.risk-high {
    background: #fee2e2;
    color: #991b1b;
}

.risk-medium {
    background: #fef3c7;
    color: #92400e;
}

.risk-low {
    background: #dcfce7;
    color: #166534;
}

.countdown-normal {
    background: #dbeafe;
    color: #1d4ed8;
}

.countdown-warning {
    background: #fef3c7;
    color: #92400e;
}

.countdown-expired {
    background: #fee2e2;
    color: #991b1b;
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

@media (max-width: 1200px) {
    .summary-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .tier-summary-grid {
        grid-template-columns: 1fr;
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