<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Audit Log</div>
                        <div class="page-subtitle">
                            Track important actions and configuration changes across the system.
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
                            @click="loadLogs"
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
                        <div class="summary-label">Total Logs</div>
                        <div class="summary-value">{{ filteredLogs.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Success</div>
                        <div class="summary-value">{{ successCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Failed</div>
                        <div class="summary-value">{{ failedCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Unique Actors</div>
                        <div class="summary-value">{{ uniqueActorCount }}</div>
                    </div>
                </div>

                <div class="toolbar-row">
                    <div class="toolbar-search">
                        <i class="pi pi-search toolbar-search-icon"></i>
                        <InputText
                            v-model="searchText"
                            placeholder="Search actor, module, target, detail..."
                        />
                    </div>

                    <div class="toolbar-filters">
                        <Dropdown
                            v-model="moduleFilter"
                            :options="moduleOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Module"
                            class="filter-dropdown"
                        />
                        <Dropdown
                            v-model="actionFilter"
                            :options="actionOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Action"
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
                    :value="filteredLogs"
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

                    <Column field="actor_name" header="Actor" style="min-width: 180px">
                        <template #body="{ data }">
                            <div class="log-actor">{{ data.actor_name || "-" }}</div>
                            <div class="log-sub">{{ data.actor_email || "-" }}</div>
                        </template>
                    </Column>

                    <Column field="module" header="Module" style="min-width: 160px">
                        <template #body="{ data }">
                            <span class="type-chip" :class="moduleClass(data.module)">
                                {{ data.module }}
                            </span>
                        </template>
                    </Column>

                    <Column field="action" header="Action" style="min-width: 180px">
                        <template #body="{ data }">
                            {{ data.action || "-" }}
                        </template>
                    </Column>

                    <Column field="target" header="Target" style="min-width: 220px">
                        <template #body="{ data }">
                            {{ data.target || "-" }}
                        </template>
                    </Column>

                    <Column field="status" header="Status" style="min-width: 140px">
                        <template #body="{ data }">
                            <span
                                class="status-badge"
                                :class="data.status === 'Success' ? 'status-active' : 'status-inactive'"
                            >
                                {{ data.status }}
                            </span>
                        </template>
                    </Column>

                    <Column field="detail" header="Detail" style="min-width: 320px">
                        <template #body="{ data }">
                            <div class="log-detail">{{ data.detail || "-" }}</div>
                        </template>
                    </Column>

                    <Column header="Action" style="min-width: 120px">
                        <template #body="{ data }">
                            <Button
                                label="View"
                                icon="pi pi-eye"
                                size="small"
                                severity="secondary"
                                outlined
                                @click="handlePreview(data)"
                            />
                        </template>
                    </Column>

                    <template #empty>
                        <div class="empty-box">
                            No audit logs found.
                        </div>
                    </template>
                </DataTable>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for audit trail, export workflow, and detailed change history.
                </div>
            </template>
        </Card>

        <Card v-if="selectedLog" class="content-card">
            <template #title>
                <div class="section-header">
                    <span>Audit Log Preview</span>
                    <Button
                        icon="pi pi-times"
                        text
                        rounded
                        class="topbar-icon-btn small-btn"
                        @click="selectedLog = null"
                    />
                </div>
            </template>

            <template #content>
                <div class="preview-grid">
                    <div class="info-box">
                        <div class="info-label">Time</div>
                        <div class="info-value">{{ formatDateTime(selectedLog.created_at) }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Actor</div>
                        <div class="info-value">{{ selectedLog.actor_name || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Actor Email</div>
                        <div class="info-value">{{ selectedLog.actor_email || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Module</div>
                        <div class="info-value">{{ selectedLog.module || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Action</div>
                        <div class="info-value">{{ selectedLog.action || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Target</div>
                        <div class="info-value">{{ selectedLog.target || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Status</div>
                        <div class="info-value">{{ selectedLog.status || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">IP Address</div>
                        <div class="info-value">{{ selectedLog.ip_address || "-" }}</div>
                    </div>

                    <div class="info-box info-box-wide">
                        <div class="info-label">Detail</div>
                        <div class="info-value">{{ selectedLog.detail || "-" }}</div>
                    </div>

                    <div class="info-box info-box-wide">
                        <div class="info-label">Payload</div>
                        <pre class="payload-box">{{ formatPayload(selectedLog.payload) }}</pre>
                    </div>
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

const pageError = ref("");
const successMessage = ref("");
const searchText = ref("");
const moduleFilter = ref("all");
const actionFilter = ref("all");
const statusFilter = ref("all");
const logs = ref([]);
const selectedLog = ref(null);

const moduleOptions = [
    { label: "All Modules", value: "all" },
    { label: "Calendar", value: "Calendar" },
    { label: "User", value: "User" },
    { label: "Ticket", value: "Ticket" },
    { label: "Leave", value: "Leave" },
    { label: "Manual Override", value: "Manual Override" },
    { label: "Security", value: "Security" }
];

const actionOptions = [
    { label: "All Actions", value: "all" },
    { label: "Update Calendar", value: "Update Calendar" },
    { label: "Unlock User", value: "Unlock User" },
    { label: "Reset Password", value: "Reset Password" },
    { label: "Manual Reassign", value: "Manual Reassign" },
    { label: "Approve Leave", value: "Approve Leave" },
    { label: "Disable User", value: "Disable User" }
];

const statusOptions = [
    { label: "All Status", value: "all" },
    { label: "Success", value: "Success" },
    { label: "Failed", value: "Failed" }
];

const mockLogs = [
    {
        id: 1,
        created_at: "2026-04-01T09:15:00Z",
        actor_name: "Super Admin",
        actor_email: "superadmin@company.com",
        module: "User",
        action: "Unlock User",
        target: "admin@company.com",
        status: "Success",
        detail: "Unlocked user after 3 failed login attempts.",
        ip_address: "10.10.10.15",
        payload: {
            email: "admin@company.com",
            failed_login_count: 0,
            is_locked: false
        }
    },
    {
        id: 2,
        created_at: "2026-04-01T08:50:00Z",
        actor_name: "Admin User",
        actor_email: "admin@company.com",
        module: "Calendar",
        action: "Update Calendar",
        target: "Cloud Operations / 2026-04-01",
        status: "Success",
        detail: "Updated Tier 2 standby assignment for Cloud Operations.",
        ip_address: "10.10.10.21",
        payload: {
            team: "Cloud Operations",
            date: "2026-04-01",
            field: "tier2_name",
            new_value: "Narin Sukjai"
        }
    },
    {
        id: 3,
        created_at: "2026-04-01T08:20:00Z",
        actor_name: "Admin User",
        actor_email: "admin@company.com",
        module: "Leave",
        action: "Approve Leave",
        target: "User One",
        status: "Success",
        detail: "Approved leave request for 2026-04-03 to 2026-04-05.",
        ip_address: "10.10.10.21",
        payload: {
            employee_name: "User One",
            start_date: "2026-04-03",
            end_date: "2026-04-05",
            status: "Approved"
        }
    },
    {
        id: 4,
        created_at: "2026-04-01T07:55:00Z",
        actor_name: "Super Admin",
        actor_email: "superadmin@company.com",
        module: "Ticket",
        action: "Manual Reassign",
        target: "INC000124",
        status: "Success",
        detail: "Reassigned ticket from Security Operations to Cloud Operations.",
        ip_address: "10.10.10.15",
        payload: {
            ticket_no: "INC000124",
            old_team: "Security Operations",
            new_team: "Cloud Operations"
        }
    },
    {
        id: 5,
        created_at: "2026-03-31T16:40:00Z",
        actor_name: "Admin User",
        actor_email: "admin@company.com",
        module: "Security",
        action: "Reset Password",
        target: "narin@company.com",
        status: "Failed",
        detail: "Password reset failed due to temporary service issue.",
        ip_address: "10.10.10.21",
        payload: {
            email: "narin@company.com",
            error: "mock_service_unavailable"
        }
    },
    {
        id: 6,
        created_at: "2026-03-31T15:10:00Z",
        actor_name: "Super Admin",
        actor_email: "superadmin@company.com",
        module: "User",
        action: "Disable User",
        target: "mali@company.com",
        status: "Success",
        detail: "Changed user status from active to inactive.",
        ip_address: "10.10.10.15",
        payload: {
            email: "mali@company.com",
            is_active: false
        }
    }
];

const loadLogs = () => {
    pageError.value = "";
    successMessage.value = "";

    try {
        logs.value = [...mockLogs];
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load audit logs.";
    }
};

const filteredLogs = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    return logs.value.filter((item) => {
        const matchKeyword = !keyword
            ? true
            : [
                  item.actor_name,
                  item.actor_email,
                  item.module,
                  item.action,
                  item.target,
                  item.detail
              ]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        const matchModule =
            moduleFilter.value === "all" ? true : item.module === moduleFilter.value;

        const matchAction =
            actionFilter.value === "all" ? true : item.action === actionFilter.value;

        const matchStatus =
            statusFilter.value === "all" ? true : item.status === statusFilter.value;

        return matchKeyword && matchModule && matchAction && matchStatus;
    });
});

const successCount = computed(() =>
    filteredLogs.value.filter((item) => item.status === "Success").length
);

const failedCount = computed(() =>
    filteredLogs.value.filter((item) => item.status === "Failed").length
);

const uniqueActorCount = computed(() =>
    new Set(filteredLogs.value.map((item) => item.actor_email).filter(Boolean)).size
);

const handlePreview = (item) => {
    selectedLog.value = item;
    successMessage.value = "";
};

const handleExport = () => {
    successMessage.value = "Export CSV clicked. (mock)";
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

const formatPayload = (payload) => {
    if (!payload) return "-";
    try {
        return JSON.stringify(payload, null, 2);
    } catch {
        return String(payload);
    }
};

const moduleClass = (module) => {
    switch (module) {
        case "Calendar":
            return "type-calendar";
        case "User":
            return "type-user";
        case "Ticket":
            return "type-ticket";
        case "Leave":
            return "type-leave";
        case "Manual Override":
            return "type-override";
        case "Security":
            return "type-security";
        default:
            return "";
    }
};

onMounted(() => {
    loadLogs();
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
    min-width: 180px;
}

.log-actor {
    font-weight: 600;
    color: var(--text-color);
}

.log-sub {
    font-size: 0.88rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
}

.log-detail {
    line-height: 1.45;
    color: var(--text-color);
}

.type-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
}

.type-calendar {
    background: #dbeafe;
    color: #1d4ed8;
}

.type-user {
    background: #dcfce7;
    color: #166534;
}

.type-ticket {
    background: #fef3c7;
    color: #92400e;
}

.type-leave {
    background: #fee2e2;
    color: #991b1b;
}

.type-override {
    background: #f3e8ff;
    color: #7e22ce;
}

.type-security {
    background: #e0f2fe;
    color: #075985;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
}

.preview-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
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

.payload-box {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: Consolas, Monaco, monospace;
    font-size: 0.88rem;
    color: var(--text-color);
    background: #f8fafc;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 0.85rem;
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

    .preview-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .info-box-wide {
        grid-column: span 2;
    }
}

@media (max-width: 768px) {
    .summary-grid,
    .preview-grid {
        grid-template-columns: 1fr;
    }

    .info-box-wide {
        grid-column: span 1;
    }

    .toolbar-search {
        max-width: 100%;
    }
}
</style>