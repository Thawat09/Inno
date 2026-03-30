<template>
    <header class="layout-topbar">
        <div class="topbar-left">
            <Button icon="pi pi-bars" text rounded class="topbar-menu-button" @click="$emit('toggle-sidebar')" />

            <div class="topbar-logo">
                <div class="logo-icon">
                    <i class="pi pi-circle-fill"></i>
                </div>
                <span>INETMS</span>
            </div>
        </div>

        <div class="topbar-center">
            <div class="topbar-search">
                <i class="pi pi-search topbar-search-icon"></i>
                <InputText v-model="searchKeyword" placeholder="Search tickets, email, team, IP..."
                    @keyup.enter="handleSearch" />
            </div>
        </div>

        <div class="topbar-right">
            <Button :icon="isDark ? 'pi pi-moon' : 'pi pi-sun'" text rounded class="topbar-icon-btn"
                @click="handleToggleTheme" />

            <div class="topbar-overlay-wrapper">
                <Button icon="pi pi-bell" text rounded class="topbar-icon-btn" @click="toggleNotifications" />
                <Badge v-if="notifications.length" :value="notifications.length > 9 ? '9+' : notifications.length"
                    class="topbar-badge" />

                <div v-if="showNotifications" class="topbar-overlay-panel notification-panel">
                    <div class="overlay-panel-header">
                        <span>Notifications</span>
                        <Button icon="pi pi-times" text rounded class="topbar-icon-btn small-btn"
                            @click="showNotifications = false" />
                    </div>

                    <div class="overlay-panel-body">
                        <div v-for="item in notifications.slice(0, 10)" :key="item.id" class="notification-item"
                            @click="openNotification(item)">
                            <div class="notification-title">{{ item.title }}</div>
                            <div class="notification-desc">{{ item.message }}</div>
                            <div class="notification-time">{{ item.time }}</div>
                        </div>

                        <div v-if="notifications.length === 0" class="overlay-empty">
                            No notifications
                        </div>
                    </div>
                </div>
            </div>

            <Button icon="pi pi-comments" text rounded class="topbar-icon-btn" @click="toggleAiChat" />

            <div class="topbar-overlay-wrapper">
                <Button icon="pi pi-user" text rounded class="topbar-icon-btn" @click="toggleAccountMenu" />

                <div v-if="showAccountMenu" class="topbar-overlay-panel account-panel">
                    <div class="account-panel-user">
                        <div class="account-name">{{ currentUser?.name || 'Guest' }}</div>
                        <div class="account-role">{{ currentUser?.role || '-' }}</div>
                    </div>

                    <button class="account-menu-item" @click="goToProfile">
                        <i class="pi pi-user"></i>
                        <span>My Profile</span>
                    </button>

                    <button class="account-menu-item" @click="goToChangePassword">
                        <i class="pi pi-key"></i>
                        <span>Change Password</span>
                    </button>

                    <button class="account-menu-item danger" @click="handleLogout">
                        <i class="pi pi-sign-out"></i>
                        <span>Logout</span>
                    </button>
                </div>
            </div>
        </div>

        <AiQuickChat :visible="showAiChat" @update:visible="showAiChat = $event" />
    </header>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser, logout } from '../services/authService'
import { getSavedTheme, toggleTheme } from '../utils/theme'
import AiQuickChat from './AiQuickChat.vue'

defineEmits(['toggle-sidebar'])

const router = useRouter()
const currentUser = getCurrentUser()

const isDark = ref(false)
const searchKeyword = ref('')
const showNotifications = ref(false)
const showAccountMenu = ref(false)
const showAiChat = ref(false)

const notifications = ref([
    { id: 1, title: 'New Ticket', message: 'INC000123 assigned to AWS team', time: '1 min ago', route: '/tickets' },
    { id: 2, title: 'Escalated', message: 'Ticket escalated to Tier 2', time: '5 mins ago', route: '/acceptance-monitor' },
    { id: 3, title: 'Leave Request', message: 'John marked leave for today', time: '10 mins ago', route: '/leave' },
    { id: 4, title: 'Account Locked', message: 'User account locked after 3 failed attempts', time: '15 mins ago', route: '/locked-users' },
    { id: 5, title: 'LINE Event', message: 'New member joined LINE group', time: '22 mins ago', route: '/line-monitor' },
    { id: 6, title: 'Manual Override', message: 'Admin changed ticket owner', time: '30 mins ago', route: '/manual-override' },
    { id: 7, title: 'AI Audit', message: 'New AI conversation logged', time: '40 mins ago', route: '/ai-audit' },
    { id: 8, title: 'SLA Warning', message: 'Ticket nearing response timeout', time: '1 hour ago', route: '/reports' },
    { id: 9, title: 'Calendar Update', message: 'Standby shift updated', time: '2 hours ago', route: '/calendar-management' },
    { id: 10, title: 'Data Mapping', message: 'Unmapped LINE user detected', time: '3 hours ago', route: '/data-mapping' }
])

onMounted(() => {
    isDark.value = getSavedTheme() === 'dark'
    document.addEventListener('click', handleOutsideClick)
})

onBeforeUnmount(() => {
    document.removeEventListener('click', handleOutsideClick)
})

const handleToggleTheme = () => {
    const nextTheme = toggleTheme()
    isDark.value = nextTheme === 'dark'
}

const handleSearch = () => {
    const keyword = searchKeyword.value.trim()
    if (!keyword) return

    router.push({
        path: '/search',
        query: { q: keyword }
    })
}

const toggleNotifications = (event) => {
    event.stopPropagation()
    showNotifications.value = !showNotifications.value
    showAccountMenu.value = false
}

const toggleAccountMenu = (event) => {
    event.stopPropagation()
    showAccountMenu.value = !showAccountMenu.value
    showNotifications.value = false
}

const toggleAiChat = () => {
    showAiChat.value = !showAiChat.value
    showNotifications.value = false
    showAccountMenu.value = false
}

const openNotification = (item) => {
    showNotifications.value = false
    if (item.route) {
        router.push(item.route)
    }
}

const goToProfile = () => {
    showAccountMenu.value = false
    router.push('/profile')
}

const goToChangePassword = () => {
    showAccountMenu.value = false
    router.push('/reset-password')
}

const handleLogout = () => {
    logout()
    showAccountMenu.value = false
    router.push('/login')
}

const handleOutsideClick = (event) => {
    const target = event.target

    if (!target.closest('.topbar-overlay-wrapper')) {
        showNotifications.value = false
        showAccountMenu.value = false
    }
}
</script>