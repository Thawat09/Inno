<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Data Mapping Queue</div>
                        <div class="page-subtitle">
                            Review unresolved mapping issues and data quality gaps.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadMappings"
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
                        <div class="summary-label">Total Issues</div>
                        <div class="summary-value">{{ mappings.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Open</div>
                        <div class="summary-value">{{ openCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Resolved</div>
                        <div class="summary-value">{{ resolvedCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">High Priority</div>
                        <div class="summary-value">{{ highPriorityCount }}</div>
                    </div>
                </div>

                <div class="toolbar-row">
                    <div class="toolbar-search">
                        <i class="pi pi-search toolbar-search-icon"></i>
                        <InputText
                            v-model="searchText"
                            placeholder="Search source, team, value, issue..."
                        />
                    </div>

                    <div class="toolbar-filters">
                        <Dropdown
                            v-model="typeFilter"
                            :options="typeOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Issue Type"
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
                            v-model="teamFilter"
                            :options="teamOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Team"
                            class="filter-dropdown"
                        />
                    </div>
                </div>

                <DataTable
                    :value="filteredMappings"
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

                    <Column header="Issue Type" style="min-width: 180px">
                        <template #body="{ data }">
                            <span class="type-chip" :class="typeClass(data.issue_type)">
                                {{ data.issue_type }}
                            </span>
                        </template>
                    </Column>

                    <Column field="source_type" header="Source" style="min-width: 140px">
                        <template #body="{ data }">
                            {{ data.source_type || "-" }}
                        </template>
                    </Column>

                    <Column field="source_value" header="Source Value" style="min-width: 240px">
                        <template #body="{ data }">
                            <div class="source-value">{{ data.source_value || "-" }}</div>
                        </template>
                    </Column>

                    <Column field="team_name" header="Team" style="min-width: 180px">
                        <template #body="{ data }">
                            {{ data.team_name || "-" }}
                        </template>
                    </Column>

                    <Column field="priority" header="Priority" style="min-width: 130px">
                        <template #body="{ data }">
                            <span class="priority-chip" :class="priorityClass(data.priority)">
                                {{ data.priority }}
                            </span>
                        </template>
                    </Column>

                    <Column field="status" header="Status" style="min-width: 130px">
                        <template #body="{ data }">
                            <span
                                class="status-badge"
                                :class="statusClass(data.status)"
                            >
                                {{ data.status }}
                            </span>
                        </template>
                    </Column>

                    <Column field="detail" header="Detail" style="min-width: 320px">
                        <template #body="{ data }">
                            <div class="mapping-detail">{{ data.detail || "-" }}</div>
                        </template>
                    </Column>

                    <Column field="created_at" header="Created At" style="min-width: 180px">
                        <template #body="{ data }">
                            {{ formatDateTime(data.created_at) }}
                        </template>
                    </Column>

                    <Column header="Actions" style="min-width: 280px">
                        <template #body="{ data }">
                            <div class="action-group">
                                <Button
                                    label="Preview"
                                    icon="pi pi-eye"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    @click="handlePreview(data)"
                                />
                                <Button
                                    v-if="data.status === 'Open'"
                                    label="Resolve"
                                    icon="pi pi-check"
                                    size="small"
                                    @click="handleResolve(data)"
                                />
                                <Button
                                    v-if="data.status === 'Open'"
                                    label="Ignore"
                                    icon="pi pi-times"
                                    size="small"
                                    severity="danger"
                                    outlined
                                    @click="handleIgnore(data)"
                                />
                            </div>
                        </template>
                    </Column>

                    <template #empty>
                        <div class="empty-box">
                            No mapping issues found.
                        </div>
                    </template>
                </DataTable>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for mapping queue, unresolved reference management, and routing/data-quality workflows.
                </div>
            </template>
        </Card>

        <Card v-if="selectedItem" class="content-card">
            <template #title>
                <div class="section-header">
                    <span>Issue Preview</span>
                    <Button
                        icon="pi pi-times"
                        text
                        rounded
                        class="topbar-icon-btn small-btn"
                        @click="selectedItem = null"
                    />
                </div>
            </template>

            <template #content>
                <div class="preview-grid">
                    <div class="info-box">
                        <div class="info-label">Issue Type</div>
                        <div class="info-value">{{ selectedItem.issue_type }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Source</div>
                        <div class="info-value">{{ selectedItem.source_type || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Source Value</div>
                        <div class="info-value">{{ selectedItem.source_value || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Team</div>
                        <div class="info-value">{{ selectedItem.team_name || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Priority</div>
                        <div class="info-value">{{ selectedItem.priority || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Status</div>
                        <div class="info-value">{{ selectedItem.status || "-" }}</div>
                    </div>

                    <div class="info-box info-box-wide">
                        <div class="info-label">Detail</div>
                        <div class="info-value">{{ selectedItem.detail || "-" }}</div>
                    </div>

                    <div class="info-box info-box-wide">
                        <div class="info-label">Suggested Action</div>
                        <div class="info-value">{{ selectedItem.suggested_action || "-" }}</div>
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
const typeFilter = ref("all");
const statusFilter = ref("all");
const teamFilter = ref("all");
const mappings = ref([]);
const selectedItem = ref(null);

const typeOptions = [
    { label: "All Types", value: "all" },
    { label: "LINE User Not Mapped", value: "LINE User Not Mapped" },
    { label: "Team Not Found", value: "Team Not Found" },
    { label: "Low Confidence", value: "Low Confidence" },
    { label: "No Standby Coverage", value: "No Standby Coverage" },
    { label: "Invalid Format", value: "Invalid Format" }
];

const statusOptions = [
    { label: "All Status", value: "all" },
    { label: "Open", value: "Open" },
    { label: "Resolved", value: "Resolved" },
    { label: "Ignored", value: "Ignored" }
];

const mockMappings = [
    {
        id: 1,
        issue_type: "LINE User Not Mapped",
        source_type: "LINE",
        source_value: "line-user-001 / displayName: John Ops",
        team_name: "Cloud Operations",
        priority: "High",
        status: "Open",
        detail: "Incoming accept action from LINE could not be mapped to an internal employee record.",
        suggested_action: "Map LINE user to employee account in user administration.",
        created_at: "2026-04-01T09:20:00Z"
    },
    {
        id: 2,
        issue_type: "Team Not Found",
        source_type: "Email Parser",
        source_value: "subject=Urgent DB issue / keyword=database-core",
        team_name: "",
        priority: "High",
        status: "Open",
        detail: "Parser could not confidently match this email to any support team.",
        suggested_action: "Review keyword mapping and update routing rule.",
        created_at: "2026-04-01T08:10:00Z"
    },
    {
        id: 3,
        issue_type: "Low Confidence",
        source_type: "AI Classifier",
        source_value: "confidence=0.42 / predictedTeam=Security Operations",
        team_name: "Security Operations",
        priority: "Medium",
        status: "Open",
        detail: "Model confidence is below the defined threshold for auto-routing.",
        suggested_action: "Review training examples or require manual validation.",
        created_at: "2026-03-31T16:30:00Z"
    },
    {
        id: 4,
        issue_type: "No Standby Coverage",
        source_type: "Calendar",
        source_value: "2026-04-01 16:00-00:00",
        team_name: "Standby Support",
        priority: "High",
        status: "Resolved",
        detail: "No active Tier 1 standby member was found for the selected time slot.",
        suggested_action: "Update calendar roster or fallback escalation rule.",
        created_at: "2026-03-31T13:45:00Z"
    },
    {
        id: 5,
        issue_type: "Invalid Format",
        source_type: "Ticket Import",
        source_value: "Requester email missing @domain",
        team_name: "Security Operations",
        priority: "Low",
        status: "Ignored",
        detail: "Input payload contains malformed requester field.",
        suggested_action: "Validate upstream source payload format.",
        created_at: "2026-03-30T11:00:00Z"
    }
];

const loadMappings = () => {
    pageError.value = "";
    successMessage.value = "";

    try {
        mappings.value = [...mockMappings];
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load data mapping queue.";
    }
};

const teamOptions = computed(() => {
    const teams = [...new Set(mappings.value.map((item) => item.team_name).filter(Boolean))];
    return [
        { label: "All Teams", value: "all" },
        ...teams.map((team) => ({ label: team, value: team }))
    ];
});

const filteredMappings = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    return mappings.value.filter((item) => {
        const matchKeyword = !keyword
            ? true
            : [
                  item.issue_type,
                  item.source_type,
                  item.source_value,
                  item.team_name,
                  item.detail,
                  item.suggested_action
              ]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        const matchType =
            typeFilter.value === "all" ? true : item.issue_type === typeFilter.value;

        const matchStatus =
            statusFilter.value === "all" ? true : item.status === statusFilter.value;

        const matchTeam =
            teamFilter.value === "all" ? true : item.team_name === teamFilter.value;

        return matchKeyword && matchType && matchStatus && matchTeam;
    });
});

const openCount = computed(() =>
    mappings.value.filter((item) => item.status === "Open").length
);

const resolvedCount = computed(() =>
    mappings.value.filter((item) => item.status === "Resolved").length
);

const highPriorityCount = computed(() =>
    mappings.value.filter((item) => item.priority === "High").length
);

const handlePreview = (item) => {
    selectedItem.value = item;
    successMessage.value = "";
};

const handleResolve = (item) => {
    item.status = "Resolved";
    successMessage.value = `Issue #${item.id} marked as resolved. (mock)`;
};

const handleIgnore = (item) => {
    item.status = "Ignored";
    successMessage.value = `Issue #${item.id} marked as ignored. (mock)`;
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

const typeClass = (type) => {
    switch (type) {
        case "LINE User Not Mapped":
            return "type-line";
        case "Team Not Found":
            return "type-team";
        case "Low Confidence":
            return "type-confidence";
        case "No Standby Coverage":
            return "type-coverage";
        case "Invalid Format":
            return "type-invalid";
        default:
            return "";
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

const statusClass = (status) => {
    switch (status) {
        case "Resolved":
            return "status-active";
        case "Ignored":
            return "status-inactive";
        default:
            return "status-pending";
    }
};

onMounted(() => {
    loadMappings();
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

.source-value,
.mapping-detail {
    line-height: 1.45;
    color: var(--text-color);
}

.type-chip,
.priority-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
}

.type-line {
    background: #dbeafe;
    color: #1d4ed8;
}

.type-team {
    background: #fee2e2;
    color: #991b1b;
}

.type-confidence {
    background: #fef3c7;
    color: #92400e;
}

.type-coverage {
    background: #dcfce7;
    color: #166534;
}

.type-invalid {
    background: #f3e8ff;
    color: #7e22ce;
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
    background: #e0f2fe;
    color: #075985;
}

.action-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
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