<template>
    <div class="auth-page">
        <Card class="auth-card">
            <template #title>
                <div class="auth-title">Set First Password</div>
            </template>

            <template #content>
                <div class="auth-form">
                    <div class="form-field">
                        <label>Email</label>
                        <InputText :modelValue="email" disabled />
                    </div>

                    <div class="form-field">
                        <label>Password</label>
                        <Password
                            v-model="password"
                            :feedback="false"
                            toggleMask
                            placeholder="Enter new password"
                            fluid
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

                    <div class="form-field">
                        <label>Confirm Password</label>
                        <Password
                            v-model="confirmPassword"
                            :feedback="false"
                            toggleMask
                            placeholder="Confirm password"
                            fluid
                        />

                        <div
                            v-if="confirmPassword"
                            class="confirm-password-status"
                            :class="passwordsMatch ? 'rule-ok' : 'rule-fail'"
                        >
                            {{ passwordsMatch ? 'Passwords match' : 'Passwords do not match' }}
                        </div>
                    </div>

                    <Message v-if="errorMessage" severity="error">
                        {{ errorMessage }}
                    </Message>

                    <Button
                        label="Save Password"
                        icon="pi pi-check"
                        :disabled="!canSubmit"
                        @click="handleSavePassword"
                    />
                </div>
            </template>
        </Card>
    </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { setFirstPassword, generateOtp } from '../services/authService'
import { validatePassword, isPasswordValid } from '../utils/passwordPolicy'

const route = useRoute()
const router = useRouter()

const email = computed(() => route.query.email || '')

const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')

const rules = computed(() => validatePassword(password.value))

const passwordsMatch = computed(() => password.value === confirmPassword.value)

const canSubmit = computed(() =>
    !!email.value &&
    !!password.value &&
    !!confirmPassword.value &&
    isPasswordValid(password.value) &&
    passwordsMatch.value
)

const ruleClass = (cond) => (cond ? 'rule-ok' : 'rule-fail')

const handleSavePassword = () => {
    errorMessage.value = ''

    if (!password.value || !confirmPassword.value) {
        errorMessage.value = 'Please fill in both password fields'
        return
    }

    if (!isPasswordValid(password.value)) {
        errorMessage.value =
            'Password must be at least 12 characters and include uppercase, lowercase, number, and special character'
        return
    }

    if (!passwordsMatch.value) {
        errorMessage.value = 'Passwords do not match'
        return
    }

    const result = setFirstPassword(email.value, password.value)

    if (!result.ok) {
        errorMessage.value = result.message
        return
    }

    const otpResult = generateOtp(email.value)

    if (!otpResult.ok) {
        errorMessage.value = otpResult.message || 'Unable to generate OTP'
        return
    }

    router.push({
        path: '/otp',
        query: {
            email: email.value,
            mockOtp: otpResult.otp
        }
    })
}
</script>

<style scoped>
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
</style>