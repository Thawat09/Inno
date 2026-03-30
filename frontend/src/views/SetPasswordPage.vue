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
                        <Password v-model="password" :feedback="false" toggleMask placeholder="Enter new password"
                            fluid />
                    </div>

                    <div class="form-field">
                        <label>Confirm Password</label>
                        <Password v-model="confirmPassword" :feedback="false" toggleMask placeholder="Confirm password"
                            fluid />
                    </div>

                    <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

                    <Button label="Save Password" icon="pi pi-check" @click="handleSavePassword" />
                </div>
            </template>
        </Card>
    </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { setFirstPassword, generateOtp } from '../services/authService'

const route = useRoute()
const router = useRouter()

const email = computed(() => route.query.email || '')

const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')

const handleSavePassword = () => {
    errorMessage.value = ''

    if (!password.value || !confirmPassword.value) {
        errorMessage.value = 'กรุณากรอกรหัสผ่านให้ครบ'
        return
    }

    if (password.value.length < 6) {
        errorMessage.value = 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร'
        return
    }

    if (password.value !== confirmPassword.value) {
        errorMessage.value = 'Password และ Confirm Password ไม่ตรงกัน'
        return
    }

    const result = setFirstPassword(email.value, password.value)

    if (!result.ok) {
        errorMessage.value = result.message
        return
    }

    const otpResult = generateOtp(email.value)

    router.push({
        path: '/otp',
        query: {
            email: email.value,
            mockOtp: otpResult.otp
        }
    })
}
</script>