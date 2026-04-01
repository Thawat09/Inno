<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Calendar Management</div>
                        <div class="page-subtitle">
                            Manage standby roster, shift coverage, and tier assignment by team and date.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="New Slot"
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
                <Message v-if="pageError" severity="error" class="mb-3">
                    {{ pageError }}
                </Message>

                <Message v-if="successMessage" severity="success" class="mb-3">
                    {{ successMessage }}
                </Message>

                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Filtered Slots</div>
                        <div class="summary-value">{{ filteredRosters.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Teams</div>
                        <div class="summary-value">{{ uniqueTeamCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Coverage Gaps</div>
                        <div class="summary-value">{{ coverageGapCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Today Slots</div>
                        <div class="summary-value">{{ todaySlotCount }}</div>
                    </div>
                </div>

                <div class="page-two-column">
                    <Card class="content-card">
                        <template #title>
                            <span>{{ editMode ? 'Edit Slot' : 'Create Slot' }}</span>
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
                                    <label>Date</label>
                                    <InputText
                                        v-model="form.date"
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
                                    <label>Coverage Status</label>
                                    <Dropdown
                                        v-model="form.coverage_ok"
                                        :options="coverageOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select coverage"
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
                                        :label="editMode ? 'Update Slot' : 'Create Slot'"
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
                                    <div class="note-title">Shift Logic</div>
                                    <div class="note-desc">
                                        Each slot should represent one time range with assigned standby tiers.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Coverage Gap</div>
                                    <div class="note-desc">
                                        If Tier 1 is unavailable or empty, future backend logic should evaluate fallback handling.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Future Features</div>
                                    <div class="note-desc">
                                        Bulk edit, copy previous month, import/export, and impact preview can be added later.
                                    </div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>

                <Card class="content-card">
                    <template #title>
                        <span>Roster Table</span>
                    </template>

                    <template #content>
                        <div class="toolbar-row">
                            <div class="toolbar-search">
                                <i class="pi pi-search toolbar-search-icon"></i>
                                <InputText
                                    v-model="searchText"
                                    placeholder="Search team, date, tier user..."
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
                                <InputText
                                    v-model="dateFilter"
                                    type="date"
                                    class="date-filter"
                                />
                            </div>
                        </div>

                        <DataTable
                            :value="filteredRosters"
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

                            <Column field="date" header="Date" style="min-width: 140px">
                                <template #body="{ data }">
                                    {{ formatDate(data.date) }}
                                </template>
                            </Column>

                            <Column field="team_name" header="Team" style="min-width: 170px" />

                            <Column field="shift_label" header="Shift" style="min-width: 150px" />

                            <Column field="tier1_name" header="Tier 1" style="min-width: 170px">
                                <template #body="{ data }">
                                    {{ data.tier1_name || "-" }}
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

                            <Column header="Coverage" style="min-width: 130px">
                                <template #body="{ data }">
                                    <span
                                        class="status-badge"
                                        :class="data.coverage_ok ? 'status-active' : 'status-inactive'"
                                    >
                                        {{ data.coverage_ok ? "Covered" : "Gap" }}
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
                                    No roster slots found.
                                </div>
                            </template>
                        </DataTable>
                    </template>
                </Card>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for roster management, bulk edit, import/export, and schedule impact analysis.
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
const dateFilter = ref("");
const editMode = ref(false);
const editingId = ref(null);
const rosters = ref([]);

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

const coverageOptions = [
    { label: "Covered", value: true },
    { label: "Gap", value: false }
];

const form = ref({
    team_name: "",
    date: "",
    shift_start: "",
    shift_end: "",
    tier1_name: "",
    tier2_name: "",
    tier3_name: "",
    coverage_ok: true,
    note: ""
});

const mockRosters = [
    {
        id: 1,
        date: "2026-04-01",
        team_name: "Cloud Operations",
        shift_start: "08:00",
        shift_end: "16:00",
        shift_label: "08:00 - 16:00",
        tier1_name: "Admin User",
        tier2_name: "Narin Sukjai",
        tier3_name: "Mali Kanit",
        coverage_ok: true,
        note: "Business hours shift"
    },
    {
        id: 2,
        date: "2026-04-01",
        team_name: "Security Operations",
        shift_start: "08:00",
        shift_end: "16:00",
        shift_label: "08:00 - 16:00",
        tier1_name: "Super Admin",
        tier2_name: "Ploy Jinda",
        tier3_name: "",
        coverage_ok: true,
        note: "SOC monitoring shift"
    },
    {
        id: 3,
        date: "2026-04-01",
        team_name: "Standby Support",
        shift_start: "16:00",
        shift_end: "00:00",
        shift_label: "16:00 - 00:00",
        tier1_name: "User One",
        tier2_name: "Krit Meechai",
        tier3_name: "",
        coverage_ok: false,
        note: "Tier 1 may be unavailable"
    },
    {
        id: 4,
        date: "2026-04-02",
        team_name: "Cloud Operations",
        shift_start: "08:00",
        shift_end: "16:00",
        shift_label: "08:00 - 16:00",
        tier1_name: "Admin User",
        tier2_name: "Narin Sukjai",
        tier3_name: "Mali Kanit",
        coverage_ok: true,
        note: ""
    }
];

const getTodayDate = () => new Date().toISOString().slice(0, 10);

const loadRosters = () => {
    pageError.value = "";
    successMessage.value = "";

    try {
        rosters.value = [...mockRosters];
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load calendar roster data.";
    }
};

const filteredRosters = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    return rosters.value.filter((item) => {
        const matchKeyword = !keyword
            ? true
            : [
                  item.team_name,
                  item.date,
                  item.shift_label,
                  item.tier1_name,
                  item.tier2_name,
                  item.tier3_name,
                  item.note
              ]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        const matchTeam =
            teamFilter.value === "all" ? true : item.team_name === teamFilter.value;

        const matchDate =
            !dateFilter.value ? true : item.date === dateFilter.value;

        return matchKeyword && matchTeam && matchDate;
    });
});

const uniqueTeamCount = computed(() => {
    return new Set(filteredRosters.value.map((item) => item.team_name)).size;
});

const coverageGapCount = computed(() => {
    return filteredRosters.value.filter((item) => !item.coverage_ok).length;
});

const todaySlotCount = computed(() => {
    const today = getTodayDate();
    return rosters.value.filter((item) => item.date === today).length;
});

const resetForm = () => {
    form.value = {
        team_name: "",
        date: "",
        shift_start: "",
        shift_end: "",
        tier1_name: "",
        tier2_name: "",
        tier3_name: "",
        coverage_ok: true,
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

    if (!form.value.team_name || !form.value.date || !form.value.shift_start || !form.value.shift_end) {
        pageError.value = "Please complete all required fields.";
        return;
    }

    const payload = {
        ...form.value,
        shift_label: `${form.value.shift_start} - ${form.value.shift_end}`
    };

    if (editMode.value && editingId.value !== null) {
        const target = rosters.value.find((item) => item.id === editingId.value);
        if (!target) {
            pageError.value = "Selected roster slot not found.";
            return;
        }

        Object.assign(target, payload);
        successMessage.value = "Roster slot updated successfully. (mock)";
    } else {
        rosters.value.unshift({
            id: Date.now(),
            ...payload
        });
        successMessage.value = "Roster slot created successfully. (mock)";
    }

    resetForm();
};

const handleEdit = (item) => {
    editMode.value = true;
    editingId.value = item.id;

    form.value = {
        team_name: item.team_name || "",
        date: item.date || "",
        shift_start: item.shift_start || "",
        shift_end: item.shift_end || "",
        tier1_name: item.tier1_name || "",
        tier2_name: item.tier2_name || "",
        tier3_name: item.tier3_name || "",
        coverage_ok: item.coverage_ok ?? true,
        note: item.note || ""
    };

    successMessage.value = "";
    pageError.value = "";
};

const handleDelete = (item) => {
    rosters.value = rosters.value.filter((row) => row.id !== item.id);
    successMessage.value = `Roster slot ${item.team_name} ${item.date} deleted. (mock)`;

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
    loadRosters();
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
.date-filter {
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