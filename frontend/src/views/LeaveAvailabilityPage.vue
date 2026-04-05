<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Leave & Availability</div>
                        <div class="page-subtitle">
                            Manage leave requests and temporary availability status.
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
                <div v-if="isLoading" class="loading-state">
                    <ProgressSpinner style="width: 50px; height: 50px" />
                </div>
                <template v-else>
                <Message v-if="pageError" severity="error" class="mb-3">
                    {{ pageError }}
                </Message>

                <Message v-if="successMessage" severity="success" class="mb-3">
                    {{ successMessage }}
                </Message>

                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Total Records</div>
                        <div class="summary-value">{{ filteredRequests.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Active Records</div>
                        <div class="summary-value">{{ activeCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Unavailable Today</div>
                        <div class="summary-value">{{ unavailableTodayCount }}</div>
                    </div>
                </div>

                <div class="page-two-column">
                    <!-- Request Form -->
                    <Card class="content-card">
                        <template #title>
                            <span>New Request</span>
                        </template>

                        <template #content>
                            <div class="form-grid">
                                <div class="form-field">
                                    <label>Request Type</label>
                                    <Dropdown
                                        v-model="form.type"
                                        :options="typeOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select type"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Team</label>
                                    <Dropdown
                                        v-model="form.team"
                                        :options="teamOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select team"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Start Date</label>
                                    <InputText
                                        v-model="form.start_date"
                                        type="date"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>End Date</label>
                                    <InputText
                                        v-model="form.end_date"
                                        type="date"
                                    />
                                </div>

                                <div class="form-field form-field-full">
                                    <label>Reason</label>
                                    <Textarea
                                        v-model="form.reason"
                                        rows="4"
                                        placeholder="Enter reason"
                                    />
                                </div>

                                <div class="form-actions">
                                    <Button
                                        label="Submit Request"
                                        icon="pi pi-check"
                                        @click="handleSubmit"
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
                    </Card>

                    <!-- Quick Notes -->
                    <Card class="content-card">
                        <template #title>
                            <span>Availability Rules</span>
                        </template>

                        <template #content>
                            <div class="notes-list">
                                <div class="note-item">
                                    <div class="note-title">Leave Request</div>
                                    <div class="note-desc">
                                        Use this for full-day leave. Requests are applied immediately (No approval required).
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Temporary Unavailable</div>
                                    <div class="note-desc">
                                        Use this when a member is temporarily unable to accept tickets.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Standby Impact</div>
                                    <div class="note-desc">
                                        Future backend logic should skip unavailable members from standby escalation automatically.
                                    </div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>

                <Card class="content-card">
                    <template #title>
                        <span>Request List</span>
                    </template>

                    <template #content>
                        <div class="toolbar-row">
                            <div class="toolbar-search">
                                <i class="pi pi-search toolbar-search-icon"></i>
                                <InputText
                                    v-model="searchText"
                                    placeholder="Search name, team, reason..."
                                />
                            </div>

                            <div class="toolbar-filters">
                                <Dropdown
                                    v-model="typeFilter"
                                    :options="filterTypeOptions"
                                    optionLabel="label"
                                    optionValue="value"
                                    placeholder="Type"
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
                            :value="filteredRequests"
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

                            <Column field="employee_name" header="Employee" style="min-width: 220px" />

                            <Column field="team_name" header="Team" style="min-width: 180px" />

                            <Column field="type" header="Type" style="min-width: 150px">
                                <template #body="{ data }">
                                    <span class="type-chip" :class="typeClass(data.type)">
                                        {{ data.type }}
                                    </span>
                                </template>
                            </Column>

                            <Column field="start_date" header="Start Date" style="min-width: 140px">
                                <template #body="{ data }">
                                    {{ formatDate(data.start_date) }}
                                </template>
                            </Column>

                            <Column field="end_date" header="End Date" style="min-width: 140px">
                                <template #body="{ data }">
                                    {{ formatDate(data.end_date) }}
                                </template>
                            </Column>

                            <Column field="reason" header="Reason" style="min-width: 260px" />

                            <Column header="Status" style="min-width: 140px">
                                <template #body="{ data }">
                                    <span
                                        class="status-badge"
                                        :class="data.status === 'Active' ? 'status-active' : 'status-inactive'"
                                    >
                                        {{ data.status }}
                                    </span>
                                </template>
                            </Column>

                            <template #empty>
                                <div class="empty-box">
                                    No leave or availability records found.
                                </div>
                            </template>
                        </DataTable>
                    </template>
                </Card>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for leave workflow, availability control, and standby impact calculation.
                </div>
                </template>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

const isLoading = ref(true);
const pageError = ref("");
const successMessage = ref("");
const searchText = ref("");
const typeFilter = ref("all");
const statusFilter = ref("all");

const requests = ref([]);

const typeOptions = [
    { label: "Leave", value: "Leave" },
    { label: "Unavailable", value: "Unavailable" }
];

const filterTypeOptions = [
    { label: "All Types", value: "all" },
    { label: "Leave", value: "Leave" },
    { label: "Unavailable", value: "Unavailable" }
];

const teamOptions = [
    { label: "Cloud Operations", value: "Cloud Operations" },
    { label: "Security Operations", value: "Security Operations" },
    { label: "Standby Support", value: "Standby Support" }
];

const statusOptions = [
    { label: "All Status", value: "all" },
    { label: "Active", value: "Active" },
    { label: "Past", value: "Past" }
];

const form = ref({
    type: "",
    team: "",
    start_date: "",
    end_date: "",
    reason: ""
});

const mockRequests = [
    {
        id: 1,
        employee_name: "Admin User",
        team_name: "Cloud Operations",
        type: "Leave",
        start_date: "2026-04-01",
        end_date: "2026-04-02",
        reason: "Personal leave",
        status: "Active"
    },
    {
        id: 2,
        employee_name: "Ploy Jinda",
        team_name: "Security Operations",
        type: "Unavailable",
        start_date: "2026-04-01",
        end_date: "2026-04-01",
        reason: "Training session",
        status: "Active"
    },
    {
        id: 3,
        employee_name: "User One",
        team_name: "Standby Support",
        type: "Leave",
        start_date: "2026-04-03",
        end_date: "2026-04-05",
        reason: "Vacation",
        status: "Active"
    },
    {
        id: 4,
        employee_name: "Narin Sukjai",
        team_name: "Cloud Operations",
        type: "Unavailable",
        start_date: "2026-04-01",
        end_date: "2026-04-01",
        reason: "Customer site visit",
        status: "Past"
    }
];

const loadData = () => {
    isLoading.value = true;
    pageError.value = "";
    successMessage.value = "";

    setTimeout(() => {
        try {
            requests.value = [...mockRequests];
        } catch (error) {
            console.error(error);
            pageError.value = "Unable to load leave and availability data.";
        } finally {
            isLoading.value = false;
        }
    }, 500);
};

const filteredRequests = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    return requests.value.filter((item) => {
        const matchKeyword = !keyword
            ? true
            : [item.employee_name, item.team_name, item.reason, item.type]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        const matchType =
            typeFilter.value === "all" ? true : item.type === typeFilter.value;

        const matchStatus =
            statusFilter.value === "all" ? true : item.status === statusFilter.value;

        return matchKeyword && matchType && matchStatus;
    });
});

const activeCount = computed(() =>
    filteredRequests.value.filter((item) => item.status === "Active").length
);

const unavailableTodayCount = computed(() =>
    requests.value.filter(
        (item) =>
            item.type === "Unavailable" &&
            item.status === "Active" &&
            isTodayInRange(item.start_date, item.end_date)
    ).length
);

const isTodayInRange = (startDate, endDate) => {
    const today = new Date().toISOString().slice(0, 10);
    return today >= startDate && today <= endDate;
};

const handleSubmit = () => {
    pageError.value = "";
    successMessage.value = "";

    if (!form.value.type || !form.value.team || !form.value.start_date || !form.value.end_date) {
        pageError.value = "Please complete all required fields.";
        return;
    }

    if (form.value.end_date < form.value.start_date) {
        pageError.value = "End date must not be earlier than start date.";
        return;
    }

    requests.value.unshift({
        id: Date.now(),
        employee_name: "Current User",
        team_name: form.value.team,
        type: form.value.type,
        start_date: form.value.start_date,
        end_date: form.value.end_date,
        reason: form.value.reason || "-",
        status: "Active"
    });

    successMessage.value = "Leave applied immediately. (No approval required)";
    resetForm();
};

const resetForm = () => {
    form.value = {
        type: "",
        team: "",
        start_date: "",
        end_date: "",
        reason: ""
    };
};

const formatDate = (value) => {
    if (!value) return "-";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;

    return date.toLocaleDateString("en-GB", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
    });
};

const typeClass = (type) => {
    return type === "Leave" ? "type-leave" : "type-unavailable";
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
    grid-template-columns: 1.1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
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

.type-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
}

.type-leave {
    background: #dbeafe;
    color: #1d4ed8;
}

.type-unavailable {
    background: #fee2e2;
    color: #991b1b;
}

.status-pending {
    background: #fef3c7;
    color: #92400e;
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

.loading-state {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 200px;
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
    .summary-grid {
        grid-template-columns: 1fr;
    }

    .toolbar-search {
        max-width: 100%;
    }
}
</style>