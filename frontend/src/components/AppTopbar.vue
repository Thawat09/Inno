<template>
    <header class="layout-topbar">
        <div class="topbar-left">
            <Button
                icon="pi pi-bars"
                text
                rounded
                class="topbar-menu-button"
                @click="$emit('toggle-sidebar')"
            />

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
                <InputText
                    v-model="searchKeyword"
                    placeholder="Search tickets, email, team, IP..."
                    @keyup.enter="handleSearch"
                />
            </div>
        </div>

        <div class="topbar-right">
            <Button
                :icon="isDark ? 'pi pi-moon' : 'pi pi-sun'"
                text
                rounded
                class="topbar-icon-btn"
                @click="handleToggleTheme"
            />

            <div class="topbar-overlay-wrapper">
                <Button
                    icon="pi pi-bell"
                    text
                    rounded
                    class="topbar-icon-btn"
                    @click="toggleNotifications"
                />
                <Badge
                    v-if="unreadCount"
                    :value="unreadCount > 9 ? '9+' : unreadCount"
                    class="topbar-badge"
                />

                <div v-if="showNotifications" class="topbar-overlay-panel notification-panel">
                    <div class="overlay-panel-header">
                        <span>Notifications</span>

                        <div class="overlay-panel-actions">
                            <Button
                                label="View All"
                                text
                                class="header-text-btn"
                                @click="goToNotificationsPage"
                            />
                            <Button
                                icon="pi pi-times"
                                text
                                rounded
                                class="topbar-icon-btn small-btn"
                                @click="showNotifications = false"
                            />
                        </div>
                    </div>

                    <div class="overlay-panel-body">
                        <div
                            v-for="item in topNotifications"
                            :key="item.id"
                            class="notification-item"
                            :class="{ 'notification-item-unread': !item.is_read }"
                            @click="openNotification(item)"
                        >
                            <div class="notification-title-row">
                                <div class="notification-title">
                                    {{ item.title }}
                                </div>
                                <span
                                    v-if="!item.is_read"
                                    class="mini-unread-dot"
                                ></span>
                            </div>

                            <div class="notification-desc">{{ item.message }}</div>
                            <div class="notification-time">{{ item.time }}</div>
                        </div>

                        <div v-if="notifications.length === 0" class="overlay-empty">
                            No notifications
                        </div>
                    </div>

                    <div v-if="notifications.length" class="overlay-panel-footer">
                        <Button
                            label="Mark All as Read"
                            text
                            class="footer-text-btn"
                            @click="markAllNotificationsRead"
                        />
                    </div>
                </div>
            </div>

            <Button
                icon="pi pi-comments"
                text
                rounded
                class="topbar-icon-btn"
                @click="toggleAiChat"
            />

            <div class="topbar-overlay-wrapper">
                <Button
                    icon="pi pi-user"
                    text
                    rounded
                    class="topbar-icon-btn"
                    @click="toggleAccountMenu"
                />

                <div v-if="showAccountMenu" class="topbar-overlay-panel account-panel">
                    <div class="account-panel-user">
                        <div class="account-name">{{ displayName }}</div>
                        <div class="account-role">{{ displayRole }}</div>
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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser, logout } from '../services/authService'
import { getSavedTheme, toggleTheme } from '../utils/theme'
import AiQuickChat from './AiQuickChat.vue'

defineEmits(['toggle-sidebar'])

const router = useRouter()

const isDark = ref(false)
const searchKeyword = ref('')
const showNotifications = ref(false)
const showAccountMenu = ref(false)
const showAiChat = ref(false)
const currentUser = ref(null)

const notifications = ref([
    {
        id: 1,
        title: 'New Ticket',
        message: 'INC000123 assigned to AWS team',
        time: '1 min ago',
        route: '/tickets',
        is_read: false
    },
    {
        id: 2,
        title: 'Escalated',
        message: 'Ticket escalated to Tier 2',
        time: '5 mins ago',
        route: '/acceptance-monitor',
        is_read: false
    },
    {
        id: 3,
        title: 'Leave Request',
        message: 'John marked leave for today',
        time: '10 mins ago',
        route: '/leave',
        is_read: true
    },
    {
        id: 4,
        title: 'Account Locked',
        message: 'User account locked after 3 failed attempts',
        time: '15 mins ago',
        route: '/locked-users',
        is_read: false
    },
    {
        id: 5,
        title: 'LINE Event',
        message: 'New member joined LINE group',
        time: '22 mins ago',
        route: '/line-monitor',
        is_read: true
    },
    {
        id: 6,
        title: 'Manual Override',
        message: 'Admin changed ticket owner',
        time: '30 mins ago',
        route: '/manual-override',
        is_read: false
    },
    {
        id: 7,
        title: 'AI Audit',
        message: 'New AI conversation logged',
        time: '40 mins ago',
        route: '/ai-audit',
        is_read: true
    },
    {
        id: 8,
        title: 'SLA Warning',
        message: 'Ticket nearing response timeout',
        time: '1 hour ago',
        route: '/reports',
        is_read: false
    },
    {
        id: 9,
        title: 'Calendar Update',
        message: 'Standby shift updated',
        time: '2 hours ago',
        route: '/calendar-management',
        is_read: true
    },
    {
        id: 10,
        title: 'Data Mapping',
        message: 'Unmapped LINE user detected',
        time: '3 hours ago',
        route: '/data-mapping',
        is_read: false
    }
])

const topNotifications = computed(() => notifications.value.slice(0, 10))
const unreadCount = computed(() => notifications.value.filter(item => !item.is_read).length)

const displayName = computed(() => {
    const user = currentUser.value
    if (!user) return 'Guest'

    const first = user.first_name?.trim() || ''
    const last = user.last_name?.trim() || ''
    const fullName = [first, last].filter(Boolean).join(' ').trim()

    return fullName || user.name || user.email || 'Guest'
})

const displayRole = computed(() => {
    const user = currentUser.value
    return user?.role_name || user?.role || '-'
})

onMounted(() => {
    isDark.value = getSavedTheme() === 'dark'
    currentUser.value = getCurrentUser()
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

    closeAllPanels()

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

const markNotificationAsRead = (id) => {
    const target = notifications.value.find(item => item.id === id)
    if (!target) return
    target.is_read = true
}

const markAllNotificationsRead = () => {
    notifications.value = notifications.value.map(item => ({
        ...item,
        is_read: true
    }))
}

const openNotification = (item) => {
    markNotificationAsRead(item.id)
    showNotifications.value = false

    if (item.route) {
        router.push(item.route)
    }
}

const goToNotificationsPage = () => {
    closeAllPanels()
    router.push('/notifications')
}

const goToProfile = () => {
    closeAllPanels()
    router.push('/profile')
}

const goToChangePassword = () => {
    closeAllPanels()
    router.push('/change-password')
}

const handleLogout = () => {
    logout()
    closeAllPanels()
    router.push('/login')
}

const closeAllPanels = () => {
    showNotifications.value = false
    showAccountMenu.value = false
}

const handleOutsideClick = (event) => {
    const target = event.target

    if (!target.closest('.topbar-overlay-wrapper')) {
        closeAllPanels()
    }
}
</script>

<style scoped>
.overlay-panel-actions {
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.header-text-btn,
.footer-text-btn {
    padding: 0.25rem 0.5rem !important;
}

.overlay-panel-footer {
    padding: 0.75rem 1rem;
    border-top: 1px solid #e5e7eb;
    display: flex;
    justify-content: center;
}

.notification-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
}

.notification-item-unread {
    background: #f0fdf4;
}

.mini-unread-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: #10b981;
    flex-shrink: 0;
}
</style>