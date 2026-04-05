<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Global Search</div>
                        <div class="page-subtitle">
                            Search tickets, users, teams, notifications, and data mapping from one place.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="runSearch"
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

                <div class="search-bar-row">
                    <div class="toolbar-search large-search">
                        <i class="pi pi-search toolbar-search-icon"></i>
                        <InputText
                            v-model="keyword"
                            placeholder="Search ticket no, subject, requester, email, team, IP, LINE user..."
                            @keyup.enter="applySearch"
                        />
                    </div>

                    <Button
                        label="Search"
                        icon="pi pi-search"
                        @click="applySearch"
                    />
                </div>

                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Total Results</div>
                        <div class="summary-value">{{ filteredResults.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Tickets</div>
                        <div class="summary-value">{{ countByType('ticket') + countByType('task') + countByType('RITM') + countByType('INC') }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Users</div>
                        <div class="summary-value">{{ countByType('user') + countByType('line') }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Emails</div>
                        <div class="summary-value">{{ countByType('email') }}</div>
                    </div>
                </div>

                <div class="toolbar-row">
                    <div class="toolbar-filters">
                        <Dropdown
                            v-model="typeFilter"
                            :options="typeOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Result Type"
                            class="filter-dropdown"
                        />
                    </div>

                    <div class="result-meta">
                        <span class="meta-text">
                            Keyword:
                            <strong>{{ keyword.trim() || '-' }}</strong>
                        </span>
                    </div>
                </div>

                <DataTable
                    :value="filteredResults"
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

                    <Column header="Type" style="min-width: 130px">
                        <template #body="{ data }">
                            <span class="type-chip" :class="typeClass(data.type)">
                                {{ data.type_label }}
                            </span>
                        </template>
                    </Column>

                    <Column header="Title" style="min-width: 260px">
                        <template #body="{ data }">
                            <div class="result-title">{{ data.title }}</div>
                            <div class="result-subtitle">{{ data.subtitle || "-" }}</div>
                        </template>
                    </Column>

                    <Column header="Detail" style="min-width: 320px">
                        <template #body="{ data }">
                            <div class="result-detail">{{ data.detail || "-" }}</div>
                        </template>
                    </Column>

                    <Column header="Reference" style="min-width: 180px">
                        <template #body="{ data }">
                            {{ data.reference || "-" }}
                        </template>
                    </Column>

                    <Column header="Actions" style="min-width: 140px">
                        <template #body="{ data }">
                            <Button
                                label="Open"
                                icon="pi pi-arrow-right"
                                size="small"
                                @click="handleOpen(data)"
                            />
                        </template>
                    </Column>

                    <template #empty>
                        <div class="empty-box">
                            No search results found.
                        </div>
                    </template>
                </DataTable>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend integration
                    for full-text search across tickets, users, teams, notifications, and mapping issues.
                </div>
                </template>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const isLoading = ref(true);
const pageError = ref("");
const keyword = ref("");
const typeFilter = ref("all");
const results = ref([]);

const typeOptions = [
    { label: "All Types", value: "all" },
    { label: "Ticket", value: "ticket" },
    { label: "Task", value: "task" },
    { label: "RITM", value: "RITM" },
    { label: "INC", value: "INC" },
    { label: "Email", value: "email" },
    { label: "User", value: "user" },
    { label: "LINE", value: "line" }
];

const mockResults = [
    {
        id: "T-001",
        type: "ticket",
        type_label: "Ticket",
        title: "INC000123",
        subtitle: "Cannot access AWS console",
        detail: "Requester: user1@company.com | Team: Cloud Operations | Status: Open",
        reference: "INC000123",
        route: "/tickets"
    },
    {
        id: "T-002",
        type: "RITM",
        type_label: "RITM",
        title: "RITM000245",
        subtitle: "Request standby escalation review",
        detail: "Requester: admin@company.com | Team: Security Operations | Status: Escalated",
        reference: "RITM000245",
        route: "/tickets"
    },
    {
        id: "U-001",
        type: "user",
        type_label: "User",
        title: "Admin User",
        subtitle: "admin@company.com",
        detail: "Role: Admin | Team: Cloud Operations",
        reference: "EMP-0002",
        route: "/users"
    },
    {
        id: "U-002",
        type: "user",
        type_label: "User",
        title: "Super Admin",
        subtitle: "superadmin@company.com",
        detail: "Role: Super Admin | Team: Management",
        reference: "EMP-0003",
        route: "/users"
    },
    {
        id: "E-001",
        type: "email",
        type_label: "Email",
        title: "System Alert: DB High Load",
        subtitle: "From: monitor@company.com",
        detail: "Email parsed but unmapped. Received at 08:00 AM.",
        reference: "MSG-10023",
        route: "/search"
    },
    {
        id: "L-001",
        type: "line",
        type_label: "LINE",
        title: "Narin Sukjai (LINE)",
        subtitle: "line-user-9988",
        detail: "Mapped to Employee EMP-0004",
        reference: "LINE-9988",
        route: "/data-mapping"
    }
];

const normalize = (value) => String(value || "").toLowerCase();

const runSearch = () => {
    isLoading.value = true;
    pageError.value = "";

    setTimeout(() => {
        try {
            const q = keyword.value.trim().toLowerCase();
            if (!q) {
                results.value = [...mockResults];
            } else {
                results.value = mockResults.filter((item) =>
                    [item.title, item.subtitle, item.detail, item.reference, item.type_label]
                        .some((value) => normalize(value).includes(q))
                );
            }
        } catch (error) {
            console.error(error);
            pageError.value = "Unable to run global search.";
        } finally {
            isLoading.value = false;
        }
    }, 600);
};

const applySearch = () => {
    router.replace({
        path: "/search",
        query: keyword.value.trim() ? { q: keyword.value.trim() } : {}
    });
};

const filteredResults = computed(() => {
    return results.value.filter((item) => {
        return typeFilter.value === "all" ? true : item.type === typeFilter.value;
    });
});

const countByType = (type) => {
    return filteredResults.value.filter((item) => item.type === type).length;
};

const typeClass = (type) => {
    switch (type) {
        case "ticket":
        case "INC":
            return "type-ticket";
        case "task":
        case "RITM":
            return "type-task";
        case "user":
            return "type-user";
        case "line":
            return "type-line";
        case "email":
            return "type-email";
        default:
            return "";
    }
};

const handleOpen = (item) => {
    if (!item.route) return;
    router.push(item.route);
};

watch(
    () => route.query.q,
    (newValue) => {
        keyword.value = String(newValue || "");
        runSearch();
    },
    { immediate: true }
);

onMounted(() => {
    keyword.value = String(route.query.q || "");
    runSearch();
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

.search-bar-row {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}

.large-search {
    flex: 1;
    min-width: 280px;
}

.toolbar-search {
    position: relative;
    width: 100%;
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

.filter-dropdown {
    min-width: 180px;
}

.result-meta {
    display: flex;
    align-items: center;
}

.meta-text {
    color: var(--text-muted);
    font-size: 0.95rem;
}

.type-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
}

.type-ticket {
    background: #dbeafe;
    color: #1d4ed8;
}

.type-user {
    background: #dcfce7;
    color: #166534;
}

.type-task {
    background: #f3e8ff;
    color: #7e22ce;
}

.type-line {
    background: #fef3c7;
    color: #92400e;
}

.type-email {
    background: #fee2e2;
    color: #991b1b;
}

.result-title {
    font-weight: 700;
    color: var(--text-color);
}

.result-subtitle {
    font-size: 0.88rem;
    color: var(--text-muted);
    margin-top: 0.2rem;
}

.result-detail {
    color: var(--text-color);
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

@media (max-width: 1200px) {
    .summary-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 768px) {
    .summary-grid {
        grid-template-columns: 1fr;
    }
}
</style>