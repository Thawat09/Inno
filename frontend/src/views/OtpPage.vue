<template>
    <div class="auth-page">
        <Card class="auth-card">
            <template #title>
                <div class="auth-title">OTP Verification</div>
            </template>

            <template #content>
                <div class="auth-form">
                    <div class="form-field">
                        <label>Email</label>
                        <InputText :modelValue="email" disabled />
                    </div>

                    <div class="form-field">
                        <label>OTP</label>
                        <InputText v-model="otp" placeholder="Enter 6-digit OTP" />
                    </div>

                    <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>
                    <Message v-if="mockOtp" severity="info">
                        Mock OTP for frontend test: <strong>{{ mockOtp }}</strong>
                    </Message>

                    <div class="auth-actions">
                        <Button label="Verify OTP" icon="pi pi-check-circle" @click="handleVerifyOtp" />
                        <Button label="Resend OTP" outlined icon="pi pi-refresh" @click="handleResendOtp" />
                    </div>
                </div>
            </template>
        </Card>
    </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { verifyOtp, generateOtp } from '../services/authService'

const route = useRoute()
const router = useRouter()

const email = computed(() => route.query.email || '')
const mockOtp = ref(route.query.mockOtp || '')
const otp = ref('')
const errorMessage = ref('')

const handleVerifyOtp = () => {
    errorMessage.value = ''

    const result = verifyOtp(email.value, otp.value)

    if (!result.ok) {
        errorMessage.value = result.message
        return
    }

    router.push('/')
}

const handleResendOtp = () => {
    const result = generateOtp(email.value)
    if (result.ok) {
        mockOtp.value = result.otp
        errorMessage.value = ''
    }
}
</script>