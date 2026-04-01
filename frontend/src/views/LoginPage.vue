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
                        <InputText
                            v-model="email"
                            type="email"
                            placeholder="Enter your email"
                            autocomplete="username"
                        />
                    </div>

                    <div class="form-field">
                        <label>Password</label>
                        <Password
                            v-model="password"
                            placeholder="Enter your password"
                            :feedback="false"
                            toggleMask
                            fluid
                            autocomplete="current-password"
                        />
                    </div>
                    
                    <div class="form-field">
                        <div class="forgot-password">
                            <a @click.prevent="goToResetPassword">Forgot password?</a>
                        </div>
                    </div>

                    <Message v-if="errorMessage" severity="error">
                        {{ errorMessage }}
                    </Message>

                    <Message v-if="infoMessage" severity="info">
                        {{ infoMessage }}
                    </Message>

                    <Button
                        label="Login"
                        icon="pi pi-sign-in"
                        :loading="isLoading"
                        :disabled="!canSubmit"
                        @click="handleLogin"
                    />

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
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { loginWithPassword, generateOtp } from "../services/authService";

const router = useRouter();

const email = ref("");
const password = ref("");
const errorMessage = ref("");
const infoMessage = ref("");
const isLoading = ref(false);

const GENERIC_LOGIN_ERROR = "Invalid email or password";
const LOCKED_ERROR =
    "This account has been locked due to multiple failed login attempts. Please contact administrator.";
const GENERIC_PROCESS_ERROR = "Unable to process login. Please try again.";

const canSubmit = computed(() => {
    return !!email.value.trim() && !!password.value;
});

const goToResetPassword = () => {
    router.push('/reset-password')
}

const handleLogin = async () => {
    errorMessage.value = "";
    infoMessage.value = "";

    if (!canSubmit.value) {
        errorMessage.value = "Please enter email and password";
        return;
    }

    isLoading.value = true;

    try {
        await new Promise((resolve) => setTimeout(resolve, 500));

        const result = loginWithPassword(email.value.trim(), password.value);

        if (!result.ok) {
            // first login flow
            if (result.code === "PASSWORD_NOT_SET") {
                router.push({
                    path: "/set-password",
                    query: { email: email.value.trim() },
                });
                return;
            }

            // reveal only locked state for existing user
            if (result.code === "LOCKED") {
                errorMessage.value = LOCKED_ERROR;
                return;
            }

            // generic for user not found / invalid password
            errorMessage.value = GENERIC_LOGIN_ERROR;
            return;
        }

        const otpResult = generateOtp(email.value.trim());

        if (!otpResult.ok) {
            errorMessage.value = GENERIC_PROCESS_ERROR;
            return;
        }

        infoMessage.value = "Login successful. Redirecting to OTP verification...";

        router.push({
            path: "/otp",
            query: {
                email: email.value.trim(),
                mockOtp: otpResult.otp,
            },
        });
    } catch (error) {
        console.error(error);
        errorMessage.value = GENERIC_PROCESS_ERROR;
    } finally {
        isLoading.value = false;
    }
};
</script>

<style scoped>
.forgot-password {
    margin-top: 0.35rem;
    text-align: center;
    font-size: 0.85rem;
}

.forgot-password a {
    color: var(--primary-color);
    cursor: pointer;
    text-decoration: none;
}

.forgot-password a:hover {
    text-decoration: underline;
}
</style>