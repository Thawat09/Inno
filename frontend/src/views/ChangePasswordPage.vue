<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">Change Password</div>
                        <div class="page-subtitle">
                            Update your password securely using your current password.
                        </div>
                    </div>

                    <div class="page-header-actions">
                        <Button
                            label="Back"
                            icon="pi pi-arrow-left"
                            severity="secondary"
                            outlined
                            @click="goBack"
                        />
                    </div>
                </div>
            </template>

            <template #content>
                <div class="change-password-layout">
                    <div class="change-password-main">
                        <div class="form-grid">
                            <div class="form-field">
                                <label>Email</label>
                                <InputText
                                    :modelValue="email"
                                    disabled
                                />
                            </div>

                            <div class="form-field">
                                <label>Current Password</label>
                                <Password
                                    v-model="currentPassword"
                                    toggleMask
                                    :feedback="false"
                                    placeholder="Enter current password"
                                    fluid
                                    autocomplete="current-password"
                                />
                            </div>

                            <div class="form-field form-field-full">
                                <label>New Password</label>
                                <Password
                                    v-model="newPassword"
                                    toggleMask
                                    :feedback="false"
                                    placeholder="Enter new password"
                                    fluid
                                    autocomplete="new-password"
                                />

                                <ul class="password-rules">
                                    <li :class="ruleClass(rules.validLength)">
                                        Minimum 12 characters
                                    </li>
                                    <li :class="ruleClass(rules.hasUpper)">
                                        At least 1 uppercase letter
                                    </li>
                                    <li :class="ruleClass(rules.hasLower)">
                                        At least 1 lowercase letter
                                    </li>
                                    <li :class="ruleClass(rules.hasNumber)">
                                        At least 1 number
                                    </li>
                                    <li :class="ruleClass(rules.hasSpecial)">
                                        At least 1 special character
                                    </li>
                                </ul>
                            </div>

                            <div class="form-field form-field-full">
                                <label>Confirm New Password</label>
                                <Password
                                    v-model="confirmPassword"
                                    toggleMask
                                    :feedback="false"
                                    placeholder="Confirm new password"
                                    fluid
                                    autocomplete="new-password"
                                />

                                <div
                                    v-if="confirmPassword"
                                    class="confirm-password-status"
                                    :class="passwordsMatch ? 'rule-ok' : 'rule-fail'"
                                >
                                    {{ passwordsMatch ? 'Passwords match' : 'Passwords do not match' }}
                                </div>
                            </div>
                        </div>

                        <Message v-if="errorMessage" severity="error" class="mb-3">
                            {{ errorMessage }}
                        </Message>

                        <Message v-if="successMessage" severity="success" class="mb-3">
                            {{ successMessage }}
                        </Message>

                        <div class="form-actions">
                            <Button
                                label="Change Password"
                                icon="pi pi-check"
                                :loading="isLoading"
                                :disabled="!canSubmit"
                                @click="handleChangePassword"
                            />
                        </div>
                    </div>

                    <div class="change-password-side">
                        <Card class="content-card">
                            <template #title>
                                <span>Instructions</span>
                            </template>

                            <template #content>
                                <div class="notes-list">
                                    <div class="note-item">
                                        <div class="note-title">Current Password</div>
                                        <div class="note-desc">
                                            You must enter your current password before setting a new one.
                                        </div>
                                    </div>

                                    <div class="note-item">
                                        <div class="note-title">Password Standard</div>
                                        <div class="note-desc">
                                            New password must be at least 12 characters and include uppercase, lowercase, number, and special character.
                                        </div>
                                    </div>

                                    <div class="note-item">
                                        <div class="note-title">Security Note</div>
                                        <div class="note-desc">
                                            After successful change, your new password will be used for the next login immediately.
                                        </div>
                                    </div>
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser, isAuthenticated, changePassword } from '../services/authService'
import { validatePassword, isPasswordValid } from '../utils/passwordPolicy'

const router = useRouter()

const currentUser = ref(null)
const email = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const isLoading = ref(false)

const rules = computed(() => validatePassword(newPassword.value))

const passwordsMatch = computed(() => newPassword.value === confirmPassword.value)

const canSubmit = computed(() =>
    !!email.value &&
    !!currentPassword.value &&
    !!newPassword.value &&
    !!confirmPassword.value &&
    isPasswordValid(newPassword.value) &&
    passwordsMatch.value
)

const ruleClass = (condition) => (condition ? 'rule-ok' : 'rule-fail')

const handleChangePassword = async () => {
    errorMessage.value = ''
    successMessage.value = ''

    if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
        errorMessage.value = 'Please complete all password fields'
        return
    }

    if (!isPasswordValid(newPassword.value)) {
        errorMessage.value =
            'New password must be at least 12 characters and include uppercase, lowercase, number, and special character'
        return
    }

    if (!passwordsMatch.value) {
        errorMessage.value = 'New password and confirm password do not match'
        return
    }

    if (currentPassword.value === newPassword.value) {
        errorMessage.value = 'New password must be different from current password'
        return
    }

    isLoading.value = true

    try {
        const result = changePassword(email.value, currentPassword.value, newPassword.value)

        if (!result.ok) {
            errorMessage.value = result.message || 'Unable to change password'
            return
        }

        successMessage.value = 'Password changed successfully.'

        currentPassword.value = ''
        newPassword.value = ''
        confirmPassword.value = ''
    } catch (error) {
        console.error(error)
        errorMessage.value = 'Unexpected error occurred'
    } finally {
        isLoading.value = false
    }
}

const goBack = () => {
    router.back()
}

onMounted(() => {
    if (!isAuthenticated()) {
        router.push('/login')
        return
    }

    const user = getCurrentUser()
    currentUser.value = user
    email.value = user?.email || ''
})
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

.change-password-layout {
    display: grid;
    grid-template-columns: 1.35fr 0.8fr;
    gap: 1rem;
    align-items: start;
}

.change-password-main,
.change-password-side {
    min-width: 0;
}

.password-rules {
    margin-top: 0.6rem;
    margin-bottom: 0;
    padding-left: 1.1rem;
    font-size: 0.9rem;
    line-height: 1.5;
}

.password-rules li {
    margin-bottom: 0.15rem;
}

.confirm-password-status {
    margin-top: 0.5rem;
    font-size: 0.9rem;
    font-weight: 500;
}

.rule-ok {
    color: #16a34a;
}

.rule-fail {
    color: #dc2626;
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

.mb-3 {
    margin-bottom: 1rem;
}

.app-dark .password-rules,
.app-dark .confirm-password-status {
    color: #d1d5db;
}

.app-dark .rule-ok {
    color: #4ade80;
}

.app-dark .rule-fail {
    color: #f87171;
}

@media (max-width: 1024px) {
    .change-password-layout {
        grid-template-columns: 1fr;
    }
}
</style>