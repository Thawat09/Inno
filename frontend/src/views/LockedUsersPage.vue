<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Locked Users</div>
                        <div class="page-subtitle">
                            Monitor and unlock user accounts that are currently locked.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadLockedUsers"
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

                <div class="toolbar-row">
                    <div class="toolbar-search">
                        <i class="pi pi-search toolbar-search-icon"></i>
                        <InputText
                            v-model="searchText"
                            placeholder="Search by email, name, or role"
                        />
                    </div>

                    <div class="toolbar-summary">
                        <span class="summary-chip">
                            Total Locked: {{ filteredUsers.length }}
                        </span>
                    </div>
                </div>

                <DataTable
                    :value="filteredUsers"
                    dataKey="email"
                    paginator
                    :rows="10"
                    responsiveLayout="scroll"
                    stripedRows
                    class="locked-users-table"
                >
                    <Column header="#" style="width: 70px">
                        <template #body="{ index }">
                            {{ index + 1 }}
                        </template>
                    </Column>

                    <Column field="display_name" header="Name" style="min-width: 220px">
                        <template #body="{ data }">
                            <div class="user-cell">
                                <Avatar
                                    :label="getAvatarLabel(data)"
                                    shape="circle"
                                    size="normal"
                                />
                                <div>
                                    <div class="user-name">{{ data.display_name || "-" }}</div>
                                    <div class="user-role">{{ data.role_name || data.role || "-" }}</div>
                                </div>
                            </div>
                        </template>
                    </Column>

                    <Column field="email" header="Email" style="min-width: 240px" />

                    <Column field="employee_code" header="Employee Code" style="min-width: 160px">
                        <template #body="{ data }">
                            {{ data.employee_code || "-" }}
                        </template>
                    </Column>

                    <Column field="main_team" header="Main Team" style="min-width: 170px">
                        <template #body="{ data }">
                            {{ data.main_team || "-" }}
                        </template>
                    </Column>

                    <Column field="failed_login_count" header="Failed Attempts" style="min-width: 150px">
                        <template #body="{ data }">
                            <span class="attempt-badge">
                                {{ data.failed_login_count ?? "-" }}
                            </span>
                        </template>
                    </Column>

                    <Column field="locked_at" header="Locked At" style="min-width: 180px">
                        <template #body="{ data }">
                            {{ formatDateTime(data.locked_at) }}
                        </template>
                    </Column>

                    <Column header="Status" style="min-width: 120px">
                        <template #body>
                            <span class="status-badge status-inactive">
                                Locked
                            </span>
                        </template>
                    </Column>

                    <Column header="Actions" style="min-width: 150px">
                        <template #body="{ data }">
                            <Button
                                label="Unlock"
                                icon="pi pi-lock-open"
                                size="small"
                                @click="handleUnlock(data)"
                            />
                        </template>
                    </Column>

                    <template #empty>
                        <div class="table-empty">
                            No locked users found.
                        </div>
                    </template>
                </DataTable>

                <div class="mock-note mt-3">
                    This page currently uses mock data from <strong>authService</strong>.
                    It is ready for future backend integration for account lock and unlock management.
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { getLockedUsers, unlockUser } from "@/services/authService";

const lockedUsers = ref([]);
const searchText = ref("");
const pageError = ref("");
const successMessage = ref("");

const normalizeLockedUser = (user) => {
    const firstName = user.first_name || "";
    const lastName = user.last_name || "";
    const nickname = user.nickname || "";

    const fullName = [firstName, lastName].filter(Boolean).join(" ").trim();
    const displayName =
        fullName || nickname || user.name || user.email?.split("@")[0] || "Unknown User";

    return {
        employee_code: user.employee_code || "",
        first_name: firstName,
        last_name: lastName,
        nickname,
        display_name: displayName,
        email: user.email || "",
        role: user.role || "user",
        role_name: user.role_name || user.role || "User",
        main_team: user.main_team || "",
        sub_team: user.sub_team || "",
        failed_login_count: user.failed_login_count ?? 0,
        locked_at: user.locked_at || user.updated_at || "",
        is_locked: true
    };
};

const loadLockedUsers = () => {
    pageError.value = "";
    successMessage.value = "";

    try {
        const users = getLockedUsers?.() || [];
        lockedUsers.value = users.map(normalizeLockedUser);
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load locked users.";
    }
};

const filteredUsers = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    if (!keyword) return lockedUsers.value;

    return lockedUsers.value.filter((user) => {
        return [
            user.display_name,
            user.email,
            user.role_name,
            user.employee_code,
            user.main_team
        ]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(keyword));
    });
});

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

const getAvatarLabel = (user) => {
    const first = user.first_name?.trim();
    const last = user.last_name?.trim();

    if (first && last) return `${first[0]}${last[0]}`.toUpperCase();
    if (first) return first[0].toUpperCase();
    if (user.email) return user.email[0].toUpperCase();
    return "U";
};

const handleUnlock = (user) => {
    pageError.value = "";
    successMessage.value = "";

    try {
        const result = unlockUser?.(user.email);

        if (result && result.ok === false) {
            pageError.value = result.message || "Unable to unlock this user.";
            return;
        }

        lockedUsers.value = lockedUsers.value.filter((item) => item.email !== user.email);
        successMessage.value = `User ${user.email} has been unlocked successfully.`;
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to unlock this user.";
    }
};

onMounted(() => {
    loadLockedUsers();
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

.toolbar-summary {
    display: flex;
    align-items: center;
}

.summary-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.55rem 0.9rem;
    border-radius: 999px;
    background: #ecfdf5;
    color: #065f46;
    font-weight: 600;
    font-size: 0.92rem;
}

.user-cell {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.user-name {
    font-weight: 600;
    color: var(--text-color);
}

.user-role {
    font-size: 0.88rem;
    color: var(--text-muted);
    margin-top: 0.2rem;
    text-transform: capitalize;
}

.attempt-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 42px;
    padding: 0.35rem 0.6rem;
    border-radius: 999px;
    background: #fee2e2;
    color: #991b1b;
    font-weight: 700;
    font-size: 0.85rem;
}

.table-empty {
    padding: 1rem;
    text-align: center;
    color: var(--text-muted);
}

.mb-3 {
    margin-bottom: 1rem;
}

.mt-3 {
    margin-top: 1rem;
}

@media (max-width: 768px) {
    .toolbar-search {
        max-width: 100%;
    }
}
</style>