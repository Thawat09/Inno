import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../services/authService'

import AppLayout from '@/layouts/AppLayout.vue'

// Auth pages
import LoginPage from '@/views/LoginPage.vue'
import SetPasswordPage from '@/views/SetPasswordPage.vue'
import OtpPage from '@/views/OtpPage.vue'
import ResetPasswordPage from '@/views/ResetPasswordPage.vue'

// Main pages
import Dashboard from '@/views/Dashboard.vue'
import ChangePasswordPage from '@/views/ChangePasswordPage.vue'

// Ticket pages
import TicketsPage from '@/views/TicketsPage.vue'
import TicketDetailPage from '@/views/TicketDetailPage.vue'
import AcceptanceMonitorPage from '@/views/AcceptanceMonitorPage.vue'
import ManualOverridePage from '@/views/ManualOverridePage.vue'

// Standby pages
import StandbyCalendarPage from '@/views/StandbyCalendarPage.vue'
import CalendarManagementPage from '@/views/CalendarManagementPage.vue'
import LeaveAvailabilityPage from '@/views/LeaveAvailabilityPage.vue'
import EscalationRulePage from '@/views/EscalationRulePage.vue'

// User pages
import TeamsMembersPage from '@/views/TeamsMembersPage.vue'
import MyProfilePage from '@/views/MyProfilePage.vue'
import UserManagementPage from '@/views/UserManagementPage.vue'
import LockedUsersPage from '@/views/LockedUsersPage.vue'

// LINE & Alert pages
import NotificationsPage from '@/views/NotificationsPage.vue'
import LineMonitoringPage from '@/views/LineMonitoringPage.vue'

// Reports pages
import ReportsSlaPage from '@/views/ReportsSlaPage.vue'
import AuditLogPage from '@/views/AuditLogPage.vue'
import AIAuditPage from '@/views/AIAuditPage.vue'

// AI page
import AIAssistantPage from '@/views/AIAssistantPage.vue'

// Tools pages
import DataMappingPage from '@/views/DataMappingPage.vue'
import GlobalSearchPage from '@/views/GlobalSearchPage.vue'

const routes = [
    // Auth group - outside AppLayout
    {
        path: '/login',
        name: 'login',
        component: LoginPage
    },
    {
        path: '/set-password',
        name: 'set-password',
        component: SetPasswordPage
    },
    {
        path: '/otp',
        name: 'otp',
        component: OtpPage
    },
    {
        path: '/reset-password',
        name: 'reset-password',
        component: ResetPasswordPage
    },

    // Main system - inside AppLayout
    {
        path: '/',
        component: AppLayout,
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                name: 'dashboard',
                component: Dashboard
            },

            // Account
            {
                path: 'change-password',
                name: 'change-password',
                component: ChangePasswordPage
            },

            // Tickets
            {
                path: 'tickets',
                name: 'tickets',
                component: TicketsPage
            },
            {
                path: 'ticket-detail',
                name: 'ticket-detail',
                component: TicketDetailPage
            },
            {
                path: 'acceptance-monitor',
                name: 'acceptance-monitor',
                component: AcceptanceMonitorPage
            },
            {
                path: 'manual-override',
                name: 'manual-override',
                component: ManualOverridePage
            },

            // Standby
            {
                path: 'calendar',
                name: 'calendar',
                component: StandbyCalendarPage
            },
            {
                path: 'calendar-management',
                name: 'calendar-management',
                component: CalendarManagementPage
            },
            {
                path: 'leave',
                name: 'leave',
                component: LeaveAvailabilityPage
            },
            {
                path: 'escalation-rule',
                name: 'escalation-rule',
                component: EscalationRulePage
            },

            // Users
            {
                path: 'teams',
                name: 'teams',
                component: TeamsMembersPage
            },
            {
                path: 'profile',
                name: 'profile',
                component: MyProfilePage
            },
            {
                path: 'users',
                name: 'users',
                component: UserManagementPage
            },
            {
                path: 'locked-users',
                name: 'locked-users',
                component: LockedUsersPage
            },

            // LINE & Alert
            {
                path: 'notifications',
                name: 'notifications',
                component: NotificationsPage
            },
            {
                path: 'line-monitor',
                name: 'line-monitor',
                component: LineMonitoringPage
            },

            // Reports
            {
                path: 'reports',
                name: 'reports',
                component: ReportsSlaPage
            },
            {
                path: 'audit-log',
                name: 'audit-log',
                component: AuditLogPage
            },
            {
                path: 'ai-audit',
                name: 'ai-audit',
                component: AIAuditPage
            },

            // AI
            {
                path: 'ai',
                name: 'ai',
                component: AIAssistantPage
            },

            // Tools
            {
                path: 'data-mapping',
                name: 'data-mapping',
                component: DataMappingPage
            },
            {
                path: 'search',
                name: 'search',
                component: GlobalSearchPage
            }
        ]
    },

    // fallback
    {
        path: '/:pathMatch(.*)*',
        redirect: '/'
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const authed = isAuthenticated()

    if (to.meta.requiresAuth && !authed) {
        next('/login')
        return
    }

    // only true auth pages should redirect when already logged in
    if (
        (to.path === '/login' ||
            to.path === '/set-password' ||
            to.path === '/otp') &&
        authed
    ) {
        next('/')
        return
    }

    next()
})

export default router