<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">LINE Monitoring</div>
                        <div class="page-subtitle">
                            Monitor LINE bot status, group activity, and recent event logs.
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

                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Groups</div>
                        <div class="summary-value">{{ groups.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Events Today</div>
                        <div class="summary-value">{{ events.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Success Events</div>
                        <div class="summary-value">{{ successCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Failed Events</div>
                        <div class="summary-value">{{ failedCount }}</div>
                    </div>
                </div>

                <div class="status-grid">
                    <Card class="content-card">
                        <template #title>
                            <span>Bot Status</span>
                        </template>

                        <template #content>
                            <div class="status-list">
                                <div class="status-item">
                                    <div class="status-label">LINE Bot</div>
                                    <span
                                        class="status-badge"
                                        :class="botStatus.bot_online ? 'status-active' : 'status-inactive'"
                                    >
                                        {{ botStatus.bot_online ? "Online" : "Offline" }}
                                    </span>
                                </div>

                                <div class="status-item">
                                    <div class="status-label">Webhook</div>
                                    <span
                                        class="status-badge"
                                        :class="botStatus.webhook_ok ? 'status-active' : 'status-inactive'"
                                    >
                                        {{ botStatus.webhook_ok ? "Connected" : "Disconnected" }}
                                    </span>
                                </div>

                                <div class="status-item">
                                    <div class="status-label">Messaging API</div>
                                    <span
                                        class="status-badge"
                                        :class="botStatus.messaging_api_ok ? 'status-active' : 'status-inactive'"
                                    >
                                        {{ botStatus.messaging_api_ok ? "Healthy" : "Issue" }}
                                    </span>
                                </div>

                                <div class="status-item">
                                    <div class="status-label">Last Sync</div>
                                    <div class="status-value">{{ formatDateTime(botStatus.last_sync_at) }}</div>
                                </div>
                            </div>
                        </template>
                    </Card>

                    <Card class="content-card">
                        <template #title>
                            <span>Recent Metrics</span>
                        </template>

                        <template #content>
                            <div class="metric-list">
                                <div class="metric-item">
                                    <div class="metric-label">Join Events</div>
                                    <div class="metric-value">{{ metrics.join_events }}</div>
                                </div>
                                <div class="metric-item">
                                    <div class="metric-label">Leave Events</div>
                                    <div class="metric-value">{{ metrics.leave_events }}</div>
                                </div>
                                <div class="metric-item">
                                    <div class="metric-label">Accept Actions</div>
                                    <div class="metric-value">{{ metrics.accept_events }}</div>
                                </div>
                                <div class="metric-item">
                                    <div class="metric-label">Duplicate Events</div>
                                    <div class="metric-value">{{ metrics.duplicate_events }}</div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>

                <div class="page-two-column">
                    <Card class="content-card">
                        <template #title>
                            <span>LINE Groups</span>
                        </template>

                        <template #content>
                            <div class="toolbar-search mb-3">
                                <i class="pi pi-search toolbar-search-icon"></i>
                                <InputText
                                    v-model="groupSearch"
                                    placeholder="Search group name..."
                                />
                            </div>

                            <div class="group-list">
                                <button
                                    v-for="group in filteredGroups"
                                    :key="group.id"
                                    type="button"
                                    class="group-item"
                                    :class="{ active: selectedGroup?.id === group.id }"
                                    @click="selectGroup(group)"
                                >
                                    <div class="group-item-top">
                                        <div class="group-name">{{ group.name }}</div>
                                        <span
                                            class="status-badge"
                                            :class="group.bot_in_group ? 'status-active' : 'status-inactive'"
                                        >
                                            {{ group.bot_in_group ? "In Group" : "Left" }}
                                        </span>
                                    </div>

                                    <div class="group-sub">
                                        Members: {{ group.member_count }}
                                    </div>

                                    <div class="group-sub">
                                        Last Activity: {{ formatDateTime(group.last_activity_at) }}
                                    </div>
                                </button>

                                <div v-if="filteredGroups.length === 0" class="empty-box">
                                    No groups found.
                                </div>
                            </div>
                        </template>
                    </Card>

                    <Card class="content-card">
                        <template #title>
                            <span>{{ selectedGroup?.name || "Group Detail" }}</span>
                        </template>

                        <template #content>
                            <template v-if="selectedGroup">
                                <div class="detail-grid">
                                    <div class="info-box">
                                        <div class="info-label">Group Name</div>
                                        <div class="info-value">{{ selectedGroup.name }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Group ID</div>
                                        <div class="info-value">{{ selectedGroup.id }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Members</div>
                                        <div class="info-value">{{ selectedGroup.member_count }}</div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Last Activity</div>
                                        <div class="info-value">{{ formatDateTime(selectedGroup.last_activity_at) }}</div>
                                    </div>
                                </div>

                                <div class="mock-note mt-3">
                                    This group detail section is prepared for future backend integration
                                    such as member list, message trace, and per-group event history.
                                </div>
                            </template>

                            <div v-else class="empty-box large">
                                Select a group to view details.
                            </div>
                        </template>
                    </Card>
                </div>

                <Card class="content-card">
                    <template #title>
                        <div class="section-header">
                            <span>Event Log</span>
                        </div>
                    </template>

                    <template #content>
                        <div class="toolbar-row">
                            <div class="toolbar-search">
                                <i class="pi pi-search toolbar-search-icon"></i>
                                <InputText
                                    v-model="eventSearch"
                                    placeholder="Search event, group, user..."
                                />
                            </div>

                            <div class="toolbar-filters">
                                <Dropdown
                                    v-model="typeFilter"
                                    :options="typeOptions"
                                    optionLabel="label"
                                    optionValue="value"
                                    placeholder="Event Type"
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
                            </div>
                        </div>

                        <DataTable
                            :value="filteredEvents"
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

                            <Column field="event_type" header="Event Type" style="min-width: 150px">
                                <template #body="{ data }">
                                    <span class="event-type-chip" :class="eventTypeClass(data.event_type)">
                                        {{ data.event_type }}
                                    </span>
                                </template>
                            </Column>

                            <Column field="group_name" header="Group" style="min-width: 220px" />

                            <Column field="actor_name" header="Actor" style="min-width: 180px">
                                <template #body="{ data }">
                                    {{ data.actor_name || "-" }}
                                </template>
                            </Column>

                            <Column field="message" header="Message" style="min-width: 320px">
                                <template #body="{ data }">
                                    {{ data.message || "-" }}
                                </template>
                            </Column>

                            <Column header="Status" style="min-width: 130px">
                                <template #body="{ data }">
                                    <span
                                        class="status-badge"
                                        :class="data.success ? 'status-active' : 'status-inactive'"
                                    >
                                        {{ data.success ? "Success" : "Failed" }}
                                    </span>
                                </template>
                            </Column>

                            <Column field="created_at" header="Time" style="min-width: 180px">
                                <template #body="{ data }">
                                    {{ formatDateTime(data.created_at) }}
                                </template>
                            </Column>

                            <template #empty>
                                <div class="empty-box">
                                    No event logs found.
                                </div>
                            </template>
                        </DataTable>
                    </template>
                </Card>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend
                    integration for LINE webhook logs, delivery result, and group activity tracking.
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

const pageError = ref("");
const groupSearch = ref("");
const eventSearch = ref("");
const typeFilter = ref("all");
const statusFilter = ref("all");

const botStatus = ref({
    bot_online: true,
    webhook_ok: true,
    messaging_api_ok: true,
    last_sync_at: "2026-04-01T10:25:00Z"
});

const metrics = ref({
    join_events: 4,
    leave_events: 1,
    accept_events: 12,
    duplicate_events: 2
});

const groups = ref([]);
const selectedGroup = ref(null);
const events = ref([]);

const typeOptions = [
    { label: "All Types", value: "all" },
    { label: "join", value: "join" },
    { label: "leave", value: "leave" },
    { label: "accept", value: "accept" },
    { label: "delivery", value: "delivery" },
    { label: "duplicate", value: "duplicate" }
];

const statusOptions = [
    { label: "All Status", value: "all" },
    { label: "Success", value: "success" },
    { label: "Failed", value: "failed" }
];

const mockGroups = [
    {
        id: "C001",
        name: "AWS Standby Team",
        member_count: 18,
        bot_in_group: true,
        last_activity_at: "2026-04-01T09:50:00Z"
    },
    {
        id: "C002",
        name: "Security Operations",
        member_count: 12,
        bot_in_group: true,
        last_activity_at: "2026-04-01T09:35:00Z"
    },
    {
        id: "C003",
        name: "Cloud Escalation War Room",
        member_count: 9,
        bot_in_group: true,
        last_activity_at: "2026-04-01T08:40:00Z"
    },
    {
        id: "C004",
        name: "Old Project Group",
        member_count: 5,
        bot_in_group: false,
        last_activity_at: "2026-03-28T14:10:00Z"
    }
];

const mockEvents = [
    {
        id: 1,
        event_type: "join",
        group_name: "AWS Standby Team",
        actor_name: "Narin Sukjai",
        message: "User joined LINE group",
        success: true,
        created_at: "2026-04-01T09:55:00Z"
    },
    {
        id: 2,
        event_type: "accept",
        group_name: "Security Operations",
        actor_name: "Ploy Jinda",
        message: "User accepted ticket from LINE notification",
        success: true,
        created_at: "2026-04-01T09:40:00Z"
    },
    {
        id: 3,
        event_type: "delivery",
        group_name: "Cloud Escalation War Room",
        actor_name: "System",
        message: "LINE message delivery succeeded",
        success: true,
        created_at: "2026-04-01T09:32:00Z"
    },
    {
        id: 4,
        event_type: "duplicate",
        group_name: "AWS Standby Team",
        actor_name: "System",
        message: "Duplicate webhook event detected",
        success: false,
        created_at: "2026-04-01T09:15:00Z"
    },
    {
        id: 5,
        event_type: "leave",
        group_name: "Old Project Group",
        actor_name: "Unknown User",
        message: "User left LINE group",
        success: true,
        created_at: "2026-03-31T16:45:00Z"
    }
];

const loadData = () => {
    pageError.value = "";

    try {
        groups.value = [...mockGroups];
        events.value = [...mockEvents];

        if (!selectedGroup.value && groups.value.length > 0) {
            selectedGroup.value = groups.value[0];
        } else if (selectedGroup.value) {
            const latest = groups.value.find((g) => g.id === selectedGroup.value.id);
            selectedGroup.value = latest || groups.value[0] || null;
        }
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load LINE monitoring data.";
    }
};

const filteredGroups = computed(() => {
    const keyword = groupSearch.value.trim().toLowerCase();
    if (!keyword) return groups.value;

    return groups.value.filter((group) =>
        [group.name, group.id]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(keyword))
    );
});

const filteredEvents = computed(() => {
    const keyword = eventSearch.value.trim().toLowerCase();

    return events.value.filter((event) => {
        const matchKeyword = !keyword
            ? true
            : [event.event_type, event.group_name, event.actor_name, event.message]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        const matchType =
            typeFilter.value === "all" ? true : event.event_type === typeFilter.value;

        const matchStatus =
            statusFilter.value === "all"
                ? true
                : statusFilter.value === "success"
                ? event.success
                : !event.success;

        return matchKeyword && matchType && matchStatus;
    });
});

const successCount = computed(() =>
    events.value.filter((event) => event.success).length
);

const failedCount = computed(() =>
    events.value.filter((event) => !event.success).length
);

const selectGroup = (group) => {
    selectedGroup.value = group;
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

const eventTypeClass = (type) => {
    switch (type) {
        case "join":
            return "type-join";
        case "leave":
            return "type-leave";
        case "accept":
            return "type-accept";
        case "delivery":
            return "type-delivery";
        case "duplicate":
            return "type-duplicate";
        default:
            return "";
    }
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

.status-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}

.status-list,
.metric-list {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
}

.status-item,
.metric-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    background: var(--card-bg);
}

.status-label,
.metric-label {
    color: var(--text-muted);
}

.status-value,
.metric-value {
    font-weight: 700;
    color: var(--text-color);
}

.page-two-column {
    display: grid;
    grid-template-columns: 360px minmax(0, 1fr);
    gap: 1rem;
    margin-bottom: 1rem;
    align-items: start;
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
    min-width: 180px;
}

.group-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.group-item {
    width: 100%;
    text-align: left;
    border: 1px solid var(--border-color);
    background: var(--card-bg);
    border-radius: 16px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.group-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-sm);
}

.group-item.active {
    border-color: #86efac;
    box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.14);
    background: #f0fdf4;
}

.group-item-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.45rem;
}

.group-name {
    font-weight: 700;
    color: var(--text-color);
}

.group-sub {
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-top: 0.2rem;
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

.info-label {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin-bottom: 0.3rem;
}

.info-value {
    font-weight: 600;
    color: var(--text-color);
    word-break: break-word;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.event-type-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
}

.type-join {
    background: #dcfce7;
    color: #166534;
}

.type-leave {
    background: #fee2e2;
    color: #991b1b;
}

.type-accept {
    background: #dbeafe;
    color: #1d4ed8;
}

.type-delivery {
    background: #fef3c7;
    color: #92400e;
}

.type-duplicate {
    background: #f3e8ff;
    color: #7e22ce;
}

.empty-box {
    padding: 1rem;
    border: 1px dashed var(--border-color);
    border-radius: 14px;
    text-align: center;
    color: var(--text-muted);
}

.empty-box.large {
    padding: 2rem 1rem;
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

    .status-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 1024px) {
    .page-two-column {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .summary-grid,
    .detail-grid {
        grid-template-columns: 1fr;
    }

    .toolbar-search {
        max-width: 100%;
    }
}
</style>