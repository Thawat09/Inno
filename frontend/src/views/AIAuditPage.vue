<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">AI Audit</div>
                        <div class="page-subtitle">
                            Analyze AI routing predictions, compare with final outcomes, and track accuracy.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" outlined @click="loadData" />
                    </div>
                </div>
            </template>

            <template #content>
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Total Predictions</div>
                        <div class="summary-value">{{ auditData.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Correct</div>
                        <div class="summary-value">{{ correctCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Incorrect</div>
                        <div class="summary-value">{{ incorrectCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Accuracy</div>
                        <div class="summary-value">{{ accuracyRate }}%</div>
                    </div>
                </div>

                <!-- FILTER -->
                <div class="toolbar-row">
                    <div class="toolbar-search">
                        <i class="pi pi-search toolbar-search-icon"></i>
                        <InputText v-model="searchText" placeholder="Search ticket, subject..." />
                    </div>

                    <div class="toolbar-filters">
                        <Dropdown v-model="resultFilter" :options="resultOptions" optionLabel="label"
                            optionValue="value" placeholder="Result" />
                    </div>
                </div>

                <!-- TABLE -->
                <DataTable :value="filteredData" paginator :rows="10" stripedRows responsiveLayout="scroll">
                    <Column field="ticket_no" header="Ticket" style="min-width:140px" />

                    <Column field="subject" header="Subject" style="min-width:260px" />

                    <Column header="AI Prediction" style="min-width:200px">
                        <template #body="{ data }">
                            <div class="audit-block">
                                <div>{{ data.predicted_team }}</div>
                                <div class="sub-text">{{ data.predicted_user }}</div>
                            </div>
                        </template>
                    </Column>

                    <Column header="Final Decision" style="min-width:200px">
                        <template #body="{ data }">
                            <div class="audit-block">
                                <div>{{ data.final_team }}</div>
                                <div class="sub-text">{{ data.final_user }}</div>
                            </div>
                        </template>
                    </Column>

                    <Column field="confidence" header="Confidence" style="min-width:120px">
                        <template #body="{ data }">
                            {{ data.confidence }}%
                        </template>
                    </Column>

                    <Column header="Result" style="min-width:140px">
                        <template #body="{ data }">
                            <span class="status-badge"
                                :class="data.is_correct ? 'status-active' : 'status-inactive'">
                                {{ data.is_correct ? "Correct" : "Incorrect" }}
                            </span>
                        </template>
                    </Column>

                    <Column field="override" header="Override" style="min-width:120px">
                        <template #body="{ data }">
                            {{ data.override ? "Yes" : "No" }}
                        </template>
                    </Column>

                    <Column field="created_at" header="Time" style="min-width:160px">
                        <template #body="{ data }">
                            {{ formatDate(data.created_at) }}
                        </template>
                    </Column>

                    <template #empty>
                        <div class="empty-box">No audit data found.</div>
                    </template>
                </DataTable>

                <div class="mock-note mt-3">
                    This page uses mock AI prediction data. Ready for backend integration with ML model logs.
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

const searchText = ref("");
const resultFilter = ref("all");
const auditData = ref([]);

const resultOptions = [
    { label: "All", value: "all" },
    { label: "Correct", value: "correct" },
    { label: "Incorrect", value: "incorrect" }
];

const mockData = [
    {
        ticket_no: "INC001",
        subject: "Cannot login AWS",
        predicted_team: "Cloud Operations",
        predicted_user: "Admin User",
        final_team: "Cloud Operations",
        final_user: "Admin User",
        confidence: 92,
        is_correct: true,
        override: false,
        created_at: "2026-04-01T09:00:00Z"
    },
    {
        ticket_no: "INC002",
        subject: "Security alert",
        predicted_team: "Cloud Operations",
        predicted_user: "Admin User",
        final_team: "Security Operations",
        final_user: "Super Admin",
        confidence: 60,
        is_correct: false,
        override: true,
        created_at: "2026-04-01T09:05:00Z"
    }
];

const loadData = () => {
    auditData.value = [...mockData];
};

const filteredData = computed(() => {
    return auditData.value.filter(item => {
        const matchSearch = !searchText.value ||
            item.ticket_no.toLowerCase().includes(searchText.value.toLowerCase()) ||
            item.subject.toLowerCase().includes(searchText.value.toLowerCase());

        const matchResult =
            resultFilter.value === "all"
                ? true
                : resultFilter.value === "correct"
                    ? item.is_correct
                    : !item.is_correct;

        return matchSearch && matchResult;
    });
});

const correctCount = computed(() =>
    auditData.value.filter(i => i.is_correct).length
);

const incorrectCount = computed(() =>
    auditData.value.filter(i => !i.is_correct).length
);

const accuracyRate = computed(() => {
    if (!auditData.value.length) return 0;
    return Math.round((correctCount.value / auditData.value.length) * 100);
});

const formatDate = (val) => {
    return new Date(val).toLocaleString("en-GB");
};

onMounted(loadData);
</script>

<style scoped>
.page-title {
    font-size: 1.25rem;
    font-weight: 700;
}

.page-subtitle {
    color: var(--text-muted);
    margin-top: 0.25rem;
    font-size: 0.95rem;
}

.audit-block {
    display: flex;
    flex-direction: column;
}

.sub-text {
    font-size: 0.85rem;
    color: var(--text-muted);
}

.summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1rem;
}

.summary-card {
    padding: 1rem;
    border-radius: 14px;
    border: 1px solid var(--border-color);
}

.summary-value {
    font-size: 1.4rem;
    font-weight: 700;
}

.toolbar-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 1rem;
    gap: 1rem;
    flex-wrap: wrap;
}

.toolbar-search {
    position: relative;
    max-width: 300px;
    width: 100%;
}

.toolbar-search-icon {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
}

.toolbar-search input {
    padding-left: 30px;
}

.empty-box {
    text-align: center;
    padding: 1rem;
    color: var(--text-muted);
}

.mt-3 {
    margin-top: 1rem;
}
</style>