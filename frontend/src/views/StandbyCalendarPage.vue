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
                <div v-if="isLoading" class="loading-state">
                    <ProgressSpinner style="width: 50px; height: 50px" />
                </div>
                <template v-else>
                <Message v-if="pageError" severity="error" class="mb-3">
                    {{ pageError }}
                </Message>

                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Filtered Schedules</div>
                        <div class="summary-value">{{ filteredSchedules.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Total Teams</div>
                        <div class="summary-value">{{ uniqueTeamCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Active T1 Today</div>
                        <div class="summary-value">{{ todayTier1Count }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Unavailable Slots</div>
                        <div class="summary-value">{{ unavailableCount }}</div>
                    </div>
                </div>

                <div class="toolbar-row">
                    <div class="toolbar-title">
                        <h2>Monthly Standby Roster</h2>
                    </div>

                    <div class="toolbar-date">
                        <label class="toolbar-date-label">Month / Year:</label>
                        <InputText
                            v-model="selectedMonth"
                            type="month"
                            class="date-input"
                        />
                    </div>
                </div>

                <Card class="content-card">
                    <template #content>
                        <TabView :activeIndex="activeTabIndex" @update:activeIndex="activeTabIndex = $event">
                            <TabPanel v-for="teamCal in teamCalendars" :key="teamCal.team_name" :header="teamCal.team_name">
                                <div class="calendar-legend">
                                    <div class="legend-item"><span class="legend-color t1-color"></span> Tier 1 (Primary)</div>
                                    <div class="legend-item"><span class="legend-color t2-color"></span> Tier 2 (Backup)</div>
                                    <div class="legend-item"><span class="legend-color t3-color"></span> Tier 3 (Escalation)</div>
                                    <div class="legend-item"><span class="legend-color gap-color"></span> Gap / Unavailable</div>
                                </div>
                                
                                <div class="calendar-month-view">
                                    <div class="calendar-days-header">
                                        <div>Sun</div><div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div>
                                    </div>
                                    <div class="calendar-grid">
                                        <div v-for="(day, idx) in teamCal.days" :key="idx" 
                                             class="calendar-cell" :class="{'empty-cell': !day.dayOfMonth, 'is-today': day.isToday}">
                                            <div class="cell-date" v-if="day.dayOfMonth">{{ day.dayOfMonth }}</div>
                                            <div class="cell-events" v-if="day.dayOfMonth">
                                                <div v-for="evt in day.events" :key="evt.id" 
                                                     class="event-chip" 
                                                     :class="[
                                                         `tier-${evt.tierLevel}-chip`,
                                                         {
                                                             'gap': evt.gap,
                                                             'span-start': evt.spanStart,
                                                             'span-middle': evt.spanMiddle,
                                                             'span-end': evt.spanEnd,
                                                             'span-start-of-week': evt.isStartOfWeek,
                                                             'span-end-of-week': evt.isEndOfWeek
                                                         }
                                                     ]">
                                                    <div v-if="!evt.hideText" class="evt-content">
                                                        <span class="evt-user">T{{ evt.tierLevel }}: {{ evt.display_name }}</span>
                                                    </div>
                                                    <div v-else class="evt-content hidden-text">&nbsp;</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </TabPanel>
                        </TabView>
                    </template>
                </Card>

                <div class="page-two-column">
                    <Card class="content-card">
                        <template #title>
                            <span>Active Coverage (Today)</span>
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

                                    <div class="coverage-tier-detail t1" :class="{'gap': item.tier1_status === 'Unavailable'}">
                                        <div class="tier-badge">T1</div>
                                        <div class="tier-contact-info">
                                            <div class="tier-person-name">{{ item.tier1_name || "Unassigned" }}</div>
                                            <div class="tier-person-phone" v-if="item.tier1_phone">
                                                <i class="pi pi-phone"></i> {{ item.tier1_phone }}
                                            </div>
                                        </div>
                                    </div>

                                    <div class="coverage-tier-detail t2" :class="{'gap': item.tier2_status === 'Unavailable'}" v-if="item.tier2_name">
                                        <div class="tier-badge">T2</div>
                                        <div class="tier-contact-info">
                                            <div class="tier-person-name">{{ item.tier2_name }}</div>
                                            <div class="tier-person-phone" v-if="item.tier2_phone">
                                                <i class="pi pi-phone"></i> {{ item.tier2_phone }}
                                            </div>
                                        </div>
                                    </div>

                                    <div class="coverage-tier-detail t3" :class="{'gap': item.tier3_status === 'Unavailable'}" v-if="item.tier3_name">
                                        <div class="tier-badge">T3</div>
                                        <div class="tier-contact-info">
                                            <div class="tier-person-name">{{ item.tier3_name }}</div>
                                            <div class="tier-person-phone" v-if="item.tier3_phone">
                                                <i class="pi pi-phone"></i> {{ item.tier3_phone }}
                                            </div>
                                        </div>
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
                                    <div class="note-title">Contact & Escalation</div>
                                    <div class="note-desc">
                                        Use the provided phone numbers for emergency contact if the assignee does not respond to LINE notifications.
                                    </div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>

                <div class="mock-note mt-3">
                    This page demonstrates dynamic recurring shifts (e.g., 7-day Monday rotations, daily rotations).
                    In the final backend, these slots are generated automatically from `standby_shift_rules`.
                </div>
                </template>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';

const isLoading = ref(true);
const pageError = ref("");
const activeTabIndex = ref(0);
const selectedMonth = ref(getTodayMonth());
const schedules = ref([]);

const teamRotations = [
    {
        team_name: "Cloud Operations",
        shift_label: "08:30 - 08:30",
        cycle_days: 7,
        anchor_date: "2024-01-01", // A known Monday
        roster: [
            { tier1_name: "Admin User", tier2_name: "Narin Sukjai", tier3_name: "Mali Kanit" },
            { tier1_name: "Narin Sukjai", tier2_name: "Admin User", tier3_name: "" }
        ]
    },
    {
        team_name: "Security Operations",
        shift_label: "08:00 - 16:00",
        cycle_days: 1, // Daily rotation
        anchor_date: "2024-01-01",
        roster: [
            { tier1_name: "Super Admin", tier2_name: "Ploy Jinda", tier3_name: "" },
            { tier1_name: "Ploy Jinda", tier2_name: "Super Admin", tier3_name: "" },
            { tier1_name: "Mali Kanit", tier2_name: "Ploy Jinda", tier3_name: "" }
        ]
    },
    {
        team_name: "Standby Support",
        shift_label: "16:00 - 00:00",
        cycle_days: 7,
        anchor_date: "2024-01-03", // A known Wednesday
        roster: [
            { tier1_name: "Krit Meechai", tier2_name: "User One", tier3_name: "" },
            { tier1_name: "User One", tier2_name: "Krit Meechai", tier3_name: "" }
        ]
    }
];

const generateMockSchedules = (yearMonth) => {
    const results = [];
    let idCounter = 1;
    const [year, month] = yearMonth.split('-');
    
    // Expand generation window to cover overlapping weeks (1 month before and after)
    const windowStart = new Date(year, parseInt(month) - 2, 15).toISOString().slice(0, 10);
    const windowEnd = new Date(year, parseInt(month), 15).toISOString().slice(0, 10);

    const getDaysDiff = (d1, d2) => {
        const date1 = new Date(d1 + "T12:00:00Z");
        const date2 = new Date(d2 + "T12:00:00Z");
        return Math.floor((date2 - date1) / (1000 * 60 * 60 * 24));
    };

    const addDays = (dateStr, days) => {
        const d = new Date(dateStr + "T12:00:00Z");
        d.setDate(d.getDate() + days);
        return d.toISOString().slice(0, 10);
    };

    teamRotations.forEach(team => {
        const diff = getDaysDiff(team.anchor_date, windowStart);
        let cycleIndex = Math.floor(diff / team.cycle_days);
        let currentStart = addDays(team.anchor_date, cycleIndex * team.cycle_days);

        while (currentStart <= windowEnd) {
            const currentEnd = addDays(currentStart, team.cycle_days - 1);
            
            let rosterIndex = cycleIndex % team.roster.length;
            if (rosterIndex < 0) rosterIndex += team.roster.length;
            const roster = team.roster[rosterIndex];

            // Example: Make someone unavailable randomly (only on the 15th of the month) for visual feedback
            const isGap = currentStart.endsWith("-15");

            results.push({
                id: idCounter++,
                start_date: currentStart,
                end_date: currentEnd,
                team_name: team.team_name,
                shift_label: team.shift_label,
                tier1_name: roster.tier1_name,
                tier1_phone: "089-999-9999",
                tier1_status: isGap ? "Unavailable" : "Available",
                tier2_name: roster.tier2_name,
                tier2_phone: "081-111-1111",
                tier2_status: "Available",
                tier3_name: roster.tier3_name,
                tier3_phone: "082-222-2222",
                tier3_status: "Available",
                coverage_ok: !isGap
            });

            currentStart = addDays(currentStart, team.cycle_days);
            cycleIndex++;
        }
    });
    return results;
};

function getTodayMonth() {
    return new Date().toISOString().slice(0, 7);
}

function getTodayDate() {
    return new Date().toISOString().slice(0, 10);
}

const loadSchedules = () => {
    isLoading.value = true;
    pageError.value = "";

    setTimeout(() => {
        try {
            schedules.value = generateMockSchedules(selectedMonth.value);
        } catch (error) {
            console.error(error);
            pageError.value = "Unable to load standby schedules.";
        } finally {
            isLoading.value = false;
        }
    }, 300); // Shorter loading time to make month-switching feel smoother
};

const teamCalendars = computed(() => {
    if (!selectedMonth.value || !schedules.value.length) return [];
    const [yearStr, monthStr] = selectedMonth.value.split('-');
    const year = parseInt(yearStr);
    const month = parseInt(monthStr) - 1;
    
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDayIndex = new Date(year, month, 1).getDay();
    
    const teams = [...new Set(schedules.value.map(s => s.team_name))];
    
    return teams.map(teamName => {
        const days = [];
        for(let i=0; i<firstDayIndex; i++) {
            days.push({ date: `empty-${i}`, dayOfMonth: '', events: [] });
        }
        
        for(let i=1; i<=daysInMonth; i++) {
            const dStr = `${year}-${String(month+1).padStart(2,'0')}-${String(i).padStart(2,'0')}`;
            const dayOfWeek = new Date(dStr).getDay();
            
            const daySchedules = schedules.value.filter(s => 
                s.team_name === teamName && dStr >= s.start_date && dStr <= s.end_date
            );
            
            const events = [];
            daySchedules.forEach(s => {
                const isStart = dStr === s.start_date;
                const isEnd = dStr === s.end_date;
                const baseSpan = {
                    spanStart: isStart && !isEnd,
                    spanMiddle: !isStart && !isEnd,
                    spanEnd: !isStart && isEnd,
                    isStartOfWeek: dayOfWeek === 0,
                    isEndOfWeek: dayOfWeek === 6,
                    hideText: !isStart && dayOfWeek !== 0
                };
                
                if (s.tier1_name) events.push({ ...baseSpan, id: `${s.id}-t1`, tierLevel: 1, display_name: s.tier1_name, gap: s.tier1_status === 'Unavailable' });
                if (s.tier2_name) events.push({ ...baseSpan, id: `${s.id}-t2`, tierLevel: 2, display_name: s.tier2_name, gap: s.tier2_status === 'Unavailable' });
                if (s.tier3_name) events.push({ ...baseSpan, id: `${s.id}-t3`, tierLevel: 3, display_name: s.tier3_name, gap: s.tier3_status === 'Unavailable' });
            });
            
            days.push({ date: dStr, dayOfMonth: i, events, isToday: dStr === getTodayDate() });
        }
        
        return { team_name: teamName, days };
    });
});

const activeTeamName = computed(() => {
    if (!teamCalendars.value.length) return "";
    return teamCalendars.value[activeTabIndex.value]?.team_name || "";
});

const filteredSchedules = computed(() => {
    return schedules.value.filter(item => item.team_name === activeTeamName.value);
});

const uniqueTeamCount = computed(() => teamCalendars.value.length);

const todayTier1Count = computed(() => {
    const today = getTodayDate();
    return filteredSchedules.value.filter(
        (item) => today >= item.start_date && today <= item.end_date && item.tier1_name
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
    const today = getTodayDate();
    return filteredSchedules.value.filter((item) => today >= item.start_date && today <= item.end_date);
});

const goToday = () => {
    selectedMonth.value = getTodayMonth();
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

watch(selectedMonth, () => {
    loadSchedules();
});

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

.toolbar-title h2 {
    margin: 0;
    font-size: 1.15rem;
    color: var(--text-color);
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

.date-input {
    min-width: 180px;
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

.coverage-tier-detail {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    border-left: 4px solid transparent;
    background: var(--surface-50);
}
.coverage-tier-detail.t1 { border-left-color: #3b82f6; background: #eff6ff; }
.coverage-tier-detail.t2 { border-left-color: #10b981; background: #ecfdf5; }
.coverage-tier-detail.t3 { border-left-color: #8b5cf6; background: #f5f3ff; }
.coverage-tier-detail.gap { border-left-color: #ef4444; background: #fef2f2; opacity: 0.7; }

.tier-badge {
    font-weight: 700;
    font-size: 0.85rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    background: rgba(0,0,0,0.05);
}
.tier-contact-info {
    display: flex;
    flex-direction: column;
}
.tier-person-name { font-weight: 700; color: var(--text-color); }
.tier-person-phone { font-size: 0.85rem; color: var(--text-muted); margin-top: 2px; }
    
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

.loading-state {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 200px;
}

/* Calendar Grid CSS */
.calendar-legend {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
    padding: 0.5rem 0;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.85rem;
    color: var(--text-muted);
}
.legend-color {
    width: 12px;
    height: 12px;
    border-radius: 3px;
}
.t1-color { background: #3b82f6; }
.t2-color { background: #10b981; }
.t3-color { background: #8b5cf6; }
.gap-color { background: #ef4444; }

.calendar-month-view {
    width: 100%;
}
.calendar-days-header {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    text-align: center;
    font-weight: 700;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}
.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 0.5rem;
}
.calendar-cell {
    border: 1px solid var(--border-color);
    border-radius: 8px;
    min-height: 100px;
    padding: 0.5rem 0;
    background: var(--card-bg);
    display: flex;
    flex-direction: column;
    gap: 0;
}
.calendar-cell.empty-cell {
    background: transparent;
    border: none;
}
.calendar-cell.is-today {
    border: 2px solid #3b82f6;
    background: #eff6ff;
}
.cell-date {
    font-weight: 700;
    font-size: 0.9rem;
    color: var(--text-color);
    padding: 0 0.5rem;
    margin-bottom: 0.2rem;
}
.cell-events {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.event-chip {
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.72rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-height: 22px;
    margin: 0 4px;
}

.tier-1-chip { background: #dbeafe; border-left: 3px solid #3b82f6; color: #1e3a8a; }
.tier-2-chip { background: #d1fae5; border-left: 3px solid #10b981; color: #065f46; }
.tier-3-chip { background: #f3e8ff; border-left: 3px solid #8b5cf6; color: #581c87; }

.event-chip.gap {
    background: #fee2e2 !important;
    border-left-color: #dc2626 !important;
    color: #991b1b !important;
    opacity: 0.8;
}
.event-chip.gap .evt-user {
    text-decoration: line-through;
    color: #7f1d1d !important;
}

.event-chip.span-start {
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    margin-right: 0;
}
.event-chip.span-middle {
    border-radius: 0;
    border-left: none;
    margin-left: 0;
    margin-right: 0;
    padding-left: 0.5rem;
}
.event-chip.span-end {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    border-left: none;
    margin-left: 0;
}
.event-chip.span-start-of-week {
    border-top-left-radius: 4px !important;
    border-bottom-left-radius: 4px !important;
    margin-left: 4px !important;
    padding-left: 0.4rem !important;
}
.event-chip.span-start-of-week.gap {
    border-left-color: #dc2626 !important;
}
.event-chip.span-end-of-week {
    border-top-right-radius: 4px !important;
    border-bottom-right-radius: 4px !important;
    margin-right: 4px !important;
}
.evt-content {
    display: flex;
    gap: 0.3rem;
}
.evt-content.hidden-text {
    visibility: hidden;
}
.evt-user { font-weight: 600; }

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