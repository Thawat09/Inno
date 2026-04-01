<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Notifications</div>
                        <div class="page-subtitle">
                            View all system notifications and track read status.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Mark All as Read"
                            icon="pi pi-check"
                            severity="secondary"
                            outlined
                            @click="handleMarkAllRead"
                        />
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadNotifications"
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
                    <div class="toolbar-search">
                        <i class="pi pi-search toolbar-search-icon"></i>
                        <InputText
                            v-model="searchText"
                            placeholder="Search title, message, type..."
                        />
                    </div>

                    <div class="toolbar-actions">
                        <Dropdown
                            v-model="statusFilter"
                            :options="statusOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Filter by status"
                            class="filter-dropdown"
                        />
                    </div>
                </div>

                <div class="notification-summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Total</div>
                        <div class="summary-value">{{ notifications.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Unread</div>
                        <div class="summary-value">{{ unreadCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Read</div>
                        <div class="summary-value">{{ readCount }}</div>
                    </div>
                </div>

                <div class="notification-list">
                    <div
                        v-for="item in filteredNotifications"
                        :key="item.id"
                        class="notification-card"
                        :class="{ unread: !item.is_read }"
                    >
                        <div class="notification-card-left">
                            <div class="notification-icon" :class="severityClass(item.severity)">
                                <i :class="severityIcon(item.severity)"></i>
                            </div>
                        </div>

                        <div class="notification-card-center">
                            <div class="notification-top-row">
                                <div class="notification-title-row">
                                    <div class="notification-card-title">
                                        {{ item.title }}
                                    </div>
                                    <span
                                        class="status-badge"
                                        :class="item.is_read ? 'status-active' : 'status-inactive'"
                                    >
                                        {{ item.is_read ? "Read" : "Unread" }}
                                    </span>
                                </div>

                                <div class="notification-time">
                                    {{ item.time }}
                                </div>
                            </div>

                            <div class="notification-message">
                                {{ item.message }}
                            </div>

                            <div class="notification-meta">
                                <span class="meta-chip">{{ item.type }}</span>
                                <span class="meta-chip" v-if="item.route">{{ item.route }}</span>
                            </div>
                        </div>

                        <div class="notification-card-right">
                            <Button
                                v-if="!item.is_read"
                                label="Mark Read"
                                icon="pi pi-check"
                                size="small"
                                severity="secondary"
                                outlined
                                @click="handleMarkRead(item.id)"
                            />
                            <Button
                                v-if="item.route"
                                label="Open"
                                icon="pi pi-arrow-right"
                                size="small"
                                @click="handleOpen(item)"
                            />
                        </div>
                    </div>

                    <div v-if="filteredNotifications.length === 0" class="table-empty">
                        No notifications found.
                    </div>
                </div>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock notifications and is ready for future
                    backend integration with notification tables and read/unread tracking.
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
const successMessage = ref("");
const searchText = ref("");
const statusFilter = ref("all");

const statusOptions = [
    { label: "All", value: "all" },
    { label: "Unread", value: "unread" },
    { label: "Read", value: "read" }
];

const notifications = ref([]);

const mockNotifications = [
    {
        id: 1,
        type: "Ticket",
        severity: "info",
        title: "New Ticket",
        message: "INC000123 assigned to AWS team",
        time: "1 min ago",
        route: "/tickets",
        is_read: false
    },
    {
        id: 2,
        type: "Escalation",
        severity: "warning",
        title: "Escalated",
        message: "Ticket escalated to Tier 2",
        time: "5 mins ago",
        route: "/acceptance-monitor",
        is_read: false
    },
    {
        id: 3,
        type: "Leave",
        severity: "info",
        title: "Leave Request",
        message: "John marked leave for today",
        time: "10 mins ago",
        route: "/leave",
        is_read: true
    },
    {
        id: 4,
        type: "Security",
        severity: "danger",
        title: "Account Locked",
        message: "User account locked after 3 failed attempts",
        time: "15 mins ago",
        route: "/locked-users",
        is_read: false
    },
    {
        id: 5,
        type: "LINE",
        severity: "success",
        title: "LINE Event",
        message: "New member joined LINE group",
        time: "22 mins ago",
        route: "/line-monitor",
        is_read: true
    },
    {
        id: 6,
        type: "Manual Override",
        severity: "warning",
        title: "Manual Override",
        message: "Admin changed ticket owner",
        time: "30 mins ago",
        route: "/manual-override",
        is_read: false
    },
    {
        id: 7,
        type: "AI Audit",
        severity: "info",
        title: "AI Audit",
        message: "New AI conversation logged",
        time: "40 mins ago",
        route: "/ai-audit",
        is_read: true
    },
    {
        id: 8,
        type: "SLA",
        severity: "warning",
        title: "SLA Warning",
        message: "Ticket nearing response timeout",
        time: "1 hour ago",
        route: "/reports",
        is_read: false
    }
];

const loadNotifications = () => {
    pageError.value = "";
    successMessage.value = "";
    notifications.value = [...mockNotifications];
};

const filteredNotifications = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    return notifications.value.filter((item) => {
        const matchStatus =
            statusFilter.value === "all"
                ? true
                : statusFilter.value === "read"
                ? item.is_read
                : !item.is_read;

        const matchKeyword = !keyword
            ? true
            : [item.title, item.message, item.type]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        return matchStatus && matchKeyword;
    });
});

const unreadCount = computed(() => notifications.value.filter((x) => !x.is_read).length);
const readCount = computed(() => notifications.value.filter((x) => x.is_read).length);

const handleMarkRead = (id) => {
    const target = notifications.value.find((item) => item.id === id);
    if (!target) return;

    target.is_read = true;
    successMessage.value = "Notification marked as read. (mock)";
};

const handleMarkAllRead = () => {
    notifications.value = notifications.value.map((item) => ({
        ...item,
        is_read: true
    }));
    successMessage.value = "All notifications marked as read. (mock)";
};

const handleOpen = (item) => {
    if (!item.route) return;
    router.push(item.route);
};

const severityClass = (severity) => {
    switch (severity) {
        case "success":
            return "sev-success";
        case "warning":
            return "sev-warning";
        case "danger":
            return "sev-danger";
        default:
            return "sev-info";
    }
};

const severityIcon = (severity) => {
    switch (severity) {
        case "success":
            return "pi pi-check-circle";
        case "warning":
            return "pi pi-exclamation-triangle";
        case "danger":
            return "pi pi-lock";
        default:
            return "pi pi-bell";
    }
};

onMounted(() => {
    loadNotifications();
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

.toolbar-actions {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.filter-dropdown {
    min-width: 180px;
}

.notification-summary-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
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

.notification-list {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
}

.notification-card {
    display: grid;
    grid-template-columns: 56px minmax(0, 1fr) auto;
    gap: 1rem;
    align-items: start;
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 18px;
    background: var(--card-bg);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.notification-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-sm);
}

.notification-card.unread {
    border-color: #86efac;
    box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.12);
}

.notification-icon {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
}

.sev-info {
    background: #dbeafe;
    color: #2563eb;
}

.sev-success {
    background: #dcfce7;
    color: #166534;
}

.sev-warning {
    background: #fef3c7;
    color: #92400e;
}

.sev-danger {
    background: #fee2e2;
    color: #991b1b;
}

.notification-top-row {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 0.45rem;
}

.notification-title-row {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
}

.notification-card-title {
    font-weight: 700;
    color: var(--text-color);
}

.notification-time {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.notification-message {
    color: var(--text-color);
    margin-bottom: 0.6rem;
    line-height: 1.45;
}

.notification-meta {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.meta-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.3rem 0.65rem;
    border-radius: 999px;
    background: #f1f5f9;
    color: #475569;
    font-size: 0.82rem;
    font-weight: 600;
}

.notification-card-right {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: flex-end;
}

.table-empty {
    padding: 1rem;
    text-align: center;
    color: var(--text-muted);
}

.mb-3 {
    margin-bottom: 1rem;
}

.mt-3 {
    margin-top: 1rem;
}

@media (max-width: 992px) {
    .notification-card {
        grid-template-columns: 1fr;
    }

    .notification-card-right {
        justify-content: flex-start;
    }
}

@media (max-width: 768px) {
    .notification-summary-grid {
        grid-template-columns: 1fr;
    }

    .toolbar-search {
        max-width: 100%;
    }
}
</style>