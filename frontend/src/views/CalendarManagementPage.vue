<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Calendar Management</div>
                        <div class="page-subtitle">
                            Configure standby shift rules, rotation cycles, and infinite tier assignments.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="New Shift Rule"
                            icon="pi pi-plus"
                            @click="startCreate"
                        />
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadRosters"
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
                        <div class="summary-label">Active Rules</div>
                        <div class="summary-value">{{ filteredRules.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Teams Configured</div>
                        <div class="summary-value">{{ uniqueTeamCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Daily Rotations</div>
                        <div class="summary-value">{{ dailyRotationCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Weekly Rotations</div>
                        <div class="summary-value">{{ weeklyRotationCount }}</div>
                    </div>
                </div>

                <div class="page-two-column">
                    <Card class="content-card">
                        <template #title>
                            <span>{{ editMode ? 'Edit Shift Rule' : 'Create Shift Rule' }}</span>
                        </template>

                        <template #content>
                            <div class="form-grid">
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
                                    <label>Effective Start Date</label>
                                    <InputText
                                        v-model="form.anchor_date"
                                        type="date"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Shift Start</label>
                                    <InputText
                                        v-model="form.shift_start"
                                        type="time"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Shift End</label>
                                    <InputText
                                        v-model="form.shift_end"
                                        type="time"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Tier 1</label>
                                    <Dropdown
                                        v-model="form.tier1_name"
                                        :options="memberOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select Tier 1"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Tier 2</label>
                                    <Dropdown
                                        v-model="form.tier2_name"
                                        :options="memberOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select Tier 2"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Tier 3</label>
                                    <Dropdown
                                        v-model="form.tier3_name"
                                        :options="memberOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select Tier 3"
                                    />
                                </div>

                                <div class="form-field">
                                    <label>Rotation Cycle</label>
                                    <Dropdown
                                        v-model="form.cycle_days"
                                        :options="rotationOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select cycle"
                                    />
                                </div>

                                <div class="form-field form-field-full">
                                    <label>Note</label>
                                    <Textarea
                                        v-model="form.note"
                                        rows="4"
                                        placeholder="Optional note"
                                    />
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
                            <span>Management Notes</span>
                        </template>

                        <template #content>
                            <div class="notes-list">
                                <div class="note-item">
                                    <div class="note-title">Infinite Rotation</div>
                                    <div class="note-desc">
                                        Setting a rule generates standby slots automatically forever based on the cycle (e.g., every 7 days).
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Effective Start Date</div>
                                    <div class="note-desc">
                                        Choose a Monday if you want weekly rotations to always switch on Mondays.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Advanced Roasters</div>
                                    <div class="note-desc">
                                        In full backend implementation, a single rule can accept multiple roster groups to cycle through.
                                    </div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>

                <Card class="content-card">
                    <template #title>
                        <span>Active Shift Rules</span>
                    </template>

                    <template #content>
                        <div class="toolbar-row">
                            <div class="toolbar-search">
                                <i class="pi pi-search toolbar-search-icon"></i>
                                <InputText
                                    v-model="searchText"
                                    placeholder="Search team, rule name, tier user..."
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

                            <Column field="anchor_date" header="Effective From" style="min-width: 140px">
                                <template #body="{ data }">
                                    {{ formatDate(data.anchor_date) }}
                                </template>
                            </Column>

                            <Column field="team_name" header="Team" style="min-width: 170px" />

                            <Column field="shift_label" header="Shift" style="min-width: 150px" />

                            <Column field="cycle_days" header="Cycle" style="min-width: 120px">
                                <template #body="{ data }">
                                    {{ data.cycle_days === 1 ? 'Daily' : data.cycle_days === 7 ? 'Weekly' : data.cycle_days + ' Days' }}
                                </template>
                            </Column>

                            <Column field="tier1_name" header="Tier 1" style="min-width: 170px">
                                <template #body="{ data }">
                                    <b>{{ data.tier1_name || "-" }}</b>
                                </template>
                            </Column>

                            <Column field="tier2_name" header="Tier 2" style="min-width: 170px">
                                <template #body="{ data }">
                                    {{ data.tier2_name || "-" }}
                                </template>
                            </Column>

                            <Column field="tier3_name" header="Tier 3" style="min-width: 170px">
                                <template #body="{ data }">
                                    {{ data.tier3_name || "-" }}
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
                                            label="Delete"
                                            icon="pi pi-trash"
                                            size="small"
                                            severity="danger"
                                            outlined
                                            @click="handleDelete(data)"
                                        />
                                    </div>
                                </template>
                            </Column>

                            <template #empty>
                                <div class="empty-box">
                                    No shift rules found.
                                </div>
                            </template>
                        </DataTable>
                    </template>
                </Card>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for generating infinite `standby_slots` based on these `standby_shift_rules`.
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
const teamFilter = ref("all");
const editMode = ref(false);
const editingId = ref(null);
const shiftRules = ref([]);

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

const memberOptions = [
    { label: "Admin User", value: "Admin User" },
    { label: "Super Admin", value: "Super Admin" },
    { label: "Narin Sukjai", value: "Narin Sukjai" },
    { label: "Ploy Jinda", value: "Ploy Jinda" },
    { label: "User One", value: "User One" },
    { label: "Krit Meechai", value: "Krit Meechai" },
    { label: "Mali Kanit", value: "Mali Kanit" }
];

const rotationOptions = [
    { label: "Daily (1 Day)", value: 1 },
    { label: "Weekly (7 Days)", value: 7 },
    { label: "Bi-Weekly (14 Days)", value: 14 }
];

const form = ref({
    team_name: "",
    anchor_date: "",
    shift_start: "",
    shift_end: "",
    tier1_name: "",
    tier2_name: "",
    tier3_name: "",
    cycle_days: 7,
    note: ""
});

const mockRules = [
    {
        id: 1,
        team_name: "Cloud Operations",
        anchor_date: "2024-01-01",
        shift_start: "08:30",
        shift_end: "08:30",
        shift_label: "08:30 - 08:30",
        cycle_days: 7,
        tier1_name: "Admin User",
        tier2_name: "Narin Sukjai",
        tier3_name: "Mali Kanit",
        note: "Weekly rotation starting Monday"
    },
    {
        id: 2,
        team_name: "Security Operations",
        anchor_date: "2024-01-01",
        shift_start: "08:00",
        shift_end: "16:00",
        shift_label: "08:00 - 16:00",
        cycle_days: 1,
        tier1_name: "Super Admin",
        tier2_name: "Ploy Jinda",
        tier3_name: "",
        note: "Daily SOC monitoring shift"
    },
    {
        id: 3,
        team_name: "Standby Support",
        anchor_date: "2024-01-03",
        shift_start: "16:00",
        shift_end: "00:00",
        shift_label: "16:00 - 00:00",
        cycle_days: 7,
        tier1_name: "User One",
        tier2_name: "Krit Meechai",
        tier3_name: "",
        note: "Weekly rotation starting Wednesday"
    }
];

const getTodayDate = () => new Date().toISOString().slice(0, 10);

const loadRules = () => {
    isLoading.value = true;
    pageError.value = "";
    successMessage.value = "";

    setTimeout(() => {
        try {
            shiftRules.value = [...mockRules];
        } catch (error) {
            pageError.value = "Unable to load shift rules data.";
        } finally {
            isLoading.value = false;
        }
    }, 500);
};

const filteredRules = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    return shiftRules.value.filter((item) => {
        const matchKeyword = !keyword
            ? true
            : [
                  item.team_name,
                  item.shift_label,
                  item.tier1_name,
                  item.tier2_name,
                  item.tier3_name
              ]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        const matchTeam =
            teamFilter.value === "all" ? true : item.team_name === teamFilter.value;

        return matchKeyword && matchTeam;
    });
});

const uniqueTeamCount = computed(() => {
    return new Set(filteredRules.value.map((item) => item.team_name)).size;
});

const dailyRotationCount = computed(() => {
    return filteredRules.value.filter((item) => item.cycle_days === 1).length;
});

const weeklyRotationCount = computed(() => {
    return filteredRules.value.filter((item) => item.cycle_days === 7).length;
});

const resetForm = () => {
    form.value = {
        team_name: "",
        anchor_date: getTodayDate(),
        shift_start: "",
        shift_end: "",
        tier1_name: "",
        tier2_name: "",
        tier3_name: "",
        cycle_days: 7,
        note: ""
    };
    editMode.value = false;
    editingId.value = null;
};

const startCreate = () => {
    resetForm();
    successMessage.value = "";
    pageError.value = "";
};

const handleSave = () => {
    pageError.value = "";
    successMessage.value = "";

    if (!form.value.team_name || !form.value.anchor_date || !form.value.shift_start || !form.value.shift_end) {
        pageError.value = "Please complete all required fields.";
        return;
    }

    const payload = {
        ...form.value,
        shift_label: `${form.value.shift_start} - ${form.value.shift_end}`
    };

    if (editMode.value && editingId.value !== null) {
        const target = shiftRules.value.find((item) => item.id === editingId.value);
        if (!target) {
            pageError.value = "Selected shift rule not found.";
            return;
        }

        Object.assign(target, payload);
        successMessage.value = "Shift rule updated successfully. The calendar will reflect this logic. (mock)";
    } else {
        shiftRules.value.unshift({
            id: Date.now(),
            ...payload
        });
        successMessage.value = `Shift rule created successfully. This will generate endless future slots. (mock)`;
    }

    resetForm();
};

const handleEdit = (item) => {
    editMode.value = true;
    editingId.value = item.id;

    form.value = {
        team_name: item.team_name || "",
        anchor_date: item.anchor_date || "",
        shift_start: item.shift_start || "",
        shift_end: item.shift_end || "",
        tier1_name: item.tier1_name || "",
        tier2_name: item.tier2_name || "",
        tier3_name: item.tier3_name || "",
        cycle_days: item.cycle_days || 7,
        note: item.note || ""
    };

    successMessage.value = "";
    pageError.value = "";
};

const handleDelete = (item) => {
    shiftRules.value = shiftRules.value.filter((row) => row.id !== item.id);
    successMessage.value = `Shift rule for ${item.team_name} deleted. (mock)`;

    if (editingId.value === item.id) {
        resetForm();
    }
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

.filter-dropdown,
.filter-dropdown {
    min-width: 170px;
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