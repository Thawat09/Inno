<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Teams & Members</div>
                        <div class="page-subtitle">
                            View team structure and member information.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadTeams"
                        />
                    </div>
                </div>
            </template>

            <template #content>
                <Message v-if="pageError" severity="error" class="mb-3">
                    {{ pageError }}
                </Message>

                <div class="team-summary-grid">
                    <div class="summary-card">
                        <div class="summary-label">Total Teams</div>
                        <div class="summary-value">{{ filteredTeams.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Total Members</div>
                        <div class="summary-value">{{ totalMembers }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Active Members</div>
                        <div class="summary-value">{{ totalActiveMembers }}</div>
                    </div>
                </div>

                <div class="page-two-column">
                    <!-- Left: Team List -->
                    <Card class="content-card">
                        <template #title>
                            <div class="section-header">
                                <span>Teams</span>
                            </div>
                        </template>

                        <template #content>
                            <div class="toolbar-search mb-3">
                                <i class="pi pi-search toolbar-search-icon"></i>
                                <InputText
                                    v-model="teamSearch"
                                    placeholder="Search team name..."
                                />
                            </div>

                            <div class="team-list">
                                <button
                                    v-for="team in filteredTeams"
                                    :key="team.id"
                                    type="button"
                                    class="team-item"
                                    :class="{ active: selectedTeam?.id === team.id }"
                                    @click="selectTeam(team)"
                                >
                                    <div class="team-item-top">
                                        <div class="team-name">{{ team.team_name }}</div>
                                        <span class="member-count-badge">
                                            {{ team.members.length }}
                                        </span>
                                    </div>

                                    <div class="team-item-sub">
                                        Leader:
                                        {{ team.team_lead_name || "-" }}
                                    </div>

                                    <div class="team-item-sub">
                                        {{ team.description || "No description" }}
                                    </div>
                                </button>

                                <div v-if="filteredTeams.length === 0" class="empty-box">
                                    No teams found.
                                </div>
                            </div>
                        </template>
                    </Card>

                    <!-- Right: Team Detail -->
                    <Card class="content-card">
                        <template #title>
                            <div class="section-header">
                                <span>{{ selectedTeam?.team_name || "Members" }}</span>
                            </div>
                        </template>

                        <template #content>
                            <template v-if="selectedTeam">
                                <div class="team-detail-header">
                                    <div>
                                        <div class="team-detail-title">
                                            {{ selectedTeam.team_name }}
                                        </div>
                                        <div class="team-detail-subtitle">
                                            {{ selectedTeam.description || "No description" }}
                                        </div>
                                    </div>

                                    <div class="team-detail-meta">
                                        <span class="status-badge status-active">
                                            {{ selectedTeam.members.length }} Members
                                        </span>
                                    </div>
                                </div>

                                <div class="team-info-grid">
                                    <div class="info-box">
                                        <div class="info-label">Team Lead</div>
                                        <div class="info-value">
                                            {{ selectedTeam.team_lead_name || "-" }}
                                        </div>
                                    </div>

                                    <div class="info-box">
                                        <div class="info-label">Main Team</div>
                                        <div class="info-value">
                                            {{ selectedTeam.team_name || "-" }}
                                        </div>
                                    </div>
                                </div>

                                <div class="toolbar-search mb-3">
                                    <i class="pi pi-search toolbar-search-icon"></i>
                                    <InputText
                                        v-model="memberSearch"
                                        placeholder="Search member name, email, role..."
                                    />
                                </div>

                                <DataTable
                                    :value="filteredMembers"
                                    dataKey="id"
                                    paginator
                                    :rows="5"
                                    responsiveLayout="scroll"
                                    stripedRows
                                >
                                    <Column header="#" style="width: 70px">
                                        <template #body="{ index }">
                                            {{ index + 1 }}
                                        </template>
                                    </Column>

                                    <Column header="Member" style="min-width: 260px">
                                        <template #body="{ data }">
                                            <div class="member-cell">
                                                <Avatar
                                                    :label="getAvatarLabel(data)"
                                                    shape="circle"
                                                />
                                                <div>
                                                    <div class="member-name">
                                                        {{ data.display_name }}
                                                    </div>
                                                    <div class="member-email">
                                                        {{ data.email || "-" }}
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </Column>

                                    <Column field="employee_code" header="Employee Code" style="min-width: 150px">
                                        <template #body="{ data }">
                                            {{ data.employee_code || "-" }}
                                        </template>
                                    </Column>

                                    <Column field="role_name" header="Role" style="min-width: 140px">
                                        <template #body="{ data }">
                                            {{ data.role_name || data.role || "-" }}
                                        </template>
                                    </Column>

                                    <Column field="phone" header="Phone" style="min-width: 140px">
                                        <template #body="{ data }">
                                            {{ data.phone || "-" }}
                                        </template>
                                    </Column>

                                    <Column header="Status" style="min-width: 120px">
                                        <template #body="{ data }">
                                            <span
                                                class="status-badge"
                                                :class="data.is_active ? 'status-active' : 'status-inactive'"
                                            >
                                                {{ data.is_active ? "Active" : "Inactive" }}
                                            </span>
                                        </template>
                                    </Column>

                                    <template #empty>
                                        <div class="empty-box">
                                            No members found.
                                        </div>
                                    </template>
                                </DataTable>
                            </template>

                            <div v-else class="empty-box large">
                                Select a team to view members.
                            </div>
                        </template>
                    </Card>
                </div>

                <div class="mock-note mt-3">
                    This page currently uses mock team and member data and is ready for future backend integration.
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

const pageError = ref("");
const teamSearch = ref("");
const memberSearch = ref("");
const teams = ref([]);
const selectedTeam = ref(null);

const mockTeams = [
    {
        id: 1,
        team_name: "Cloud Operations",
        description: "Responsible for cloud infrastructure operations and monitoring.",
        team_lead_name: "Admin User",
        members: [
            {
                id: 101,
                employee_code: "EMP-0002",
                first_name: "Admin",
                last_name: "User",
                email: "admin@company.com",
                phone: "0899999999",
                role: "admin",
                role_name: "Admin",
                is_active: true
            },
            {
                id: 102,
                employee_code: "EMP-0004",
                first_name: "Narin",
                last_name: "Sukjai",
                email: "narin@company.com",
                phone: "0811111111",
                role: "engineer",
                role_name: "Cloud Engineer",
                is_active: true
            },
            {
                id: 103,
                employee_code: "EMP-0005",
                first_name: "Mali",
                last_name: "Kanit",
                email: "mali@company.com",
                phone: "0822222222",
                role: "engineer",
                role_name: "System Engineer",
                is_active: false
            }
        ]
    },
    {
        id: 2,
        team_name: "Security Operations",
        description: "Responsible for security alerts, incidents, and audit activities.",
        team_lead_name: "Super Admin",
        members: [
            {
                id: 201,
                employee_code: "EMP-0003",
                first_name: "Super",
                last_name: "Admin",
                email: "superadmin@company.com",
                phone: "0888888888",
                role: "super_admin",
                role_name: "Super Admin",
                is_active: true
            },
            {
                id: 202,
                employee_code: "EMP-0006",
                first_name: "Ploy",
                last_name: "Jinda",
                email: "ploy@company.com",
                phone: "0833333333",
                role: "analyst",
                role_name: "Security Analyst",
                is_active: true
            }
        ]
    },
    {
        id: 3,
        team_name: "Standby Support",
        description: "Responsible for on-call support and after-hours service coverage.",
        team_lead_name: "User One",
        members: [
            {
                id: 301,
                employee_code: "EMP-0001",
                first_name: "User",
                last_name: "One",
                email: "user1@company.com",
                phone: "0812345678",
                role: "employee",
                role_name: "Employee",
                is_active: true
            },
            {
                id: 302,
                employee_code: "EMP-0007",
                first_name: "Krit",
                last_name: "Meechai",
                email: "krit@company.com",
                phone: "0844444444",
                role: "support",
                role_name: "Support Engineer",
                is_active: true
            }
        ]
    }
];

const loadTeams = () => {
    pageError.value = "";

    try {
        teams.value = mockTeams.map((team) => ({
            ...team,
            members: team.members.map((member) => ({
                ...member,
                display_name: [member.first_name, member.last_name].filter(Boolean).join(" ").trim() || member.email
            }))
        }));

        if (!selectedTeam.value && teams.value.length > 0) {
            selectedTeam.value = teams.value[0];
        } else if (selectedTeam.value) {
            const latest = teams.value.find((t) => t.id === selectedTeam.value.id);
            selectedTeam.value = latest || teams.value[0] || null;
        }
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load team data.";
    }
};

const filteredTeams = computed(() => {
    const keyword = teamSearch.value.trim().toLowerCase();
    if (!keyword) return teams.value;

    return teams.value.filter((team) =>
        [team.team_name, team.team_lead_name, team.description]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(keyword))
    );
});

const filteredMembers = computed(() => {
    if (!selectedTeam.value) return [];

    const keyword = memberSearch.value.trim().toLowerCase();
    if (!keyword) return selectedTeam.value.members;

    return selectedTeam.value.members.filter((member) =>
        [
            member.display_name,
            member.email,
            member.role_name,
            member.employee_code,
            member.phone
        ]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(keyword))
    );
});

const totalMembers = computed(() =>
    teams.value.reduce((sum, team) => sum + team.members.length, 0)
);

const totalActiveMembers = computed(() =>
    teams.value.reduce(
        (sum, team) => sum + team.members.filter((member) => member.is_active).length,
        0
    )
);

const selectTeam = (team) => {
    selectedTeam.value = team;
    memberSearch.value = "";
};

const getAvatarLabel = (member) => {
    const first = member.first_name?.trim();
    const last = member.last_name?.trim();

    if (first && last) return `${first[0]}${last[0]}`.toUpperCase();
    if (first) return first[0].toUpperCase();
    if (member.email) return member.email[0].toUpperCase();
    return "U";
};

onMounted(() => {
    loadTeams();
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

.team-summary-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
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
    grid-template-columns: 360px minmax(0, 1fr);
    gap: 1rem;
    align-items: start;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
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

.team-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.team-item {
    width: 100%;
    text-align: left;
    border: 1px solid var(--border-color);
    background: var(--card-bg);
    border-radius: 16px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.team-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-sm);
}

.team-item.active {
    border-color: #86efac;
    box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.14);
    background: #f0fdf4;
}

.team-item-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.45rem;
}

