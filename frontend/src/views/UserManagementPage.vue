<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">User Administration</div>
                        <div class="page-subtitle">
                            Manage user accounts, roles, team assignment, and access status.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Add User"
                            icon="pi pi-plus"
                            @click="handleAddUser"
                        />
                        <Button
                            label="Refresh"
                            icon="pi pi-refresh"
                            severity="secondary"
                            outlined
                            @click="loadUsers"
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
                        <div class="summary-label">Total Users</div>
                        <div class="summary-value">{{ users.length }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Active</div>
                        <div class="summary-value">{{ activeCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Inactive</div>
                        <div class="summary-value">{{ inactiveCount }}</div>
                    </div>

                    <div class="summary-card">
                        <div class="summary-label">Locked</div>
                        <div class="summary-value">{{ lockedCount }}</div>
                    </div>
                </div>

                <div class="toolbar-row">
                    <div class="toolbar-search">
                        <i class="pi pi-search toolbar-search-icon"></i>
                        <InputText
                            v-model="searchText"
                            placeholder="Search name, email, employee code..."
                        />
                    </div>

                    <div class="toolbar-filters">
                        <Dropdown
                            v-model="statusFilter"
                            :options="statusOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Status"
                            class="filter-dropdown"
                        />
                        <Dropdown
                            v-model="roleFilter"
                            :options="roleOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Role"
                            class="filter-dropdown"
                        />
                    </div>
                </div>

                <DataTable
                    :value="filteredUsers"
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

                    <Column header="User" style="min-width: 280px">
                        <template #body="{ data }">
                            <div class="user-cell">
                                <Avatar
                                    :label="getAvatarLabel(data)"
                                    shape="circle"
                                />
                                <div>
                                    <div class="user-name">
                                        {{ data.display_name }}
                                    </div>
                                    <div class="user-email">
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
                            {{ data.role_name || "-" }}
                        </template>
                    </Column>

                    <Column field="main_team" header="Main Team" style="min-width: 160px">
                        <template #body="{ data }">
                            {{ data.main_team || "-" }}
                        </template>
                    </Column>

                    <Column field="failed_login_count" header="Failed Login" style="min-width: 130px">
                        <template #body="{ data }">
                            {{ data.failed_login_count ?? 0 }}
                        </template>
                    </Column>

                    <Column field="last_login_at" header="Last Login" style="min-width: 180px">
                        <template #body="{ data }">
                            {{ formatDateTime(data.last_login_at) }}
                        </template>
                    </Column>

                    <Column header="Status" style="min-width: 150px">
                        <template #body="{ data }">
                            <div class="status-group">
                                <span
                                    class="status-badge"
                                    :class="data.is_active ? 'status-active' : 'status-inactive'"
                                >
                                    {{ data.is_active ? "Active" : "Inactive" }}
                                </span>

                                <span
                                    v-if="data.is_locked"
                                    class="status-badge status-inactive"
                                >
                                    Locked
                                </span>
                            </div>
                        </template>
                    </Column>

                    <Column header="Actions" style="min-width: 320px">
                        <template #body="{ data }">
                            <div class="action-group">
                                <Button
                                    label="View"
                                    icon="pi pi-eye"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    @click="handleViewUser(data)"
                                />
                                <Button
                                    label="Edit"
                                    icon="pi pi-pencil"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    @click="handleEditUser(data)"
                                />
                                <Button
                                    label="Reset Password"
                                    icon="pi pi-key"
                                    size="small"
                                    severity="secondary"
                                    outlined
                                    @click="handleResetPassword(data)"
                                />
                                <Button
                                    v-if="data.is_locked"
                                    label="Unlock"
                                    icon="pi pi-lock-open"
                                    size="small"
                                    @click="handleUnlockUser(data)"
                                />
                                <Button
                                    v-else
                                    :label="data.is_active ? 'Disable' : 'Enable'"
                                    :icon="data.is_active ? 'pi pi-ban' : 'pi pi-check-circle'"
                                    size="small"
                                    :severity="data.is_active ? 'danger' : 'success'"
                                    outlined
                                    @click="handleToggleActive(data)"
                                />
                            </div>
                        </template>
                    </Column>

                    <template #empty>
                        <div class="empty-box">
                            No users found.
                        </div>
                    </template>
                </DataTable>

                <div class="mock-note mt-3">
                    This page currently uses frontend mock data and is ready for future backend
                    integration for user administration, reset password, and status management.
                </div>
            </template>
        </Card>

        <!-- Mock Detail Preview -->
        <Card v-if="selectedUser" class="content-card">
            <template #title>
                <div class="section-header">
                    <span>User Preview</span>
                    <Button
                        icon="pi pi-times"
                        text
                        rounded
                        class="topbar-icon-btn small-btn"
                        @click="selectedUser = null"
                    />
                </div>
            </template>

            <template #content>
                <div class="preview-grid">
                    <div class="info-box">
                        <div class="info-label">Name</div>
                        <div class="info-value">{{ selectedUser.display_name }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Email</div>
                        <div class="info-value">{{ selectedUser.email || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Employee Code</div>
                        <div class="info-value">{{ selectedUser.employee_code || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Role</div>
                        <div class="info-value">{{ selectedUser.role_name || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Main Team</div>
                        <div class="info-value">{{ selectedUser.main_team || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Sub Team</div>
                        <div class="info-value">{{ selectedUser.sub_team || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Phone</div>
                        <div class="info-value">{{ selectedUser.phone || "-" }}</div>
                    </div>

                    <div class="info-box">
                        <div class="info-label">Last Login</div>
                        <div class="info-value">{{ formatDateTime(selectedUser.last_login_at) }}</div>
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
const statusFilter = ref("all");
const roleFilter = ref("all");
const selectedUser = ref(null);
const users = ref([]);

const statusOptions = [
    { label: "All Status", value: "all" },
    { label: "Active", value: "active" },
    { label: "Inactive", value: "inactive" },
    { label: "Locked", value: "locked" }
];

const roleOptions = [
    { label: "All Roles", value: "all" },
    { label: "Super Admin", value: "super_admin" },
    { label: "Admin", value: "admin" },
    { label: "Employee", value: "employee" },
    { label: "Engineer", value: "engineer" },
    { label: "Analyst", value: "analyst" }
];

const mockUsers = [
    {
        id: 1,
        employee_code: "EMP-0001",
        first_name: "User",
        last_name: "One",
        nickname: "U1",
        phone: "0812345678",
        email: "user1@company.com",
        role: "employee",
        role_name: "Employee",
        main_team: "Standby Support",
        sub_team: "Night Shift",
        failed_login_count: 0,
        last_login_at: "2026-04-01T09:20:00Z",
        is_active: true,
        is_locked: false
    },
    {
        id: 2,
        employee_code: "EMP-0002",
        first_name: "Admin",
        last_name: "User",
        nickname: "Admin",
        phone: "0899999999",
        email: "admin@company.com",
        role: "admin",
        role_name: "Admin",
        main_team: "Cloud Operations",
        sub_team: "AWS Team",
        failed_login_count: 1,
        last_login_at: "2026-04-01T08:15:00Z",
        is_active: true,
        is_locked: false
    },
    {
        id: 3,
        employee_code: "EMP-0003",
        first_name: "Super",
        last_name: "Admin",
        nickname: "SA",
        phone: "0888888888",
        email: "superadmin@company.com",
        role: "super_admin",
        role_name: "Super Admin",
        main_team: "Management",
        sub_team: "Platform",
        failed_login_count: 0,
        last_login_at: "2026-03-31T16:45:00Z",
        is_active: true,
        is_locked: false
    },
    {
        id: 4,
        employee_code: "EMP-0004",
        first_name: "Narin",
        last_name: "Sukjai",
        nickname: "Narin",
        phone: "0811111111",
        email: "narin@company.com",
        role: "engineer",
        role_name: "Cloud Engineer",
        main_team: "Cloud Operations",
        sub_team: "Azure Team",
        failed_login_count: 3,
        last_login_at: "",
        is_active: true,
        is_locked: true
    },
    {
        id: 5,
        employee_code: "EMP-0005",
        first_name: "Mali",
        last_name: "Kanit",
        nickname: "Mali",
        phone: "0822222222",
        email: "mali@company.com",
        role: "analyst",
        role_name: "Security Analyst",
        main_team: "Security Operations",
        sub_team: "SOC",
        failed_login_count: 0,
        last_login_at: "2026-03-30T14:00:00Z",
        is_active: false,
        is_locked: false
    }
];

const normalizeUser = (user) => {
    const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ").trim();

    return {
        ...user,
        display_name: fullName || user.nickname || user.email || "Unknown User"
    };
};

const loadUsers = () => {
    pageError.value = "";
    successMessage.value = "";

    try {
        users.value = mockUsers.map(normalizeUser);
    } catch (error) {
        console.error(error);
        pageError.value = "Unable to load user data.";
    }
};

const filteredUsers = computed(() => {
    const keyword = searchText.value.trim().toLowerCase();

    return users.value.filter((user) => {
        const matchKeyword = !keyword
            ? true
            : [
                  user.display_name,
                  user.email,
                  user.employee_code,
                  user.main_team,
                  user.sub_team,
                  user.role_name
              ]
                  .filter(Boolean)
                  .some((value) => value.toLowerCase().includes(keyword));

        const matchStatus =
            statusFilter.value === "all"
                ? true
                : statusFilter.value === "active"
                ? user.is_active && !user.is_locked
                : statusFilter.value === "inactive"
                ? !user.is_active
                : user.is_locked;

        const matchRole =
            roleFilter.value === "all" ? true : user.role === roleFilter.value;

        return matchKeyword && matchStatus && matchRole;
    });
});

const activeCount = computed(() =>
    users.value.filter((user) => user.is_active && !user.is_locked).length
);

const inactiveCount = computed(() =>
    users.value.filter((user) => !user.is_active).length
);

const lockedCount = computed(() =>
    users.value.filter((user) => user.is_locked).length
);

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

const handleAddUser = () => {
    successMessage.value = "Add User clicked. (mock)";
};

const handleViewUser = (user) => {
    selectedUser.value = user;
    successMessage.value = "";
};

const handleEditUser = (user) => {
    selectedUser.value = user;
    successMessage.value = `Edit user ${user.email}. (mock)`;
};

const handleResetPassword = (user) => {
    successMessage.value = `Reset password requested for ${user.email}. (mock)`;
};

const handleUnlockUser = (user) => {
    user.is_locked = false;
    user.failed_login_count = 0;
    successMessage.value = `User ${user.email} unlocked successfully. (mock)`;
};

const handleToggleActive = (user) => {
    user.is_active = !user.is_active;
    successMessage.value = user.is_active
        ? `User ${user.email} enabled successfully. (mock)`
        : `User ${user.email} disabled successfully. (mock)`;
};

onMounted(() => {
    loadUsers();
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

.user-cell {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.user-name {
    font-weight: 600;
    color: var(--text-color);
}

.user-email {
    font-size: 0.88rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
}

.status-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.action-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
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

.info-label {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin-bottom: 0.3rem;
}

.info-value {
    font-weight: 600;
    color: var(--text-color);
    word-break: break-word;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
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
}

@media (max-width: 768px) {
    .summary-grid,
    .preview-grid {
        grid-template-columns: 1fr;
    }

    .toolbar-search {
        max-width: 100%;
    }
}
</style>