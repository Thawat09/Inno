<template>
    <div class="auth-page">
        <Card class="auth-card">
            <template #title>
                <div class="auth-title">Reset Password</div>
            </template>

            <template #content>
                <div class="auth-form">
                    <div class="form-field">
                        <label>Email</label>
                        <InputText v-model="email" placeholder="Enter your email" />
                    </div>

                    <div class="form-field">
                        <label>OTP</label>
                        <InputText v-model="otp" placeholder="Enter OTP" />
                    </div>

                    <div class="auth-actions">
                        <Button
                            label="Send OTP"
                            icon="pi pi-send"
                            outlined
                            :loading="isSendingOtp"
                            :disabled="!email"
                            @click="handleSendOtp"
                        />
                        <Button
                            label="Resend OTP"
                            icon="pi pi-refresh"
                            outlined
                            :loading="isSendingOtp"
                            :disabled="!email"
                            @click="handleSendOtp"
                        />
                    </div>

                    <Message v-if="mockOtp" severity="info">
                        Mock OTP: <strong>{{ mockOtp }}</strong>
                    </Message>

                    <div class="form-field">
                        <label>New Password</label>
                        <Password v-model="password" toggleMask :feedback="false" />

                        <ul class="password-rules">
                            <li :class="ruleClass(rules.validLength)">Minimum 12 characters</li>
                            <li :class="ruleClass(rules.hasUpper)">Uppercase</li>
                            <li :class="ruleClass(rules.hasLower)">Lowercase</li>
                            <li :class="ruleClass(rules.hasNumber)">Number</li>
                            <li :class="ruleClass(rules.hasSpecial)">Special</li>
                        </ul>
                    </div>

                    <div class="form-field">
                        <label>Confirm Password</label>
                        <Password v-model="confirmPassword" toggleMask :feedback="false" />

                        <div
                            v-if="confirmPassword"
                            :class="passwordsMatch ? 'rule-ok' : 'rule-fail'"
                            class="confirm-password-status"
                        >
                            {{ passwordsMatch ? 'Passwords match' : 'Passwords do not match' }}
                        </div>
                    </div>

                    <Message v-if="errorMessage" severity="error">
                        {{ errorMessage }}
                    </Message>

                    <Message v-if="successMessage" severity="success">
                        {{ successMessage }}
                    </Message>

                    <Button
                        label="Reset Password"
                        icon="pi pi-check"
                        :loading="isLoading"
                        :disabled="!canSubmit"
                        @click="handleReset"
                    />

                    <div class="login">
                        <a @click.prevent="goToLogin">Back to Login</a>
                    </div>
                </div>
            </template>
        </Card>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { generateOtp, verifyOtp, resetPassword } from '../services/authService'
import { validatePassword, isPasswordValid } from '../utils/passwordPolicy'

const router = useRouter()

const email = ref('')
const otp = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const mockOtp = ref('')
const isLoading = ref(false)
const isSendingOtp = ref(false)

const rules = computed(() => validatePassword(password.value))
const passwordsMatch = computed(() => password.value === confirmPassword.value)

const canSubmit = computed(() =>
    email.value &&
    otp.value &&
    password.value &&
    confirmPassword.value &&
    isPasswordValid(password.value) &&
    passwordsMatch.value
)

const ruleClass = (c) => (c ? 'rule-ok' : 'rule-fail')

const handleSendOtp = () => {
    errorMessage.value = ''
    mockOtp.value = ''

    if (!email.value) {
        errorMessage.value = 'Please enter email'
        return
    }

    isSendingOtp.value = true

    const result = generateOtp(email.value)

    if (!result.ok) {
        errorMessage.value = result.message
    } else {
        mockOtp.value = result.otp
    }

    isSendingOtp.value = false
}

const goToLogin = () => {
    router.push('/login')
}

const handleReset = () => {
    errorMessage.value = ''
    successMessage.value = ''

    if (!isPasswordValid(password.value)) {
        errorMessage.value = 'Password format invalid'
        return
    }

    if (!passwordsMatch.value) {
        errorMessage.value = 'Passwords do not match'
        return
    }

    const otpResult = verifyOtp(email.value, otp.value)

    if (!otpResult.ok) {
        errorMessage.value = otpResult.message
        return
    }

    const result = resetPassword(email.value, password.value)

    if (!result.ok) {
        errorMessage.value = result.message
        return
    }

    successMessage.value = 'Password reset successful'

    setTimeout(() => {
        router.push('/login')
    }, 1000)
}
</script>

<style scoped>
.password-rules {
    margin-top: 0.5rem;
    font-size: 0.85rem;
}

.rule-ok {
    color: #16a34a;
}

.rule-fail {
    color: #dc2626;
}

.confirm-password-status {
    margin-top: 0.5rem;
    font-size: 0.9rem;
}

.login{
    margin-top: 0.35rem;
    text-align: center;
    font-size: 0.85rem;
}

.login a {
    color: var(--primary-color);
    cursor: pointer;
    text-decoration: none;
}

.login a:hover {
    text-decoration: underline;
}
</style>