.team-name {
    font-weight: 700;
    color: var(--text-color);
}

.member-count-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 34px;
    padding: 0.3rem 0.55rem;
    border-radius: 999px;
    background: #dcfce7;
    color: #166534;
    font-weight: 700;
    font-size: 0.82rem;
}

.team-item-sub {
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-top: 0.2rem;
    line-height: 1.4;
}

.team-detail-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}

.team-detail-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-color);
}

.team-detail-subtitle {
    color: var(--text-muted);
    margin-top: 0.25rem;
}

.team-info-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}

.info-box {
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    background: var(--card-bg);
}

.info-label {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin-bottom: 0.3rem;
}

.info-value {
    font-weight: 600;
    color: var(--text-color);
}

.member-cell {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.member-name {
    font-weight: 600;
    color: var(--text-color);
}

.member-email {
    font-size: 0.88rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
}

.empty-box {
    padding: 1rem;
    border: 1px dashed var(--border-color);
    border-radius: 14px;
    text-align: center;
    color: var(--text-muted);
}

.empty-box.large {
    padding: 2rem 1rem;
}

.mb-3 {
    margin-bottom: 1rem;
}

.mt-3 {
    margin-top: 1rem;
}

@media (max-width: 1024px) {
    .page-two-column {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .team-summary-grid {
        grid-template-columns: 1fr;
    }

    .team-info-grid {
        grid-template-columns: 1fr;
    }
}
</style>