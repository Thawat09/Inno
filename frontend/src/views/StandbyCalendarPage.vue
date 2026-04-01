<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Standby Calendar</div>
                        <div class="page-subtitle">
                            View standby schedule by team, date, and tier coverage.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Today"
                            icon="pi pi-calendar"
                            severity="secondary"
                            outlined
                            @click="goToday"
                        />
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadSchedules"
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
                        <div class="summary-label">Schedules</div>
                        <div class="summary-value">{{ filteredSchedules.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Teams</div>
                        <div class="summary-value">{{ uniqueTeamCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Today Tier 1</div>
                        <div class="summary-value">{{ todayTier1Count }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Unavailable Slots</div>
                        <div class="summary-value">{{ unavailableCount }}</div>
                    </div>
                </div>

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
                            v-model="viewMode"
                            :options="viewOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="View Mode"
                            class="filter-dropdown"
                        />
                    </div>

                    <div class="toolbar-date">
                        <label class="toolbar-date-label">Reference Date</label>
                        <InputText
                            v-model="selectedDate"
                            type="date"
                            class="date-input"
                        />
                    </div>
                </div>

                <div class="calendar-meta-bar">
                    <div class="calendar-meta-title">
                        {{ currentViewTitle }}
                    </div>
                    <div class="calendar-meta-subtitle">
                        Team:
                        <strong>{{ selectedTeamLabel }}</strong>
                    </div>
                </div>

                <Card class="content-card">
                    <template #title>
                        <span>Standby Schedule</span>
                    </template>

                    <template #content>
                        <DataTable
                            :value="filteredSchedules"
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

                            <Column field="team_name" header="Team" style="min-width: 180px" />

                            <Column field="shift_label" header="Shift" style="min-width: 160px">
                                <template #body="{ data }">
                                    {{ data.shift_label }}
                                </template>
                            </Column>

                            <Column header="Tier 1" style="min-width: 220px">
                                <template #body="{ data }">
                                    <div class="tier-user-box">
                                        <div class="tier-user-name">
                                            {{ data.tier1_name || "-" }}
                                        </div>
                                        <div class="tier-user-sub">
                                            {{ data.tier1_status || "-" }}
                                        </div>
                                    </div>
                                </template>
                            </Column>

                            <Column header="Tier 2" style="min-width: 220px">
                                <template #body="{ data }">
                                    <div class="tier-user-box">
                                        <div class="tier-user-name">
                                            {{ data.tier2_name || "-" }}
                                        </div>
                                        <div class="tier-user-sub">
                                            {{ data.tier2_status || "-" }}
                                        </div>
                                    </div>
                                </template>
                            </Column>

                            <Column header="Tier 3" style="min-width: 220px">
                                <template #body="{ data }">
                                    <div class="tier-user-box">
                                        <div class="tier-user-name">
                                            {{ data.tier3_name || "-" }}
                                        </div>
                                        <div class="tier-user-sub">
                                            {{ data.tier3_status || "-" }}
                                        </div>
                                    </div>
                                </template>
                            </Column>

                            <Column header="Coverage" style="min-width: 140px">
                                <template #body="{ data }">
                                    <span
                                        class="status-badge"
                                        :class="data.coverage_ok ? 'status-active' : 'status-inactive'"
                                    >
                                        {{ data.coverage_ok ? "Covered" : "Gap" }}
                                    </span>
                                </template>
                            </Column>

                            <template #empty>
                                <div class="empty-box">
                                    No standby schedules found.
                                </div>
                            </template>
                        </DataTable>
                    </template>
                </Card>

                <div class="page-two-column">
                    <Card class="content-card">
                        <template #title>
                            <span>Current Active Coverage</span>
                        </template>

                        <template #content>
                            <div v-if="activeCoverage.length" class="coverage-list">
                                <div
                                    v-for="item in activeCoverage"
                                    :key="item.id"
                                    class="coverage-card"
                                >
                                    <div class="coverage-top">
                                        <div class="coverage-team">{{ item.team_name }}</div>
                                        <span
                                            class="status-badge"
                                            :class="item.coverage_ok ? 'status-active' : 'status-inactive'"
                                        >
                                            {{ item.coverage_ok ? "Covered" : "Gap" }}
                                        </span>
                                    </div>

                                    <div class="coverage-shift">{{ item.shift_label }}</div>

                                    <div class="coverage-tier-row">
                                        <strong>Tier 1:</strong> {{ item.tier1_name || "-" }}
                                    </div>
                                    <div class="coverage-tier-row">
                                        <strong>Tier 2:</strong> {{ item.tier2_name || "-" }}
                                    </div>
                                    <div class="coverage-tier-row">
                                        <strong>Tier 3:</strong> {{ item.tier3_name || "-" }}
                                    </div>
                                </div>
                            </div>

                            <div v-else class="empty-box">
                                No active coverage found for selected date.
                            </div>
                        </template>
                    </Card>

                    <Card class="content-card">
                        <template #title>
                            <span>Coverage Notes</span>
                        </template>

                        <template #content>
                            <div class="notes-list">
                                <div class="note-item">
                                    <div class="note-title">Tier Coverage Rule</div>
                                    <div class="note-desc">
                                        If a tier is unavailable, the next tier should be considered for escalation.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">Unavailable Members</div>
                                    <div class="note-desc">
                                        Unavailable or inactive members should be skipped automatically in future backend logic.
                                    </div>
                                </div>

                                <div class="note-item">
                                    <div class="note-title">View Mode</div>
                                    <div class="note-desc">
                                        Monthly and weekly views are simplified in this frontend version and are ready for enhancement later.
                                    </div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for standby roster, team shift logic, and tier escalation rules.
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

const pageError = ref("");
const teamFilter = ref("all");
const viewMode = ref("day");
const selectedDate = ref(getTodayDate());
const schedules = ref([]);

const viewOptions = [
    { label: "Daily View", value: "day" },
    { label: "Weekly View", value: "week" },
    { label: "Monthly View", value: "month" }
];

const mockSchedules = [
    {
        id: 1,
        date: "2026-04-01",
        team_name: "Cloud Operations",
        shift_label: "08:00 - 16:00",
        tier1_name: "Admin User",
        tier1_status: "Available",
        tier2_name: "Narin Sukjai",
        tier2_status: "Available",
        tier3_name: "Mali Kanit",
        tier3_status: "Unavailable",
        coverage_ok: true
    },
    {
        id: 2,
        date: "2026-04-01",
        team_name: "Security Operations",
        shift_label: "08:00 - 16:00",
        tier1_name: "Super Admin",
        tier1_status: "Available",
        tier2_name: "Ploy Jinda",
        tier2_status: "Available",
        tier3_name: "",
        tier3_status: "",
        coverage_ok: true
    },
    {
        id: 3,
        date: "2026-04-01",
        team_name: "Standby Support",
        shift_label: "16:00 - 00:00",
        tier1_name: "User One",
        tier1_status: "Unavailable",
        tier2_name: "Krit Meechai",
        tier2_status: "Available",
        tier3_name: "",
        tier3_status: "",
        coverage_ok: false
    },
    {
        id: 4,
        date: "2026-04-02",
        team_name: "Cloud Operations",
        shift_label: "08:00 - 16:00",
        tier1_name: "Admin User",
        tier1_status: "Available",
        tier2_name: "Narin Sukjai",
        tier2_status: "Available",
        tier3_name: "Mali Kanit",
        tier3_status: "Available",
        coverage_ok: true
    },
    {
        id: 5,
        date: "2026-04-03",
        team_name: "Security Operations",
        shift_label: "08:00 - 16:00",
        tier1_name: "Super Admin",
        tier1_status: "Available",
        tier2_name: "Ploy Jinda",
        tier2_status: "Unavailable",
        tier3_name: "",
        tier3_status: "",
        coverage_ok: true
    },
    {
        id: 6,
        date: "2026-04-10",
        team_name: "Standby Support",
        shift_label: "00:00 - 08:00",
        tier1_name: "Krit Meechai",
        tier1_status: "Available",
        tier2_name: "User One",
        tier2_status: "Available",
        tier3_name: "",
        tier3_status: "",
        coverage_ok: true
    }
];

function getTodayDate() {
    return new Date().toISOString().slice(0, 10);
}

const loadSchedules = () => {
    pageError.value = "";

    try {
        schedules.value = [...mockSchedules];
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load standby schedules.";
    }
};

const teamOptions = computed(() => {
    const teams = [...new Set(schedules.value.map((item) => item.team_name))];
    return [
        { label: "All Teams", value: "all" },
        ...teams.map((team) => ({ label: team, value: team }))
    ];
});

const selectedTeamLabel = computed(() => {
    const found = teamOptions.value.find((item) => item.value === teamFilter.value);
    return found?.label || "All Teams";
});

const filteredSchedules = computed(() => {
    let data = [...schedules.value];

    if (teamFilter.value !== "all") {
        data = data.filter((item) => item.team_name === teamFilter.value);
    }

    if (viewMode.value === "day") {
        data = data.filter((item) => item.date === selectedDate.value);
    } else if (viewMode.value === "week") {
        const start = new Date(selectedDate.value);
        const end = new Date(selectedDate.value);
        end.setDate(end.getDate() + 6);

        data = data.filter((item) => {
            const current = new Date(item.date);
            return current >= start && current <= end;
        });
    } else if (viewMode.value === "month") {
        const month = selectedDate.value.slice(0, 7);
        data = data.filter((item) => item.date.startsWith(month));
    }

    return data.sort((a, b) => {
        if (a.date === b.date) {
            return a.team_name.localeCompare(b.team_name);
        }
        return a.date.localeCompare(b.date);
    });
});

const currentViewTitle = computed(() => {
    if (viewMode.value === "day") {
        return `Daily Schedule - ${formatDate(selectedDate.value)}`;
    }
    if (viewMode.value === "week") {
        return `Weekly Schedule from ${formatDate(selectedDate.value)}`;
    }
    return `Monthly Schedule - ${selectedDate.value.slice(0, 7)}`;
});

const uniqueTeamCount = computed(() => {
    return new Set(filteredSchedules.value.map((item) => item.team_name)).size;
});

const todayTier1Count = computed(() => {
    return schedules.value.filter(
        (item) => item.date === selectedDate.value && item.tier1_name
    ).length;
});

const unavailableCount = computed(() => {
    return filteredSchedules.value.filter(
        (item) =>
            item.tier1_status === "Unavailable" ||
            item.tier2_status === "Unavailable" ||
            item.tier3_status === "Unavailable"
    ).length;
});

const activeCoverage = computed(() => {
    return schedules.value.filter((item) => item.date === selectedDate.value);
});

const goToday = () => {
    selectedDate.value = getTodayDate();
    viewMode.value = "day";
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
    loadSchedules();
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

.toolbar-filters {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.toolbar-date {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.toolbar-date-label {
    font-weight: 600;
    color: var(--text-color);
}

.filter-dropdown {
    min-width: 180px;
}

.date-input {
    min-width: 180px;
}

.calendar-meta-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    padding: 1rem 1.1rem;
    border: 1px solid var(--border-color);
    border-radius: 16px;
    background: var(--card-bg);
    margin-bottom: 1rem;
}

.calendar-meta-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-color);
}

.calendar-meta-subtitle {
    color: var(--text-muted);
}

.tier-user-box {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.tier-user-name {
    font-weight: 600;
    color: var(--text-color);
}

.tier-user-sub {
    font-size: 0.88rem;
    color: var(--text-muted);
}

.page-two-column {
    display: grid;
    grid-template-columns: 1.1fr 1fr;
    gap: 1rem;
    margin-top: 1rem;
}

.coverage-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.coverage-card {
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1rem;
    background: var(--card-bg);
}

.coverage-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.4rem;
}

.coverage-team {
    font-weight: 700;
    color: var(--text-color);
}

.coverage-shift {
    color: var(--text-muted);
    margin-bottom: 0.75rem;
}

.coverage-tier-row {
    color: var(--text-color);
    margin-bottom: 0.35rem;
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

    .toolbar-date {
        align-items: flex-start;
        flex-direction: column;
    }
}
</style>