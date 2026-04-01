<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Escalation Rule Management</div>
                        <div class="page-subtitle">
                            Configure team-specific timeout, retry, fallback, and escalation behavior.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="New Rule"
                            icon="pi pi-plus"
                            @click="startCreate"
                        />
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadRules"
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
                        <div class="summary-label">Rules</div>
                        <div class="summary-value">{{ filteredRules.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Enabled</div>
                        <div class="summary-value">{{ enabledCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Teams</div>
                        <div class="summary-value">{{ uniqueTeamCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Avg Retry</div>
                        <div class="summary-value">{{ avgRetryCount }}</div>
                    </div>
                </div>

                <div class="page-two-column">
                    <Card class="content-card">
                        <template #title>
                            <span>{{ editMode ? 'Edit Rule' : 'Create Rule' }}</span>
                        </template>

                        <template #content>
                            <div class="form-grid">
                                <div class="form-field">
                                    <label>Rule Name</label>
                                    <InputText
                                        v-model="form.rule_name"
                                        placeholder="Enter rule name"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Team</label>
                                    <Dropdown
                                        v-model="form.team_name"
                                        :options="teamOptionsNoAll"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select team"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Tier 1 Timeout (min)</label>
                                    <InputNumber
                                        v-model="form.tier1_timeout_min"
                                        :min="0"
                                        :useGrouping="false"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Tier 2 Timeout (min)</label>
                                    <InputNumber
                                        v-model="form.tier2_timeout_min"
                                        :min="0"
                                        :useGrouping="false"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Tier 3 Timeout (min)</label>
                                    <InputNumber
                                        v-model="form.tier3_timeout_min"
                                        :min="0"
                                        :useGrouping="false"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Retry Count</label>
                                    <InputNumber
                                        v-model="form.retry_count"
                                        :min="0"
                                        :useGrouping="false"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Notify If No Acceptance</label>
                                    <InputText
                                        v-model="form.notify_target"
                                        placeholder="e.g. Team Lead / Manager / Admin Group"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Rule Status</label>
                                    <Dropdown
                                        v-model="form.is_enabled"
                                        :options="enabledOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select status"
                                    />
                                </div>

                                <div class="form-field form-field-full">
                                    <label>Rule Description</label>
                                    <Textarea
                                        v-model="form.description"
                                        rows="3"
                                        placeholder="Describe purpose or scope of this rule"
                                    />
                                </div>

                                <div class="checkbox-grid form-field-full">
                                    <label class="checkbox-item">
                                        <input
                                            v-model="form.skip_leave"
                                            type="checkbox"
                                        />
                                        <span>Skip users on leave</span>
                                    </label>

                                    <label class="checkbox-item">
                                        <input
                                            v-model="form.skip_inactive"
                                            type="checkbox"
                                        />
                                        <span>Skip inactive users</span>
                                    </label>

                                    <label class="checkbox-item">
                                        <input
                                            v-model="form.skip_unavailable"
                                            type="checkbox"
                                        />
                                        <span>Skip unavailable users</span>
                                    </label>

                                    <label class="checkbox-item">
                                        <input
                                            v-model="form.allow_fallback_notify"
                                            type="checkbox"
                                        />
                                        <span>Send fallback notification if no acceptance</span>
                                    </label>
                                </div>

                                <div class="form-actions">
                                    <Button
                                        :label="editMode ? 'Update Rule' : 'Create Rule'"
                                        icon="pi pi-check"
                                        @click="handleSave"
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

                    <Card class="content-card">
                        <template #title>
                            <span>Rule Notes</span>
                        </template>

                        <template #content>
                            <div class="notes-list">
                                <div class="note-item">
                                    <div class="note-title">Per-Team Behavior</div>
                                    <div class="note-desc">
                                        Each team can use different timeout and retry values.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Skip Logic</div>
                                    <div class="note-desc">
                                        Future backend logic should skip users who are on leave, inactive, or temporarily unavailable.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">No Acceptance Flow</div>
                                    <div class="note-desc">
                                        If no one accepts after the final tier, the system can notify fallback target groups automatically.
                                    </div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>

                <Card class="content-card">
                    <template #title>
                        <span>Escalation Rules</span>
                    </template>

                    <template #content>
                        <div class="toolbar-row">
                            <div class="toolbar-search">
                                <i class="pi pi-search toolbar-search-icon"></i>
                                <InputText
                                    v-model="searchText"
                                    placeholder="Search rule name, team, notify target..."
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
                                    v-model="enabledFilter"
                                    :options="filterEnabledOptions"
                                    optionLabel="label"
                                    optionValue="value"
                                    placeholder="Status"
                                    class="filter-dropdown"
                                />
                            </div>
                        </div>

                        <DataTable
                            :value="filteredRules"
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

                            <Column field="rule_name" header="Rule Name" style="min-width: 220px" />

                            <Column field="team_name" header="Team" style="min-width: 180px" />

                            <Column header="Timeouts" style="min-width: 220px">
                                <template #body="{ data }">
                                    <div class="timeout-box">
                                        T1 {{ data.tier1_timeout_min }}m /
                                        T2 {{ data.tier2_timeout_min }}m /
                                        T3 {{ data.tier3_timeout_min }}m
                                    </div>
                                </template>
                            </Column>

                            <Column field="retry_count" header="Retry" style="min-width: 110px" />

                            <Column field="notify_target" header="Fallback Notify" style="min-width: 220px">
                                <template #body="{ data }">
                                    {{ data.notify_target || "-" }}
                                </template>
                            </Column>

                            <Column header="Status" style="min-width: 120px">
                                <template #body="{ data }">
                                    <span
                                        class="status-badge"
                                        :class="data.is_enabled ? 'status-active' : 'status-inactive'"
                                    >
                                        {{ data.is_enabled ? "Enabled" : "Disabled" }}
                                    </span>
                                </template>
                            </Column>

                            <Column header="Actions" style="min-width: 220px">
                                <template #body="{ data }">
                                    <div class="action-group">
                                        <Button
                                            label="Edit"
                                            icon="pi pi-pencil"
                                            size="small"
                                            severity="secondary"
                                            outlined
                                            @click="handleEdit(data)"
                                        />
                                        <Button
                                            :label="data.is_enabled ? 'Disable' : 'Enable'"
                                            :icon="data.is_enabled ? 'pi pi-ban' : 'pi pi-check-circle'"
                                            size="small"
                                            :severity="data.is_enabled ? 'danger' : 'success'"
                                            outlined
                                            @click="handleToggleEnabled(data)"
                                        />
                                    </div>
                                </template>
                            </Column>

                            <template #empty>
                                <div class="empty-box">
                                    No escalation rules found.
                                </div>
                            </template>
                        </DataTable>
                    </template>
                </Card>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for escalation engine configuration, fallback flow, and team-specific routing behavior.
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
const teamFilter = ref("all");
const enabledFilter = ref("all");
const editMode = ref(false);
const editingId = ref(null);
const rules = ref([]);

const teamOptions = [
    { label: "All Teams", value: "all" },
    { label: "Cloud Operations", value: "Cloud Operations" },
    { label: "Security Operations", value: "Security Operations" },
    { label: "Standby Support", value: "Standby Support" }
];

const teamOptionsNoAll = [
    { label: "Cloud Operations", value: "Cloud Operations" },
    { label: "Security Operations", value: "Security Operations" },
    { label: "Standby Support", value: "Standby Support" }
];

const enabledOptions = [
    { label: "Enabled", value: true },
    { label: "Disabled", value: false }
];

const filterEnabledOptions = [
    { label: "All Status", value: "all" },
    { label: "Enabled", value: "enabled" },
    { label: "Disabled", value: "disabled" }
];

const form = ref({
    rule_name: "",
    team_name: "",
    tier1_timeout_min: 5,
    tier2_timeout_min: 5,
    tier3_timeout_min: 5,
    retry_count: 0,
    notify_target: "",
    description: "",
    skip_leave: true,
    skip_inactive: true,
    skip_unavailable: true,
    allow_fallback_notify: true,
    is_enabled: true
});

const mockRules = [
    {
        id: 1,
        rule_name: "Cloud Ops Standard Escalation",
        team_name: "Cloud Operations",
        tier1_timeout_min: 5,
        tier2_timeout_min: 5,
        tier3_timeout_min: 10,
        retry_count: 1,
        notify_target: "Cloud Team Lead",
        description: "Standard business-hour escalation rule for cloud operations.",
        skip_leave: true,
        skip_inactive: true,
        skip_unavailable: true,
        allow_fallback_notify: true,
        is_enabled: true
    },
    {
        id: 2,
        rule_name: "Security Fast Escalation",
        team_name: "Security Operations",
        tier1_timeout_min: 3,
        tier2_timeout_min: 3,
        tier3_timeout_min: 5,
        retry_count: 2,
        notify_target: "SOC Manager",
        description: "Fast escalation for security-related incidents.",
        skip_leave: true,
        skip_inactive: true,
        skip_unavailable: true,
        allow_fallback_notify: true,
        is_enabled: true
    },
    {
        id: 3,
        rule_name: "Standby Support After-Hours",
        team_name: "Standby Support",
        tier1_timeout_min: 7,
        tier2_timeout_min: 7,
        tier3_timeout_min: 10,
        retry_count: 1,
        notify_target: "After-hours Admin Group",
        description: "Fallback coverage for after-hours standby support.",
        skip_leave: true,
        skip_inactive: true,
        skip_unavailable: true,
        allow_fallback_notify: false,
        is_enabled: false
    }
];

const loadRules = () => {
    pageError.value = "";
    successMessage.value = "";

    try {
        rules.value = [...mockRules];
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load escalation rules.";
    }
};

const filteredRules = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    return rules.value.filter((item) => {
        const matchKeyword = !keyword
            ? true
            : [
                  item.rule_name,
                  item.team_name,
                  item.notify_target,
                  item.description
              ]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        const matchTeam =
            teamFilter.value === "all" ? true : item.team_name === teamFilter.value;

        const matchEnabled =
            enabledFilter.value === "all"
                ? true
                : enabledFilter.value === "enabled"
                ? item.is_enabled
                : !item.is_enabled;

        return matchKeyword && matchTeam && matchEnabled;
    });
});

const enabledCount = computed(() => {
    return filteredRules.value.filter((item) => item.is_enabled).length;
});

const uniqueTeamCount = computed(() => {
    return new Set(filteredRules.value.map((item) => item.team_name)).size;
});

const avgRetryCount = computed(() => {
    if (!filteredRules.value.length) return 0;
    const total = filteredRules.value.reduce((sum, item) => sum + Number(item.retry_count || 0), 0);
    return Math.round((total / filteredRules.value.length) * 10) / 10;
});

const resetForm = () => {
    form.value = {
        rule_name: "",
        team_name: "",
        tier1_timeout_min: 5,
        tier2_timeout_min: 5,
        tier3_timeout_min: 5,
        retry_count: 0,
        notify_target: "",
        description: "",
        skip_leave: true,
        skip_inactive: true,
        skip_unavailable: true,
        allow_fallback_notify: true,
        is_enabled: true
    };
    editMode.value = false;
    editingId.value = null;
};

const startCreate = () => {
    resetForm();
    pageError.value = "";
    successMessage.value = "";
};

const handleSave = () => {
    pageError.value = "";
    successMessage.value = "";

    if (!form.value.rule_name || !form.value.team_name) {
        pageError.value = "Please complete rule name and team.";
        return;
    }

    const payload = {
        ...form.value,
        tier1_timeout_min: Number(form.value.tier1_timeout_min || 0),
        tier2_timeout_min: Number(form.value.tier2_timeout_min || 0),
        tier3_timeout_min: Number(form.value.tier3_timeout_min || 0),
        retry_count: Number(form.value.retry_count || 0)
    };

    if (editMode.value && editingId.value !== null) {
        const target = rules.value.find((item) => item.id === editingId.value);
        if (!target) {
            pageError.value = "Selected rule not found.";
            return;
        }

        Object.assign(target, payload);
        successMessage.value = "Escalation rule updated successfully. (mock)";
    } else {
        rules.value.unshift({
            id: Date.now(),
            ...payload
        });
        successMessage.value = "Escalation rule created successfully. (mock)";
    }

    resetForm();
};

const handleEdit = (item) => {
    editMode.value = true;
    editingId.value = item.id;

    form.value = {
        rule_name: item.rule_name || "",
        team_name: item.team_name || "",
        tier1_timeout_min: item.tier1_timeout_min ?? 5,
        tier2_timeout_min: item.tier2_timeout_min ?? 5,
        tier3_timeout_min: item.tier3_timeout_min ?? 5,
        retry_count: item.retry_count ?? 0,
        notify_target: item.notify_target || "",
        description: item.description || "",
        skip_leave: item.skip_leave ?? true,
        skip_inactive: item.skip_inactive ?? true,
        skip_unavailable: item.skip_unavailable ?? true,
        allow_fallback_notify: item.allow_fallback_notify ?? true,
        is_enabled: item.is_enabled ?? true
    };

    pageError.value = "";
    successMessage.value = "";
};

const handleToggleEnabled = (item) => {
    item.is_enabled = !item.is_enabled;
    successMessage.value = item.is_enabled
        ? `Rule "${item.rule_name}" enabled. (mock)`
        : `Rule "${item.rule_name}" disabled. (mock)`;
};

onMounted(() => {
    loadRules();
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
    min-width: 170px;
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

.timeout-box {
    color: var(--text-color);
    line-height: 1.45;
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

    .toolbar-search {
        max-width: 100%;
    }
}
</style>