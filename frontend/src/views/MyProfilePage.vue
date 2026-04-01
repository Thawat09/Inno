<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="profile-header">
                    <div>
                        <div class="profile-title">My Profile</div>
                        <div class="profile-subtitle">
                            View and update your personal information
                        </div>
                    </div>

                    <div class="profile-header-actions">
                        <Button
                            v-if="!editMode"
                            label="Edit Profile"
                            icon="pi pi-pencil"
                            @click="startEdit"
                        />
                        <template v-else>
                            <Button
                                label="Cancel"
                                icon="pi pi-times"
                                severity="secondary"
                                outlined
                                @click="cancelEdit"
                            />
                            <Button
                                label="Save"
                                icon="pi pi-check"
                                @click="saveProfile"
                            />
                        </template>
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

                <div class="profile-layout">
                    <!-- Left: Summary -->
                    <div class="profile-summary">
                        <div class="profile-summary-card">
                            <Avatar
                                :label="avatarLabel"
                                size="xlarge"
                                shape="circle"
                                class="profile-avatar"
                            />

                            <div class="profile-display-name">
                                {{ fullNameDisplay }}
                            </div>

                            <div class="profile-display-role">
                                {{ profile.role_name || "-" }}
                            </div>

                            <div class="profile-display-email">
                                {{ profile.email || "-" }}
                            </div>

                            <div class="profile-badges">
                                <span
                                    class="status-badge"
                                    :class="profile.is_active ? 'status-active' : 'status-inactive'"
                                >
                                    {{ profile.is_active ? "Active" : "Inactive" }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Detail -->
                    <div class="profile-detail">
                        <!-- Editable Section -->
                        <Card class="content-card">
                            <template #title>
                                <span>Personal Information</span>
                            </template>

                            <template #content>
                                <div class="form-grid">
                                    <div class="form-field">
                                        <label>First Name</label>
                                        <InputText
                                            v-model="form.first_name"
                                            :disabled="!editMode"
                                            placeholder="Enter first name"
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>Last Name</label>
                                        <InputText
                                            v-model="form.last_name"
                                            :disabled="!editMode"
                                            placeholder="Enter last name"
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>Nickname</label>
                                        <InputText
                                            v-model="form.nickname"
                                            :disabled="!editMode"
                                            placeholder="Enter nickname"
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>Phone</label>
                                        <InputText
                                            v-model="form.phone"
                                            :disabled="!editMode"
                                            placeholder="Enter phone number"
                                        />
                                    </div>
                                </div>
                            </template>
                        </Card>

                        <!-- Readonly Section -->
                        <Card class="content-card">
                            <template #title>
                                <span>Account Information</span>
                            </template>

                            <template #content>
                                <div class="form-grid">
                                    <div class="form-field">
                                        <label>Employee Code</label>
                                        <InputText
                                            :modelValue="profile.employee_code || '-'"
                                            disabled
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>Email</label>
                                        <InputText
                                            :modelValue="profile.email || '-'"
                                            disabled
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>Main Team</label>
                                        <InputText
                                            :modelValue="profile.main_team || '-'"
                                            disabled
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>Sub Team</label>
                                        <InputText
                                            :modelValue="profile.sub_team || '-'"
                                            disabled
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>Role</label>
                                        <InputText
                                            :modelValue="profile.role_name || '-'"
                                            disabled
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>Last Login</label>
                                        <InputText
                                            :modelValue="formatDateTime(profile.last_login_at)"
                                            disabled
                                        />
                                    </div>

                                    <div class="form-field">
                                        <label>Status</label>
                                        <InputText
                                            :modelValue="profile.is_active ? 'Active' : 'Inactive'"
                                            disabled
                                        />
                                    </div>
                                </div>
                            </template>
                        </Card>

                        <!-- Future-ready Security Section -->
                        <Card class="content-card">
                            <template #title>
                                <span>Security</span>
                            </template>

                            <template #content>
                                <div class="security-row">
                                    <div>
                                        <div class="security-title">Password</div>
                                        <div class="security-subtitle">
                                            For security reasons, password details are hidden.
                                        </div>
                                    </div>

                                    <Button
                                        label="Change Password"
                                        icon="pi pi-lock"
                                        severity="secondary"
                                        outlined
                                        disabled
                                    />
                                </div>

                                <div class="mock-note">
                                    This button is reserved for future backend integration.
                                    Sensitive fields such as password hash, salt, and failed login count
                                    are not displayed on this page.
                                </div>
                            </template>
                        </Card>
                    </div>
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { getCurrentUser } from "@/services/authService";

const editMode = ref(false);
const pageError = ref("");
const successMessage = ref("");

const profile = ref({
    employee_code: "",
    first_name: "",
    last_name: "",
    nickname: "",
    phone: "",
    email: "",
    main_team: "",
    sub_team: "",
    role_name: "",
    last_login_at: "",
    is_active: true
});

const form = ref({
    first_name: "",
    last_name: "",
    nickname: "",
    phone: ""
});

const originalForm = ref({
    first_name: "",
    last_name: "",
    nickname: "",
    phone: ""
});

const avatarLabel = computed(() => {
    const first = form.value.first_name?.trim();
    const last = form.value.last_name?.trim();

    if (first && last) {
        return `${first[0]}${last[0]}`.toUpperCase();
    }

    if (first) {
        return first[0].toUpperCase();
    }

    if (profile.value.email) {
        return profile.value.email[0].toUpperCase();
    }

    return "U";
});

const fullNameDisplay = computed(() => {
    const first = (form.value.first_name || "").trim();
    const last = (form.value.last_name || "").trim();
    const nickname = (form.value.nickname || "").trim();

    const fullName = [first, last].filter(Boolean).join(" ");

    if (fullName && nickname) {
        return `${fullName} (${nickname})`;
    }

    if (fullName) {
        return fullName;
    }

    if (nickname) {
        return nickname;
    }

    return profile.value.email || "Unknown User";
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

const mapUserToProfile = (user) => {
    return {
        employee_code: user.employee_code || "EMP-0001",
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        nickname: user.nickname || "",
        phone: user.phone || "",
        email: user.email || "",
        main_team: user.main_team || "Infrastructure",
        sub_team: user.sub_team || "Cloud Operations",
        role_name: user.role_name || user.role || "User",
        last_login_at: user.last_login_at || new Date().toISOString(),
        is_active: user.is_active ?? true
    };
};

const loadProfile = () => {
    pageError.value = "";
    successMessage.value = "";

    const currentUser = getCurrentUser();

    if (!currentUser) {
        pageError.value = "Unable to load current user profile.";
        return;
    }

    const mapped = mapUserToProfile(currentUser);
    profile.value = mapped;

    form.value = {
        first_name: mapped.first_name,
        last_name: mapped.last_name,
        nickname: mapped.nickname,
        phone: mapped.phone
    };

    originalForm.value = { ...form.value };
};

const startEdit = () => {
    successMessage.value = "";
    editMode.value = true;
};

const cancelEdit = () => {
    form.value = { ...originalForm.value };
    editMode.value = false;
};

const saveProfile = () => {
    pageError.value = "";
    successMessage.value = "";

    if (!form.value.first_name?.trim()) {
        pageError.value = "First name is required.";
        return;
    }

    profile.value = {
        ...profile.value,
        first_name: form.value.first_name.trim(),
        last_name: form.value.last_name.trim(),
        nickname: form.value.nickname.trim(),
        phone: form.value.phone.trim()
    };

    originalForm.value = { ...form.value };
    editMode.value = false;
    successMessage.value = "Profile updated successfully. (mock)";
    
    console.log("Mock profile payload for backend:", {
        first_name: profile.value.first_name,
        last_name: profile.value.last_name,
        nickname: profile.value.nickname,
        phone: profile.value.phone
    });
};

onMounted(() => {
    loadProfile();
});
</script>

<style scoped>
.profile-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    flex-wrap: wrap;
}

.profile-title {
    font-size: 1.25rem;
    font-weight: 700;
}

.profile-subtitle {
    color: var(--text-muted);
    margin-top: 0.25rem;
    font-size: 0.95rem;
}

.profile-header-actions {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.profile-layout {
    display: grid;
    grid-template-columns: 320px minmax(0, 1fr);
    gap: 1rem;
    align-items: start;
}

.profile-summary {
    position: sticky;
    top: calc(var(--topbar-height) + 1rem);
}

.profile-summary-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    padding: 1.5rem;
    text-align: center;
}

.profile-avatar {
    margin-bottom: 1rem;
}

.profile-display-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-color);
    margin-bottom: 0.35rem;
    word-break: break-word;
}

.profile-display-role {
    font-size: 0.95rem;
    color: var(--text-muted);
    margin-bottom: 0.35rem;
}

.profile-display-email {
    font-size: 0.92rem;
    color: var(--text-muted);
    margin-bottom: 1rem;
    word-break: break-word;
}

.profile-badges {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.profile-detail {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.security-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.security-title {
    font-weight: 700;
    color: var(--text-color);
    margin-bottom: 0.25rem;
}

.security-subtitle {
    color: var(--text-muted);
    font-size: 0.95rem;
}

.mb-3 {
    margin-bottom: 1rem;
}

@media (max-width: 992px) {
    .profile-layout {
        grid-template-columns: 1fr;
    }

    .profile-summary {
        position: static;
    }
}
</style>