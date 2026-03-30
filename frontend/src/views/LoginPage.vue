<template>
    <div class="auth-page">
        <Card class="auth-card">
            <template #title>
                <div class="auth-title">Login</div>
            </template>

            <template #content>
                <div class="auth-form">
                    <div class="form-field">
                        <label>Email</label>
                        <InputText v-model="email" placeholder="Enter your email" />
                    </div>

                    <div class="form-field">
                        <label>Password</label>
                        <Password v-model="password" placeholder="Enter your password" :feedback="false" toggleMask
                            fluid />
                    </div>

                    <Message v-if="errorMessage" severity="error">{{
                        errorMessage
                        }}</Message>
                    <Message v-if="infoMessage" severity="info">{{
                        infoMessage
                        }}</Message>

                    <Button label="Login" icon="pi pi-sign-in" @click="handleLogin" />

                    <div class="mock-note">
                        <p><strong>Mock users:</strong></p>
                        <p>user1@company.com → first login, no password</p>
                        <p>admin@company.com / Admin123!</p>
                        <p>superadmin@company.com / Super123!</p>
                    </div>
                </div>
            </template>
        </Card>
    </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { loginWithPassword, generateOtp } from "../services/authService";

const router = useRouter();

const email = ref("");
const password = ref("");
const errorMessage = ref("");
const infoMessage = ref("");

const handleLogin = () => {
    errorMessage.value = "";
    infoMessage.value = "";

    const result = loginWithPassword(email.value, password.value);

    if (!result.ok) {
        if (result.code === "PASSWORD_NOT_SET") {
            router.push({
                path: "/set-password",
                query: { email: email.value },
            });
            return;
        }

        errorMessage.value = result.message;
        return;
    }

    const otpResult = generateOtp(email.value);

    if (!otpResult.ok) {
        errorMessage.value = otpResult.message;
        return;
    }

    router.push({
        path: "/otp",
        query: {
            email: email.value,
            mockOtp: otpResult.otp,
        },
    });
};
</script>